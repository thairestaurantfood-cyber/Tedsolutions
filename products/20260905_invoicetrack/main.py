import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/invoicetrack.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client, amount, due_date, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('''
        INSERT INTO invoices (client, amount, due_date, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (client, amount, due_date, status, created_at))
    conn.commit()
    conn.close()

def list_invoices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM invoices')
    invoices = c.fetchall()
    conn.close()
    return invoices

def mark_paid(invoice_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE invoices
        SET status = 'Paid'
        WHERE id = ?
    ''', (invoice_id,))
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    add_invoice('Client A', 100.00, '2023-12-31', 'Pending')
    add_invoice('Client B', 200.00, '2023-12-15', 'Paid')
    add_invoice('Client C', 150.00, '2023-11-30', 'Overdue')
    invoices = list_invoices()
    print(f"{'ID':<5}{'Client':<10}{'Amount':<10}{'Due Date':<15}{'Status':<10}{'Created At':<20}")
    for invoice in invoices:
        print(f"{invoice[0]:<5}{invoice[1]:<10}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<10}{invoice[5]:<20}")

def main():
    parser = argparse.ArgumentParser(description="InvoiceTrack")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--client', required=True)
    add_parser.add_argument('--amount', type=float, required=True)
    add_parser.add_argument('--due-date', required=True)
    add_parser.add_argument('--status', required=True)
    list_parser = subparsers.add_parser('list')
    mark_parser = subparsers.add_parser('mark')
    mark_parser.add_argument('--id', type=int, required=True)
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == 'add':
        add_invoice(args.client, args.amount, args.due_date, args.status)
    elif args.command == 'list':
        invoices = list_invoices()
        print(f"{'ID':<5}{'Client':<10}{'Amount':<10}{'Due Date':<15}{'Status':<10}{'Created At':<20}")
        for invoice in invoices:
            print(f"{invoice[0]:<5}{invoice[1]:<10}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<10}{invoice[5]:<20}")
    elif args.command == 'mark':
        mark_paid(args.id)

if __name__ == "__main__":
    main()