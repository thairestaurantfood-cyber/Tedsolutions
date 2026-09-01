import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/invoicechaser.db')

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
            status TEXT NOT NULL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client_name, amount, due_date, status, notes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (client_name, amount, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?)
    ''', (client_name, amount, due_date, status, notes))
    conn.commit()
    conn.close()

def list_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoices')
    invoices = cursor.fetchall()
    conn.close()

    if not invoices:
        print("No invoices found.")
        return

    print(f"{'ID':<5}{'Client':<15}{'Amount':<10}{'Due Date':<12}{'Status':<10}{'Notes':<20}")
    print("-" * 72)
    for invoice in invoices:
        print(f"{invoice[0]:<5}{invoice[1]:<15}{invoice[2]:<10}{invoice[3]:<12}{invoice[4]:<10}{invoice[5]:<20}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    invoices_data = [
        ("Client A", 100.00, "2023-10-01", "Sent", "First invoice"),
        ("Client B", 200.50, "2023-10-05", "Paid", "Second invoice"),
        ("Client C", 150.75, "2023-10-10", "Overdue", "Third invoice")
    ]
    for invoice in invoices_data:
        add_invoice(*invoice)
    print("=== Invoice List ===")
    list_invoices()
    print("\n=== Reminder Report ===")
    overdue = [inv for inv in invoices_data if inv[3] == "Overdue"]
    if overdue:
        print(f"Found {len(overdue)} overdue invoice(s):")
        for inv in overdue:
            print(f"  - {inv[0]}: ${inv[1]} due {inv[2]}")
            print(f"    Reminder: Please pay your invoice of ${inv[1]} that was due on {inv[2]}.")
    else:
        print("No overdue invoices.")
    print("\n=== Summary ===")
    total = sum(inv[1] for inv in invoices_data)
    paid = sum(inv[1] for inv in invoices_data if inv[3] == "Paid")
    pending = total - paid
    print(f"Total invoiced: ${total:.2f}")
    print(f"Paid: ${paid:.2f}")
    print(f"Pending: ${pending:.2f}")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='InvoiceChaser - Track and manage invoices.')
    parser.add_argument('--demo', action='store_true', help='Run demo mode with sample data')
    
    # CRITICAL: Use parse_known_args to check for --demo before subparsers
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    # If not demo, set up subparsers for normal operation
    subs = parser.add_subparsers(dest='command')

    # add subcommand
    add_parser = subs.add_parser('add', help='Add a new invoice')
    add_parser.add_argument('--client', required=True, help='Client name')
    add_parser.add_argument('--amount', type=float, required=True, help='Invoice amount')
    add_parser.add_argument('--due', required=True, help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('--status', required=True, help='Invoice status')
    add_parser.add_argument('--notes', help='Additional notes')

    # list subcommand
    list_parser = subs.add_parser('list', help='List all invoices')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_invoice(args.client, args.amount, args.due, args.status, args.notes)
    elif args.command == 'list':
        list_invoices()

if __name__ == '__main__':
    main()