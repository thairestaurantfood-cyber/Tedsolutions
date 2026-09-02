import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/sqlite_studio_demo.db')

def get_table_schema(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    print(f"{'Column':<15}{'Type':<10}{'NotNull':<10}{'Default':<15}{'PrimaryKey':<10}")
    print('-' * 60)
    for column in columns:
        print(f"{column[1]:<15}{column[2]:<10}{'YES' if column[3] else 'NO':<10}{str(column[4]):<15}{'YES' if column[5] else 'NO':<10}")

    conn.close()

def get_foreign_keys(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    foreign_keys = cursor.fetchall()

    if foreign_keys:
        print(f"\nForeign Keys for {table_name}:")
        print(f"{'ID':<5}{'Sequence':<10}{'Table':<15}{'From':<15}{'To':<15}{'On Update':<15}{'On Delete':<15}{'Match':<15}")
        print('-' * 90)
        for fk in foreign_keys:
            print(f"{fk[0]:<5}{fk[1]:<10}{fk[2]:<15}{fk[3]:<15}{fk[4]:<15}{fk[5]:<15}{fk[6]:<15}{fk[7]:<15}")
    else:
        print(f"\nNo foreign keys found for {table_name}")

    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create projects table with foreign key to users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Insert sample data into users
    cursor.execute('''
    INSERT INTO users (name, email) VALUES
    ('Alice', 'alice@example.com'),
    ('Bob', 'bob@example.com'),
    ('Charlie', 'charlie@example.com')
    ''')

    # Insert sample data into projects
    cursor.execute('''
    INSERT INTO projects (user_id, title, description) VALUES
    (1, 'Website Redesign', 'Complete redesign of company website'),
    (1, 'Mobile App', 'Develop new mobile application'),
    (2, 'Marketing Campaign', 'Q1 marketing campaign planning'),
    (3, 'Database Migration', 'Migrate legacy database to new system')
    ''')

    conn.commit()

    print("Users Table Schema:")
    get_table_schema('users')
    print("\nProjects Table Schema:")
    get_table_schema('projects')

    print("\nForeign Key Relationships:")
    get_foreign_keys('projects')

    print("\nUsers Data:")
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    print(f"{'ID':<5}{'Name':<10}{'Email':<25}{'Created At':<20}")
    print('-' * 60)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<25}{row[3]:<20}")

    print("\nProjects Data:")
    cursor.execute('SELECT * FROM projects')
    rows = cursor.fetchall()
    print(f"{'ID':<5}{'User ID':<10}{'Title':<20}{'Description':<30}{'Created At':<20}")
    print('-' * 85)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<20}{row[3]:<30}{row[4]:<20}")

    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="SQLiteStudio")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

if __name__ == "__main__":
    main()