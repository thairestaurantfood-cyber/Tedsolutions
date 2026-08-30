import os
import sys
import sqlite3
import argparse

DB_PATH = os.path.expanduser('~/sqlite_studio_demo.db')

def execute_query(db_path, query, params=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if query.strip().upper().startswith('SELECT'):
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            # Print header
            print("\nQuery Results:")
            print("-" * (sum(len(col) + 2 for col in columns) + len(columns) - 1))

            # Print column headers
            header = "  ".join(f"{col:<{len(col)+2}}" for col in columns)
            print(header)
            print("-" * len(header))

            # Print rows
            for row in rows:
                row_str = "  ".join(f"{str(val):<{len(columns[i])+2}}" for i, val in enumerate(row))
                print(row_str)

            print("-" * len(header))
            print(f"Showing {len(rows)} rows\n")
        else:
            conn.commit()
            print(f"Query executed successfully. {cursor.rowcount} rows affected.")

    except sqlite3.Error as e:
        print(f"Error executing query: {e}")
    finally:
        conn.close()

def show_table_data(db_path, table_name, page=1, per_page=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]

    # Calculate offset for pagination
    offset = (page - 1) * per_page

    # Get total count for pagination info
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = cursor.fetchone()[0]

    # Get data for current page
    cursor.execute(f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (per_page, offset))
    rows = cursor.fetchall()

    conn.close()

    # Calculate pagination info
    total_pages = (total_rows + per_page - 1) // per_page
    start_row = offset + 1
    end_row = min(offset + per_page, total_rows)

    # Print header
    print(f"\nTable: {table_name} (Page {page}/{total_pages}, Rows {start_row}-{end_row}/{total_rows})")
    print("-" * (sum(len(col) + 2 for col in columns) + len(columns) - 1))

    # Print column headers
    header = "  ".join(f"{col:<{len(col)+2}}" for col in columns)
    print(header)
    print("-" * len(header))

    # Print rows
    for row in rows:
        row_str = "  ".join(f"{str(val):<{len(columns[i])+2}}" for i, val in enumerate(row))
        print(row_str)

    print("-" * len(header))
    print(f"Showing {len(rows)} rows\n")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            age INTEGER NOT NULL
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Insert sample users
    cursor.executemany('''
        INSERT INTO users (name, email, age)
        VALUES (?, ?, ?)
    ''', [
        ('Alice', 'alice@example.com', 30),
        ('Bob', 'bob@example.com', 25),
        ('Charlie', 'charlie@example.com', 35),
        ('David', 'david@example.com', 40),
        ('Eve', 'eve@example.com', 28)
    ])

    # Insert sample orders
    cursor.executemany('''
        INSERT INTO orders (user_id, product, amount, order_date)
        VALUES (?, ?, ?, ?)
    ''', [
        (1, 'Laptop', 999.99, '2023-01-15'),
        (1, 'Mouse', 19.99, '2023-01-15'),
        (2, 'Keyboard', 49.99, '2023-02-20'),
        (3, 'Monitor', 199.99, '2023-03-10'),
        (4, 'Headphones', 79.99, '2023-04-05'),
        (5, 'Webcam', 59.99, '2023-05-12')
    ])

    conn.commit()

    # Show first page of users table
    show_table_data(DB_PATH, 'users', page=1, per_page=5)

    # Show first page of orders table
    show_table_data(DB_PATH, 'orders', page=1, per_page=5)

    # Execute a sample query
    print("\nExecuting sample query:")
    execute_query(DB_PATH, '''
        SELECT u.name, o.product, o.amount, o.order_date
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE u.age > 30
        ORDER BY o.order_date DESC
    ''')

    conn.close()
    sys.exit(0)

def list_tables(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]

def main():
    parser = argparse.ArgumentParser(description="SQLiteStudio - SQLite Database Browser")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample database')
    parser.add_argument('--db', default=DB_PATH, help='Path to SQLite database file')

    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add subcommands here
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

if __name__ == "__main__":
    main()