import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/paylink.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO payments (amount, description, status, created_at, updated_at)
        VALUES (100.0, 'Freelance Project', 'pending', ?, ?)
    ''', (datetime.now().isoformat(), datetime.now().isoformat()))
    c.execute('''
        INSERT INTO payments (amount, description, status, created_at, updated_at)
        VALUES (250.50, 'Web Development', 'paid', ?, ?)
    ''', (datetime.now().isoformat(), datetime.now().isoformat()))
    c.execute('''
        INSERT INTO payments (amount, description, status, created_at, updated_at)
        VALUES (75.25, 'Consulting', 'pending', ?, ?)
    ''', (datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM payments')
    rows = c.fetchall()
    conn.close()

    print(f"{'ID':<5} {'Amount':<10} {'Description':<20} {'Status':<10} {'Created':<20}")
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<10.2f} {row[2]:<20} {row[3]:<10} {row[4]:<20}")
    print("Demo complete.")

def create_payment(amount, description):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO payments (amount, description, status, created_at, updated_at)
        VALUES (?, ?, 'pending', ?, ?)
    ''', (amount, description, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    payment_id = c.lastrowid
    conn.close()
    print(f"Payment link created: {payment_id}")

def list_payments():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM payments')
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No payments found")
        return

    print(f"{'ID':<5} {'Amount':<10} {'Description':<20} {'Status':<10} {'Created':<20}")
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<10.2f} {row[2]:<20} {row[3]:<10} {row[4]:<20}")

def payment_status(payment_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM payments WHERE id = ?', (payment_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        print("Payment not found")
        return

    print(f"ID: {row[0]}")
    print(f"Amount: {row[1]:.2f}")
    print(f"Description: {row[2]}")
    print(f"Status: {row[3]}")
    print(f"Created: {row[4]}")
    print(f"Updated: {row[5]}")

def remove_payment(payment_id):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM payments WHERE id = ?', (payment_id,))
    conn.commit()
    conn.close()
    print(f"Payment {payment_id} removed")

def main():
    parser = argparse.ArgumentParser(description="PayLink - Simple Payment Link Generator")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample payments')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    create_parser = subparsers.add_parser('create', help='Create a new payment link')
    create_parser.add_argument('amount', type=float, help='Payment amount')
    create_parser.add_argument('description', type=str, help='Payment description')

    subparsers.add_parser('list', help='List all payment links')

    status_parser = subparsers.add_parser('status', help='Check payment status')
    status_parser.add_argument('payment_id', type=int, help='Payment ID')

    subparsers.add_parser('remove', help='Remove a payment link')
    remove_parser = subparsers.add_parser('remove')
    remove_parser.add_argument('payment_id', type=int, help='Payment ID')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'create':
        create_payment(args.amount, args.description)
    elif args.command == 'list':
        list_payments()
    elif args.command == 'status':
        payment_status(args.payment_id)
    elif args.command == 'remove':
        remove_payment(args.payment_id)

if __name__ == "__main__":
    main()