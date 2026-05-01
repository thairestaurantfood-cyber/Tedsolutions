import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import re
import time

DB_PATH = os.path.expanduser("~/.tax_cruncher.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS tax_rules (region TEXT PRIMARY KEY, rate REAL)")
    conn.execute("CREATE TABLE IF NOT EXISTS income (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, amount REAL, description TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, quarter TEXT, amount REAL, paid_date TEXT)")
    conn.close()

def load_sample_data():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM income")
    conn.execute("DELETE FROM payments")

    sample_income = [
        ("2024-01-15", 1500.0, "Freelance project A"),
        ("2024-01-20", 800.0, "Consulting work"),
        ("2024-02-05", 2200.0, "Web development"),
        ("2024-03-10", 1800.0, "App design"),
        ("2024-03-25", 3000.0, "Mobile app project")
    ]

    conn.executemany("INSERT INTO income (date, amount, description) VALUES (?, ?, ?)", sample_income)
    conn.commit()

    conn.execute("INSERT OR IGNORE INTO tax_rules VALUES (?, ?)", ("SEA", 0.30))
    conn.commit()
    conn.close()

def set_tax_rule(region, rate):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR REPLACE INTO tax_rules VALUES (?, ?)", (region, rate))
    conn.commit()
    conn.close()
    print(f"Tax rule set: {region} at {rate*100:.1f}%")

def get_payment_deadline(quarter):
    quarters = {
        "Q1": "2024-04-15",
        "Q2": "2024-07-15",
        "Q3": "2024-10-15",
        "Q4": "2025-01-15"
    }
    return quarters.get(quarter, "2025-01-15")

def calculate_quarterly_estimates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT rate FROM tax_rules LIMIT 1")
    result = cursor.fetchone()
    if not result:
        print("Error: No tax rule set. Please set tax rules first.")
        conn.close()
        return None
    tax_rate = result[0]

    cursor.execute("SELECT date, amount FROM income ORDER BY date")
    income_data = cursor.fetchall()

    quarters = {
        "Q1": {"start": "2024-01-01", "end": "2024-03-31", "income": 0.0},
        "Q2": {"start": "2024-04-01", "end": "2024-06-30", "income": 0.0},
        "Q3": {"start": "2024-07-01", "end": "2024-09-30", "income": 0.0},
        "Q4": {"start": "2024-10-01", "end": "2024-12-31", "income": 0.0}
    }

    for date_str, amount in income_data:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        quarter = f"Q{((date.month-1)//3)+1}"
        quarters[quarter]["income"] += amount

    estimates = []
    for quarter, data in quarters.items():
        tax_estimate = data["income"] * tax_rate
        payment_deadline = get_payment_deadline(quarter)
        estimates.append({
            "quarter": quarter,
            "income": data["income"],
            "tax_estimate": tax_estimate,
            "payment_deadline": payment_deadline
        })

    conn.close()
    return estimates

def generate_report(estimates):
    report = []
    total_income = 0
    total_tax = 0

    for est in estimates:
        report.append(f"{est['quarter']}: Income=${est['income']:.2f}, Tax=${est['tax_estimate']:.2f}, Due={est['payment_deadline']}")
        total_income += est['income']
        total_tax += est['tax_estimate']

    report.append(f"\nTotal Income: ${total_income:.2f}")
    report.append(f"Total Estimated Tax: ${total_tax:.2f}")
    report.append(f"Effective Tax Rate: {total_tax/total_income*100:.1f}%")

    return "\n".join(report)

def main():
    get_db()

    parser = argparse.ArgumentParser(description="Tax Cruncher CLI - Quarterly tax estimates for freelancers")
    parser.add_argument("--demo", action="store_true", help="Load sample data and show quarterly estimates")
    parser.add_argument("--set-tax", nargs=2, metavar=("REGION", "RATE"), help="Set tax rate for region (e.g., SEA 0.30)")
    parser.add_argument("--report", action="store_true", help="Generate tax report")

    args = parser.parse_args()

    if args.demo:
        load_sample_data()
        estimates = calculate_quarterly_estimates()
        if estimates:
            print(generate_report(estimates))

    elif args.set_tax:
        region, rate = args.set_tax
        try:
            set_tax_rule(region, float(rate))
        except ValueError:
            print("Error: Rate must be a number")

    elif args.report:
        estimates = calculate_quarterly_estimates()
        if estimates:
            print(generate_report(estimates))

    else:
        parser.print_help()

if __name__ == "__main__":
    main()