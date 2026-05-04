import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

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
    # Expected CSV columns: title,start,end,timezone,guests
    title = row.get('title', '')
    start_str = row.get('start', '')
    end_str = row.get('end', '')
    tz = row.get('timezone', 'UTC')
    guests = int(row.get('guests', 1))

    try:
        start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
    except Exception:
        # Fallback parsing for common formats
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
                (source, event_id, title, start_ts, end_ts, timezone, duration_minutes, guests, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r['source'],
                r['event_id'],
                r['title'],
                r['start_ts'],
                r['end_ts'],
                r['timezone'],
                r['duration_minutes'],
                r['guests'],
                json.dumps({'raw': r})
            ))
            inserted += 1

        conn.commit()
        return inserted

def demo():
    conn = get_db()
    conn.execute("DELETE FROM bookings")

    # Hardcoded sample data simulating Calendly and Google Calendar exports
    sample_data = [
        {
            'source': 'calendly',
            'event_id': 'cal_123',
            'title': 'Client Onboarding',
            'start_ts': datetime(2024, 6, 1, 10, 0).timestamp(),
            'end_ts': datetime(2024, 6, 1, 11, 0).timestamp(),
            'timezone': 'America/New_York',
            'duration_minutes': 60,
            'guests': 1
        },
        {
            'source': 'google',
            'event_id': 'gcal_456',
            'title': 'Team Sync',
            'start_ts': datetime(2024, 6, 1, 11, 30).timestamp(),
            'end_ts': datetime(2024, 6, 1, 12, 0).timestamp(),
            'timezone': 'America/New_York',
            'duration_minutes': 30,
            'guests': 3
        },
        {
            'source': 'calendly',
            'event_id': 'cal_789',
            'title': 'Product Demo',
            'start_ts': datetime(2024, 6, 1, 12, 30).timestamp(),
            'end_ts': datetime(2024, 6, 1, 13, 15).timestamp(),
            'timezone': 'America/New_York',
            'duration_minutes': 45,
            'guests': 2
        }
    ]

    for row in sample_data:
        conn.execute("""
            INSERT INTO bookings
            (source, event_id, title, start_ts, end_ts, timezone, duration_minutes, guests, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['source'],
            row['event_id'],
            row['title'],
            row['start_ts'],
            row['end_ts'],
            row['timezone'],
            row['duration_minutes'],
            row['guests'],
            json.dumps({'raw': row})
        ))

    conn.commit()

    # Print formatted table
    cur = conn.execute("""
        SELECT id, source, title, start_ts, end_ts, timezone, duration_minutes, guests
        FROM bookings
        ORDER BY start_ts
    """)
    rows = cur.fetchall()

    print("DoubleCheck Demo — Bookings Imported")
    print("-" * 60)
    print(f"{'ID':<4} {'Source':<10} {'Title':<20} {'Start (UTC)':<20} {'End (UTC)':<20} {'TZ':<10} {'Dur':<5} {'Guests'}")
    print("-" * 60)
    for r in rows:
        start_dt = datetime.fromtimestamp(r[3]).strftime('%Y-%m-%d %H:%M:%S')
        end_dt = datetime.fromtimestamp(r[4]).strftime('%Y-%m-%d %H:%M:%S')
        print(f"{r[0]:<4} {r[1]:<10} {r[2]:<20} {start_dt:<20} {end_dt:<20} {r[5]:<10} {r[6]:<5} {r[7]}")
    print("-" * 60)
    print(f"Total: {len(rows)} bookings stored in {DB_PATH}")

def main():
    parser = argparse.ArgumentParser(description="DoubleCheck CLI — Detect booking conflicts across platforms")
    parser.add_argument('--demo', action='store_true', help="Run demo with hardcoded data")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Import bookings from CSV')
    add_parser.add_argument('csv_path', help='Path to CSV file')
    add_parser.add_argument('--source', required=True, help='Source name (e.g., calendly, google)')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    conn = get_db()

    if args.command == 'add':
        try:
            count = add_bookings_from_csv(conn, args.csv_path, args.source)
            print(f"Imported {count} bookings from {args.csv_path} as source '{args.source}'")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()