import os
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/mcp_router.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            command TEXT NOT NULL,
            args TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_server(name, command, args=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute(
        'INSERT OR REPLACE INTO servers (name, command, args, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        (name, command, args or '[]', now, now)
    )
    conn.commit()
    conn.close()

def list_servers():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, command, args FROM servers')
    rows = c.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    add_server('file', 'python', '["-m", "mcp.server.file"]')
    add_server('git', 'node', '["/path/to/git-server.js"]')
    add_server('python', 'python', '["-m", "mcp.server.python"]')

    rows = list_servers()
    print("MCP Servers:")
    print("Name | Command | Args")
    print("---|---|---")
    for name, command, args in rows:
        print(f"{name} | {command} | {args}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    args, _ = parser.parse_known_args()
    if args.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add an MCP server')
    add_parser.add_argument('--name', required=True)
    add_parser.add_parser('add', help='Add an MCP server')
    add_parser.add_argument('--command', required=True)
    add_parser.add_argument('--args', default='[]')

    list_parser = subparsers.add_parser('list', help='List MCP servers')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_server(args.name, args.command, args.args)
    elif args.command == 'list':
        rows = list_servers()
        print("MCP Servers:")
        print("Name | Command | Args")
        print("---|---|---")
        for name, command, args in rows:
            print(f"{name} | {command} | {args}")

if __name__ == '__main__':
    main()