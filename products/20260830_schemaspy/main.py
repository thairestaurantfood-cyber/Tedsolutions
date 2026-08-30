import os
import sys
import sqlite3
import argparse

DB_PATH = os.path.expanduser('~/schemaspy_demo.db')

def table_exists(db_path, table_name):
    """Check if a table exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_table_schema(db_path, table_name):
    if not table_exists(db_path, table_name):
        print(f"Error: Table '{table_name}' not found in database", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    print(f"\nSchema for table: {table_name}")
    print(f"{'Column':<15}{'Type':<10}{'Not Null':<10}{'Default':<10}{'Primary Key':<15}")
    print("-" * 60)
    for column in columns:
        print(f"{column[1]:<15}{column[2]:<10}{str(bool(column[3])):<10}{str(column[4]):<10}{str(bool(column[5])):<15}")

    conn.close()

def get_foreign_keys(db_path, table_name):
    if not table_exists(db_path, table_name):
        print(f"Error: Table '{table_name}' not found in database", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = cursor.fetchall()

    if fks:
        print(f"\nForeign keys for table: {table_name}")
        print(f"{'ID':<5}{'Sequence':<10}{'Table':<15}{'From':<15}{'To':<15}")
        print("-" * 60)
        for fk in fks:
            print(f"{fk[0]:<5}{fk[1]:<10}{fk[2]:<15}{fk[3]:<15}{fk[4]:<15}")

    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        age INTEGER,
        is_active BOOLEAN
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        product TEXT NOT NULL,
        price REAL NOT NULL,
        order_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL
        )
    ''')

    cursor.executemany('''
        INSERT INTO users (name, email, age, is_active)
        VALUES (?, ?, ?, ?)
    ''', [
        ('Alice', 'alice@example.com', 30, True),
        ('Bob', 'bob@example.com', 25, False),
        ('Charlie', 'charlie@example.com', 35, True)
    ])

    cursor.executemany('''
        INSERT INTO orders (user_id, product, price, order_date)
        VALUES (?, ?, ?, ?)
    ''', [
        (1, 'Laptop', 999.99, '2023-01-15'),
        (1, 'Mouse', 19.99, '2023-01-16'),
        (2, 'Keyboard', 49.99, '2023-02-20'),
        (3, 'Monitor', 199.99, '2023-03-10')
    ])

    cursor.executemany('''
        INSERT INTO products (name, category, price, stock)
        VALUES (?, ?, ?, ?)
    ''', [
        ('Laptop', 'Electronics', 999.99, 10),
        ('Mouse', 'Accessories', 19.99, 50),
        ('Keyboard', 'Accessories', 49.99, 30),
        ('Monitor', 'Electronics', 199.99, 15)
    ])

    conn.commit()

    print("\nUsers Table:")
    print(f"{'ID':<5}{'Name':<10}{'Email':<20}{'Age':<5}{'Active':<10}")
    print("-" * 55)
    for row in cursor.execute('SELECT * FROM users'):
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<20}{row[3]:<5}{str(row[4]):<10}")

    print("\nOrders Table:")
    print(f"{'ID':<5}{'User ID':<10}{'Product':<15}{'Price':<10}{'Order Date':<15}")
    print("-" * 60)
    for row in cursor.execute('SELECT * FROM orders'):
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<15}{row[3]:<10}{row[4]:<15}")

    print("\nProducts Table:")
    print(f"{'ID':<5}{'Name':<15}{'Category':<15}{'Price':<10}{'Stock':<10}")
    print("-" * 55)
    for row in cursor.execute('SELECT * FROM products'):
        print(f"{row[0]:<5}{row[1]:<15}{row[2]:<15}{row[3]:<10}{row[4]:<10}")

    get_table_schema(DB_PATH, 'users')
    get_table_schema(DB_PATH, 'orders')
    get_table_schema(DB_PATH, 'products')

    get_foreign_keys(DB_PATH, 'orders')

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
    parser = argparse.ArgumentParser(description='SchemaSpy - CLI tool to visualize and document database schemas')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample database')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    list_parser = subparsers.add_parser('list', help='List all tables in the database')
    list_parser.add_argument('db_path', help='Path to the SQLite database file')

    schema_parser = subparsers.add_parser('schema', help='Show schema for a specific table')
    schema_parser.add_argument('db_path', help='Path to the SQLite database file')
    schema_parser.add_argument('table_name', help='Name of the table to show schema for')

    fk_parser = subparsers.add_parser('foreign-keys', help='Show foreign keys for a specific table')
    fk_parser.add_argument('db_path', help='Path to the SQLite database file')
    fk_parser.add_argument('table_name', help='Name of the table to show foreign keys for')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        tables = list_tables(args.db_path)
        print("Tables in database:")
        for table in tables:
            print(f"- {table}")
    elif args.command == 'schema':
        get_table_schema(args.db_path, args.table_name)
    elif args.command == 'foreign-keys':
        get_foreign_keys(args.db_path, args.table_name)

if __name__ == "__main__":
    main()