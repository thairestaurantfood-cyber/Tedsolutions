import os
import sys
import json
import sqlite3
import argparse
import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.pyanalyst/pyanalyst.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER NOT NULL,
            insight_type TEXT NOT NULL,
            summary TEXT NOT NULL,
            details TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id)
        )
    """)
    conn.commit()
    return conn

def add_dataset(name: str, path: str):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO datasets (name, path, created_at) VALUES (?, ?, ?)",
            (name, path, datetime.datetime.utcnow().isoformat())
        )
        conn.commit()
        print(f"Added dataset: {name}")
    except sqlite3.IntegrityError:
        print(f"Dataset '{name}' already exists")
    finally:
        conn.close()

def list_datasets():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, name, path, created_at FROM datasets ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No datasets found")
        return

    max_name = max(len(row['name']) for row in rows)
    max_path = max(len(row['path']) for row in rows)

    header = f"{'ID':<4} {'Name':<{max_name}} {'Path':<{max_path}} {'Created'}"
    print(header)
    print("-" * len(header))

    for row in rows:
        print(f"{row['id']:<4} {row['name']:<{max_name}} {row['path']:<{max_path}} {row['created_at']}")

def demo():
    conn = get_db()
    cur = conn.cursor()

    # Clear existing demo data
    cur.execute("DELETE FROM insights")
    cur.execute("DELETE FROM datasets")

    # Insert hardcoded datasets
    demo_datasets = [
        ("sales_2024", "/home/user/data/sales_2024.csv", "2024-01-15T10:00:00"),
        ("users_2024", "/home/user/data/users_2024.csv", "2024-01-16T11:30:00"),
    ]

    for name, path, created in demo_datasets:
        cur.execute(
            "INSERT INTO datasets (name, path, created_at) VALUES (?, ?, ?)",
            (name, path, created)
        )

    conn.commit()

    # Query and display
    list_datasets()
    conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--name', required=True)
    add_parser.add_argument('--path', required=True)

    subparsers.add_parser('list')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_dataset(args.name, args.path)
    elif args.command == 'list':
        list_datasets()

if __name__ == '__main__':
    main()