import argparse
import json
import os
import sys
import sqlite3
import re
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.jarvis/agent_bridge.db')

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    try:
        os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wrapped_tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                command TEXT NOT NULL,
                args TEXT NOT NULL,
                help_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        demo_data = [
            ('ls', 'ls', '["-l"]', 'List directory contents', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('grep', 'grep', '["-r", "pattern"]', 'Search text using patterns', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('find', 'find', '["-name", "filename"]', 'Search for files in a directory hierarchy', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ]

        cursor.executemany('''
            INSERT INTO wrapped_tools (tool_name, command, args, help_text, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', demo_data)

        conn.commit()

        print(f"{'ID':<5}{'Tool Name':<15}{'Command':<15}{'Args':<20}{'Help Text':<30}{'Created At'}")
        print("-" * 90)

        cursor.execute('SELECT * FROM wrapped_tools')
        rows = cursor.fetchall()

        for row in rows:
            print(f"{row[0]:<5}{row[1]:<15}{row[2]:<15}{row[3]:<20}{row[4]:<30}{row[5]}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="AgentBridge - CLI Tool Wrapper Registry")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')

    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add subparsers for other commands here if needed

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

if __name__ == "__main__":
    main()