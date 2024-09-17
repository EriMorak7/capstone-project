import sqlite3
import hashlib

def connect_db():
    return sqlite3.connect('banking_app.db')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(full_name, username, password, initial_deposit):
    if initial_deposit < 0:
        print("Initial deposit cannot be negative.")
        return

    hashed_password = hash_password(password)
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO Users (full_name, username, password, balance) 
            VALUES (?, ?, ?, ?)
        ''', (full_name, username, hashed_password, initial_deposit))
        conn.commit()
        print("Registration successful.")
    except sqlite3.IntegrityError:
        print("Username already exists.")
    finally:
        conn.close()

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    hashed_password = hash_password(password)
    cursor.execute('SELECT user_id FROM Users WHERE username = ? AND password = ?', (username, hashed_password))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result[0] 
    print("Invalid username or password.")
    return None

def deposit(user_id, amount):
    if amount <= 0:
        print("Deposit amount must be positive.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('UPDATE Users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    cursor.execute('INSERT INTO Transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', (user_id, 'deposit', amount))

    conn.commit()
    conn.close()
    print("Deposit successful.")

def withdraw(user_id, amount):
    if amount <= 0:
        print("Withdrawal amount must be positive.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM Users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]

    if balance >= amount:
        cursor.execute('UPDATE Users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
        cursor.execute('INSERT INTO Transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', (user_id, 'withdrawal', amount))
        conn.commit()
        print("Withdrawal successful.")
    else:
        print("Insufficient funds.")
    conn.close()

def get_balance(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT balance FROM Users WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]
    conn.close()
    return balance

def transaction_history(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Transactions WHERE user_id = ?', (user_id,))
    transactions = cursor.fetchall()
    conn.close()
    return transactions

def main():
    while True:
        print("\nWelcome to the Banking App")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            full_name = input("Full Name: ")
            username = input("Username: ")
            password = input("Password: ")
            try:
                initial_deposit = float(input("Initial Deposit: "))
                register_user(full_name, username, password, initial_deposit)
            except ValueError:
                print("Invalid deposit amount. Must be a number.")

        elif choice == '2':
            username = input("Username: ")
            password = input("Password: ")
            user_id = login_user(username, password)
            if user_id:
                while True:
                    print("\n1. Deposit")
                    print("2. Withdraw")
                    print("3. Check Balance")
                    print("4. Transaction History")
                    print("5. Logout")
                    transaction_choice = input("Enter your choice: ")

                    if transaction_choice == '1':
                        try:
                            amount = float(input("Amount to deposit: "))
                            deposit(user_id, amount)
                        except ValueError:
                            print("Invalid amount. Must be a number.")
                    
                    elif transaction_choice == '2':
                        try:
                            amount = float(input("Amount to withdraw: "))
                            withdraw(user_id, amount)
                        except ValueError:
                            print("Invalid amount. Must be a number.")
                    
                    elif transaction_choice == '3':
                        balance = get_balance(user_id)
                        print(f"Your balance is {balance:.2f}")

                    elif transaction_choice == '4':
                        history = transaction_history(user_id)
                        for txn in history:
                            print(txn)
                    
                    elif transaction_choice == '5':
                        break

        elif choice == '3':
            break

if __name__ == "__main__":
    main()
