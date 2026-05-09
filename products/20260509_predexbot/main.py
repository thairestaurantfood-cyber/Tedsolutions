import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/predexbot.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS markets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            symbol TEXT NOT NULL UNIQUE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id INTEGER NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (market_id) REFERENCES markets (id)
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

    # Insert markets
    markets = [
        ('Kalshi', 'KAL_ES1!'),
        ('Polymarket', 'PM_BTC2024'),
        ('SX.bet', 'SX_AAPL')
    ]
    c.executemany('INSERT INTO markets (name, symbol) VALUES (?, ?)', markets)

    # Insert trades
    trades = [
        (1, 'BUY', 4500.50, 2.0),
        (1, 'SELL', 4505.25, 1.5),
        (2, 'BUY', 0.0001, 100.0),
        (3, 'SELL', 180.75, 3.0)
    ]
    c.executemany('INSERT INTO trades (market_id, side, price, size) VALUES (?, ?, ?, ?)', trades)

    conn.commit()

    # Print formatted table
    print("MARKETS:")
    c.execute('SELECT id, name, symbol FROM markets')
    rows = c.fetchall()
    print("+----+------------+------------+")
    print("| ID | Name       | Symbol     |")
    print("+----+------------+------------+")
    for row in rows:
        print(f"| {row[0]:<2} | {row[1]:<10} | {row[2]:<10} |")
    print("+----+------------+------------+")

    print("\nTRADES:")
    c.execute('''
        SELECT t.id, m.name, t.side, t.price, t.size, t.timestamp
        FROM trades t JOIN markets m ON t.market_id = m.id
    ''')
    rows = c.fetchall()
    print("+----+------------+------+--------+------+---------------------+")
    print("| ID | Market     | Side | Price  | Size | Timestamp           |")
    print("+----+------------+------+--------+------+---------------------+")
    for row in rows:
        print(f"| {row[0]:<2} | {row[1]:<10} | {row[2]:<4} | {row[3]:<6.2f} | {row[4]:<4.1f} | {row[5]:<19} |")
    print("+----+------------+------+--------+------+---------------------+")

    conn.close()

def add_market(name, symbol):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO markets (name, symbol) VALUES (?, ?)', (name, symbol))
        conn.commit()
        print(f"Added market: {name} ({symbol})")
    except sqlite3.IntegrityError:
        print(f"Market {symbol} already exists")
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='PredexBot - Market Prediction Database')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    parser.add_argument('--add-market', nargs=2, metavar=('NAME', 'SYMBOL'), help='Add new market')
    args = parser.parse_args()

    if args.demo:
        demo()
    elif args.add_market:
        add_market(args.add_market[0], args.add_market[1])
    else:
        parser.print_help()

if __name__ == '__main__':
    main()