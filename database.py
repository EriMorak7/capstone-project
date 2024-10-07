import sqlite3

def create_connection(db_file):
    """Create a database connection to the SQLite database."""
    conn = sqlite3.connect(db_file)
    return conn

def create_tables(conn):
    """Create tables for users and transactions."""
    with conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                account_number TEXT NOT NULL UNIQUE,
                balance REAL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')

def setup_database(db_file):
    """Set up the database by creating tables."""
    conn = create_connection(db_file)
    create_tables(conn)
    conn.close()

if __name__ == "__main__":
    setup_database('banking.db')
