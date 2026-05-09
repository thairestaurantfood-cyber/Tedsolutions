import os
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/betbot3000.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kalshi_price REAL,
            polymarket_price REAL,
            sx_price REAL,
            created_at TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER,
            market TEXT NOT NULL,
            price REAL NOT NULL,
            direction TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(event_id) REFERENCES events(id)
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    events = [
        ('Will Bitcoin hit $100k by Dec 31 2024?', 0.65, 0.68, 0.62),
        ('Will Trump win 2024 election?', 0.45, 0.42, 0.48),
        ('Will AI regulation pass US Senate in 2024?', 0.35, 0.32, 0.38)
    ]

    for name, kalshi, poly, sx in events:
        c.execute('''
            INSERT INTO events (name, kalshi_price, polymarket_price, sx_price, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, kalshi, poly, sx, datetime.now().isoformat()))

    conn.commit()

    c.execute('SELECT * FROM events')
    rows = c.fetchall()
    print('Events:')
    print('ID | Name | Kalshi | Polymarket | SX | Created')
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")

    conn.close()
    print("Demo complete.")

def add_event(args):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO events (name, kalshi_price, polymarket_price, sx_price, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (args.name, args.kalshi, args.polymarket, args.sx, datetime.now().isoformat()))
    conn.commit()
    print(f"Added event: {args.name}")
    conn.close()

def list_events(args):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM events')
    rows = c.fetchall()
    print('Events:')
    print('ID | Name | Kalshi | Polymarket | SX | Created')
    for row in rows:
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    conn.close()

def generate_report(args):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    report_type = args.type
    filename = args.filename

    if report_type == 'arbitrage':
        c.execute('''
            SELECT e.name,
                   e.kalshi_price,
                   e.polymarket_price,
                   e.sx_price,
                   CASE
                       WHEN ABS(e.kalshi_price - e.polymarket_price) > 0.1 THEN 'Kalshi-Polymarket'
                       WHEN ABS(e.kalshi_price - e.sx_price) > 0.1 THEN 'Kalshi-SX'
                       WHEN ABS(e.polymarket_price - e.sx_price) > 0.1 THEN 'Polymarket-SX'
                       ELSE 'No arbitrage'
                   END as opportunity
            FROM events e
            WHERE ABS(e.kalshi_price - e.polymarket_price) > 0.1
               OR ABS(e.kalshi_price - e.sx_price) > 0.1
               OR ABS(e.polymarket_price - e.sx_price) > 0.1
        ''')
        rows = c.fetchall()
        with open(filename, 'w') as f:
            f.write('Event Name,Kalshi Price,Polymarket Price,SX Price,Opportunity\n')
            for row in rows:
                f.write(f'{row[0]},{row[1]},{row[2]},{row[3]},"{row[4]}"\n')
        print(f"Arbitrage report generated: {filename}")

    elif report_type == 'price_history':
        c.execute('''
            SELECT e.name,
                   t.market,
                   t.price,
                   t.direction,
                   t.created_at
            FROM trades t
            JOIN events e ON t.event_id = e.id
            ORDER BY t.created_at DESC
        ''')
        rows = c.fetchall()
        with open(filename, 'w') as f:
            f.write('Event Name,Market,Price,Direction,Timestamp\n')
            for row in rows:
                f.write(f'{row[0]},{row[1]},{row[2]},{row[3]},{row[4]}\n')
        print(f"Price history report generated: {filename}")

    conn.close()

def check_alerts(args):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    threshold = args.threshold

    c.execute('''
        SELECT e.name,
               e.kalshi_price,
               e.polymarket_price,
               e.sx_price,
               CASE
                   WHEN e.kalshi_price > ? THEN 'Kalshi high'
                   WHEN e.polymarket_price > ? THEN 'Polymarket high'
                   WHEN e.sx_price > ? THEN 'SX high'
                   ELSE 'No alerts'
               END as alert
        FROM events e
        WHERE e.kalshi_price > ?
           OR e.polymarket_price > ?
           OR e.sx_price > ?
    ''', (threshold, threshold, threshold, threshold, threshold, threshold))

    rows = c.fetchall()
    if rows:
        print("Alerts:")
        print('Event | Kalshi | Polymarket | SX | Alert')
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]}")
    else:
        print("No alerts triggered")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description="BetBot3000 - Market Arbitrage Tool")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a new event')
    add_parser.add_argument('name', type=str)
    add_parser.add_argument('--kalshi', type=float, default=0.5)
    add_parser.add_argument('--polymarket', type=float, default=0.5)
    add_parser.add_argument('--sx', type=float, default=0.5)

    list_parser = subparsers.add_parser('list', help='List all events')

    report_parser = subparsers.add_parser('report', help='Generate reports')
    report_parser.add_argument('--type', choices=['arbitrage', 'price_history'], required=True)
    report_parser.add_argument('--filename', type=str, default='report.csv')

    alert_parser = subparsers.add_parser('alerts', help='Check price alerts')
    alert_parser.add_argument('--threshold', type=float, default=0.7)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_event(args)
    elif args.command == 'list':
        list_events(args)
    elif args.command == 'report':
        generate_report(args)
    elif args.command == 'alerts':
        check_alerts(args)

if __name__ == '__main__':
    main()