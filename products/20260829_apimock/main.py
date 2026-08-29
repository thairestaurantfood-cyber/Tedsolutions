import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

DB_PATH = os.path.expanduser('~/apimock.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            method TEXT NOT NULL,
            schema TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_endpoint(path, method, schema):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO endpoints (path, method, schema)
        VALUES (?, ?, ?)
    ''', (path, method, schema))
    conn.commit()
    conn.close()

def list_endpoints():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, path, method, created_at FROM endpoints')
    endpoints = cursor.fetchall()
    conn.close()

    print(f"{'ID':<5}{'Path':<20}{'Method':<10}{'Created':<20}")
    print('-' * 55)
    for endpoint in endpoints:
        print(f"{endpoint[0]:<5}{endpoint[1]:<20}{endpoint[2]:<10}{endpoint[3]:<20}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()

    endpoints = [
        ('/users', 'GET', '{"type": "array", "items": {"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}}'),
        ('/users', 'POST', '{"type": "object", "properties": {"name": {"type": "string"}}}'),
        ('/users/{id}', 'GET', '{"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}')
    ]

    for endpoint in endpoints:
        add_endpoint(*endpoint)

    list_endpoints()
    sys.exit(0)

def main():
    if '--demo' in sys.argv:
        demo()
        return

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('path', type=str)
    add_parser.add_argument('method', type=str)
    add_parser.add_argument('schema', type=str)

    list_parser = subparsers.add_parser('list')

    args = parser.parse_args()

    if not hasattr(args, 'command'):
        parser.print_help()
        return

    if args.command == 'add':
        add_endpoint(args.path, args.method, args.schema)
    elif args.command == 'list':
        list_endpoints()

if __name__ == "__main__":
    main()