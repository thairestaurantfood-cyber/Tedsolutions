import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/voker.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            agent_name TEXT NOT NULL,
            session_id TEXT NOT NULL,
            log_level TEXT NOT NULL,
            message TEXT NOT NULL,
            metadata TEXT,
            file_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_log(agent_name, session_id, log_level, message, metadata=None, file_path=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    metadata_str = json.dumps(metadata) if metadata else None
    c.execute('''
        INSERT INTO logs (timestamp, agent_name, session_id, log_level, message, metadata, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, agent_name, session_id, log_level, message, metadata_str, file_path))
    conn.commit()
    conn.close()

def generate_report(format_type='console'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if format_type == 'csv':
        print("id,timestamp,agent_name,session_id,log_level,message,metadata,file_path")
        c.execute('SELECT * FROM logs ORDER BY timestamp DESC')
        for row in c.fetchall():
            print(",".join(str(x) if x is not None else "" for x in row))
    else:
        c.execute('SELECT * FROM logs ORDER BY timestamp DESC')
        rows = c.fetchall()
        if not rows:
            print("No logs found")
            return

        print(f"{'ID':<5} {'Timestamp':<25} {'Agent':<20} {'Session':<15} {'Level':<8} {'Message':<30} {'File'}")
        print("-" * 140)
        for row in rows:
            print(f"{row[0]:<5} {row[1]:<25} {row[2]:<20} {row[3]:<15} {row[4]:<8} {row[5][:30]:<30} {row[7] if row[7] else 'None'}")

    conn.close()

def error_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT agent_name, COUNT(*) as error_count, session_id
        FROM logs
        WHERE log_level = 'ERROR'
        GROUP BY agent_name, session_id
        ORDER BY error_count DESC
    ''')
    errors = c.fetchall()
    conn.close()

    if not errors:
        print("No errors found")
        return

    print("\nError Summary:")
    print(f"{'Agent':<20} {'Errors':<10} {'Session'}")
    print("-" * 45)
    for agent, count, session in errors:
        print(f"{agent:<20} {count:<10} {session}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    add_log(
        agent_name="invoice_processor",
        session_id="sess_001",
        log_level="INFO",
        message="Processing invoice PDF",
        metadata={"invoice_id": "INV-2024-001", "amount": 1250.50},
        file_path="/tmp/invoice.pdf"
    )
    add_log(
        agent_name="invoice_processor",
        session_id="sess_001",
        log_level="INFO",
        message="Invoice processed successfully",
        metadata={"invoice_id": "INV-2024-001", "amount": 1250.50},
        file_path="/tmp/invoice_processed.pdf"
    )
    add_log(
        agent_name="email_agent",
        session_id="sess_002",
        log_level="WARNING",
        message="Email server connection slow",
        metadata={"response_time": 4500},
        file_path=None
    )
    add_log(
        agent_name="file_organizer",
        session_id="sess_003",
        log_level="ERROR",
        message="Failed to move file: permission denied",
        metadata={"source": "/tmp/file.txt", "target": "/archive/file.txt"},
        file_path="/tmp/file.txt"
    )
    add_log(
        agent_name="file_organizer",
        session_id="sess_003",
        log_level="INFO",
        message="File moved successfully",
        metadata={"source": "/tmp/file.txt", "target": "/archive/file.txt"},
        file_path="/archive/file.txt"
    )

    print("\nVoker Demo Report:")
    print("=" * 80)
    generate_report()
    print("\nError Summary:")
    print("=" * 80)
    error_summary()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="Voker - Agent Logging System")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    report_parser = subparsers.add_parser('report', help='Generate log report')
    report_parser.add_argument('--csv', action='store_true', help='Output in CSV format')

    subparsers.add_parser('errors', help='Show error summary')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    init_db()
    if args.command == 'report':
        generate_report('csv' if args.csv else 'console')
    elif args.command == 'errors':
        error_summary()

if __name__ == '__main__':
    main()