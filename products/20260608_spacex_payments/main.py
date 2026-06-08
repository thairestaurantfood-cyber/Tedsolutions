#!/usr/bin/env python3
"""
SpaceX Payments CLI - Track Google's $920M/month payments to SpaceX for xAI compute capacity.
"""

import argparse
import sqlite3
import sys
import os
from pathlib import Path

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "spacex_payments.db")

# Schema for payment tracking
SCHEMA = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL
);
"""

def init_db():
    """Initialize the database with schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    conn.commit()
    conn.close()

def add_payment(date, amount, description, status):
    """Add a new payment record."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO payments (date, amount, description, status)
        VALUES (?, ?, ?, ?)
        """,
        (date, amount, description, status)
    )
    conn.commit()
    conn.close()
    print(f"Payment added: {date} - ${amount:,.2f} - {description}")

def list_payments():
    """List all payments in a formatted table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments")
    rows = cursor.fetchall()
    
    if not rows:
        print("No payments found.")
        conn.close()
        return
    
    # Get column names
    cursor.execute("PRAGMA table_info(payments)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Print formatted table
    print("\n" + "=" * 100)
    print("SpaceX Payments Tracker")
    print("=" * 100)
    
    # Print header
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        formatted_row = [
            str(row[0]),  # id
            row[1],       # date
            f"${row[2]:,.2f}",  # amount formatted
            row[3],       # description
            row[4]        # status
        ]
        print(" | ".join(formatted_row))
    
    print("=" * 100)
    print(f"Total payments: {len(rows)}")
    
    conn.close()

def demo_mode():
    """Run the demo: delete DB, insert 3 hardcoded rows, print formatted table."""
    # Delete database file if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Initialize fresh database
    init_db()
    
    # Insert 3 hardcoded payment entries with ALL fields filled
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    demo_data = [
        ("2026-06-01", 920000000.00, "June 2026 payment for xAI compute capacity", "completed"),
        ("2026-07-01", 920000000.00, "July 2026 payment for xAI compute capacity", "pending"),
        ("2026-08-01", 920000000.00, "August 2026 payment for xAI compute capacity", "scheduled"),
    ]
    
    cursor.executemany(
        """
        INSERT INTO payments (date, amount, description, status)
        VALUES (?, ?, ?, ?)
        """,
        demo_data
    )
    conn.commit()
    
    # Print formatted table with headers
    list_payments()
    
    print(f"\nDemo complete. Database saved to: {DB_PATH}")
    print("Total rows inserted: 3")
    
    conn.close()
    sys.exit(0)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SpaceX Payments CLI - Track Google's payments to SpaceX for xAI compute capacity"
    )
    
    # Parse known args first (before subparsers)
    args, remaining = parser.parse_known_args()
    
    # Check for demo flag
    if "--demo" in remaining:
        demo_mode()
    
    # Add subparsers for actual functionality
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add payment command
    add_parser = subparsers.add_parser("add", help="Add a new payment")
    add_parser.add_argument("--date", help="Payment date (YYYY-MM-DD)", required=True)
    add_parser.add_argument("--amount", type=float, help="Payment amount", required=True)
    add_parser.add_argument("--description", help="Payment description", required=True)
    add_parser.add_argument("--status", help="Payment status", required=True)
    
    # List payments command
    list_parser = subparsers.add_parser("list", help="List all payments")
    
    # Parse full arguments
    args = parser.parse_args()
    
    if args.command == "add":
        init_db()
        add_payment(args.date, args.amount, args.description, args.status)
    elif args.command == "list":
        init_db()
        list_payments()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()