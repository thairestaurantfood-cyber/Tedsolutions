#!/usr/bin/env python3
"""
Keybench - Scriptable, extensible performance tool for key value stores.
"""

import argparse
import sqlite3
import sys
import os
from pathlib import Path

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), "keybench.db")

# Schema for key value store performance metrics
SCHEMA = """
CREATE TABLE IF NOT EXISTS benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    keys INTEGER NOT NULL,
    duration_ms REAL NOT NULL,
    throughput_ops REAL NOT NULL,
    latency_ms REAL NOT NULL,
    timestamp TEXT NOT NULL
);
"""

def init_db():
    """Initialize the database with schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    conn.commit()
    conn.close()

def demo():
    """Run the demo: delete DB, insert 3 hardcoded rows, print formatted table."""
    # Delete database file if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    # Initialize fresh database
    init_db()
    
    # Insert 3 hardcoded benchmark entries with ALL fields filled
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    demo_data = [
        ("Redis", "GET", 1000, 45.2, 22124.35, 0.45, "2026-06-08T12:00:00"),
        ("Redis", "SET", 1000, 52.1, 19193.86, 0.52, "2026-06-08T12:00:01"),
        ("SQLite", "GET", 1000, 120.5, 8298.76, 1.21, "2026-06-08T12:00:02"),
    ]
    
    cursor.executemany(
        """
        INSERT INTO benchmarks 
        (store_name, operation, keys, duration_ms, throughput_ops, latency_ms, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        demo_data
    )
    conn.commit()
    
    # Print formatted table with headers
    cursor.execute("SELECT * FROM benchmarks")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(benchmarks)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Print header
    print("\n" + "=" * 80)
    print("Keybench Demo - Performance Benchmarks")
    print("=" * 80)
    
    # Print column headers
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(field) for field in row))
    
    print("=" * 80)
    print(f"\nDemo complete. Database saved to: {DB_PATH}")
    print("Total rows inserted: 3")
    
    conn.close()
    sys.exit(0)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Keybench - Key Value Store Performance Benchmarking Tool"
    )
    
    # Parse known args first (before subparsers)
    args, remaining = parser.parse_known_args()
    
    # Check for demo flag
    if "--demo" in remaining:
        demo()
    
    # Add subparsers for actual functionality
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run performance benchmarks")
    bench_parser.add_argument("--store", help="Key value store name", required=True)
    bench_parser.add_argument("--operation", help="Operation type (GET/SET/DELETE)", required=True)
    bench_parser.add_argument("--keys", type=int, help="Number of keys to test", required=True)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List stored benchmarks")
    list_parser.add_argument("--store", help="Filter by store name")
    list_parser.add_argument("--operation", help="Filter by operation type")
    
    # Parse full arguments
    args = parser.parse_args()
    
    if args.command == "benchmark":
        # In a real implementation, this would run actual benchmarks
        # For this demo-focused spec, we just ensure the structure exists
        init_db()
        print(f"Benchmark command would run for {args.store} - {args.operation} with {args.keys} keys")
        print("Actual benchmarking logic would go here (not required for --demo spec)")
    
    elif args.command == "list":
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT * FROM benchmarks"
        params = []
        
        if args.store:
            query += " WHERE store_name = ?"
            params.append(args.store)
            if args.operation:
                query += " AND operation = ?"
                params.append(args.operation)
        elif args.operation:
            query += " WHERE operation = ?"
            params.append(args.operation)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if rows:
            cursor.execute("PRAGMA table_info(benchmarks)")
            columns = [col[1] for col in cursor.fetchall()]
            print(" | ".join(columns))
            print("-" * 80)
            for row in rows:
                print(" | ".join(str(field) for field in row))
        else:
            print("No benchmarks found.")
        
        conn.close()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
