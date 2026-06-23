import os
import sqlite3
from datetime import datetime
import argparse

DB_PATH = os.path.expanduser('~/.cloudagent.db')

def create_table():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cloudflare_accounts (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            api_key TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_account(name, email, api_key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO cloudflare_accounts (name, email, api_key) VALUES (?, ?, ?)', (name, email, api_key))
    conn.commit()
    conn.close()

def list_accounts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, email, created_at FROM cloudflare_accounts')
    rows = c.fetchall()
    print(f"{'ID':<10} {'Name':<20} {'Email':<40} {'Created At':<20}")
    for row in rows:
        print(f"{row[0]:<10} {row[1]:<20} {row[2]:<40} {row[3]:<20}")
    conn.close()

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    create_table()
    add_account('Demo Account', 'demo@example.com', 'DEMO_API_KEY')
    print(f"{'ID':<10} {'Name':<20} {'Email':<40} {'Created At':<20}")
    list_accounts()

def main():
    if '--demo' in sys.argv:
        demo()
        return
    parser = argparse.ArgumentParser(description='Cloudflare Account Manager')
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a new Cloudflare account')
    add_parser.add_argument('name', type=str, help='Account name')
    add_parser.add_argument('email', type=str, help='Account email')
    add_parser.add_argument('api_key', type=str, help='Cloudflare API key')
    list_parser = subparsers.add_parser('list', help='List all Cloudflare accounts')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    create_table()
    if args.command == 'add':
        add_account(args.name, args.email, args.api_key)
    elif args.command == 'list':
        list_accounts()

if __name__ == "__main__":
    main()