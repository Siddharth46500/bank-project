import mysql.connector as mycon
import time
import calendar
import datetime
import json
import decimal
from decimal import Decimal, getcontext

# Set decimal precision for financial calculations
getcontext().prec = 28

# Helper functions for safe decimal handling
def safe_decimal(value):
    """Convert value to Decimal safely"""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        return Decimal(value)
    if isinstance(value, int):
        return Decimal(value)
    return Decimal(str(value))

def format_decimal(value):
    """Format Decimal for display"""
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    return str(value)

def safe_float_input(prompt):
    """Get float input from user and convert to Decimal"""
    while True:
        try:
            value = float(input(prompt))
            if value < 0:
                print("Value cannot be negative!")
                continue
            return Decimal(str(value))
        except ValueError:
            print("Invalid input! Please enter a valid number.")

# Database connection with timeout settings
def get_connection():
    return mycon.connect(
        host="localhost",
        user="root",
        passwd="skgamer465",
        database="bank",
        autocommit=True,
        connection_timeout=30
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

    # Create TRANSACTION_HISTORY table (simplified without blockchain)
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
                       remark TEXT NOT NULL,
                       transaction_date DATE NOT NULL,
                       transaction_time TIME NOT NULL,
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

    # Convert balance to Decimal for proper database handling
    balance_decimal = safe_decimal(balance)

    query = """
            INSERT INTO ACCOUNTS(name, phone_num, pin, balance, account_type)
            VALUES (%s, %s, %s, %s, %s)
            """
    values = (name, phone_no, pin, balance_decimal, account_type)

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

def save_transaction_to_db(from_acc, to_acc, amount, remark):
    """Save transaction to MySQL database (now integrated into transfer_money)"""
    # This function is kept for compatibility but transactions are now saved 
    # within the transfer_money function to avoid separate database operations
    try:
        # This function is deprecated - transactions are now saved in transfer_money
        print("Note: Transaction logging is now handled within transfer operation.")
    except Exception as e:
        print(f"Warning: Could not log transaction: {e}")
    return True

def transfer_money(from_acc, to_acc, amount, remark="Transfer"):
    """Transfer money between accounts with proper transaction handling"""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Set transaction isolation level to reduce lock contention
        cursor.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        
        # Convert amount to Decimal for safe arithmetic operations
        amount_decimal = safe_decimal(amount)

        # Use row-level locking to prevent deadlocks
        # Lock both accounts in consistent order to avoid deadlock
        if from_acc < to_acc:
            cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (from_acc,))
            from_result = cursor.fetchone()
            cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (to_acc,))
            to_result = cursor.fetchone()
        else:
            cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (to_acc,))
            to_result = cursor.fetchone()
            cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (from_acc,))
            from_result = cursor.fetchone()

        if not from_result:
            print("From account does not exist!")
            return False

        if not to_result:
            print("To account does not exist!")
            return False

        from_acc_balance = from_result[0]
        to_acc_balance = to_result[0]

        if from_acc_balance >= amount_decimal:
            # Update balances in the same transaction
            new_from_balance = from_acc_balance - amount_decimal
            new_to_balance = to_acc_balance + amount_decimal

            # Update both accounts atomically
            cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                           (new_from_balance, from_acc))
            cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                           (new_to_balance, to_acc))

            # Insert transaction record in the same transaction
            cursor.execute("""
                INSERT INTO TRANSACTION_HISTORY
                (from_account, to_account, amount, remark_encrypted, transaction_date, transaction_time)
                VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())
            """, (from_acc, to_acc, amount_decimal, remark))

            connection.commit()
            print("Transfer successful!")
            return True
        else:
            print("Insufficient balance in the from account.")
            connection.rollback()
            return False

    except mycon.Error as e:
        if e.errno == 1205:  # Lock wait timeout
            print("Transfer failed due to database lock timeout. Please try again.")
        else:
            print(f"Database error during transfer: {e}")
        try:
            connection.rollback()
        except:
            pass
        return False
    except Exception as e:
        print(f"Error during transfer: {e}")
        try:
            connection.rollback()
        except:
            pass
        return False
    finally:
        cursor.close()
        connection.close()

def get_transaction_history(account_no):
    """Get transaction history from database"""
    print("\n=== Transaction History ===")
    connection = get_connection()
    cursor = connection.cursor()

    query = """
            SELECT th.transaction_date, 
                   th.transaction_time, 
                   th.from_account,
                   th.to_account, 
                   th.amount, 
                   th.remark_encrypted
            FROM TRANSACTION_HISTORY th
            WHERE th.from_account = %s 
               OR th.to_account = %s
            ORDER BY th.transaction_date DESC, th.transaction_time DESC LIMIT 10
            """

    cursor.execute(query, (account_no, account_no))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions found.")
    else:
        for trans in transactions:
            print(f"\nDate: {trans[0]} Time: {trans[1]}")
            print(f"From: {trans[2]} To: {trans[3]} Amount: ₹{format_decimal(trans[4])}")
            print(f"Remark: {trans[5]}")

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
        print("6. Logout")

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
            print(f"Balance: ₹{format_decimal(balance)}")

        elif choice == 2:
            try:
                to_acc = int(input("ENTER THE ACCOUNT NUMBER TO TRANSFER MONEY: "))
                amount = safe_float_input("ENTER THE AMOUNT TO TRANSFER: ")
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
            print("LOGGING OUT...")
            time.sleep(1)
            print("LOGGED OUT SUCCESSFULLY!")
            break

        else:
            print("INVALID CHOICE!")

def main():
    # Initialize database
    init_database()

    while True:
        print("\n" + "=" * 50)
        print("WELCOME TO BANK MANAGEMENT SYSTEM")
        print("=" * 50)
        time.sleep(0.5)

        print("\n1. OPEN ACCOUNT")
        print("2. LOGIN ACCOUNT")
        print("3. ABOUT")
        print("4. EXIT")

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

                balance = safe_float_input("ENTER INITIAL DEPOSIT AMOUNT: ")

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
            print("BANK MANAGEMENT SYSTEM - VERSION 2.0")
            print("=" * 50)
            print("\nDeveloped by: SIDHARTH and RITESH")
            print("\nFeatures:")
            print("- Secure account management")
            print("- Real-time balance tracking")
            print("- Transaction history")
            print("- PIN and personal info management")
            time.sleep(3)

        elif choice == 4:
            print("\nEXITING...")
            time.sleep(1)
            print("THANK YOU FOR USING BANK MANAGEMENT SYSTEM!")
            print("GOODBYE!")
            break

        else:
            print("INVALID CHOICE! Please try again.")

if __name__ == "__main__":
    main()
