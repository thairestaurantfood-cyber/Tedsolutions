import os
import sys
import json
import sqlite3
from datetime import datetime
from argparse import ArgumentParser, Namespace

DB_PATH = os.path.expanduser('~/mcp_inspector.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS mcp_calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            server_name TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            parameters TEXT NOT NULL,
            response_time_ms INTEGER,
            success INTEGER NOT NULL,
            error_message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_call(server_name, tool_name, parameters, response_time_ms=None, success=1, error_message=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO mcp_calls
        (timestamp, server_name, tool_name, parameters, response_time_ms, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        server_name,
        tool_name,
        json.dumps(parameters),
        response_time_ms,
        success,
        error_message
    ))
    conn.commit()
    conn.close()

def get_recent_calls(limit):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM mcp_calls ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = c.fetchall()
    conn.close()
    return rows

def clear_log():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Insert hardcoded demo data
    demo_calls = [
        ('ac_ledger', 'record_transaction', {'account': '12345', 'amount': 100.00, 'description': 'Payment'}, 50, 1, None),
        ('ac_market', 'get_price', {'symbol': 'AAPL'}, 30, 1, None),
        ('agent_registry', 'register_agent', {'name': 'John Doe', 'email': 'john.doe@example.com'}, 20, 1, None)
    ]

    for call in demo_calls:
        log_call(*call)

    # Query and print formatted table
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM mcp_calls ORDER BY timestamp DESC')
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No calls logged")
        return

    # Print header
    print("ID | Timestamp | Server       | Tool            | Parameters                   | Response(ms) | Success | Error")
    print("-" * 120)

    # Print rows
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]:<15} | {row[3]:<18} | {row[4]:<36} | {row[5]} | {row[6]} | {row[7]}")

def main():
    parser = ArgumentParser(description="MCP Inspector")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()  # check --demo FIRST
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')  # NO required=True
    # add subparsers here...
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

if __name__ == "__main__":
    main()