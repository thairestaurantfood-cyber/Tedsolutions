import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.buildguard/reports.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        path TEXT NOT NULL,
        score INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        passed INTEGER NOT NULL,
        syntax_ok INTEGER NOT NULL,
        demo_ok INTEGER NOT NULL,
        help_ok INTEGER NOT NULL,
        checked_at TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = init_db()
    runs = [
        ('AgentLog', '/home/tedsa/jarvis/products/20260507_agentlog/main.py', 13, 12, 1, 1, 1, 1, '2026-05-07 08:03:00'),
        ('SRTDoctor', '/home/tedsa/jarvis/products/20260507_srtdoctor/main.py', 13, 12, 1, 1, 1, 1, '2026-05-07 08:01:00'),
        ('tokentamer', '/home/tedsa/jarvis/products/20260506_tokentamer/main.py', 6, 12, 0, 1, 0, 1, '2026-05-06 08:05:00'),
        ('invoicer', '/home/tedsa/jarvis/products/20260426_invoicer/main.py', 2, 12, 0, 0, 0, 0, '2026-04-26 08:10:00'),
    ]
    conn.executemany(
        "INSERT INTO runs (product, path, score, max_score, passed, syntax_ok, demo_ok, help_ok, checked_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        runs)
    conn.commit()
    print("BuildGuardCLI — Eval History")
    print("=" * 70)
    print(f"{'ID':<4} {'Product':<20} {'Score':<8} {'Pass':<6} {'Syntax':<8} {'Demo':<6} {'Help':<6}")
    print("-" * 70)
    for row in conn.execute("SELECT id, product, score, max_score, passed, syntax_ok, demo_ok, help_ok FROM runs").fetchall():
        passed = '✅' if row[4] else '❌'
        syntax = '✅' if row[5] else '❌'
        demo = '✅' if row[6] else '❌'
        help_ = '✅' if row[7] else '❌'
        print(f"{row[0]:<4} {row[1]:<20} {row[2]}/{row[3]:<5} {passed:<6} {syntax:<8} {demo:<6} {help_:<6}")
    conn.close()

def list_reports():
    conn = init_db()
    rows = conn.execute("SELECT * FROM srt_reports ORDER BY generated_at DESC").fetchall()
    if not rows:
        print("No reports found")
        return

    print("SRT Reports:")
    print("ID | Filename | Original | Cleaned | Duplicates | Timestamps | Formatting | Generated")
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]} | {row[7]}")

    conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    subparsers.add_parser('report', help='Generate report for SRT file')
    subparsers.add_parser('list', help='List all reports')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'report':
        generate_report("example.srt")
    elif args.command == 'list':
        list_reports()
if __name__ == '__main__':
    main()
