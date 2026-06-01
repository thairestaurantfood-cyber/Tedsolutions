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
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT NOT NULL,
        notes TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client_name, amount, issue_date, due_date, status, notes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (client_name, amount, issue_date, due_date, status, notes))
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

    print(f"{'ID':<5}{'Client':<20}{'Amount':<10}{'Issue Date':<15}{'Due Date':<15}{'Status':<10}{'Notes':<20}")
    print("-" * 90)
    for invoice in invoices:
        print(f"{invoice[0]:<5}{invoice[1]:<20}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<15}{invoice[5]:<10}{invoice[6]:<20}")

def generate_report(start_date, end_date):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT client_name, amount, issue_date, due_date, status, notes
    FROM invoices
    WHERE issue_date BETWEEN ? AND ?
    ''', (start_date, end_date))
    invoices = cursor.fetchall()
    conn.close()

    if not invoices:
        print("No invoices found in the specified date range.")
        return

    print(f"Invoice Report from {start_date} to {end_date}")
    print(f"{'Client':<20}{'Amount':<10}{'Issue Date':<15}{'Due Date':<15}{'Status':<10}{'Notes':<20}")
    print("-" * 90)
    total_amount = 0
    for invoice in invoices:
        print(f"{invoice[0]:<20}{invoice[1]:<10}{invoice[2]:<15}{invoice[3]:<15}{invoice[4]:<10}{invoice[5]:<20}")
        total_amount += invoice[1]
    print("-" * 90)
    print(f"{'Total':<20}{total_amount:<10}")

def check_overdue_invoices():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    SELECT client_name, amount, due_date
    FROM invoices
    WHERE due_date < ? AND status != 'Paid'
    ''', (today,))
    overdue_invoices = cursor.fetchall()
    conn.close()

    if not overdue_invoices:
        print("No overdue invoices found.")
        return

    print("Overdue Invoices:")
    print(f"{'Client':<20}{'Amount':<10}{'Due Date':<15}")
    print("-" * 45)
    for invoice in overdue_invoices:
        print(f"{invoice[0]:<20}{invoice[1]:<10}{invoice[2]:<15}")

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
    VALUES ('Acme Corp', 1000.00, '2023-01-01', '2023-01-31', 'Paid', 'Quarterly payment')
    ''')
    cursor.execute('''
    INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
    VALUES ('Globex Inc', 1500.00, '2023-02-01', '2023-02-28', 'Pending', 'Monthly service')
    ''')
    cursor.execute('''
    INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
    VALUES ('Initech', 2000.00, '2023-03-01', '2023-03-31', 'Overdue', 'Annual maintenance')
    ''')
    conn.commit()
    cursor.execute('SELECT * FROM invoices')
    invoices = cursor.fetchall()
    conn.close()

    print(f"{'ID':<5}{'Client':<20}{'Amount':<10}{'Issue Date':<15}{'Due Date':<15}{'Status':<10}{'Notes':<20}")
    print("-" * 90)
    for invoice in invoices:
        print(f"{invoice[0]:<5}{invoice[1]:<20}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<15}{invoice[5]:<10}{invoice[6]:<20}")
    print("Demo complete.")

def main():
    parser = argparse.ArgumentParser(description="InvoiceChaser - Invoice tracking tool")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add invoice command
    add_parser = subparsers.add_parser('add', help='Add a new invoice')
    add_parser.add_argument('--client', required=True, help='Client name')
    add_parser.add_argument('--amount', type=float, required=True, help='Invoice amount')
    add_parser.add_argument('--issue-date', required=True, help='Issue date (YYYY-MM-DD)')
    add_parser.add_argument('--due-date', required=True, help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('--status', required=True, help='Invoice status')
    add_parser.add_argument('--notes', help='Additional notes')

    # List invoices command
    subparsers.add_parser('list', help='List all invoices')

    # Generate report command
    report_parser = subparsers.add_parser('report', help='Generate invoice report')
    report_parser.add_argument('--start-date', required=True, help='Start date (YYYY-MM-DD)')
    report_parser.add_argument('--end-date', required=True, help='End date (YYYY-MM-DD)')

    # Check overdue invoices command
    subparsers.add_parser('overdue', help='Check for overdue invoices')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_invoice(args.client, args.amount, args.issue_date, args.due_date, args.status, args.notes)
        print("Invoice added successfully.")
    elif args.command == 'list':
        list_invoices()
    elif args.command == 'report':
        generate_report(args.start_date, args.end_date)
    elif args.command == 'overdue':
        check_overdue_invoices()

if __name__ == "__main__":
    main()