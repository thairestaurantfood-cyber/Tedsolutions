import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def get_db():
    """Initialize database with schema if needed."""
    db_path = os.path.expanduser("~/.chasepy/invoices.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'unpaid',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def add_invoice(client, amount, due_date, notes=""):
    """Add a new invoice to the database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO invoices (client, amount, due_date, notes) VALUES (?, ?, ?, ?)",
        (client, amount, due_date, notes)
    )
    conn.commit()
    conn.close()
    print(f"✅ Added invoice for {client}: ${amount:.2f} due {due_date}")

def list_invoices(status=None):
    """List all invoices, optionally filtered by status."""
    conn = get_db()
    query = "SELECT id, client, amount, due_date, status FROM invoices"
    params = []

    if status:
        query += " WHERE status = ?"
        params.append(status)

    query += " ORDER BY due_date ASC"

    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No invoices found.")
        return

    print("\n📋 Invoices:")
    print("-" * 60)
    for row in rows:
        id, client, amount, due_date, status = row
        print(f"ID: {id} | Client: {client} | Amount: ${amount:.2f} | Due: {due_date} | Status: {status}")

def send_reminders(days_before=3):
    """Send reminders for invoices due soon."""
    conn = get_db()
    today = datetime.now().date()
    target_date = today + timedelta(days=days_before)

    cursor = conn.execute(
        "SELECT id, client, amount, due_date FROM invoices WHERE status = 'unpaid' AND due_date <= ?",
        (target_date.strftime("%Y-%m-%d"),)
    )
    invoices = cursor.fetchall()
    conn.close()

    if not invoices:
        print(f"No invoices due within {days_before} days.")
        return

    print(f"\n📢 Reminders for invoices due within {days_before} days:")
    print("-" * 60)
    for id, client, amount, due_date in invoices:
        days_left = (datetime.strptime(due_date, "%Y-%m-%d").date() - today).days
        print(f"ID: {id} | Client: {client} | Amount: ${amount:.2f} | Due in {days_left} days ({due_date})")

def demo():
    """Run demo with sample data."""
    conn = get_db()
    conn.execute("DELETE FROM invoices")
    conn.commit()

    sample_data = [
        ("Acme Corp", 1500.00, "2026-05-15", "Project A"),
        ("Globex Inc", 2300.50, "2026-05-10", "Project B"),
        ("Initech", 950.75, "2026-05-20", "Project C"),
        ("Wayne Enterprises", 5000.00, "2026-05-05", "Project D"),
        ("Stark Industries", 7500.50, "2026-05-25", "Project E")
    ]

    conn.executemany(
        "INSERT INTO invoices (client, amount, due_date, notes) VALUES (?, ?, ?, ?)",
        sample_data
    )
    conn.commit()
    print("\n=== ChasePy Demo ===")
    print("\nOverdue invoices requiring reminders:\n")
    conn2 = get_db()
    rows = conn2.execute(
        "SELECT client, amount, due_date, status FROM invoices ORDER BY due_date"
    ).fetchall()
    today = __import__("datetime").date.today().isoformat()
    for r in rows:
        overdue = "🔴 OVERDUE" if r[2] < today else "🟡 upcoming"
        print(f"  {overdue} | {r[0]:<20} | ${r[1]:>8.2f} | due {r[2]}")
    conn2.close()
    print(f"\n📧 Reminder sequences would be sent to {len(rows)} clients")
    print("✅ Demo complete — use --help for full commands")

def main():
    parser = argparse.ArgumentParser(description="ChasePy — Invoice reminder tool for freelancers")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    # Parse --demo first before requiring subcommand
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command', required=True)

    add_parser = subparsers.add_parser('add', help='Add a new invoice')
    add_parser.add_argument('--client', required=True, help='Client name')
    add_parser.add_argument('--amount', type=float, required=True, help='Invoice amount')
    add_parser.add_argument('--due', required=True, help='Due date (YYYY-MM-DD)')
    add_parser.add_argument('--notes', default='', help='Additional notes')

    list_parser = subparsers.add_parser('list', help='List invoices')
    list_parser.add_argument('--status', help='Filter by status (paid/unpaid)')

    remind_parser = subparsers.add_parser('remind', help='Send reminders')
    remind_parser.add_argument('--days', type=int, default=3, help='Days before due')


    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if args.command == 'add':
        add_invoice(args.client, args.amount, args.due, args.notes)
    elif args.command == 'list':
        list_invoices(args.status)
    elif args.command == 'remind':
        send_reminders(args.days)

if __name__ == "__main__":
    main()