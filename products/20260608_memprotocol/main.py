import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/memprotocol.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_memory(agent, key, value):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO memory (agent, key, value, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (agent, key, value, datetime.now(), datetime.now()))
    conn.commit()
    conn.close()

def list_memory():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, agent, key, value, created_at, updated_at FROM memory')
    rows = cursor.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    add_memory('agent1', 'key1', 'value1')
    add_memory('agent2', 'key2', 'value2')
    rows = list_memory()
    print(f"{'ID':<5}{'Agent':<10}{'Key':<10}{'Value':<10}{'Created':<20}{'Updated':<20}")
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<10}{row[3]:<10}{row[4]:<20}{row[5]:<20}")
    sys.exit(0)

def main():
    if '--demo' in sys.argv:
        demo()
        return
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--agent', required=True)
    add_parser.add_argument('--key', required=True)
    add_parser.add_argument('--value', required=True)

    list_parser = subparsers.add_parser('list')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_memory(args.agent, args.key, args.value)
    elif args.command == 'list':
        rows = list_memory()
        print(f"{'ID':<5}{'Agent':<10}{'Key':<10}{'Value':<10}{'Created':<20}{'Updated':<20}")
        for row in rows:
            print(f"{row[0]:<5}{row[1]:<10}{row[2]:<10}{row[3]:<10}{row[4]:<20}{row[5]:<20}")

if __name__ == "__main__":
    main()