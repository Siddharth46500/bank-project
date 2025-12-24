import mysql.connector as mycon
import time
from cryptography.fernet import Fernet  # Fixed: Changed from Fermat to Fernet
import calendar
import datetime
import hashlib
import json
from flask import Flask, jsonify

# Generate a key for encryption (in production, store this securely)
try:
    with open("secret.key", "rb") as key_file:
        key = key_file.read()
except FileNotFoundError:
    key = Fernet.generate_key()  # Fixed: Changed from Fermat to Fernet
    with open("secret.key", "wb") as key_file:  # Fixed: Changed 'mb' to 'wb'
        key_file.write(key)

cipher_suite = Fernet(key)  # Fixed: Changed from Fermat to Fernet


class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []  # Initialize pending_transactions FIRST
        self.create_block(proof=1, previous_hash='0')  # Then create the first block

    def create_block(self, proof, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.datetime.now()),
            'proof': proof,
            'previous_hash': previous_hash,
            'transactions': self.pending_transactions.copy()  # Now this will work
        }
        self.chain.append(block)
        self.pending_transactions = []  # Clear pending transactions
        return block

    def add_transaction(self, from_acc, to_acc, amount, remark):
        """Add a transaction to pending transactions"""
        encrypted_remark = cipher_suite.encrypt(remark.encode()).decode()

        transaction = {
            'from': from_acc,
            'to': to_acc,
            'amount': amount,
            'timestamp': str(datetime.datetime.now()),
            'remark_encrypted': encrypted_remark,
            'remark_decrypted': remark  # Store decrypted version temporarily
        }
        self.pending_transactions.append(transaction)
        return len(self.chain) + 1  # Return index of block that will contain this transaction

    def print_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False

        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof ** 2 - previous_proof ** 2).encode()).hexdigest()
            if hash_operation[:5] == '00000':
                check_proof = True
            else:
                new_proof += 1

        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1

        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False

            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof ** 2 - previous_proof ** 2).encode()).hexdigest()

            if hash_operation[:5] != '00000':
                return False
            previous_block = block
            block_index += 1

        return True

    def get_transaction_history(self, account_no):
        """Get all transactions for a specific account"""
        history = []
        for block in self.chain:
            for transaction in block.get('transactions', []):
                if transaction['from'] == account_no or transaction['to'] == account_no:
                    # Decrypt the remark for display
                    try:
                        decrypted_remark = cipher_suite.decrypt(
                            transaction['remark_encrypted'].encode()).decode()
                    except:
                        decrypted_remark = "Decryption failed"

                    history.append({
                        'block_index': block['index'],
                        'timestamp': transaction['timestamp'],
                        'from': transaction['from'],
                        'to': transaction['to'],
                        'amount': transaction['amount'],
                        'remark': decrypted_remark,
                        'block_hash': self.hash(block)
                    })
        return history


# Create blockchain instance
blockchain = Blockchain()

# Create Flask app for blockchain endpoints
app = Flask(__name__)


# Blockchain API endpoints
@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block = blockchain.print_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)

    response = {
        'message': 'A block is MINED',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        'transactions': len(block['transactions'])
    }
    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def display_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/valid', methods=['GET'])
def valid():
    valid = blockchain.chain_valid(blockchain.chain)
    if valid:
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200


# Database connection
def get_connection():
    return mycon.connect(
        host="localhost",
        user="root",
        passwd="skgamer465",
        database="bank"
    )


# Initialize database
def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    # Create ACCOUNTS table if not exists
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS ACCOUNTS
                   (
                       account_no
                       INT
                       AUTO_INCREMENT
                       PRIMARY
                       KEY,
                       name
                       VARCHAR
                   (
                       100
                   ) NOT NULL,
                       phone_num VARCHAR
                   (
                       15
                   ) NOT NULL,
                       pin INT NOT NULL,
                       balance DECIMAL
                   (
                       15,
                       2
                   ) DEFAULT 0.00,
                       account_type VARCHAR
                   (
                       20
                   ) NOT NULL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                   """)

    # Create TRANSACTION_HISTORY table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS TRANSACTION_HISTORY
                   (
                       id
                       INT
                       AUTO_INCREMENT
                       PRIMARY
                       KEY,
                       from_account
                       INT
                       NOT
                       NULL,
                       to_account
                       INT
                       NOT
                       NULL,
                       amount
                       DECIMAL
                   (
                       15,
                       2
                   ) NOT NULL,
                       remark_encrypted TEXT NOT NULL,
                       transaction_date DATE NOT NULL,
                       transaction_time TIME NOT NULL,
                       block_index INT,
                       FOREIGN KEY
                   (
                       from_account
                   ) REFERENCES ACCOUNTS
                   (
                       account_no
                   ),
                       FOREIGN KEY
                   (
                       to_account
                   ) REFERENCES ACCOUNTS
                   (
                       account_no
                   )
                       )
                   """)

    connection.commit()
    cursor.close()
    connection.close()


