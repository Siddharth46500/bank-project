import mysql.connector as mycon
import time
import calendar
import datetime
import json
import decimal
from decimal import Decimal, getcontext
from smtplib import SMTP 

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
        passwd="root",
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
                       email VARCHAR
                   (
                       255
                   ),
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

    # Check if email column exists, add it if missing
    cursor.execute("""
        SELECT COUNT(*) as column_exists
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'bank'
        AND TABLE_NAME = 'ACCOUNTS'
        AND COLUMN_NAME = 'email'
    """)

    if cursor.fetchone()[0] == 0:
        print("Adding email column to ACCOUNTS table...")
        cursor.execute("ALTER TABLE ACCOUNTS ADD COLUMN email VARCHAR(255)")
        connection.commit()

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

    # Create ADMIN table
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS ADMIN
                   (
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       username VARCHAR(50) UNIQUE NOT NULL,
                       password VARCHAR(255) NOT NULL,
                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                   """)

    # Insert default admin if not exists
    cursor.execute("SELECT COUNT(*) FROM ADMIN WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO ADMIN (username, password) VALUES (%s, %s)",
                       ('admin', 'admin123'))
        print("Default admin account created (username: admin, password: admin123)")

    connection.commit()
    cursor.close()
    connection.close()

def validate_email_format(email):
    """Validate email format using regex"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def account_open(name, phone_no, pin, balance, account_type, email=None):
    """Open a new account with optional email (regex validation only)"""
    connection = get_connection()
    cursor = connection.cursor()

    # Convert balance to Decimal for proper database handling
    balance_decimal = safe_decimal(balance)

    # Initialize email variables
    email_to_store = None

    # Validate email format if provided
    if email:
        if validate_email_format(email):
            email_to_store = email
            print(f"Email format validated: {email}")
        else:
            print("❌ Invalid email format! Account will be created without email.")
            email_to_store = None

    query = """
            INSERT INTO ACCOUNTS(name, phone_num, email, pin, balance, account_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
    values = (name, phone_no, email_to_store, pin, balance_decimal, account_type)

    try:
        cursor.execute(query, values)
        account_no = cursor.lastrowid
        connection.commit()
        print(f"Account created successfully! Account Number: {account_no}")

        if email_to_store:
            print(f"Email: {email_to_store}")

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

def fetch_email(account_num):
    """Fetch email address for an account"""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT email FROM ACCOUNTS WHERE account_no = %s", (account_num,))
    result = cursor.fetchone()

    cursor.close()
    connection.close()

    return result[0] if result else None

def update_email(account_num, new_email):
    """Update email address for an account with regex validation"""
    connection = get_connection()
    cursor = connection.cursor()

    email_to_store = new_email

    # Validate email format
    if not validate_email_format(new_email):
        print("❌ Invalid email format!")
        return False

    try:
        cursor.execute("UPDATE ACCOUNTS SET email = %s WHERE account_no = %s",
                       (email_to_store, account_num))
        connection.commit()
        return True
    except Exception as e:
        print(f"Error updating email: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

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

def deposit_money(account_no, amount):
    """Deposit money into account with transaction logging"""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Convert amount to Decimal for safe arithmetic operations
        amount_decimal = safe_decimal(amount)

        # Lock the account for update
        cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (account_no,))
        result = cursor.fetchone()

        if not result:
            print("Account does not exist!")
            return False

        current_balance = result[0]
        new_balance = current_balance + amount_decimal

        # Update balance
        cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                       (new_balance, account_no))

        # Insert transaction record
        cursor.execute("""
            INSERT INTO TRANSACTION_HISTORY
            (from_account, to_account, amount, remark_encrypted, transaction_date, transaction_time)
            VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())
        """, (0, account_no, amount_decimal, "Deposit"))

        connection.commit()
        print(f"Deposit successful! New balance: ₹{format_decimal(new_balance)}")
        return True

    except Exception as e:
        print(f"Error during deposit: {e}")
        try:
            connection.rollback()
        except:
            pass
        return False
    finally:
        cursor.close()
        connection.close()

def withdraw_money(account_no, amount):
    """Withdraw money from account with balance check and transaction logging"""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Convert amount to Decimal for safe arithmetic operations
        amount_decimal = safe_decimal(amount)

        # Lock the account for update
        cursor.execute("SELECT balance FROM ACCOUNTS WHERE account_no = %s FOR UPDATE", (account_no,))
        result = cursor.fetchone()

        if not result:
            print("Account does not exist!")
            return False

        current_balance = result[0]

        if current_balance < amount_decimal:
            print("Insufficient balance!")
            return False

        new_balance = current_balance - amount_decimal

        # Update balance
        cursor.execute("UPDATE ACCOUNTS SET balance = %s WHERE account_no = %s",
                       (new_balance, account_no))

        # Insert transaction record
        cursor.execute("""
            INSERT INTO TRANSACTION_HISTORY
            (from_account, to_account, amount, remark_encrypted, transaction_date, transaction_time)
            VALUES (%s, %s, %s, %s, CURDATE(), CURTIME())
        """, (account_no, 0, amount_decimal, "Withdrawal"))

        connection.commit()
        print(f"Withdrawal successful! New balance: ₹{format_decimal(new_balance)}")
        return True

    except Exception as e:
        print(f"Error during withdrawal: {e}")
        try:
            connection.rollback()
        except:
            pass
        return False
    finally:
        cursor.close()
        connection.close()

def delete_account(account_no):
    """Delete user account and all associated transactions"""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Check if account exists
        cursor.execute("SELECT account_no FROM ACCOUNTS WHERE account_no = %s", (account_no,))
        if not cursor.fetchone():
            print("Account does not exist!")
            return False

        # Delete all transactions related to this account
        cursor.execute("DELETE FROM TRANSACTION_HISTORY WHERE from_account = %s OR to_account = %s",
                       (account_no, account_no))

        # Delete the account
        cursor.execute("DELETE FROM ACCOUNTS WHERE account_no = %s", (account_no,))

        connection.commit()
        return True

    except Exception as e:
        print(f"Error deleting account: {e}")
        try:
            connection.rollback()
        except:
            pass
        return False
    finally:
        cursor.close()
        connection.close()

def admin_login(username, password):
    """Authenticate admin user"""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT id FROM ADMIN WHERE username = %s AND password = %s",
                       (username, password))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        print(f"Admin login error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

def admin_panel():
    """Admin panel with account management features"""
    while True:
        print("\n" + "=" * 50)
        print("ADMIN PANEL")
        print("=" * 50)
        print("\n1. View all accounts")
        print("2. View all transactions")
        print("3. Delete user account")
        print("4. View system statistics")
        print("5. Logout")

        try:
            choice = int(input("\nENTER YOUR CHOICE: "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice == 1:
            # View all accounts
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT account_no, name, phone_num, email, balance, account_type FROM ACCOUNTS")
            accounts = cursor.fetchall()
            cursor.close()
            connection.close()

            if not accounts:
                print("No accounts found.")
            else:
                print("\n" + "=" * 80)
                print("ALL ACCOUNTS")
                print("=" * 80)
                print(f"{'Account No':<12} {'Name':<20} {'Phone':<15} {'Email':<25} {'Balance':<12} {'Type':<10}")
                print("-" * 80)
                for acc in accounts:
                    email = acc[3] if acc[3] else "N/A"
                    print(f"{acc[0]:<12} {acc[1]:<20} {acc[2]:<15} {email:<25} ₹{format_decimal(acc[4]):<11} {acc[5]:<10}")

        elif choice == 2:
            # View all transactions
            connection = get_connection()
            cursor = connection.cursor()
            cursor.execute("""
                SELECT th.transaction_date, th.transaction_time, th.from_account, th.to_account,
                       th.amount, th.remark_encrypted
                FROM TRANSACTION_HISTORY th
                ORDER BY th.transaction_date DESC, th.transaction_time DESC LIMIT 50
            """)
            transactions = cursor.fetchall()
            cursor.close()
            connection.close()

            if not transactions:
                print("No transactions found.")
            else:
                print("\n" + "=" * 100)
                print("RECENT TRANSACTIONS")
                print("=" * 100)
                print(f"{'Date':<12} {'Time':<10} {'From':<8} {'To':<8} {'Amount':<12} {'Remark':<30}")
                print("-" * 100)
                for trans in transactions:
                    from_acc = str(trans[2]) if trans[2] != 0 else "DEPOSIT"
                    to_acc = str(trans[3]) if trans[3] != 0 else "WITHDRAWAL"
                    print(f"{trans[0]:<12} {trans[1]:<10} {from_acc:<8} {to_acc:<8} ₹{format_decimal(trans[4]):<11} {trans[5]:<30}")

        elif choice == 3:
            # Delete user account
            try:
                account_no = int(input("ENTER ACCOUNT NUMBER TO DELETE: "))
                confirm = input(f"ARE YOU SURE YOU WANT TO DELETE ACCOUNT {account_no}? (YES/NO): ").upper()
                if confirm == 'YES':
                    if delete_account(account_no):
                        print("ACCOUNT DELETED SUCCESSFULLY!")
                    else:
                        print("ACCOUNT DELETION FAILED!")
                else:
                    print("Account deletion cancelled.")
            except ValueError:
                print("Invalid account number!")

        elif choice == 4:
            # View system statistics
            connection = get_connection()
            cursor = connection.cursor()

            # Total accounts
            cursor.execute("SELECT COUNT(*) FROM ACCOUNTS")
            total_accounts = cursor.fetchone()[0]

            # Total balance
            cursor.execute("SELECT SUM(balance) FROM ACCOUNTS")
            total_balance = cursor.fetchone()[0] or 0

            # Total transactions
            cursor.execute("SELECT COUNT(*) FROM TRANSACTION_HISTORY")
            total_transactions = cursor.fetchone()[0]

            # Account types breakdown
            cursor.execute("SELECT account_type, COUNT(*) FROM ACCOUNTS GROUP BY account_type")
            account_types = cursor.fetchall()

            cursor.close()
            connection.close()

            print("\n" + "=" * 50)
            print("SYSTEM STATISTICS")
            print("=" * 50)
            print(f"Total Accounts: {total_accounts}")
            print(f"Total Balance: ₹{format_decimal(total_balance)}")
            print(f"Total Transactions: {total_transactions}")
            print("\nAccount Types:")
            for acc_type, count in account_types:
                print(f"  {acc_type}: {count}")

        elif choice == 5:
            print("LOGGING OUT FROM ADMIN PANEL...")
            time.sleep(1)
            print("LOGGED OUT SUCCESSFULLY!")
            break

        else:
            print("INVALID CHOICE!")

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

def email_management_menu(account_no):
    """Email management submenu"""
    while True:
        print("\n=== EMAIL MANAGEMENT ===")
        current_email = fetch_email(account_no)

        if current_email:
            print(f"Current email: {current_email}")
        else:
            print("No email address associated with this account.")

        print("\n1. Add/Update email")
        print("2. Back to main menu")

        try:
            choice = int(input("ENTER YOUR CHOICE: "))
        except ValueError:
            print("Invalid input! Please enter a number.")
            continue

        if choice == 1:
            new_email = input("ENTER NEW EMAIL ADDRESS: ")

            if update_email(account_no, new_email):
                print("✅ Email updated successfully!")
            else:
                print("❌ Failed to update email.")

        elif choice == 2:
            break

        else:
            print("Invalid choice!")

def login(account_no, pin):
    print("\nWelcome to login page")

    while True:
        print("\n1. Check account details")
        print("2. Deposit money")
        print("3. Withdraw money")
        print("4. Transfer money")
        print("5. Change PIN")
        print("6. Update personal info")
        print("7. Check transaction history")
        print("8. Email management")
        print("9. Delete account")
        print("10. Logout")

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
            email = fetch_email(account_no)

            print("\nFetching account details...")
            time.sleep(1)
            print("Account details fetched successfully!")
            print("\nACCOUNT DETAILS:")
            print("-----------------")
            print(f"Account Number: {account_no}")
            print(f"Name: {name}")
            print(f"Phone Number: {phone_no}")
            if email:
                print(f"Email: {email}")
            else:
                print("Email: Not provided")
            print(f"Account Type: {account_type}")
            print(f"Balance: ₹{format_decimal(balance)}")

        elif choice == 2:
            # Deposit money
            try:
                amount = safe_float_input("ENTER THE AMOUNT TO DEPOSIT: ")
                if amount <= 0:
                    print("Amount must be positive!")
                    continue

                if deposit_money(account_no, amount):
                    print("DEPOSIT SUCCESSFUL!")
                else:
                    print("DEPOSIT FAILED!")

            except ValueError:
                print("Invalid input!")

        elif choice == 3:
            # Withdraw money
            try:
                amount = safe_float_input("ENTER THE AMOUNT TO WITHDRAW: ")
                if amount <= 0:
                    print("Amount must be positive!")
                    continue

                if withdraw_money(account_no, amount):
                    print("WITHDRAWAL SUCCESSFUL!")
                else:
                    print("WITHDRAWAL FAILED!")

            except ValueError:
                print("Invalid input!")

        elif choice == 4:
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

        elif choice == 5:
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

        elif choice == 6:
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

        elif choice == 7:
            get_transaction_history(account_no)

        elif choice == 8:
            email_management_menu(account_no)

        elif choice == 9:
            # Delete account
            confirm = input("ARE YOU SURE YOU WANT TO DELETE YOUR ACCOUNT? THIS ACTION CANNOT BE UNDONE! (YES/NO): ").upper()
            if confirm == 'YES':
                if delete_account(account_no):
                    print("ACCOUNT DELETED SUCCESSFULLY!")
                    return  # Exit login function
                else:
                    print("ACCOUNT DELETION FAILED!")
            else:
                print("Account deletion cancelled.")

        elif choice == 10:
            print("LOGGING OUT...")
            time.sleep(1)
            print("LOGGED OUT SUCCESSFULLY!")
            break

        else:
            print("INVALID CHOICE!")

# 2
def main():
    # Initialize database
    init_database()

    while True:
        print("\n" + "=" * 50)
        print("WELCOME TO BANK MANAGEMENT SYSTEM")
        print("=" * 50)
        time.sleep(0.5)

        print("\n1. OPEN ACCOUNT")
        print("2. USER ACCOUNT")
        print("3. ADMIN LOGIN")
        print("4. ABOUT")
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
            
            # Email input with regex validation
            email_choice = input("Do you want to provide email address? (Y/N): ").upper()
            email = None

            if email_choice == 'Y':
                email = input("ENTER YOUR EMAIL ADDRESS: ")
                if not validate_email_format(email):
                    print("❌ Invalid email format! Account will be created without email.")
                    email = None

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

                account_no = account_open(name, phone_no, pin, balance, account_type, email)
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
            # Admin login
            print("\n=== ADMIN LOGIN ===")
            username = input("ENTER ADMIN USERNAME: ")
            password = input("ENTER ADMIN PASSWORD: ")

            if admin_login(username, password):
                print("\nAdmin login successful!")
                admin_panel()
            else:
                print("Invalid admin credentials!")

        elif choice == 4:
            print("\n" + "=" * 50)
            print("BANK MANAGEMENT SYSTEM - VERSION 3.0")
            print("=" * 50)
            print("\nDeveloped by: SIDHARTH and RITESH")
            print("\nFeatures:")
            print("- Secure account management")
            print("- Email validation with regex")
            print("- Deposit and withdrawal functionality")
            print("- Account deletion")
            print("- Admin panel for system management")
            print("- Real-time balance tracking")
            print("- Transaction history")
            print("- PIN and personal info management")
            print("- Email management")
            print("- No blockchain - simplified system")
            time.sleep(3)

        elif choice == 5:
            print("\nEXITING...")
            time.sleep(1)
            print("THANK YOU FOR USING BANK MANAGEMENT SYSTEM!")
            print("GOODBYE!")
            break

        else:
            print("INVALID CHOICE! Please try again.")

if __name__ == "__main__":
    main()