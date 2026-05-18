import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.jarvis/clitrack.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            data_type TEXT NOT NULL,
            amount REAL,
            description TEXT,
            category TEXT,
            tags TEXT
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    demo_data = [
        ('2024-01-15 10:30:00', 'csv', 'expense', 125.50, 'Office Supplies', 'Office', 'purchase'),
        ('2024-01-16 14:20:00', 'json', 'income', 850.00, 'Consulting', 'Revenue', 'service'),
        ('2024-01-17 09:15:00', 'csv', 'expense', 45.20, 'Internet Bill', 'Utilities', 'recurring'),
        ('2024-01-18 16:45:00', 'json', 'expense', 2800.00, 'New Laptop', 'Equipment', 'asset'),
        ('2024-01-19 11:00:00', 'csv', 'income', 320.00, 'Workshop Fee', 'Revenue', 'event')
    ]

    cur.executemany('''
        INSERT INTO records (timestamp, source, data_type, amount, description, category, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', demo_data)
    conn.commit()

    cur.execute('SELECT * FROM records ORDER BY timestamp DESC')
    rows = cur.fetchall()

    print("\n=== CliTrack Demo Records ===")
    print(f"{'ID':<3} {'Timestamp':<19} {'Source':<6} {'Type':<7} {'Amount':<8} {'Description':<15} {'Category':<10} {'Tags':<8}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<3} {row[1]:<19} {row[2]:<6} {row[3]:<7} {row[4]:<8.2f} {row[5]:<15} {row[6]:<10} {row[7]:<8}")
    print("\nTotal records:", len(rows))
    conn.close()
    print("Demo complete.")

def add_record(source, data_type, amount, description, category, tags):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cur.execute('''
        INSERT INTO records (timestamp, source, data_type, amount, description, category, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, source, data_type, amount, description, category, tags))
    conn.commit()
    conn.close()
    print(f"Added record: {description} ({amount})")

def list_records(limit=None):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    query = 'SELECT * FROM records ORDER BY timestamp DESC'
    if limit:
        query += f' LIMIT {limit}'

    cur.execute(query)
    rows = cur.fetchall()

    print("\n=== CliTrack Records ===")
    print(f"{'ID':<3} {'Timestamp':<19} {'Source':<6} {'Type':<7} {'Amount':<8} {'Description':<15} {'Category':<10} {'Tags':<8}")
    print("-" * 100)
    for row in rows:
        print(f"{row[0]:<3} {row[1]:<19} {row[2]:<6} {row[3]:<7} {row[4]:<8.2f} {row[5]:<15} {row[6]:<10} {row[7]:<8}")
    print("\nTotal records:", len(rows))
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="CliTrack - CLI expense/income tracker")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a new record')
    add_parser.add_argument('--source', required=True, help='Source of data (csv/json)')
    add_parser.add_argument('--type', required=True, dest='data_type', help='Type (income/expense)')
    add_parser.add_argument('--amount', type=float, required=True, help='Amount')
    add_parser.add_argument('--description', required=True, help='Description')
    add_parser.add_argument('--category', required=True, help='Category')
    add_parser.add_argument('--tags', required=True, help='Tags')

    list_parser = subparsers.add_parser('list', help='List records')
    list_parser.add_argument('--limit', type=int, help='Limit number of records')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_record(args.source, args.data_type, args.amount, args.description, args.category, args.tags)
    elif args.command == 'list':
        list_records(args.limit)

if __name__ == "__main__":
    main()