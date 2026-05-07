import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser('~/srt_cleaner.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file TEXT NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        line INTEGER NOT NULL,
        indexed_at TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = init_db()
    symbols = [
        ('~/jarvis/evolve.py', 'load_critical_rules', 'function', 190, '2026-05-07 08:00:00'),
        ('~/jarvis/evolve.py', 'rag_inject', 'function', 810, '2026-05-07 08:00:00'),
        ('~/jarvis/evolve.py', 'CRITICAL_RULES', 'variable', 199, '2026-05-07 08:00:00'),
        ('~/jarvis/buildguard.py', 'guard', 'function', 173, '2026-05-07 08:00:00'),
        ('~/jarvis/buildguard.py', 'check_syntax', 'function', 85, '2026-05-07 08:00:00'),
        ('~/jarvis/daily_plan.py', 'pick_next_product', 'function', 12, '2026-05-07 08:00:00'),
        ('~/jarvis/hermes.py', 'HermesAgent', 'class', 1, '2026-05-07 08:00:00'),
    ]
    conn.executemany(
        "INSERT INTO symbols (file, name, kind, line, indexed_at) VALUES (?, ?, ?, ?, ?)",
        symbols)
    conn.commit()
    print("ContextCraft — Codebase Index Demo")
    print("=" * 70)
    print(f"{'ID':<4} {'File':<30} {'Name':<25} {'Kind':<10} {'Line':<6}")
    print("-" * 70)
    for row in conn.execute("SELECT id, file, name, kind, line FROM symbols ORDER BY file, line").fetchall():
        print(f"{row[0]:<4} {row[1]:<30} {row[2]:<25} {row[3]:<10} {row[4]:<6}")
    total = conn.execute('SELECT COUNT(*) FROM symbols').fetchone()[0]
    print(f"\nTotal symbols indexed: {total}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='SRT Cleaner - Remove duplicates and validate SRT files')
    parser.add_argument('--demo', action='store_true', help='Run demo with hardcoded SRT data')
    args = parser.parse_args()

    if args.demo:
        demo()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()