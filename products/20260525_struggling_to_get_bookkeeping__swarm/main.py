#!/usr/bin/env python3
"""
Struggling to get bookkeeping/accounting clients — what’s worked for you?
A CLI tool to track and analyze client acquisition strategies.
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = "clients.db"
SCHEMA = "CREATE TABLE IF NOT EXISTS strategies (id INTEGER PRIMARY KEY AUTOINCREMENT, strategy_name TEXT NOT NULL, description TEXT, success_rate REAL, cost REAL, time_investment TEXT, client_type TEXT, notes TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()

def demo_mode():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data = [
        ("Networking Events", "Attend local business networking events", 0.65, 50.0, "2-3 hours", "Small Business", "Bring business cards", datetime.now().isoformat(), datetime.now().isoformat()),
        ("Referral Program", "Offer incentives for client referrals", 0.75, 100.0, "Ongoing", "Individuals", "$50 gift card per referral", datetime.now().isoformat(), datetime.now().isoformat()),
        ("Social Media Ads", "Run targeted LinkedIn/Facebook ads", 0.45, 300.0, "1 hour setup", "Startups", "Focus on local groups", datetime.now().isoformat(), datetime.now().isoformat()),
        ("Cold Emailing", "Send personalized emails to businesses", 0.30, 20.0, "1 hour/20 emails", "Small Business", "Personalize each email", datetime.now().isoformat(), datetime.now().isoformat())
    ]
    
    cursor.executemany("INSERT INTO strategies VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
    conn.commit()
    
    cursor.execute("SELECT * FROM strategies")
    rows = cursor.fetchall()
    columns = [col[1] for col in cursor.execute("PRAGMA table_info(strategies)").fetchall()]
    
    col_widths = [max(len(str(col)), 12) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    print(" | ".join(col.rjust(width) for col, width in zip(columns, col_widths)))
    print("-" * sum(col_widths) + "-" * 3 * (len(col_widths) - 1))
    
    for row in rows:
        print(" | ".join(str(val).ljust(width) for val, width in zip(row, col_widths)))
    
    conn.close()
    sys.exit(0)

def add_strategy(args):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO strategies (strategy_name, description, success_rate, cost, time_investment, client_type, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (args.name, args.description, args.success_rate, args.cost, args.time_investment, args.client_type, args.notes))
    conn.commit()
    conn.close()
    print(f"Added strategy: {args.name}")

def list_strategies(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies")
    rows = cursor.fetchall()
    
    if not rows:
        print("No strategies found.")
        return
    
    columns = [col[1] for col in cursor.execute("PRAGMA table_info(strategies)").fetchall()]
    col_widths = [max(len(str(col)), 12) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    print(" | ".join(col.rjust(width) for col, width in zip(columns, col_widths)))
    print("-" * sum(col_widths) + "-" * 3 * (len(col_widths) - 1))
    
    for row in rows:
        print(" | ".join(str(val).ljust(width) for val, width in zip(row, col_widths)))
    
    conn.close()

def search_strategies(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM strategies WHERE strategy_name LIKE ? OR client_type LIKE ?", (f"%{args.query}%", f"%{args.query}%"))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"No strategies found for '{args.query}'")
        return
    
    columns = [col[1] for col in cursor.execute("PRAGMA table_info(strategies)").fetchall()]
    col_widths = [max(len(str(col)), 12) for col in columns]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    print(" | ".join(col.rjust(width) for col, width in zip(columns, col_widths)))
    print("-" * sum(col_widths) + "-" * 3 * (len(col_widths) - 1))
    
    for row in rows:
        print(" | ".join(str(val).ljust(width) for val, width in zip(row, col_widths)))
    
    conn.close()

def analyze_strategies(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*), AVG(success_rate), AVG(cost) FROM strategies")
    total, avg_success, avg_cost = cursor.fetchone()
    
    print(f"\nAnalysis: {total} strategies")
    print(f"Avg Success: {avg_success:.1%}, Avg Cost: ${avg_cost:.2f}")
    
    cursor.execute("SELECT strategy_name, success_rate FROM strategies ORDER BY success_rate DESC LIMIT 1")
    best = cursor.fetchone()
    if best:
        print(f"Best: {best[0]} ({best[1]:.1%})")
    
    cursor.execute("SELECT strategy_name, cost, success_rate FROM strategies ORDER BY (cost/NULLIF(success_rate,0)) ASC LIMIT 1")
    cost_eff = cursor.fetchone()
    if cost_eff:
        print(f"Most cost-effective: {cost_eff[0]} (${cost_eff[1]:.2f}, {cost_eff[2]:.1%})")
    
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Client Acquisition Strategy Tracker")
    parser.add_argument("--demo", action="store_true", help="Run demo mode")
    args, remaining = parser.parse_known_args()
    
    if args.demo:
        demo_mode()
    
    init_db()
    
    parser = argparse.ArgumentParser(description="Client Acquisition Strategy Tracker")
    subparsers = parser.add_subparsers(dest="command")
    
    add_p = subparsers.add_parser("add")
    add_p.add_argument("--name", required=True)
    add_p.add_argument("--description", required=True)
    add_p.add_argument("--success-rate", type=float, required=True)
    add_p.add_argument("--cost", type=float, required=True)
    add_p.add_argument("--time-investment", required=True)
    add_p.add_argument("--client-type", required=True)
    add_p.add_argument("--notes", default="")
    add_p.set_defaults(func=add_strategy)
    
    list_p = subparsers.add_parser("list")
    list_p.set_defaults(func=list_strategies)
    
    search_p = subparsers.add_parser("search")
    search_p.add_argument("query")
    search_p.set_defaults(func=search_strategies)
    
    analyze_p = subparsers.add_parser("analyze")
    analyze_p.set_defaults(func=analyze_strategies)
    
    args = parser.parse_args(remaining)
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
