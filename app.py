import sqlite3
import getpass
import re
import time
from database import create_connection

DB_FILE = 'banking.db'

def validate_full_name(name):
    """Validate the full name for length and character restrictions."""
    if len(name) < 4 or len(name) > 255:
        return False, "Full name must be between 4 and 255 characters."
    if not all(c.isalpha() or c.isspace() for c in name):
        return False, "Full name can only contain letters and spaces."
    return True, ""

def validate_username(username):
    """Validate the username for length and allowed characters."""
    if not (3 <= len(username) <= 20):
        return False, "Username must be between 3 and 20 characters."
    if re.match("^[a-zA-Z0-9_]+$", username) is None:
        return False, "Username can only contain letters, numbers, and underscores."
    return True, ""

def validate_password(password):
    """Validate the password for complexity requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search("[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search("[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search("[0-9]", password):
        return False, "Password must contain at least one digit."
    return True, ""

def validate_initial_deposit(amount):
    """Check if the initial deposit meets minimum requirements."""
    if not isinstance(amount, (int, float)):
        return False, "Initial deposit must be a numeric value."
    if amount < 1000:
        return False, "Initial deposit must be at least 1000."
    return True, ""

def collect_and_validate_input(prompt, validation_function):
    """Collect input and validate using the provided validation function."""
    while True:
        user_input = input(prompt)
        valid, message = validation_function(user_input)
        if valid:
            return user_input
        else:
            print(message)


def login_user(conn):
    """Authenticate a user and return user data upon successful login."""
    while True:
        username = input("Enter your username: ").strip()
        password = getpass.getpass("Enter your password: ").strip()

        if not username or not password:
            print("Username and password cannot be blank.")
            continue

        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

        if user and user[3] == password:  # Check password
            print("Login successful!")
            return user
        else:
            print("Invalid username or password.")
            return None

def deposit(conn, user_id):
    """Deposit an amount into the user's account."""
    while True:
        try:
            amount = float(input("Enter deposit amount: "))
            if amount <= 0:
                print("Deposit amount must be positive.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    with conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, user_id))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'deposit', amount))
        print(f"Successfully deposited {amount}.")

def withdrawal(conn, user_id):
    """Withdraw an amount from the user's account."""
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]

    while True:
        try:
            amount = float(input("Enter withdrawal amount: "))
            if amount <= 0 or amount > balance:
                print(f"Invalid withdrawal amount. Your balance is {balance}.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

    with conn:
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'withdrawal', amount))
        print(f"Successfully withdrew {amount}.")

def balance_inquiry(conn, user_id):
    """Display the user's current account balance."""
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    print(f"Your current balance is: {balance}")

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

def transfer(conn, user_id):
    """Transfer money to another user's account."""
    while True:
        recipient_account_number = input("Enter recipient's account number: ").strip()
        amount = float(input("Enter transfer amount: "))

        if amount <= 0:
            print("Invalid transfer amount. Must be positive.")
            continue

        cursor = conn.cursor()
        cursor.execute('SELECT id, balance, full_name FROM users WHERE account_number = ?', (recipient_account_number,))
        recipient = cursor.fetchone()

        if not recipient:
            print("Recipient account does not exist.")
            continue

        if recipient[0] == user_id:  # Prevent self-transfer
            print("Cannot transfer money to yourself.")
            continue

        if amount > recipient[1]:  # Check sender's balance
            print("Insufficient funds for transfer.")
            continue

        break

    with conn:
        # Update balances
        cursor.execute('UPDATE users SET balance = balance - ? WHERE id = ?', (amount, user_id))
        cursor.execute('UPDATE users SET balance = balance + ? WHERE id = ?', (amount, recipient[0]))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (user_id, 'transfer', amount))
        cursor.execute('INSERT INTO transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', 
                       (recipient[0], 'received', amount))
        print(f"Successfully transferred {amount} to {recipient[2]}'s account.")

def account_details(conn, user_id):
    """Display account details for the logged-in user."""
    cursor = conn.cursor()
    cursor.execute('SELECT full_name, account_number, balance FROM users WHERE id = ?', (user_id,))
    details = cursor.fetchone()
    print(f"Account Details:\nFull Name: {details[0]}\nAccount Number: {details[1]}\nBalance: {details[2]}")

def register_user(conn):
    """Register a new user in the database."""
    while True:
        full_name = collect_and_validate_input("Enter your full name: ", validate_full_name)
        username = collect_and_validate_input("Choose a username: ", validate_username)
        
        # Check if username already exists
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            print("Username already exists. Please choose a different username.")
            continue  # Restart the registration process

        password = None
        while password is None:
            password_input = getpass.getpass("Choose a password: ")
            valid, message = validate_password(password_input)
            if valid:
                password = password_input
            else:
                print(message)

        while True:
            try:
                initial_deposit = float(input("Enter initial deposit (min 1000): "))
                valid, message = validate_initial_deposit(initial_deposit)
                if valid:
                    break
                else:
                    print(message)
            except ValueError:
                print("Invalid input. Please enter a numeric value.")

        # Generate a simple account number
        account_number = str(int(time.time()))
        
        # Hashing Password (This is a placeholder; in a real application, use a proper hashing function)
        hashed_password = password
        
        # Registration
        with conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (full_name, username, password, account_number, balance) VALUES (?, ?, ?, ?, ?)', 
                           (full_name, username, hashed_password, account_number, initial_deposit))
            print(f"Registration successful! Your account number is {account_number}.")
            time.sleep(1)

        # Automatically log in the user after successful registration
        return login_user(conn)


def main():
    """Main application logic for the banking system."""
    conn = create_connection(DB_FILE)

    while True:
        print("\n1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")

        if choice == '1':
            user = register_user(conn)
            if user:
                user_id = user[0]  # User ID from the database
                while True:
                    print("\n1. Deposit\n2. Withdraw\n3. Balance Inquiry\n4. Transaction History\n5. Transfer\n6. Account Details\n7. Logout")
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
                        account_details(conn, user_id)
                    elif action == '7':
                        print("Logging out...")
                        break
                    else:
                        print("Invalid option.")
                    time.sleep(1)
        elif choice == '2':
            user = login_user(conn)
            if user:
                user_id = user[0]  # User ID from the database
                while True:
                    print("\n1. Deposit\n2. Withdraw\n3. Balance Inquiry\n4. Transaction History\n5. Transfer\n6. Account Details\n7. Logout")
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
                        account_details(conn, user_id)
                    elif action == '7':
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
