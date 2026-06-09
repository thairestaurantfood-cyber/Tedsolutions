import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/invoice_chaser.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        amount REAL NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'unpaid',
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id)
    )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client_name, amount, due_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO invoices (client_name, amount, due_date)
    VALUES (?, ?, ?)
    ''', (client_name, amount, due_date))
    conn.commit()
    conn.close()

def list_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoices')
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Insert demo data
    demo_data = [
        ('Client A', 100.00, '2023-12-31'),
        ('Client B', 200.00, '2024-01-31'),
        ('Client C', 150.00, '2024-02-28')
    ]
    for client_name, amount, due_date in demo_data:
        add_invoice(client_name, amount, due_date)

    # Print formatted table
    invoices = list_invoices()
    print(f"{'ID':<5}{'Client':<15}{'Amount':<10}{'Due Date':<15}{'Status':<10}")
    print("-" * 50)
    for invoice in invoices:
        print(f"{invoice[0]:<5}{invoice[1]:<15}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<10}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--client', required=True)
    add_parser.add_argument('--amount', type=float, required=True)
    add_parser.add_argument('--due', required=True)

    # List command
    subparsers.add_parser('list')

    args = parser.parse_args()

    if not hasattr(args, 'command'):
        parser.print_help()
        return

    init_db()

    if args.command == 'add':
        add_invoice(args.client, args.amount, args.due)
        print("Invoice added successfully")
    elif args.command == 'list':
        invoices = list_invoices()
        print(f"{'ID':<5}{'Client':<15}{'Amount':<10}{'Due Date':<15}{'Status':<10}")
        print("-" * 50)
        for invoice in invoices:
            print(f"{invoice[0]:<5}{invoice[1]:<15}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<10}")

if __name__ == '__main__':
    main()