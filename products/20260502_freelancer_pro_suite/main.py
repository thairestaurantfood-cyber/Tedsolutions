#!/usr/bin/env python3
"""FreelancerOS — complete freelance business CLI: clients, invoices, tax, proposals"""
import os, sys, sqlite3, argparse
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/.freelancer_pro_suite.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT, phone TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER, number TEXT UNIQUE, issue_date TEXT,
            due_date TEXT, amount REAL, status TEXT DEFAULT 'draft',
            description TEXT, FOREIGN KEY(client_id) REFERENCES clients(id));
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER, amount REAL, received_date TEXT, notes TEXT);
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER, title TEXT, description TEXT,
            amount REAL, status TEXT DEFAULT 'draft', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    return conn

def add_client(name, email=""):
    db = get_db()
    cur = db.execute("INSERT INTO clients (name,email) VALUES (?,?)", (name, email))
    db.commit(); db.close()
    return cur.lastrowid

def list_clients():
    db = get_db()
    rows = db.execute("SELECT id,name,email FROM clients ORDER BY name").fetchall()
    db.close(); return rows

def add_invoice(client_id, number, due_date, amount, status="sent", desc=""):
    db = get_db()
    today = date.today().isoformat()
    try:
        cur = db.execute(
            "INSERT OR IGNORE INTO invoices (client_id,number,issue_date,due_date,amount,status,description) VALUES (?,?,?,?,?,?,?)",
            (client_id, number, today, due_date, amount, status, desc))
        db.commit()
    finally:
        db.close()

def list_invoices():
    db = get_db()
    rows = db.execute("""SELECT i.number,c.name,i.amount,i.due_date,i.status
        FROM invoices i JOIN clients c ON i.client_id=c.id
        ORDER BY i.due_date""").fetchall()
    db.close(); return rows

def get_overdue():
    today = date.today().isoformat()
    db = get_db()
    rows = db.execute("""SELECT i.number,c.name,i.amount,i.due_date
        FROM invoices i JOIN clients c ON i.client_id=c.id
        WHERE i.due_date < ? AND i.status != 'paid'
        ORDER BY i.due_date""", (today,)).fetchall()
    db.close(); return rows

def add_income(client_id, amount, notes=""):
    db = get_db()
    db.execute("INSERT INTO income (client_id,amount,received_date,notes) VALUES (?,?,?,?)",
        (client_id, amount, date.today().isoformat(), notes))
    db.commit(); db.close()

def tax_estimate():
    db = get_db()
    rows = db.execute("SELECT amount FROM income").fetchall()
    db.close()
    total = sum(r[0] for r in rows)
    rate  = 0.20
    return total, total * rate

def add_proposal(client_id, title, desc, amount):
    db = get_db()
    db.execute("INSERT INTO proposals (client_id,title,description,amount) VALUES (?,?,?,?)",
        (client_id, title, desc, amount))
    db.commit(); db.close()

def list_proposals():
    db = get_db()
    rows = db.execute("""SELECT p.title,c.name,p.amount,p.status
        FROM proposals p JOIN clients c ON p.client_id=c.id
        ORDER BY p.created_at DESC""").fetchall()
    db.close(); return rows

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    print("\n=== FreelancerOS Demo — Your Complete Freelance Business ===\n")
    c1 = add_client("Acme Corp", "billing@acme.com")
    c2 = add_client("Tech Startup", "hello@startup.io")
    print("📋 CLIENTS:")
    for c in list_clients():
        print(f"  #{c[0]} {c[1]:20} {c[2]}")
    add_invoice(c1, "INV-001", "2026-04-15", 1500.00, "overdue", "Web development")
    add_invoice(c2, "INV-002", "2026-05-20", 2200.00, "sent",    "App design")
    add_invoice(c1, "INV-003", "2026-06-01", 3000.00, "draft",   "SEO package")
    print("\n💰 INVOICES:")
    for inv in list_invoices():
        flag = "🔴" if inv[4] == "overdue" else "🟡" if inv[4] == "sent" else "⚪"
        print(f"  {flag} {inv[0]:10} {inv[1]:20} ${inv[2]:>8.2f}  due {inv[3]}  [{inv[4]}]")
    overdue = get_overdue()
    if overdue:
        print(f"\n⚠️  OVERDUE ALERTS ({len(overdue)} invoice{'s' if len(overdue)>1 else ''}):")
        for o in overdue:
            print(f"  🔴 {o[0]} — {o[1]} — ${o[2]:.2f} — was due {o[3]}")
    add_income(c1, 1500.00, "INV-001 paid via bank transfer")
    add_income(c2,  800.00, "Partial payment INV-002")
    total_inc, tax = tax_estimate()
    print(f"\n📊 TAX ESTIMATE:")
    print(f"  Total income:    ${total_inc:>8.2f}")
    print(f"  Estimated tax:   ${tax:>8.2f}  (20% rate)")
    print(f"  Keep aside:      ${tax:>8.2f}")
    add_proposal(c1, "Website Redesign Q3", "Full redesign modern UI/UX", 3500.00)
    add_proposal(c2, "Mobile App MVP",       "Cross-platform React Native app", 5000.00)
    print(f"\n📝 PROPOSALS:")
    for p in list_proposals():
        print(f"  {p[0]:30} {p[1]:20} ${p[2]:>8.2f}  [{p[3]}]")
    print(f"\n✅ FreelancerOS — $49/mo — clients invoices tax proposals in one CLI")

def main():
    parser = argparse.ArgumentParser(description="FreelancerOS — complete freelance business CLI")
    parser.add_argument("--demo", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo(); return
    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.add_parser("clients",   help="List clients")
    subparsers.add_parser("invoices",  help="List invoices")
    subparsers.add_parser("overdue",   help="Show overdue invoices")
    subparsers.add_parser("tax",       help="Tax estimate")
    subparsers.add_parser("proposals", help="List proposals")
    args = parser.parse_args()
    get_db()
    if   args.cmd == "clients":   [print(f"  #{c[0]} {c[1]} {c[2] or ''}") for c in list_clients()]
    elif args.cmd == "invoices":  [print(f"  {i[0]} ${i[2]:.2f} [{i[4]}]") for i in list_invoices()]
    elif args.cmd == "overdue":   [print(f"  🔴 {o[0]} {o[1]} ${o[2]:.2f}") for o in get_overdue()]
    elif args.cmd == "tax":       print(f"  Income: ${tax_estimate()[0]:.2f}  Tax: ${tax_estimate()[1]:.2f}")
    elif args.cmd == "proposals": [print(f"  {p[0]} ${p[2]:.2f} [{p[3]}]") for p in list_proposals()]
    else: parser.print_help()

if __name__ == "__main__":
    main()