def account_open(name, phone_no, pin, balance, account_type):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            INSERT INTO ACCOUNTS(name, phone_num, pin, balance, account_type)
            VALUES (%s, %s, %s, %s, %s) \
            """
    values = (name, phone_no, pin, balance, account_type)

    try:
        cursor.execute(query, values)
        account_no = cursor.lastrowid
        connection.commit()
        print(f"Account created successfully! Account Number: {account_no}")
    except Exception as exception:
        print(f"Error creating account: {exception}")
        account_no = None
    finally:
        cursor.close()
        connection.close()

    return account_no


def fetch_balance(account_num):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else 0


def fetch_name(account_num):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None


def fetch_account_type(account_num):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT account_type FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None


def fetch_phone_no(account_num):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT phone_num FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None


def fetch_pin(account_num):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT pin FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None


def save_transaction_to_db(from_acc, to_acc, amount, remark, block_index=None):
    """Save transaction to MySQL database"""
    connection = get_connection()
    cursor = connection.cursor()

    # Encrypt remark
    encrypted_remark = cipher_suite.encrypt(remark.encode()).decode()

    query = """
            INSERT INTO TRANSACTION_HISTORY
            (from_account, to_account, amount, remark_encrypted, transaction_date, transaction_time, block_index)
            VALUES (%s, %s, %s, %s, CURDATE(), CURTIME(), %s) \
            """
    values = (from_acc, to_acc, amount, encrypted_remark, block_index)

    try:
        cursor.execute(query, values)
        connection.commit()
    except Exception as e:
        print(f"Error saving transaction to database: {e}")
    finally:
        cursor.close()
        connection.close()


def transfer_money(from_acc, to_acc, amount, remark="Transfer"):
    """Transfer money between accounts using blockchain"""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check if both accounts exist
        cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s", (from_acc,))
        from_result = cursor.fetchone()

        cursor.execute("SELECT account_no FROM ACCOUNTS WHERE account_no = %s", (to_acc,))
        to_result = cursor.fetchone()

        if not from_result:
            print("From account does not exist!")
            return False

        if not to_result:
            print("To account does not exist!")
            return False

        from_acc_balance = from_result[0]

        if from_acc_balance >= amount:
            # Update balances
            new_from_balance = from_acc_balance - amount

            cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s", (to_acc,))
            to_acc_balance = cursor.fetchone()[0]
            new_to_balance = to_acc_balance + amount

            # Update accounts
            cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                           (new_from_balance, from_acc))
            cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                           (new_to_balance, to_acc))

            # Add transaction to blockchain
            transaction_index = blockchain.add_transaction(from_acc, to_acc, amount, remark)

            # Save to database
            save_transaction_to_db(from_acc, to_acc, amount, remark, transaction_index)

            connection.commit()
            print("Transfer successful!")

            # Mine a block after every transaction
            print("Mining block with transactions...")
            previous_block = blockchain.print_previous_block()
            previous_proof = previous_block['proof']
            proof = blockchain.proof_of_work(previous_proof)
            previous_hash = blockchain.hash(previous_block)
            blockchain.create_block(proof, previous_hash)
            print("Block mined successfully!")

            return True
        else:
            print("Insufficient balance in the from account.")
            return False

    except Exception as e:
        print(f"Error during transfer: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()
        connection.close()


def get_transaction_history(account_no):
    """Get transaction history from blockchain"""
    print("\n=== Blockchain Transaction History ===")
    history = blockchain.get_transaction_history(account_no)

    if not history:
        print("No transactions found in blockchain.")
        return

    for i, transaction in enumerate(history, 1):
        print(f"\nTransaction {i}:")
        print(f"  Block #{transaction['block_index']}")
        print(f"  Date/Time: {transaction['timestamp']}")
        print(f"  From: {transaction['from']}")
        print(f"  To: {transaction['to']}")
        print(f"  Amount: ₹{transaction['amount']}")
        print(f"  Remark: {transaction['remark']}")
        print(f"  Block Hash: {transaction['block_hash'][:20]}...")

    # Also show database history
    print("\n=== Database Transaction History ===")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            SELECT th.transaction_date, \
                   th.transaction_time, \
                   th.from_account,
                   th.to_account, \
                   th.amount, \
                   th.remark_encrypted, \
                   th.block_index
            FROM TRANSACTION_HISTORY th
            WHERE th.from_account = %s \
               OR th.to_account = %s
            ORDER BY th.transaction_date DESC, th.transaction_time DESC LIMIT 10 \
            """

    cursor.execute(query, (account_no, account_no))
    db_transactions = cursor.fetchall()

    if not db_transactions:
        print("No transactions found in database.")
    else:
        for trans in db_transactions:
            try:
                decrypted_remark = cipher_suite.decrypt(trans[5].encode()).decode()
            except:
                decrypted_remark = "Decryption failed"

            print(f"\nDate: {trans[0]} Time: {trans[1]}")
            print(f"From: {trans[2]} To: {trans[3]} Amount: ₹{trans[4]}")
            print(f"Remark: {decrypted_remark}")
            print(f"Block Index: {trans[6] if trans[6] else 'Pending'}")

    cursor.close()
    connection.close()


