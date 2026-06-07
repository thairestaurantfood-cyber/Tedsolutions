import os
import sys
import sqlite3
import argparse
from datetime import datetime
import random
import string

DB_PATH = os.path.expanduser('~/sandbox.db')

def generate_ngrok_url():
    return f"https://{random.choice(string.ascii_lowercase)}{random.randint(1000, 9999)}.ngrok.io"

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sandboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            container_id TEXT,
            preview_url TEXT,
            status TEXT DEFAULT 'running',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sandboxes (name, container_id, preview_url, status)
        VALUES (?, ?, ?, ?)
    ''', ('demo-app', 'abc123', generate_ngrok_url(), 'running'))
    cursor.execute('''
        INSERT INTO sandboxes (name, container_id, preview_url, status)
        VALUES (?, ?, ?, ?)
    ''', ('test-app', 'def456', generate_ngrok_url(), 'stopped'))
    cursor.execute('''
        INSERT INTO sandboxes (name, container_id, preview_url, status)
        VALUES (?, ?, ?, ?)
    ''', ('sample-app', 'ghi789', generate_ngrok_url(), 'running'))
    conn.commit()
    cursor.execute('SELECT * FROM sandboxes')
    rows = cursor.fetchall()
    print(f"{'ID':<5}{'Name':<15}{'Container ID':<20}{'Preview URL':<30}{'Status':<10}{'Created At':<20}")
    print("-" * 90)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<15}{row[2]:<20}{row[3]:<30}{row[4]:<10}{row[5]:<20}")
    conn.close()
    print("\nDemo complete.")

def add_sandbox(name):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    container_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    preview_url = generate_ngrok_url()
    cursor.execute('''
        INSERT INTO sandboxes (name, container_id, preview_url)
        VALUES (?, ?, ?)
    ''', (name, container_id, preview_url))
    conn.commit()
    conn.close()
    print(f"Sandbox '{name}' created with container ID {container_id} and preview URL {preview_url}")

def list_sandboxes():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sandboxes')
    rows = cursor.fetchall()
    print(f"{'ID':<5}{'Name':<15}{'Container ID':<20}{'Preview URL':<30}{'Status':<10}{'Created At':<20}")
    print("-" * 90)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<15}{row[2]:<20}{row[3]:<30}{row[4]:<10}{row[5]:<20}")
    conn.close()

def report_sandboxes():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT status, COUNT(*) FROM sandboxes GROUP BY status')
    rows = cursor.fetchall()
    print(f"{'Status':<10}{'Count':<10}")
    print("-" * 20)
    for row in rows:
        print(f"{row[0]:<10}{row[1]:<10}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Sandbox CLI")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a new sandbox')
    add_parser.add_argument('name', help='Name of the sandbox')
    list_parser = subparsers.add_parser('list', help='List all sandboxes')
    report_parser = subparsers.add_parser('report', help='Generate a report of sandboxes')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == 'add':
        add_sandbox(args.name)
    elif args.command == 'list':
        list_sandboxes()
    elif args.command == 'report':
        report_sandboxes()

if __name__ == "__main__":
    main()