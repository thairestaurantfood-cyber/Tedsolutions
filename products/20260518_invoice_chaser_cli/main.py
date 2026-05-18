import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = os.path.expanduser("~/.jarvis/invoice_chaser.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            amount REAL NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client, amount, issue_date, due_date, notes=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO invoices (client, amount, issue_date, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client, amount, issue_date, due_date, 'unpaid', notes))
    conn.commit()
    conn.close()
    print(f"Added invoice for {client}: {amount} due on {due_date}")

def list_invoices():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, client, amount, issue_date, due_date, status, notes
        FROM invoices
        ORDER BY due_date
    ''')
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No invoices found")
        return

    print(f"{'ID':<5} {'Client':<20} {'Amount':<10} {'Issue Date':<12} {'Due Date':<12} {'Status':<10} {'Notes':<20}")
    print("-" * 90)
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<10.2f} {row[3]:<12} {row[4]:<12} {row[5]:<10} {row[6] or '':<20}")

def mark_paid(invoice_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE invoices
        SET status = 'paid'
        WHERE id = ?
    ''', (invoice_id,))
    conn.commit()
    conn.close()
    print(f"Marked invoice {invoice_id} as paid")

def generate_overdue_report():
    today = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, client, amount, issue_date, due_date, status, notes
        FROM invoices
        WHERE due_date < ? AND status != 'paid'
        ORDER BY due_date
    ''', (today,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No overdue invoices")
        return

    print(f"{'ID':<5} {'Client':<20} {'Amount':<10} {'Due Date':<12} {'Days Overdue':<12} {'Notes':<20}")
    print("-" * 80)
    for row in rows:
        due_date = datetime.strptime(row[4], '%Y-%m-%d')
        days_overdue = (datetime.now() - due_date).days
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<10.2f} {row[4]:<12} {days_overdue:<12} {row[6] or '':<20}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    today = datetime.now().date()
    demo_data = [
        ("Client A", 100.50, (today - timedelta(days=30)).strftime('%Y-%m-%d'), (today - timedelta(days=15)).strftime('%Y-%m-%d')),
        ("Client B", 200.75, (today - timedelta(days=45)).strftime('%Y-%m-%d'), (today - timedelta(days=20)).strftime('%Y-%m-%d')),
        ("Client C", 150.25, (today - timedelta(days=20)).strftime('%Y-%m-%d'), (today + timedelta(days=10)).strftime('%Y-%m-%d'))
    ]
    for client, amount, issue_date, due_date in demo_data:
        c.execute('''
            INSERT INTO invoices (client, amount, issue_date, due_date, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client, amount, issue_date, due_date, 'unpaid', 'Demo invoice'))
    conn.commit()
    conn.close()
    print("Demo invoices created:")
    list_invoices()

def main():
    parser = argparse.ArgumentParser(description="Invoice Chaser CLI")
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a new invoice')
    add_parser.add_argument('--client', required=True)
    add_parser.add_argument('--amount', type=float, required=True)
    add_parser.add_argument('--issue-date', required=True)
    add_parser.add_argument('--due-date', required=True)
    add_parser.add_argument('--notes', default=None)

    list_parser = subparsers.add_parser('list', help='List all invoices')
    paid_parser = subparsers.add_parser('paid', help='Mark an invoice as paid')
    paid_parser.add_argument('--id', type=int, required=True)

    overdue_parser = subparsers.add_parser('overdue', help='Generate overdue report')
    demo_parser = subparsers.add_parser('demo', help='Create demo invoices')

    args = parser.parse_args()

    if args.command == 'add':
        add_invoice(args.client, args.amount, args.issue_date, args.due_date, args.notes)
    elif args.command == 'list':
        list_invoices()
    elif args.command == 'paid':
        mark_paid(args.id)
    elif args.command == 'overdue':
        generate_overdue_report()
    elif args.command == 'demo':
        demo()

if __name__ == "__main__":
    main()