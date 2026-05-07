import os
import sqlite3
import argparse
from datetime import datetime

def create_db():
    db_path = os.path.expanduser('~/.agentlog.db')
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  message TEXT)''')
    conn.commit()
    conn.close()

def add_log(message):
    db_path = os.path.expanduser('~/.agentlog.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO logs (timestamp, message) VALUES (?, ?)", (timestamp, message))
    conn.commit()
    conn.close()

def list_logs():
    db_path = os.path.expanduser('~/.agentlog.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT * FROM logs ORDER BY timestamp DESC')
    rows = c.fetchall()
    for row in rows:
        print(f"{row[1]} - {row[2]}")
    conn.close()

def filter_logs(keyword):
    db_path = os.path.expanduser('~/.agentlog.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM logs WHERE message LIKE ?", ('%' + keyword + '%',))
    rows = c.fetchall()
    for row in rows:
        print(f"{row[1]} - {row[2]}")
    conn.close()

def demo():
    create_db()
    add_log('This is a demo log entry.')
    list_logs()
    filter_logs('demo')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        exit()
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a log entry')
    add_parser.add_argument('message', type=str)
    add_parser.set_defaults(func=add_log)
    subparsers.add_parser('list', help='List all logs').set_defaults(func=list_logs)
    filter_parser = subparsers.add_parser('filter', help='Filter logs by keyword')
    filter_parser.add_argument('keyword', type=str)
    filter_parser.set_defaults(func=filter_logs)
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        exit()
    args.func(args.message if args.command == 'add' else args.keyword)