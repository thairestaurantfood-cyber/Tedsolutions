import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.freelancer_pro_suite.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        address TEXT,
        tax_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        number TEXT NOT NULL UNIQUE,
        issue_date TEXT NOT NULL,
        due_date TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('draft', 'sent', 'paid', 'overdue')),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        client_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        payment_date TEXT NOT NULL,
        payment_method TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE SET NULL,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('draft', 'sent', 'accepted', 'rejected')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

def add_client(name, email=None, phone=None, address=None, tax_id=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clients (name, email, phone, address, tax_id) VALUES (?, ?, ?, ?, ?)",
        (name, email, phone, address, tax_id)
    )
    conn.commit()
    client_id = cursor.lastrowid
    conn.close()
    return client_id

def list_clients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM clients ORDER BY name")
    clients = cursor.fetchall()
    conn.close()
    return clients

def add_invoice(client_id, number, issue_date, due_date, amount, status="draft", description=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO invoices
        (client_id, number, issue_date, due_date, amount, status, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (client_id, number, issue_date, due_date, amount, status, description)
    )
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    return invoice_id

def list_invoices():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.id, i.number, i.issue_date, i.due_date, i.amount, i.status,
           c.name as client_name
    FROM invoices i
    JOIN clients c ON i.client_id = c.id
    ORDER BY i.issue_date DESC
    """)
    invoices = cursor.fetchall()
    conn.close()
    return invoices

def add_income(invoice_id, client_id, amount, payment_date, payment_method=None, notes=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO income
        (invoice_id, client_id, amount, payment_date, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (invoice_id, client_id, amount, payment_date, payment_method, notes)
    )
    conn.commit()
    income_id = cursor.lastrowid
    conn.close()
    return income_id

def list_income():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT i.id, i.amount, i.payment_date, i.payment_method,
           c.name as client_name, inv.number as invoice_number
    FROM income i
    JOIN clients c ON i.client_id = c.id
    LEFT JOIN invoices inv ON i.invoice_id = inv.id
    ORDER BY i.payment_date DESC
    """)
    income = cursor.fetchall()
    conn.close()
    return income

def add_proposal(client_id, title, description, amount, status="draft"):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO proposals
        (client_id, title, description, amount, status)
        VALUES (?, ?, ?, ?, ?)""",
        (client_id, title, description, amount, status)
    )
    conn.commit()
    proposal_id = cursor.lastrowid
    conn.close()
    return proposal_id

def list_proposals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT p.id, p.title, p.amount, p.status,
           c.name as client_name
    FROM proposals p
    JOIN clients c ON p.client_id = c.id
    ORDER BY p.created_at DESC
    """)
    proposals = cursor.fetchall()
    conn.close()
    return proposals

def demo():
    print("\n=== Freelancer Pro Suite - Demo ===")

    # Initialize database
    init_db()

    # Add sample clients
    client1 = add_client("Acme Corp", "billing@acme.com", "+1234567890", "123 Business St, NY")
    client2 = add_client("Tech Startup", "contact@startup.io", "+1987654321", "456 Innovation Ave, SF")

    print("\nAdded sample clients:")
    for client in list_clients():
        print(f"  {client[0]}: {client[1]} ({client[2]})")

    # Add sample invoices
    invoice1 = add_invoice(client1, "INV-2024-001", "2024-05-01", "2024-05-15", 1500.00, "sent", "Website development")
    invoice2 = add_invoice(client2, "INV-2024-002", "2024-05-05", "2024-05-20", 2200.00, "draft", "Mobile app design")

    print("\nAdded sample invoices:")
    for invoice in list_invoices():
        print(f"  {invoice[1]}: ${invoice[4]:.2f} ({invoice[5]}) for {invoice[6]}")

    # Add sample income
    income1 = add_income(invoice1, client1, 1500.00, "2024-05-10", "Bank Transfer", "Full payment received")

    print("\nAdded sample income:")
    for inc in list_income():
        print(f"  ${inc[1]:.2f} from {inc[4]} on {inc[2]}")

    # Add sample proposals
    proposal1 = add_proposal(client1, "Website Redesign", "Complete website redesign with modern UI", 3500.00, "sent")
    proposal2 = add_proposal(client2, "Mobile App", "Cross-platform mobile application development", 5000.00, "draft")

    print("\nAdded sample proposals:")
    for proposal in list_proposals():
        print(f"  {proposal[1]}: ${proposal[2]:.2f} ({proposal[3]}) for {proposal[4]}")

    print("\nDemo completed successfully!")

def main():
    parser = argparse.ArgumentParser(description="Freelancer Pro Suite - Unified CLI for client management, invoicing, and proposals")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    # Initialize database
    init_db()

    # Main CLI interface would go here
    print("Freelancer Pro Suite initialized. Use --demo to see sample data or implement CLI commands.")

if __name__ == "__main__":
    main()