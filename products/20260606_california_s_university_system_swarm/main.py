
import argparse
import sqlite3
import os
import sys
from datetime import datetime

DATABASE_FILE = "intern_applications.db"

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            applied_date TEXT NOT NULL,
            skills TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_application(name, email, status, applied_date, skills):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO applications (name, email, status, applied_date, skills) VALUES (?, ?, ?, ?, ?)",
                       (name, email, status, applied_date, skills))
        conn.commit()
        print(f"Application for {name} added.")
    except sqlite3.IntegrityError:
        print(f"Error: Application with email {email} already exists.")
    finally:
        conn.close()

def list_applications():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, status, applied_date, skills FROM applications")
    rows = cursor.fetchall()
    conn.close()
    return rows

def format_table(headers, rows):
    if not rows:
        return "No applications found."

    col_widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    header_line = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
    separator_line = "-+-".join("-" * col_width for col_width in col_widths)
    
    table = [header_line, separator_line]
    for row in rows:
        table.append(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))
    return "\n".join(table)

def demo_mode():
    if os.path.exists(DATABASE_FILE):
        os.remove(DATABASE_FILE)
        print(f"Removed existing database: {DATABASE_FILE}")
    
    init_db(DATABASE_FILE)
    print("Running demo mode...")

    # Insert 3+ hardcoded rows
    add_application("Alice Wonderland", "alice@example.com", "New", "2024-05-01", "Python, ML")
    add_application("Bob Thebuilder", "bob@example.com", "Reviewing", "2024-05-05", "Data Science, SQL")
    add_application("Charlie Chaplin", "charlie@example.com", "Interview", "2024-05-10", "NLP, Python")
    add_application("Diana Prince", "diana@example.com", "Rejected", "2024-05-12", "Computer Vision")

    print("\n--- Current Applications ---")
    headers = ["Name", "Email", "Status", "Applied Date", "Skills"]
    print(format_table(headers, list_applications()))
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Great Question Applied AI Interns CLI Tool")
    
    known_args, _ = parser.parse_known_args()

    # If --demo is present, run demo_mode and exit
    if "--demo" in sys.argv:
        demo_mode()

    # Subparsers for regular commands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new intern application")
    add_parser.add_argument("--name", help="Intern's name")
    add_parser.add_argument("--email", help="Intern's email")
    add_parser.add_argument("--status", choices=["New", "Reviewing", "Interview", "Rejected", "Hired"],
                            default="New", help="Application status")
    add_parser.add_argument("--skills", help="Comma-separated skills")

    # List command
    list_parser = subparsers.add_parser("list", help="List all intern applications")

    args = parser.parse_args()

    init_db(DATABASE_FILE)

    if args.command == "add":
        if not all([args.name, args.email]):
            print("Error: --name and --email are required for 'add' command.")
            sys.exit(1)
        applied_date = datetime.now().strftime("%Y-%m-%d")
        add_application(args.name, args.email, args.status, applied_date, args.skills)
    elif args.command == "list":
        headers = ["Name", "Email", "Status", "Applied Date", "Skills"]
        print(format_table(headers, list_applications()))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
