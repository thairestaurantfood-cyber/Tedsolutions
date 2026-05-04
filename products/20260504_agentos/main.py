import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_NAME = "agentos.db"
DB_PATH = os.path.expanduser(os.path.join("~", ".agentos", DB_NAME))

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            command TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_agent(name: str, description: str, command: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO agents (name, description, command, created_at) VALUES (?, ?, ?, ?)",
        (name, description, command, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def list_agents():
    conn = get_db()
    rows = conn.execute("SELECT id, name, description, command, created_at FROM agents ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def demo():
    init_db()
    conn = get_db()
    conn.execute("DELETE FROM agents")
    conn.commit()

    # Insert hardcoded demo data
    demo_agents = [
        ("Web Scraper", "Scrape product prices from e-commerce sites", "python scraper.py --url {url} --output prices.json"),
        ("Email Summarizer", "Summarize long email threads", "python summarizer.py --input emails/ --output summary.txt"),
        ("Invoice Generator", "Generate invoices from CSV data", "python invoice.py --data invoices.csv --template basic.html")
    ]
    conn.executemany(
        "INSERT INTO agents (name, description, command, created_at) VALUES (?, ?, ?, ?)",
        [(name, desc, cmd, datetime.utcnow().isoformat()) for name, desc, cmd in demo_agents]
    )
    conn.commit()
    conn.close()

    # Print formatted table
    rows = list_agents()
    if not rows:
        print("No agents found")
        return

    # Calculate column widths
    col_widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
    headers = ["ID", "Name", "Description", "Command", "Created At"]
    col_widths = [max(len(h), w) for h, w in zip(headers, col_widths)]

    # Print header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        line = " | ".join(str(item).ljust(w) for item, w in zip(row, col_widths))
        print(line)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    init_db()

    if args.command == 'add':
        parser_add = subparsers.add_parser('add')
        parser_add.add_argument('--name', required=True)
        parser_add.add_argument('--description', required=True)
        parser_add.add_argument('--command', required=True)
        args = parser.parse_args()
        add_agent(args.name, args.description, args.command)
        print(f"Added agent: {args.name}")
    elif args.command == 'list':
        rows = list_agents()
        if not rows:
            print("No agents found")
            return
        headers = ["ID", "Name", "Description", "Command", "Created At"]
        col_widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
        col_widths = [max(len(h), w) for h, w in zip(headers, col_widths)]
        header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
        print(header_line)
        print("-" * len(header_line))
        for row in rows:
            line = " | ".join(str(item).ljust(w) for item, w in zip(row, col_widths))
            print(line)

if __name__ == '__main__':
    main()