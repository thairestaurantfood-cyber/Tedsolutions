import os
import sys
import json
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import subprocess
import urllib.request
import re
import time

# Define get_db() to create tables if they don't exist
def get_db():
    db_path = os.path.expanduser("~/.invoicetracker.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT
        )
    ''')
    conn.commit()
    return conn

# Function to add a client to the database
def add_client(conn, name, email, phone):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO clients (name, email, phone) VALUES (?, ?, ?)', (name, email, phone))
    conn.commit()

# Function to add an invoice to the database
def add_invoice(conn, client, amount, currency, due_date, notes=None):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (client, amount, currency, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client, amount, currency, due_date, 'pending', notes))
    conn.commit()

# Function to list all invoices with a specific status
def list_invoices(conn, status=None):
    cursor = conn.cursor()
    query = "SELECT * FROM invoices"
    if status:
        query += f" WHERE status = '{status}'"
    cursor.execute(query)
    return cursor.fetchall()

# Function to mark an invoice as paid by ID
def mark_paid(conn, invoice_id):
    cursor = conn.cursor()
    cursor.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (invoice_id,))
    conn.commit()

# Function to list all overdue invoices with days overdue calculated from datetime.now()
def list_overdue_invoices(conn):
    today = datetime.now()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM invoices
        WHERE status = 'pending'
          AND due_date < ?
    ''', (today.strftime('%Y-%m-%d'),))
    overdue_invoices = cursor.fetchall()
    for invoice in overdue_invoices:
        days_overdue = (today - datetime.strptime(invoice[4], '%Y-%m-%d')).days
        print(f"Invoice ID: {invoice[0]}, Client: {invoice[1]}, Amount: {invoice[2]} {invoice[3]}, Due Date: {invoice[4]}, Status: {invoice[5]}, Days Overdue: {days_overdue}")
    return overdue_invoices

# Function to display total outstanding, total paid this month, count overdue
def display_summary(conn):
    today = datetime.now()
    cursor = conn.cursor()

    # Total outstanding
    cursor.execute('''
        SELECT SUM(amount) AS total_outstanding
        FROM invoices
        WHERE status != 'paid'
    ''')
    total_outstanding = cursor.fetchone()[0]

    # Total paid this month
    cursor.execute('''
        SELECT SUM(amount) AS total_paid_this_month
        FROM invoices
        WHERE status = 'paid'
          AND strftime('%Y-%m', created) = strftime('%Y-%m', ?)
    ''', (today,))
    total_paid_this_month = cursor.fetchone()[0]

    # Count overdue
    cursor.execute('''
        SELECT COUNT(*) AS count_overdue
        FROM invoices
        WHERE status = 'pending'
          AND due_date < ?
    ''', (today.strftime('%Y-%m-%d'),))
    count_overdue = cursor.fetchone()[0]

    print(f"Total Outstanding: {total_outstanding}")
    print(f"Total Paid This Month: {total_paid_this_month}")
    print(f"Count Overdue: {count_overdue}")

# Function to export all invoices to a CSV file
def export_invoices(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM invoices')
    rows = cursor.fetchall()

    with open(os.path.expanduser("~/.jarvis/invoices_export.csv"), 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['ID', 'Client', 'Amount', 'Currency', 'Due Date', 'Status', 'Notes'])
        for row in rows:
            writer.writerow(row)

# Function to calculate average payment delay
def calculate_average_payment_delay(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT AVG(TIMESTAMPDIFF(DAY, created, due_date)) AS avg_payment_delay
        FROM invoices
        WHERE status != 'paid'
    ''')
    return cursor.fetchone()[0]

# Function to find best/worst paying clients from historical data
def find_best_worst_paying_clients(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT client, SUM(amount) AS total_spent
        FROM invoices
        WHERE status != 'pending'
        GROUP BY client
        ORDER BY total_spent DESC
        LIMIT 1
    ''')
    best_client = cursor.fetchone()

    cursor.execute('''
        SELECT client, SUM(amount) AS total_spent
        FROM invoices
        WHERE status != 'paid'
        GROUP BY client
        ORDER BY total_spent ASC
        LIMIT 1
    ''')
    worst_client = cursor.fetchone()

    print(f"Best Paying Client: {best_client[0]}, Total Spent: {best_client[1]}")
    print(f"Worst Paying Client: {worst_client[0]}, Total Spent: {worst_client[1]}")

# Main function to handle command-line arguments and execute commands
def main():
    parser = argparse.ArgumentParser(description="InvoiceTracker CLI tool")
    parser.add_argument("--add-client", help="Add a client with name, email, and phone")
    parser.add_argument("--add-invoice", help="Add an invoice for a client with amount, due date, and notes")
    parser.add_argument("--list", help="List all invoices with status")
    parser.add_argument("--paid", help="Mark an invoice as paid by ID")
    parser.add_argument("--demo", action="store_true", help="Run demo with offline hardcoded data")
    parser.add_argument("--overdue", action="store_true", help="List invoices past due date with days overdue calculated from datetime.now()")
    parser.add_argument("--summary", action="store_true", help="Display total outstanding, total paid this month, count overdue")
    parser.add_argument("--export", action="store_true", help="Export all invoices to ~/invoices_export.csv using csv module")
    parser.add_argument("--client", help="Show all invoices for one client")
    parser.add_argument("--search", help="Find invoices by client name or notes")
    parser.add_argument("--stats", action="store_true", help="Display average payment delay, best/worst paying clients from historical data")

    args = parser.parse_args()

    conn = get_db()
    cursor = conn.cursor()

    if args.demo:
        # Offline hardcoded data for demonstration
        clients_data = [
            ("Alice Smith", "alice@example.com", "123-456-7890"),
            ("Bob Johnson", "bob@example.com", "987-654-3210"),
            ("Charlie Brown", "charlie@example.com", "555-555-5555")
        ]
        invoices_data = [
            ("Alice Smith",   1500.0, "THB", "2026-04-15", "overdue",  "Website redesign"),
            ("Bob Johnson",   3200.0, "USD", "2026-04-20", "overdue",  "API integration"),
            ("Charlie Brown", 800.0,  "USD", "2026-05-01", "pending",  "Logo design"),
            ("Alice Smith",   2400.0, "THB", "2026-05-10", "pending",  "Monthly retainer"),
            ("Bob Johnson",   1100.0, "USD", "2026-05-15", "paid",     "Consulting session")
        ]

        for client in clients_data:
            add_client(conn, *client)

        for invoice in invoices_data:
            add_invoice(conn, *invoice)

    if args.add_client:
        add_client(conn, args.add_client.split(", ")[0], args.add_client.split(", ")[1], args.add_client.split(", ")[2])
        print("Client added successfully.")

    elif args.add_invoice:
        add_invoice(conn, args.add_invoice.split(", ")[0], float(args.add_invoice.split(", ")[1]), args.add_invoice.split(", ")[2], args.add_invoice.split(", ")[3], args.add_invoice.split(", ")[4])
        print("Invoice added successfully.")

    elif args.list:
        invoices = list_invoices(conn, args.list)
        for