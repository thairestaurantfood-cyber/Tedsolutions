#!/usr/bin/env python3
"""
Ask HN: Do you know any company that's making money with LLMs?
A simple CLI tool to track companies making money with LLMs.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Database setup
DB_PATH = Path("askhn_companies.db")

# Schema for the companies table
SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    revenue_model TEXT,
    website TEXT,
    founded_year INTEGER,
    notes TEXT
);
"""

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    conn.commit()
    conn.close()

def demo_mode():
    """Run the demo mode: delete DB, insert sample data, and print table."""
    # Delete the database file if it exists
    if DB_PATH.exists():
        DB_PATH.unlink()
    
    # Initialize a fresh database
    init_db()
    
    # Insert sample data
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    sample_companies = [
        {
            "name": "OpenAI",
            "description": "AI research and deployment company",
            "revenue_model": "API subscriptions, enterprise solutions",
            "website": "https://openai.com",
            "founded_year": 2015,
            "notes": "Pioneer in LLM technology"
        },
        {
            "name": "Anthropic",
            "description": "AI safety and research company",
            "revenue_model": "Enterprise contracts, API access",
            "website": "https://anthropic.com",
            "founded_year": 2021,
            "notes": "Focus on safe and interpretable AI"
        },
        {
            "name": "Mistral AI",
            "description": "Cutting-edge AI lab based in France",
            "revenue_model": "Open-source models, enterprise solutions",
            "website": "https://mistral.ai",
            "founded_year": 2023,
            "notes": "Known for efficient open models"
        }
    ]
    
    for company in sample_companies:
        cursor.execute(
            """
            INSERT INTO companies (name, description, revenue_model, website, founded_year, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                company["name"],
                company["description"],
                company["revenue_model"],
                company["website"],
                company["founded_year"],
                company["notes"]
            )
        )
    
    conn.commit()
    
    # Print formatted table
    cursor.execute("SELECT * FROM companies")
    rows = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(companies)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Print header
    print("\n" + "=" * 80)
    print("Ask HN: Companies Making Money with LLMs")
    print("=" * 80)
    
    # Print column headers
    header = " | ".join(columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(item) for item in row))
    
    print("=" * 80)
    print(f"\nTotal companies: {len(rows)}")
    
    conn.close()
    sys.exit(0)

def main():
    """Main entry point for the CLI tool."""
    parser = argparse.ArgumentParser(
        description="Ask HN: Track companies making money with LLMs"
    )
    
    # Parse known args first to handle --demo before subparsers
    args, remaining = parser.parse_known_args()
    
    # Check for demo flag
    if "--demo" in remaining:
        demo_mode()
    
    # Add subparsers for other commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new company")
    add_parser.add_argument("--name", required=True, help="Company name")
    add_parser.add_argument("--description", help="Company description")
    add_parser.add_argument("--revenue-model", help="Revenue model")
    add_parser.add_argument("--website", help="Company website")
    add_parser.add_argument("--founded-year", type=int, help="Year founded")
    add_parser.add_argument("--notes", help="Additional notes")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all companies")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search companies")
    search_parser.add_argument("--query", required=True, help="Search query")
    
    # Parse full arguments
    args = parser.parse_args()
    
    # Initialize database
    init_db()
    
    if args.command == "add":
        # Add company logic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO companies (name, description, revenue_model, website, founded_year, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                args.name,
                args.description,
                args.revenue_model,
                args.website,
                args.founded_year,
                args.notes
            )
        )
        conn.commit()
        print(f"Added company: {args.name}")
        conn.close()
        
    elif args.command == "list":
        # List companies logic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM companies")
        rows = cursor.fetchall()
        
        if not rows:
            print("No companies found.")
        else:
            # Get column names
            cursor.execute("PRAGMA table_info(companies)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Print header
            print("\n" + "=" * 80)
            print("Ask HN: Companies Making Money with LLMs")
            print("=" * 80)
            
            # Print column headers
            header = " | ".join(columns)
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in rows:
                print(" | ".join(str(item) for item in row))
            
            print("=" * 80)
            print(f"\nTotal companies: {len(rows)}")
        
        conn.close()
        
    elif args.command == "search":
        # Search companies logic
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Search in multiple fields
        query = f"%{args.query}%"
        cursor.execute(
            """
            SELECT * FROM companies
            WHERE name LIKE ? OR description LIKE ? OR revenue_model LIKE ? OR website LIKE ? OR notes LIKE ?
            """,
            (query, query, query, query, query)
        )
        rows = cursor.fetchall()
        
        if not rows:
            print(f"No companies found matching: {args.query}")
        else:
            # Get column names
            cursor.execute("PRAGMA table_info(companies)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Print header
            print("\n" + "=" * 80)
            print(f"Search Results for: {args.query}")
            print("=" * 80)
            
            # Print column headers
            header = " | ".join(columns)
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in rows:
                print(" | ".join(str(item) for item in row))
            
            print("=" * 80)
            print(f"\nFound {len(rows)} companies")
        
        conn.close()
    
    else:
        # No command provided, show help
        parser.print_help()

if __name__ == "__main__":
    main()