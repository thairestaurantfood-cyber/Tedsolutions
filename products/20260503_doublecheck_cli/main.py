import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/doublecheck.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            booking_id TEXT NOT NULL,
            customer TEXT NOT NULL,
            start_ts INTEGER NOT NULL,
            end_ts INTEGER NOT NULL,
            details TEXT,
            UNIQUE(source, booking_id)
        )
    ''')
    conn.commit()
    return conn

def add_bookings_from_csv(conn, csv_path):
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}", file=sys.stderr)
        return False

    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required = {'source', 'booking_id', 'customer', 'start_ts', 'end_ts'}
            if not required.issubset(reader.fieldnames):
                print(f"Error: CSV missing required columns: {required - set(reader.fieldnames)}", file=sys.stderr)
                return False

            cur = conn.cursor()
            inserted = 0
            for row in reader:
                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO bookings
                        (source, booking_id, customer, start_ts, end_ts, details)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        row['source'],
                        row['booking_id'],
                        row['customer'],
                        int(row['start_ts']),
                        int(row['end_ts']),
                        row.get('details', '')
                    ))
                    inserted += cur.rowcount
                except (ValueError, KeyError) as e:
                    print(f"Warning: Skipping malformed row: {row} - {e}", file=sys.stderr)
                    continue

            conn.commit()
            print(f"Added {inserted} bookings from {csv_path}")
            return True
    except Exception as e:
        print(f"Error reading CSV: {e}", file=sys.stderr)
        return False

def detect_overlaps(conn):
    cur = conn.cursor()
    cur.execute('''
        SELECT b1.customer as cust1, b1.start_ts as start1, b1.end_ts as end1,
               b2.customer as cust2, b2.start_ts as start2, b2.end_ts as end2
        FROM bookings b1
        JOIN bookings b2 ON b1.id < b2.id
        WHERE b1.end_ts > b2.start_ts AND b1.start_ts < b2.end_ts
    ''')
    overlaps = cur.fetchall()
    return overlaps

def generate_report(conn):
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as total FROM bookings')
    total = cur.fetchone()['total']

    cur.execute('''
        SELECT source, COUNT(*) as count
        FROM bookings
        GROUP BY source
        ORDER BY count DESC
    ''')
    sources = cur.fetchall()

    cur.execute('''
        SELECT customer, COUNT(*) as count
        FROM bookings
        GROUP BY customer
        ORDER BY count DESC
        LIMIT 5
    ''')
    top_customers = cur.fetchall()

    return {
        'total_bookings': total,
        'sources': sources,
        'top_customers': top_customers
    }

def demo():
    conn = get_db()
    cur = conn.cursor()

    hardcoded_data = [
        ('Booking.com', 'b1001', 'Alice Tan', 1704067200, 1704153600, 'Standard room'),
        ('Airbnb', 'ab2022', 'Bob Lee', 1704153600, 1704240000, 'Entire apartment'),
        ('Booking.com', 'b1002', 'Charlie Wong', 1704240000, 1704326400, 'Deluxe suite'),
        ('Agoda', 'ag3001', 'Alice Tan', 1704326400, 1704412800, 'Beach view'),
        ('Airbnb', 'ab2023', 'David Kim', 1704067200, 1704153600, 'Private room')
    ]

    try:
        cur.executemany('''
            INSERT OR IGNORE INTO bookings
            (source, booking_id, customer, start_ts, end_ts, details)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', hardcoded_data)
        conn.commit()

        overlaps = detect_overlaps(conn)
        if overlaps:
            print("\n⚠️  OVERLAPPING BOOKINGS DETECTED:")
            for o in overlaps:
                print(f"  {o['cust1']} ({datetime.fromtimestamp(o['start1'])}) overlaps with {o['cust2']} ({datetime.fromtimestamp(o['start2'])})")
        else:
            print("\n✅ No overlapping bookings detected")

        report = generate_report(conn)
        print(f"\n📊 REPORT:")
        print(f"  Total bookings: {report['total_bookings']}")
        print(f"  Top sources:")
        for s in report['sources']:
            print(f"    {s['source']}: {s['count']} bookings")
        print(f"  Top customers:")
        for c in report['top_customers']:
            print(f"    {c['customer']}: {c['count']} bookings")

    except Exception as e:
        print(f"Demo failed: {e}", file=sys.stderr)
    finally:
        conn.close()
        print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="DoubleCheck CLI - Detect booking conflicts and overlaps")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    import_cmd = subparsers.add_parser('import', help='Import bookings from CSV')
    import_cmd.add_argument('csv_path', help='Path to CSV file')
    import_cmd.set_defaults(func=lambda args: add_bookings_from_csv(get_db(), args.csv_path))

    check_cmd = subparsers.add_parser('check', help='Check for overlapping bookings')
    check_cmd.set_defaults(func=lambda args: print_overlaps(get_db()))

    report_cmd = subparsers.add_parser('report', help='Generate booking report')
    report_cmd.set_defaults(func=lambda args: print_report(get_db()))

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

def print_overlaps(conn):
    overlaps = detect_overlaps(conn)
    if overlaps:
        print("\n⚠️  OVERLAPPING BOOKINGS DETECTED:")
        for o in overlaps:
            print(f"  {o['cust1']} ({datetime.fromtimestamp(o['start1'])}) overlaps with {o['cust2']} ({datetime.fromtimestamp(o['start2'])})")
    else:
        print("\n✅ No overlapping bookings detected")

def print_report(conn):
    report = generate_report(conn)
    print(f"\n📊 BOOKING REPORT:")
    print(f"  Total bookings: {report['total_bookings']}")
    print(f"  Top sources:")
    for s in report['sources']:
        print(f"    {s['source']}: {s['count']} bookings")
    print(f"  Top customers:")
    for c in report['top_customers']:
        print(f"    {c['customer']}: {c['count']} bookings")

if __name__ == '__main__':
    main()