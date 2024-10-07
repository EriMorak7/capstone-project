import sqlite3
import getpass
import re
import time
from database import create_connection

DB_FILE = 'banking.db'

def validate_full_name(name):
    """Validate the full name for length and character restrictions."""
    return len(name) >= 4 and len(name) <= 255 and all(c.isalpha() or c.isspace() for c in name)

def validate_username(username):
    """Validate the username for length and allowed characters."""
    return 3 <= len(username) <= 20 and re.match("^[a-zA-Z0-9_]+$", username) is not None

def validate_password(password):
    """Validate the password for complexity requirements."""
    return (len(password) >= 8 and 
            re.search("[a-z]", password) and 
            re.search("[A-Z]", password) and 
            re.search("[0-9]", password))

def validate_initial_deposit(amount):
    """Check if the initial deposit meets minimum requirements."""
    return isinstance(amount, (int, float)) and amount >= 1000

def register_user(conn):
    """Register a new user in the database."""
    full_name = input("Enter your full name: ")
    if not validate_full_name(full_name):
        print("Invalid full name.")
        return
    
    username = input("Choose a username: ")
    if not validate_username(username):
        print("Invalid username.")
        return
    
    password = getpass.getpass("Choose a password: ")
    if not validate_password(password):
        print("Invalid password. Must be at least 8 characters")
        return
    
    initial_deposit = float(input("Enter initial deposit (min 1000): "))
    if not validate_initial_deposit(initial_deposit):
        print("Invalid deposit amount.")
        return

 # Generate a simple account number
    account_number = str(int(time.time())) 
    
# Hashing Password 
    hashed_password = password  
    
# Registration
    with conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (full_name, username, password, account_number, balance) VALUES (?, ?, ?, ?, ?)', 
                       (full_name, username, hashed_password, account_number, initial_deposit))
        print(f"Registration successful! Your account number is {account_number}. Please log in.")
        time.sleep(1)

# Login
def login_user(conn):
    """Authenticate a user and return user data upon successful login."""
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")

    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()

    if user and user[3] == password:  # Check password
        print("Login successful!")
        return user
    else:
        print("Invalid username or password.")
        return None

# Deposit
def deposit(conn, user_id):
    """Deposit an amount into the user's account."""
    amount = float(input("Enter deposit amount: "))
    if amount <= 0:
        print("Invalid amount.")
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'deposit', amount))
        print(f"Successfully deposited {amount}.")

# Withdrawal
def withdrawal(conn, user_id):
    """Withdraw an amount from the user's account."""
    amount = float(input("Enter withdrawal amount: "))
    
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]

    if amount <= 0 or amount > balance:
        print("Invalid withdrawal amount.")
        return

    with conn:
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'withdrawal', amount))
        print(f"Successfully withdrew {amount}.")

# Balance Inquiry
def balance_inquiry(conn, user_id):
    """Display the user's current account balance."""
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    print(f"Your current balance is: {balance}")

# Transaction History
def transaction_history(conn, user_id):
    """Display the user's transaction history."""
    cursor = conn.cursor()
    cursor.execute('SELECT transaction_type, amount, timestamp FROM transactions WHERE user_id = ?', (user_id,))
    transactions = cursor.fetchall()
    
    if transactions:
        print("Transaction History:")
        for transaction in transactions:
            print(f"{transaction[2]}: {transaction[0]} of {transaction[1]}")
    else:
        print("No transactions found.")

# Transfer
def transfer(conn, user_id):
    """Transfer money to another user's account."""
    recipient_account_number = input("Enter recipient's account number: ")
    amount = float(input("Enter transfer amount: "))

    # Check if recipient exists
    cursor = conn.cursor()
    cursor.execute('SELECT id, balance FROM users WHERE account_number = ?', (recipient_account_number,))
    recipient = cursor.fetchone()

    if not recipient:
        print("Recipient account does not exist.")
        return

    if amount <= 0:
        print("Invalid transfer amount.")
        return

    if amount > recipient[1]:  # Check sender's balance
        print("Insufficient funds for transfer.")
        return

    with conn:
        # Update balances
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient[0]))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'transfer', amount))
        print(f"Successfully transferred {amount} to account {recipient_account_number}.")

# Main Application
def main():
    """Main application logic for the banking system."""
    conn = create_connection(DB_FILE)

    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            register_user(conn)
        elif choice == '2':
            user = login_user(conn)
            if user:
                user_id = user[0]  # User ID from the database
                while True:
                    print("\n1. Deposit\n2. Withdraw\n3. Balance Inquiry\n4. Transaction History\n5. Transfer\n6. Logout")
                    action = input("Choose an action: ")

                    if action == '1':
                        deposit(conn, user_id)
                    elif action == '2':
                        withdrawal(conn, user_id)
                    elif action == '3':
                        balance_inquiry(conn, user_id)
                    elif action == '4':
                        transaction_history(conn, user_id)
                    elif action == '5':
                        transfer(conn, user_id)
                    elif action == '6':
                        print("Logging out...")
                        break
                    else:
                        print("Invalid option.")
                    time.sleep(1)
        elif choice == '3':
            print("Exiting the application.")
            break
        else:
            print("Invalid option.")
    
    conn.close()

if __name__ == "__main__":
    main()