def login(account_no, pin):
    print("\nWelcome to login page")

    while True:
        print("\n1. Check account details")
        print("2. Transfer money")
        print("3. Change PIN")
        print("4. Update personal info")
        print("5. Check transaction history")
        print("6. View blockchain info")
        print("7. Logout")

        try:
            choice = int(input("ENTER YOUR CHOICE: "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice == 1:
            name = fetch_name(account_no)
            balance = fetch_balance(account_no)
            account_type = fetch_account_type(account_no)
            phone_no = fetch_phone_no(account_no)

            print("\nFetching account details...")
            time.sleep(1)
            print("Account details fetched successfully!")
            print("\nACCOUNT DETAILS:")
            print("-----------------")
            print(f"Account Number: {account_no}")
            print(f"Name: {name}")
            print(f"Phone Number: {phone_no}")
            print(f"Account Type: {account_type}")
            print(f"Balance: ₹{balance}")

        elif choice == 2:
            try:
                to_acc = int(input("ENTER THE ACCOUNT NUMBER TO TRANSFER MONEY: "))
                amount = float(input("ENTER THE AMOUNT TO TRANSFER: "))
                remark = input("ENTER REMARK FOR TRANSACTION: ")

                if amount <= 0:
                    print("Amount must be positive!")
                    continue

                if to_acc == account_no:
                    print("Cannot transfer to yourself!")
                    continue

                success = transfer_money(account_no, to_acc, amount, remark)
                if success:
                    print("TRANSFER COMPLETE!")

            except ValueError:
                print("Invalid input!")

        elif choice == 3:
            try:
                new_pin = int(input("ENTER YOUR NEW PIN (4-6 digits): "))
                if len(str(new_pin)) < 4 or len(str(new_pin)) > 6:
                    print("PIN must be 4-6 digits!")
                    continue

                connection = get_connection()
                cursor = connection.cursor()
                cursor.execute("UPDATE ACCOUNTS SET PIN = %s WHERE account_no = %s",
                               (new_pin, account_no))
                connection.commit()
                cursor.close()
                connection.close()
                print("PIN CHANGED SUCCESSFULLY!")

            except ValueError:
                print("Invalid PIN format!")

        elif choice == 4:
            update_choice = input("DO YOU WANT TO UPDATE YOUR PERSONAL INFO (Y/N): ")
            if update_choice.upper() == 'Y':
                new_phone_no = input("ENTER YOUR NEW PHONE NUMBER: ")
                new_name = input("ENTER YOUR NEW NAME: ")

                connection = get_connection()
                cursor = connection.cursor()

                try:
                    cursor.execute("UPDATE ACCOUNTS SET phone_num = %s WHERE account_no = %s",
                                   (new_phone_no, account_no))
                    cursor.execute("UPDATE ACCOUNTS SET name = %s WHERE account_no = %s",
                                   (new_name, account_no))
                    connection.commit()
                    print("PERSONAL INFO UPDATED SUCCESSFULLY!")
                except Exception as e:
                    print(f"Error updating info: {e}")
                finally:
                    cursor.close()
                    connection.close()

        elif choice == 5:
            get_transaction_history(account_no)

        elif choice == 6:
            print("\n=== Blockchain Information ===")
            print(f"Total Blocks: {len(blockchain.chain)}")
            print(f"Pending Transactions: {len(blockchain.pending_transactions)}")
            print(f"Chain Valid: {blockchain.chain_valid(blockchain.chain)}")

            view_chain = input("View full chain? (Y/N): ")
            if view_chain.upper() == 'Y':
                print("\nBlockchain:")
                for i, block in enumerate(blockchain.chain):
                    print(f"\nBlock {i + 1}:")
                    print(f"  Hash: {blockchain.hash(block)[:20]}...")
                    print(f"  Transactions: {len(block.get('transactions', []))}")
                    print(f"  Timestamp: {block['timestamp']}")

        elif choice == 7:
            print("LOGGING OUT...")
            time.sleep(1)
            print("LOGGED OUT SUCCESSFULLY!")
            break

        else:
            print("INVALID CHOICE!")


def main():
    # Initialize database
    init_database()

    print("Initializing blockchain...")
    time.sleep(1)

    while True:
        print("\n" + "=" * 50)
        print("WELCOME TO BANK MANAGEMENT SYSTEM WITH BLOCKCHAIN")
        print("=" * 50)
        time.sleep(0.5)

        print("\n1. OPEN ACCOUNT")
        print("2. LOGIN ACCOUNT")
        print("3. ABOUT")
        print("4. BLOCKCHAIN INFO")
        print("5. EXIT")

        try:
            choice = int(input("\nENTER YOUR CHOICE: "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice == 1:
            print("\n=== OPEN NEW ACCOUNT ===")
            name = input("ENTER YOUR NAME: ")
            phone_no = input("ENTER YOUR PHONE NUMBER: ")

            try:
                pin = int(input("ENTER YOUR PIN (4-6 digits): "))
                if len(str(pin)) < 4 or len(str(pin)) > 6:
                    print("PIN must be 4-6 digits!")
                    continue

                balance = float(input("ENTER INITIAL DEPOSIT AMOUNT: "))
                if balance < 0:
                    print("Balance cannot be negative!")
                    continue

                account_type = input("ENTER ACCOUNT TYPE (SAVINGS/CURRENT): ").upper()
                if account_type not in ['SAVINGS', 'CURRENT']:
                    print("Account type must be SAVINGS or CURRENT!")
                    continue

                account_no = account_open(name, phone_no, pin, balance, account_type)
                if account_no:
                    print(f"\nAccount opened successfully!")
                    print(f"Your account number is: {account_no}")
                    print("Please remember this number for future login.")

            except ValueError:
                print("Invalid input format!")

        elif choice == 2:
            print("\n=== LOGIN ===")
            try:
                account_no = int(input("ENTER YOUR ACCOUNT NUMBER: "))
                pin = int(input("ENTER YOUR PIN: "))

                stored_pin = fetch_pin(account_no)
                if stored_pin is None:
                    print("Account not found!")
                    continue

                if stored_pin == pin:
                    print("\nLogin successful!")
                    login(account_no, pin)
                else:
                    print("Invalid PIN!")

            except ValueError:
                print("Invalid input format!")

        elif choice == 3:
            print("\n" + "=" * 50)
            print("BANK MANAGEMENT SYSTEM WITH BLOCKCHAIN - VERSION 2.0")
            print("=" * 50)
            print("\nDeveloped by: SIDHARTH and RITESH")
            print("\nFeatures:")
            print("- Secure account management")
            print("- Blockchain-based transaction recording")
            print("- Encrypted transaction remarks")
            print("- Real-time balance tracking")
            print("- Transaction history with blockchain verification")
            time.sleep(3)

        elif choice == 4:
            print("\n=== BLOCKCHAIN INFORMATION ===")
            print(f"Total Blocks: {len(blockchain.chain)}")
            print(f"Pending Transactions: {len(blockchain.pending_transactions)}")
            print(f"Chain Valid: {blockchain.chain_valid(blockchain.chain)}")

            # Display some blockchain stats
            total_transactions = 0
            for block in blockchain.chain:
                total_transactions += len(block.get('transactions', []))

            print(f"Total Transactions in Blockchain: {total_transactions}")
            print(f"First Block Timestamp: {blockchain.chain[0]['timestamp']}")
            print(f"Last Block Timestamp: {blockchain.chain[-1]['timestamp']}")

            view_details = input("\nView blockchain details? (Y/N): ")
            if view_details.upper() == 'Y':
                print("\nBlockchain Structure:")
                for i, block in enumerate(blockchain.chain):
                    print(f"\nBlock #{i + 1}:")
                    print(f"  Hash: {blockchain.hash(block)[:30]}...")
                    print(f"  Previous Hash: {block['previous_hash'][:30]}...")
                    print(f"  Proof: {block['proof']}")
                    print(f"  Transactions: {len(block.get('transactions', []))}")

        elif choice == 5:
            print("\nEXITING...")
            time.sleep(1)
            print("THANK YOU FOR USING BANK MANAGEMENT SYSTEM!")
            print("GOODBYE!")
            break

        else:
            print("INVALID CHOICE! Please try again.")


def run_flask():
    """Run Flask server in a separate thread for blockchain API"""
    import threading
    flask_thread = threading.Thread(target=lambda: app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False
    ))
    flask_thread.daemon = True
    flask_thread.start()
    print("Blockchain API running at http://127.0.0.1:5000")


if __name__ == "__main__":
    # Start Flask server for blockchain API
    run_flask()
    time.sleep(1)


    # Run main application
    main()