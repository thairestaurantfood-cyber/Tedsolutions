import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/hermeswatch.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS status_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent TEXT NOT NULL,
        status TEXT NOT NULL,
        builds_today INTEGER DEFAULT 0,
        last_build TEXT,
        last_score INTEGER,
        cron_healthy INTEGER DEFAULT 1,
        checked_at TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = init_db()
    rows = [
        ('hermes-gateway', 'running', 0, None, None, 1, '2026-05-07 08:00:00'),
        ('jarvis-builder', 'complete', 4, '20260507_mcprouter', 12, 1, '2026-05-07 08:05:00'),
        ('hermes-overseer', 'running', 2, '20260507_agentlog', 13, 1, '2026-05-07 09:00:00'),
        ('daily-planner', 'idle', 0, None, None, 1, '2026-05-07 00:00:00'),
        ('meta-evolution', 'scheduled', 0, None, None, 1, '2026-05-07 22:30:00'),
    ]
    conn.executemany(
        "INSERT INTO status_log (agent, status, builds_today, last_build, last_score, cron_healthy, checked_at) VALUES (?,?,?,?,?,?,?)",
        rows)
    conn.commit()
    print("HermesWatch — Agent Status Dashboard")
    print("=" * 75)
    print(f"{'ID':<4} {'Agent':<20} {'Status':<12} {'Builds':<7} {'Last Build':<22} {'Score':<6} {'Cron':<5}")
    print("-" * 75)
    for row in conn.execute("SELECT id, agent, status, builds_today, last_build, last_score, cron_healthy FROM status_log").fetchall():
        score = str(row[5]) if row[5] else '-'
        build = row[4] or '-'
        cron = '✅' if row[6] else '❌'
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<12} {row[3]:<7} {build:<22} {score:<6} {cron:<5}")
    conn.close()

def show_status(conn):
    print("HermesWatch — Current Agent Status")
    print("=" * 75)
    print(f"{'ID':<4} {'Agent':<20} {'Status':<12} {'Builds':<7} {'Last Build':<22} {'Score':<6} {'Cron':<5}")
    print("-" * 75)
    for row in conn.execute("SELECT id, agent, status, builds_today, last_build, last_score, cron_healthy FROM status_log").fetchall():
        score = str(row[5]) if row[5] else '-'
        build = row[4] or '-'
        cron = '✅' if row[6] else '❌'
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<12} {row[3]:<7} {build:<22} {score:<6} {cron:<5}")

def show_history(conn):
    print("HermesWatch — Build History")
    print("=" * 75)
    print(f"{'ID':<4} {'Agent':<20} {'Status':<12} {'Builds':<7} {'Last Build':<22} {'Score':<6} {'Checked At':<20}")
    print("-" * 75)
    for row in conn.execute("SELECT id, agent, status, builds_today, last_build, last_score, checked_at FROM status_log ORDER BY id DESC").fetchall():
        score = str(row[5]) if row[5] else '-'
        build = row[4] or '-'
        print(f"{row[0]:<4} {row[1]:<20} {row[2]:<12} {row[3]:<7} {build:<22} {score:<6} {row[6]:<20}")

def main():
    parser = argparse.ArgumentParser(description="HermesWatch — Hermes agent status dashboard")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    status_parser = subparsers.add_parser('status', help='Show current Hermes status')
    history_parser = subparsers.add_parser('history', help='Show build history')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    conn = init_db()
    if args.command == 'status':
        show_status(conn)
    elif args.command == 'history':
        show_history(conn)
    conn.close()

if __name__ == "__main__":
    main()