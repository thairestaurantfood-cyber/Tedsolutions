import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re
import time

DB_PATH = os.path.expanduser('~/.doublecheck/bookings.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            event_id TEXT,
            title TEXT,
            start_ts REAL NOT NULL,
            end_ts REAL NOT NULL,
            timezone TEXT NOT NULL,
            duration_minutes INTEGER NOT NULL,
            guests INTEGER DEFAULT 1,
            payload TEXT,
            created_at REAL DEFAULT (strftime('%s','now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings(start_ts)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_bookings_end ON bookings(end_ts)
    """)
    conn.commit()
    return conn

def parse_csv_row(row, source):
    title = row.get('title', '')
    start_str = row.get('start', '')
    end_str = row.get('end', '')
    tz = row.get('timezone', 'UTC')
    guests = int(row.get('guests', 1))

    try:
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    except Exception:
        try:
            start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
            end_dt = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            raise ValueError(f"Unparseable datetime in row: {row}")

    duration = int((end_dt - start_dt).total_seconds() / 60)

    return {
        'source': source,
        'title': title,
        'start_ts': start_dt.timestamp(),
        'end_ts': end_dt.timestamp(),
        'timezone': tz,
        'duration_minutes': duration,
        'guests': guests,
        'event_id': row.get('event_id', '')
    }

def add_bookings_from_csv(conn, csv_path, source):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            try:
                parsed = parse_csv_row(row, source)
                rows.append(parsed)
            except Exception as e:
                print(f"Skipping row due to error: {e}", file=sys.stderr)

        if not rows:
            print("No valid rows found in CSV.", file=sys.stderr)
            return 0

        inserted = 0
        for r in rows:
            conn.execute("""
                INSERT INTO bookings
                (source, event_id, title, start_ts, end_ts, timezone, duration_minutes, guests)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r['source'], r['event_id'], r['title'], r['start_ts'],
                r['end_ts'], r['timezone'], r['duration_minutes'], r['guests']
            ))
            inserted += 1
        conn.commit()
        return inserted

def demo():
    conn = get_db()
    conn.execute("DELETE FROM bookings")

    demo_data = [
        {
            'source': 'google',
            'event_id': 'evt_001',
            'title': 'Team Sync',
            'start': '2026-05-05 09:00:00',
            'end': '2026-05-05 10:00:00',
            'timezone': 'Asia/Bangkok',
            'guests': 3
        },
        {
            'source': 'outlook',
            'event_id': 'evt_002',
            'title': 'Client Call',
            'start': '2026-05-05 14:00:00',
            'end': '2026-05-05 15:30:00',
            'timezone': 'Asia/Bangkok',
            'guests': 1
        }
    ]

    for row in demo_data:
        start_dt = datetime.strptime(row['start'], '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(row['end'], '%Y-%m-%d %H:%M:%S')
        duration = int((end_dt - start_dt).total_seconds() / 60)

        conn.execute("""
            INSERT INTO bookings
            (source, event_id, title, start_ts, end_ts, timezone, duration_minutes, guests)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['source'], row['event_id'], row['title'],
            start_dt.timestamp(), end_dt.timestamp(),
            row['timezone'], duration, row['guests']
        ))

    conn.commit()
    conn.close()
    print("Demo data loaded. Use 'doublecheck show' to view.")

def show_bookings(conn):
    cur = conn.execute("""
        SELECT id, source, title, start_ts, end_ts, timezone, guests
        FROM bookings
        ORDER BY start_ts
    """)
    rows = cur.fetchall()

    if not rows:
        print("No bookings found.")
        return

    for r in rows:
        start_dt = datetime.fromtimestamp(r[3])
        end_dt = datetime.fromtimestamp(r[4])
        print(f"{r[0]} | {r[1]} | {r[2]} | {start_dt} | {end_dt} | {r[5]} | Guests: {r[6]}")

def main():
    parser = argparse.ArgumentParser(description='DoubleCheck CLI - Booking conflict checker')
    parser.add_argument('--demo', action='store_true', help='Load demo data')
    parser.add_argument('command', nargs='?', choices=['show'], help='Command to run')

    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if args.command == 'show':
        conn = get_db()
        show_bookings(conn)
        conn.close()
        return

    parser.print_help()

if __name__ == '__main__':
    main()