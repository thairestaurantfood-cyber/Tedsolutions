#!/usr/bin/env python3
"""
All-in-One Marketing Dashboard CLI
Track and analyze marketing campaigns across multiple channels
"""

import sys
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = Path.home() / ".marketing_dashboard.db"


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema"""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            channel TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            budget REAL,
            impressions INTEGER,
            clicks INTEGER,
            conversions INTEGER,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def delete_db() -> None:
    """Delete the database file"""
    if DB_PATH.exists():
        DB_PATH.unlink()


def insert_demo_data(conn: sqlite3.Connection) -> None:
    """Insert 3+ hardcoded rows with all fields filled"""
    demo_data = [
        ("Summer Social Media Blitz", "Facebook", "2024-06-01", "2024-06-30", 5000.0, 150000, 8500, 1200, "Completed", "Targeted Gen Z audience with video ads", datetime.now().isoformat()),
        ("Email Nurture Campaign", "Email", "2024-05-15", "2024-07-15", 2500.0, 50000, 12000, 1800, "Active", "Drip campaign for lead nurturing", datetime.now().isoformat()),
        ("Influencer Partnership", "Instagram", "2024-07-01", "2024-07-31", 15000.0, 500000, 150000, 12000, "Active", "Collaboration with 3 micro-influencers", datetime.now().isoformat())
    ]
    
    conn.executemany(
        """
        INSERT INTO campaigns (
            name, channel, start_date, end_date, budget,
            impressions, clicks, conversions, status, notes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        demo_data
    )
    conn.commit()


def print_formatted_table(conn: sqlite3.Connection) -> None:
    """Print campaigns in a formatted table with headers"""
    cursor = conn.execute("SELECT * FROM campaigns")
    rows = cursor.fetchall()
    
    if not rows:
        print("No campaigns found.")
        return
    
    # Get column names
    columns = [desc[0] for desc in cursor.description]
    
    # Calculate column widths
    col_widths = {col: len(col) for col in columns}
    for row in rows:
        for i, value in enumerate(row):
            col_name = columns[i]
            if value is not None:
                col_widths[col_name] = max(col_widths[col_name], len(str(value)))
    
    # Print header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        line = " | ".join(
            str(value).ljust(col_widths[columns[i]]) if value is not None else "NULL".ljust(col_widths[columns[i]])
            for i, value in enumerate(row)
        )
        print(line)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="All-in-One Marketing Dashboard"
    )
    
    # Handle --demo before subparsers
    args, remaining = parser.parse_known_args()
    
    if "--demo" in sys.argv:
        delete_db()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            init_db(conn)
            insert_demo_data(conn)
            print_formatted_table(conn)
        finally:
            conn.close()
        return 0
    
    # Main parser
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Add campaign command
    add_parser = subparsers.add_parser("add", help="Add a new campaign")
    add_parser.add_argument("--name", required=True, help="Campaign name")
    add_parser.add_argument("--channel", required=True, help="Marketing channel")
    add_parser.add_argument("--start-date", required=True, help="Start date (YYYY-MM-DD)")
    add_parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    add_parser.add_argument("--budget", type=float, required=True, help="Campaign budget")
    add_parser.add_argument("--impressions", type=int, required=True, help="Number of impressions")
    add_parser.add_argument("--clicks", type=int, required=True, help="Number of clicks")
    add_parser.add_argument("--conversions", type=int, required=True, help="Number of conversions")
    add_parser.add_argument("--status", required=True, help="Campaign status")
    add_parser.add_argument("--notes", help="Additional notes")
    add_parser.set_defaults(func=lambda args: add_campaign(args))
    
    # List campaigns command
    list_parser = subparsers.add_parser("list", help="List all campaigns")
    list_parser.set_defaults(func=lambda args: list_campaigns(args))
    
    # Get campaign command
    get_parser = subparsers.add_parser("get", help="Get campaign details")
    get_parser.add_argument("id", type=int, help="Campaign ID")
    get_parser.set_defaults(func=lambda args: get_campaign(args))
    
    # Parse remaining arguments
    args = parser.parse_args(remaining)
    
    # Execute command
    args.func(args)
    return 0


def add_campaign(args: argparse.Namespace) -> None:
    """Add a new campaign to the database"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        
        conn.execute(
            """
            INSERT INTO campaigns (
                name, channel, start_date, end_date, budget,
                impressions, clicks, conversions, status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                args.name,
                args.channel,
                args.start_date,
                args.end_date if args.end_date else None,
                args.budget,
                args.impressions,
                args.clicks,
                args.conversions,
                args.status,
                args.notes if args.notes else None,
                datetime.now().isoformat()
            )
        )
        conn.commit()
        print(f"Campaign added successfully (ID: {conn.execute('SELECT last_insert_rowid()').fetchone()[0]})")
    finally:
        conn.close()


def list_campaigns(args: argparse.Namespace) -> None:
    """List all campaigns"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        print_formatted_table(conn)
    finally:
        conn.close()


def get_campaign(args: argparse.Namespace) -> None:
    """Get details for a specific campaign"""
    conn = sqlite3.connect(str(DB_PATH))
    try:
        init_db(conn)
        cursor = conn.execute("SELECT * FROM campaigns WHERE id = ?", (args.id,))
        row = cursor.fetchone()
        
        if row:
            columns = [desc[0] for desc in cursor.description]
            for col, val in zip(columns, row):
                print(f"{col}: {val if val is not None else 'N/A'}")
        else:
            print(f"Campaign with ID {args.id} not found.")
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())