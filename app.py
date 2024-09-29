import sqlite3
import hashlib
import re

def connect_db():
    return sqlite3.connect('banking_app.db')

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def validate_username(username):
    return bool(re.match("^[a-zA-Z0-9_]{3,20}$", username))

def validate_password(password):
    return len(password) >= 6

def validate_initial_deposit(initial_deposit):
    return initial_deposit >= 0

def validate_full_name(full_name):
    return bool(re.match("^[a-zA-Z\s]+$", full_name))

def register_user(full_name, username, password, initial_deposit):
    if not validate_full_name(full_name):
        print("Full name can only contain alphabets and spaces.")
        return
    if not validate_initial_deposit(initial_deposit):
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
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()

    hashed_password = hash_password(password)
    try:
        cursor.execute('SELECT user_id FROM Users WHERE username = ? AND password = ?', (username, hashed_password))
        result = cursor.fetchone()
    except Exception as e:
        print(f"An error occurred during login: {e}")
        return None
    finally:
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

    try:
        cursor.execute('UPDATE Users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        cursor.execute('INSERT INTO Transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', (user_id, 'deposit', amount))
        conn.commit()
        print("Deposit successful.")
    except Exception as e:
        print(f"An error occurred during deposit: {e}")
    finally:
        conn.close()

def withdraw(user_id, amount):
    if amount <= 0:
        print("Withdrawal amount must be positive.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT balance FROM Users WHERE user_id = ?', (user_id,))
        balance = cursor.fetchone()[0]

        if balance >= amount:
            cursor.execute('UPDATE Users SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
            cursor.execute('INSERT INTO Transactions (user_id, transaction_type, amount) VALUES (?, ?, ?)', (user_id, 'withdrawal', amount))
            conn.commit()
            print("Withdrawal successful.")
        else:
            print("Insufficient funds.")
    except Exception as e:
        print(f"An error occurred during withdrawal: {e}")
    finally:
        conn.close()

def get_balance(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT balance FROM Users WHERE user_id = ?', (user_id,))
        balance = cursor.fetchone()[0]
        return balance
    except Exception as e:
        print(f"An error occurred while fetching balance: {e}")
        return None
    finally:
        conn.close()

def transaction_history(user_id):
    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT * FROM Transactions WHERE user_id = ?', (user_id,))
        transactions = cursor.fetchall()
        return transactions
    except Exception as e:
        print(f"An error occurred while fetching transaction history: {e}")
        return []
    finally:
        conn.close()

def main():
    while True:
        print("\nWelcome to the Banking App")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            full_name = input("Full Name: ")
            if not validate_full_name(full_name):
                print("Invalid Name.")
                continue
            
            username = input("Username: ")
            if not validate_username(username):
                print("Invalid username")
                continue
            
            password = input("Password (at least 6 characters): ")
            if not validate_password(password):
                print("Invalid password. It must be at least 6 characters long.")
                continue
            
            try:
                initial_deposit = float(input("Initial Deposit: "))
                if not validate_initial_deposit(initial_deposit):
                    print("Invalid deposit amount. Must be a non-negative number.")
                    continue
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
                            print("Invalid input. Must be a number.")
                    
                    elif transaction_choice == '2':
                        try:
                            amount = float(input("Amount to withdraw: "))
                            withdraw(user_id, amount)
                        except ValueError:
                            print("Invalid input. Must be a number.")
                    
                    elif transaction_choice == '3':
                        balance = get_balance(user_id)
                        if balance is not None:
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
