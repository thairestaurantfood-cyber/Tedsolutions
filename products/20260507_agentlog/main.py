import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/agentlog.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            script TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            duration_seconds INTEGER,
            errors INTEGER DEFAULT 0,
            steps INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    runs = [
        ('jarvis-builder', 'evolve.py', 'completed', '2026-05-07 08:00:00', '2026-05-07 08:03:42', 222, 0, 13),
        ('hermes-overseer', 'hermes_check.py', 'completed', '2026-05-07 09:00:00', '2026-05-07 09:00:18', 18, 0, 7),
        ('daily-planner', 'daily_plan.py', 'failed', '2026-05-07 00:00:00', '2026-05-07 00:00:05', 5, 1, 2),
    ]
    c.executemany(
        "INSERT INTO runs (agent_name, script, status, started_at, ended_at, duration_seconds, errors, steps) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        runs)
    conn.commit()
    print("AgentLog Demo — Structured Agent Run History")
    print("=" * 65)
    print(f"{'ID':<4} {'Agent':<20} {'Status':<10} {'Duration':>8} {'Errors':>6} {'Steps':>5}")
    print("-" * 65)
    c.execute("SELECT id, agent_name, status, duration_seconds, errors, steps FROM runs")
    for row in c.fetchall():
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<10} {row[3]:>7}s {row[4]:>6} {row[5]:>5}")
    conn.close()

def add_file(path: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: File not found: {path}")
        conn.close()
        return

    try:
        stat = file_path.stat()
        c.execute('''
            INSERT OR IGNORE INTO files
            (path, original_name, size_bytes, duration_seconds, created_at, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            str(file_path),
            file_path.name,
            stat.st_size,
            None,
            datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'pending'
        ))
        conn.commit()
        print(f"Added file: {path}")
    except Exception as e:
        print(f"Error adding file: {e}")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='File tracking system')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a file to tracking')
    add_parser.add_argument('path', type=str, help='Path to file to add')
    args = parser.parse_args()
    if args.command == 'add':
        add_file(args.path)
        add_file(args.path)

if __name__ == '__main__':
    main()