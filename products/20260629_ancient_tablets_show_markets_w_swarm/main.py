import argparse
import sqlite3
import os
import sys
from datetime import datetime

DB_NAME = "ancient_tablets.db"

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tablets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            item TEXT NOT NULL,
            price REAL NOT NULL,
            currency TEXT NOT NULL,
            description TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_tablet(date, location, item, price, currency, description=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tablets (date, location, item, price, currency, description) VALUES (?, ?, ?, ?, ?, ?)",
        (date, location, item, price, currency, description)
    )
    conn.commit()
    conn.close()

def get_all_tablets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, location, item, price, currency, description FROM tablets")
    rows = cursor.fetchall()
    conn.close()
    return rows

def format_tablets(tablets):
    if not tablets:
        return "No ancient tablets found."

    headers = ["ID", "DATE", "LOCATION", "ITEM", "PRICE", "CURRENCY", "DESCRIPTION"]
    col_widths = [len(h) for h in headers]

    for row in tablets:
        for i, col in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(col)))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator_line = "-+-".join("-" * w for w in col_widths)

    output = [header_line, separator_line]
    for row in tablets:
        row_str = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(row))
        output.append(row_str)

    return "\n".join(output)

def run_demo():
    print("Running demo mode...")
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Deleted existing database: {DB_NAME}")

    init_db(DB_NAME)
    print("Database initialized.")

    print("Inserting hardcoded demo data...")
    add_tablet("2300 BCE", "Ur", "Grain", 10.5, "Shekel", "First recorded grain trade")
    add_tablet("2250 BCE", "Mari", "Copper Ingot", 500.0, "Mina", "Trade along Euphrates")
    add_tablet("2100 BCE", "Ebla", "Textile", 25.0, "Silver", "Luxury goods exchange")
    add_tablet("2000 BCE", "Babylon", "Land Plot", 1200.0, "Shekel", "Legal record of land sale")
    print("Demo data inserted.")

    print("\n--- Ancient Tablets Records ---")
    tablets = get_all_tablets()
    print(format_tablets(tablets))
    print("-----------------------------\n")

    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="A CLI tool to record and display ancient market transactions."
    )
    # Define a temporary parser for --demo to use parse_known_args
    demo_parser = argparse.ArgumentParser(add_help=False)
    demo_parser.add_argument('--demo', action='store_true', help='Run in demo mode.')
    
    args, remaining_argv = demo_parser.parse_known_args()

    if args.demo:
        run_demo()

    # Now build the full parser with subparsers for actual commands
    # Use remaining_argv to parse only the commands after --demo (if any)
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new ancient tablet record")
    add_parser.add_argument("--date", help="Date of the record (e.g., '2300 BCE')")
    add_parser.add_argument("--location", help="Location of the record")
    add_parser.add_argument("--item", help="Item traded")
    add_parser.add_argument("--price", type=float, help="Price of the item")
    add_parser.add_argument("--currency", help="Currency used")
    add_parser.add_argument("--description", help="Optional description")
    add_parser.set_defaults(func=lambda args: (
        add_tablet(args.date, args.location, args.item, args.price, args.currency, args.description)
        if all([args.date, args.location, args.item, args.price, args.currency])
        else print("Error: Missing required arguments for 'add' command.")
    ))

    # List command
    list_parser = subparsers.add_parser("list", help="List all ancient tablet records")
    list_parser.set_defaults(func=lambda args: print(format_tablets(get_all_tablets())))

    # If no command is given, parse_args will show help message
    if not remaining_argv:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args(remaining_argv)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
