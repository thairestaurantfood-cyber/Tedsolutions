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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            report_type TEXT NOT NULL,
            parameters TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            file_path TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            triggered_at TEXT NOT NULL,
            resolved_at TEXT,
            is_resolved INTEGER DEFAULT 0
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

def generate_report(name: str, report_type: str, parameters: str):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO reports (name, report_type, parameters, generated_at, file_path) VALUES (?, ?, ?, ?, ?)",
            (name, report_type, parameters, datetime.datetime.utcnow().isoformat(), "")
        )
        conn.commit()
        print(f"Generated report: {name}")
    except sqlite3.IntegrityError:
        print(f"Report '{name}' already exists")
    finally:
        conn.close()

def demo():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM datasets")
    cur.execute("DELETE FROM insights")
    cur.execute("DELETE FROM reports")
    cur.execute("DELETE FROM alerts")
    conn.commit()

    cur.execute("""
        INSERT OR IGNORE INTO datasets (name, path, created_at)
        VALUES (?, ?, ?)
    """, ("Sample Sales", "/data/sales.csv", "2026-01-01T00:00:00"))
    cur.execute("""
        INSERT OR IGNORE INTO datasets (name, path, created_at)
        VALUES (?, ?, ?)
    """, ("Customer Churn", "/data/churn.csv", "2026-01-02T00:00:00"))
    cur.execute("""
        INSERT OR IGNORE INTO insights (dataset_id, insight_type, summary, details, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (1, "correlation", "High correlation between price and quantity", "Price ↑ → Quantity ↑", "2026-01-03T00:00:00"))
    cur.execute("""
        INSERT OR IGNORE INTO reports (name, report_type, parameters, generated_at, file_path)
        VALUES (?, ?, ?, ?, ?)
    """, ("Sales Summary", "summary", "{}", "2026-01-04T00:00:00", "/reports/sales_summary.pdf"))
    cur.execute("""
        INSERT OR IGNORE INTO alerts (alert_type, message, severity, triggered_at, resolved_at, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ("data_quality", "Missing values detected in churn dataset", "medium", "2026-01-05T00:00:00", None, 0))

    conn.commit()

    print("\n=== DEMO DATASETS ===")
    for row in cur.execute("SELECT id, name, path, created_at FROM datasets ORDER BY id"):
        print(f"Dataset: {row['name']} | {row['path']}")

    print("\n=== DEMO INSIGHTS ===")
    for row in cur.execute("SELECT insight_type, summary, details FROM insights ORDER BY id"):
        print(f"{row['insight_type']}: {row['summary']} | {row['details']}")

    print("\n=== DEMO REPORTS ===")
    for row in cur.execute("SELECT name, report_type, generated_at FROM reports ORDER BY id"):
        print(f"Report: {row['name']} ({row['report_type']}) | {row['generated_at']}")

    print("\n=== DEMO ALERTS ===")
    for row in cur.execute("SELECT alert_type, message, severity FROM alerts WHERE is_resolved = 0 ORDER BY id"):
        print(f"Alert: {row['alert_type']} | {row['message']} ({row['severity']})")

    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="PyAnalyst - CLI Data Analysis Tool")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a dataset')
    add_parser.add_argument('name', help='Dataset name')
    add_parser.add_argument('path', help='Dataset file path')
    add_parser.set_defaults(func=lambda args: add_dataset(args.name, args.path))

    list_parser = subparsers.add_parser('list', help='List all datasets')
    list_parser.set_defaults(func=lambda args: list_datasets())

    report_parser = subparsers.add_parser('report', help='Generate a report')
    report_parser.add_argument('name', help='Report name')
    report_parser.add_argument('--type', dest='report_type', default='summary', help='Report type')
    report_parser.add_argument('--params', dest='parameters', default='{}', help='Report parameters')
    report_parser.set_defaults(func=lambda args: generate_report(args.name, args.report_type, args.parameters))

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == '__main__':
    main()