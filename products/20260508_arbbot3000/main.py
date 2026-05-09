import os
import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/arb3000.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            event_id TEXT NOT NULL,
            market_id TEXT NOT NULL,
            outcome TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Insert sample events
    events = [
        ('event_1', 'Super Bowl Winner', '2024-02-11 00:00:00', 'open'),
        ('event_2', 'Election 2024', '2024-11-05 00:00:00', 'open')
    ]
    cur.executemany("INSERT INTO events (event_id, title, start_time, status) VALUES (?, ?, ?, ?)", events)

    # Insert sample markets
    markets = [
        ('Kalshi', 'event_1', 'market_1', 'Chiefs', 0.65, '2024-01-01 00:00:00'),
        ('Kalshi', 'event_1', 'market_2', '49ers', 0.35, '2024-01-01 00:00:00'),
        ('Polymarket', 'event_2', 'market_3', 'Biden', 0.45, '2024-01-01 00:00:00'),
        ('Polymarket', 'event_2', 'market_4', 'Trump', 0.55, '2024-01-01 00:00:00'),
        ('SX.bet', 'event_1', 'market_5', 'Chiefs', 0.62, '2024-01-01 00:00:00'),
        ('SX.bet', 'event_1', 'market_6', '49ers', 0.38, '2024-01-01 00:00:00')
    ]
    cur.executemany("""
        INSERT INTO markets
        (name, event_id, market_id, outcome, price, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, markets)

    conn.commit()
    conn.close()

    # Print formatted table
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT e.event_id, e.title, m.name, m.outcome, m.price
        FROM events e
        JOIN markets m ON e.event_id = m.event_id
        ORDER BY e.event_id, m.name, m.price DESC
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No data found")
        return

    # Calculate max lengths
    col_widths = [max(len(str(item)) for item in col) for col in zip(*rows)]
    headers = ['Event ID', 'Title', 'Market', 'Outcome', 'Price']
    col_widths = [max(len(h), w) for h, w in zip(headers, col_widths)]

    # Print header
    header_line = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))

    # Print rows
    for row in rows:
        print(" | ".join(str(item).ljust(w) for item, w in zip(row, col_widths)))

def main():
    parser = argparse.ArgumentParser(description='ArbBot3000 - Arbitrage Market Data Tool')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    args = parser.parse_args()

    if args.demo:
        demo()
    elif args.init:
        init_db()
        print(f"Database initialized at {DB_PATH}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()