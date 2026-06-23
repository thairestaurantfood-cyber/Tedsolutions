#!/usr/bin/env python3
"""Stripe ToS violation tracker."""

import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
DB_PATH = Path.home() / ".tellhn.db"


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            service TEXT NOT NULL,
            issue TEXT NOT NULL,
            severity TEXT NOT NULL,
            details TEXT,
            resolved INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            customer_id TEXT,
            metadata TEXT
        )
        """
    )


def delete_db() -> None:
    """Delete the database file."""
    DB_PATH.unlink(missing_ok=True)


def insert_demo_data(conn: sqlite3.Connection) -> None:
    """Insert 3+ hardcoded rows with all fields filled."""
    # Insert violations
    now = datetime.now().isoformat()
    violations = [
        (now, "Stripe", "Biometric data collection without consent", "high",
         json.dumps({"tos_version": "2024-06-01", "biometric_type": "fingerprint"}), 0),
        (now, "Stripe", "Payment freeze without notification", "critical",
         json.dumps({"frozen_since": "2024-06-05T10:00:00Z"}), 0),
        (now, "Stripe", "Unilateral ToS change requiring biometrics", "high",
         json.dumps({"effective_date": "2024-07-01"}), 0),
    ]
    conn.executemany("INSERT INTO violations (timestamp, service, issue, severity, details, resolved) VALUES (?, ?, ?, ?, ?, ?)", violations)

    # Insert payments
    payments = [
        ("txn_001", 150.50, "USD", now, "frozen", "cust_123", json.dumps({"product": "premium_subscription"})),
        ("txn_002", 75.25, "USD", now, "frozen", "cust_456", json.dumps({"product": "api_access"})),
        ("txn_003", 200.00, "USD", now, "frozen", "cust_789", json.dumps({"product": "enterprise_plan"})),
    ]
    conn.executemany("INSERT INTO payments (transaction_id, amount, currency, timestamp, status, customer_id, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)", payments)
    conn.commit()


def print_table(data: list[tuple], headers: list[str]) -> None:
    """Print formatted table with headers."""
    if not data:
        print("No data to display.")
        return

    # Calculate column widths with minimum padding
    col_widths = [max(len(str(item)) for item in col) + 2 for col in zip(*data, headers)]

    # Print header
    header_line = " | ".join(f"{h:^{w}}" for h, w in zip(headers, col_widths))
    print("=" * len(header_line))
    print(header_line)
    print("=" * len(header_line))

    # Print rows
    for row in data:
        print(" | ".join(f"{str(item):<{w}}" for item, w in zip(row, col_widths)))
    print("=" * len(header_line))


def list_violations(conn: sqlite3.Connection) -> None:
    """List all violations."""
    rows = conn.execute("SELECT id, timestamp, service, issue, severity FROM violations WHERE resolved = 0").fetchall()
    print_table(rows, ["ID", "Timestamp", "Service", "Issue", "Severity"]) if rows else print("No active violations found.")


def list_frozen_payments(conn: sqlite3.Connection) -> None:
    """List all frozen payments."""
    rows = conn.execute("SELECT transaction_id, amount, currency, timestamp, customer_id FROM payments WHERE status = 'frozen'").fetchall()
    print_table(rows, ["Transaction ID", "Amount", "Currency", "Timestamp", "Customer ID"]) if rows else print("No frozen payments found.")


def resolve_violation(conn: sqlite3.Connection, violation_id: int) -> None:
    """Mark a violation as resolved."""
    conn.execute("UPDATE violations SET resolved = 1 WHERE id = ?", (violation_id,))
    conn.commit()
    print(f"Violation {violation_id} marked as resolved.")


def unfreeze_payment(conn: sqlite3.Connection, transaction_id: str) -> None:
    """Unfreeze a payment."""
    conn.execute("UPDATE payments SET status = 'active' WHERE transaction_id = ?", (transaction_id,))
    conn.commit()
    print(f"Payment {transaction_id} unfrozen.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tell HN: Stripe ToS update demands biometrics")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")

    args = parser.parse_args()

    if args.demo:
        delete_db()
        conn = sqlite3.connect(str(DB_PATH))
        init_db(conn)
        insert_demo_data(conn)

        # Print violations
        print("\n=== ACTIVE VIOLATIONS ===")
        list_violations(conn)

        # Print frozen payments
        print("\n=== FROZEN PAYMENTS ===")
        list_frozen_payments(conn)

        conn.close()
        return 0

    # violations subcommand
    violations_parser = subparsers.add_parser("violations", help="Manage violations")
    violations_sub = violations_parser.add_subparsers(dest="violation_cmd", required=True)

    list_parser = violations_sub.add_parser("list", help="List active violations")

    resolve_parser = violations_sub.add_parser("resolve", help="Resolve a violation")
    resolve_parser.add_argument("violation_id", type=int, help="ID of violation to resolve")

    # payments subcommand
    payments_parser = subparsers.add_parser("payments", help="Manage payments")
    payments_sub = payments_parser.add_subparsers(dest="payment_cmd", required=True)

    list_payments_parser = payments_sub.add_parser("list", help="List frozen payments")

    unfreeze_parser = payments_sub.add_parser("unfreeze", help="Unfreeze a payment")
    unfreeze_parser.add_argument("transaction_id", help="Transaction ID to unfreeze")

    args = parser.parse_args()

    # Add subparsers for main functionality
    subparsers = parser.add_subparsers(dest="command")
    
    # violations subcommand
    violations_parser = subparsers.add_parser("violations", help="Manage violations")
    violations_sub = violations_parser.add_subparsers(dest="violation_cmd", required=True)
    
    violations_sub.add_parser("list", help="List active violations")
    
    resolve_parser = violations_sub.add_parser("resolve", help="Resolve a violation")
    resolve_parser.add_argument("violation_id", type=int, help="ID of violation to resolve")
    
    # payments subcommand
    payments_parser = subparsers.add_parser("payments", help="Manage payments")
    payments_sub = payments_parser.add_subparsers(dest="payment_cmd", required=True)
    
    payments_sub.add_parser("list", help="List frozen payments")
    
    unfreeze_parser = payments_sub.add_parser("unfreeze", help="Unfreeze a payment")
    unfreeze_parser.add_argument("transaction_id", help="Transaction ID to unfreeze")
    
    args = parser.parse_args()
    
    if args.demo:
        delete_db()
        conn = sqlite3.connect(str(DB_PATH))
        init_db(conn)
        insert_demo_data(conn)
        print("\n=== ACTIVE VIOLATIONS ===")
        list_violations(conn)
        print("\n=== FROZEN PAYMENTS ===")
        list_frozen_payments(conn)
        conn.close()
        return 0
    
    with sqlite3.connect(str(DB_PATH)) as conn:
        init_db(conn)
        if hasattr(args, 'command'):
            if args.command == "violations":
                list_violations(conn) if args.violation_cmd == "list" else resolve_violation(conn, args.violation_id)
            elif args.command == "payments":
                list_frozen_payments(conn) if args.payment_cmd == "list" else unfreeze_payment(conn, args.transaction_id)

    return 0

if __name__ == "__main__":
    sys.exit(main())
