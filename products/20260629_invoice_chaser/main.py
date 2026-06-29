import argparse
import os
import sqlite3

DB_PATH = os.path.expanduser('~/.invoice_chaser.db')

def create_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date DATE NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_invoice(client, amount, due_date, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (client, amount, due_date, status) VALUES (?, ?, ?, ?)
    ''', (client, amount, due_date, status))
    conn.commit()
    conn.close()

def list_invoices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoices')
    rows = cursor.fetchall()
    conn.close()
    return rows

def demo():
    create_db()
    add_invoice('Client A', 150.0, '2023-10-01', 'pending')
    add_invoice('Client B', 300.0, '2023-11-01', 'paid')
    rows = list_invoices()
    print(f"{'ID':<10} {'Client':<15} {'Amount':<10} {'Due Date':<15} {'Status':<10}")
    for row in rows:
        print(f"{row[0]:<10} {row[1]:<15} {row[2]:<10} {row[3]:<15} {row[4]:<10}")

def main():
    parser = argparse.ArgumentParser()
    if '--demo' in sys.argv:
        demo()
        return
    parser.add_argument('--demo', action='store_true')
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a new invoice')
    add_parser.add_argument('client', type=str, help='Client name')
    add_parser.add_argument('amount', type=float, help='Invoice amount')
    add_parser.add_argument('due_date', type=str, help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('status', type=str, help='Invoice status (pending, paid)')
    list_parser = subparsers.add_parser('list', help='List all invoices')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == 'add':
        add_invoice(args.client, args.amount, args.due_date, args.status)
        print("Invoice added successfully")
    elif args.command == 'list':
        rows = list_invoices()
        print(f"{'ID':<10} {'Client':<15} {'Amount':<10} {'Due Date':<15} {'Status':<10}")
        for row in rows:
            print(f"{row[0]:<10} {row[1]:<15} {row[2]:<10} {row[3]:<15} {row[4]:<10}")

if __name__ == "__main__":
    main()