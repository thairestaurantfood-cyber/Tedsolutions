import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.arbbot/arb.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS markets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_id TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        end_time TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS contracts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        market_id INTEGER NOT NULL,
        contract_id TEXT NOT NULL,
        title TEXT NOT NULL,
        yes_price REAL NOT NULL,
        no_price REAL NOT NULL,
        volume REAL,
        FOREIGN KEY (market_id) REFERENCES markets(id)
    )
    """)
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()

    markets = [
        ("m1", "kalshi", "Will it rain tomorrow?", "Prediction market for weather", "2024-12-31T23:59:59", now),
        ("m2", "polymarket", "Will Bitcoin hit $100k?", "Crypto price prediction", "2024-12-25T18:00:00", now),
        ("m3", "metaculus", "Will AI surpass human intelligence?", "AI timeline prediction", "2025-01-15T00:00:00", now)
    ]

    for market in markets:
        conn.execute(
            "INSERT INTO markets (market_id, source, title, description, end_time, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            market
        )
        market_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        contracts = [
            (market_id, "c1", "Yes", 0.65, 0.35, 1250.5),
            (market_id, "c2", "No", 0.35, 0.65, 890.2)
        ]
        for contract in contracts:
            conn.execute(
                "INSERT INTO contracts (market_id, contract_id, title, yes_price, no_price, volume) VALUES (?, ?, ?, ?, ?, ?)",
                contract
            )

    conn.commit()

    print("MARKETS:")
    print(f"{'ID':<4} {'MarketID':<10} {'Source':<12} {'Title':<40} {'EndTime'}")
    print("-" * 110)
    for row in conn.execute("SELECT id, market_id, source, title, end_time FROM markets"):
        print(f"{row[0]:<4} {row[1]:<10} {row[2]:<12} {row[3]:<40} {row[4]}")

    print("\nCONTRACTS:")
    print(f"{'ID':<4} {'Market':<40} {'Contract':<10} {'Yes':<6} {'No':<6} {'Volume'}")
    print("-" * 80)
    for row in conn.execute("""
        SELECT c.id, m.title, c.title, c.yes_price, c.no_price, c.volume
        FROM contracts c
        JOIN markets m ON c.market_id=m.id
    """):
        print(f"{row[0]:<4} {row[1]:<40} {row[2]:<10} {row[3]:<6.2f} {row[4]:<6.2f} {row[5]}")

    conn.close()
    print("\nDemo complete.")

def add_market(args):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    now = datetime.utcnow().isoformat()
    try:
        conn.execute(
            "INSERT INTO markets (market_id, source, title, description, end_time, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (args.market_id, args.source, args.title, args.description or "", args.end_time, now)
        )
        conn.commit()
        print(f"Added market: {args.title} (ID: {args.market_id})")
    except sqlite3.IntegrityError:
        print(f"Error: Market ID {args.market_id} already exists")
    finally:
        conn.close()

def add_contract(args):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        market_id = conn.execute(
            "SELECT id FROM markets WHERE market_id = ?",
            (args.market_id,)
        ).fetchone()
        if not market_id:
            print(f"Error: Market {args.market_id} not found")
            return

        conn.execute(
            "INSERT INTO contracts (market_id, contract_id, title, yes_price, no_price, volume) VALUES (?, ?, ?, ?, ?, ?)",
            (market_id[0], args.contract_id, args.title, args.yes_price, args.no_price, args.volume or 0)
        )
        conn.commit()
        print(f"Added contract: {args.title} to market {args.market_id}")
    except sqlite3.IntegrityError:
        print(f"Error: Contract ID {args.contract_id} already exists for this market")
    finally:
        conn.close()

def list_markets(args):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    markets = conn.execute("SELECT id, market_id, source, title, end_time FROM markets").fetchall()
    if not markets:
        print("No markets found")
        return

    print("MARKETS:")
    print(f"{'ID':<4} {'MarketID':<10} {'Source':<12} {'Title':<40} {'EndTime'}")
    print("-" * 110)
    for row in markets:
        print(f"{row[0]:<4} {row[1]:<10} {row[2]:<12} {row[3]:<40} {row[4]}")
    conn.close()

def list_contracts(args):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    contracts = conn.execute("""
        SELECT c.id, m.market_id, m.title, c.contract_id, c.title, c.yes_price, c.no_price, c.volume
        FROM contracts c
        JOIN markets m ON c.market_id=m.id
    """).fetchall()
    if not contracts:
        print("No contracts found")
        return

    print("CONTRACTS:")
    print(f"{'ID':<4} {'MarketID':<10} {'MarketTitle':<30} {'ContractID':<10} {'Title':<10} {'Yes':<6} {'No':<6} {'Volume'}")
    print("-" * 100)
    for row in contracts:
        print(f"{row[0]:<4} {row[1]:<10} {row[2]:<30} {row[3]:<10} {row[4]:<10} {row[5]:<6.2f} {row[6]:<6.2f} {row[7]}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Arbitrage Bot - CLI for prediction market arbitrage")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample arbitrage data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    market_parser = subparsers.add_parser('market', help='Market operations')
    market_subparsers = market_parser.add_subparsers(dest='market_command')

    add_market_parser = market_subparsers.add_parser('add', help='Add a new market')
    add_market_parser.add_argument('--market-id', required=True, help='Unique market identifier')
    add_market_parser.add_argument('--source', required=True, help='Market source (kalshi, polymarket, etc)')
    add_market_parser.add_argument('--title', required=True, help='Market title')
    add_market_parser.add_argument('--description', help='Market description')
    add_market_parser.add_argument('--end-time', required=True, help='Market end time (ISO format)')

    list_market_parser = market_subparsers.add_parser('list', help='List all markets')

    contract_parser = subparsers.add_parser('contract', help='Contract operations')
    contract_subparsers = contract_parser.add_subparsers(dest='contract_command')

    add_contract_parser = contract_subparsers.add_parser