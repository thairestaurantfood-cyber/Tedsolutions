import os, sys, sqlite3, argparse
from datetime import datetime, date

DB_PATH = os.path.expanduser("~/.freelancer_pro_suite.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, email TEXT, phone TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
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
            amount REAL, status TEXT DEFAULT 'draft',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    return conn

def cmd_clients(args):
    db = get_db()
    if args.add:
        parts = args.add.split(",")
        name = parts[0].strip()
        email = parts[1].strip() if len(parts) > 1 else ""
        cur = db.execute("INSERT INTO clients (name,email) VALUES (?,?)", (name, email))
        db.commit()
        print(f"✅ Client added: {name} (id={cur.lastrowid})")
    else:
        rows = db.execute("SELECT id,name,email FROM clients ORDER BY name").fetchall()
        if not rows:
            print("No clients yet. Use: clients --add 'Name, email@x.com'")
        else:
            print(f"\n{'ID':<5} {'NAME':<25} {'EMAIL'}")
            print("-" * 55)
            for r in rows:
                print(f"{r[0]:<5} {r[1]:<25} {r[2] or '-'}")
    db.close()

def cmd_invoice(args):
    db = get_db()
    if args.add:
        # format: client_id,number,due_date,amount,description
        p = args.add.split(",")
        if len(p) < 4:
            print("Usage: invoice --add 'client_id,INV-001,2026-06-01,1500,Description'")
            return
        cid, num, due, amt = p[0].strip(), p[1].strip(), p[2].strip(), float(p[3].strip())
        desc = p[4].strip() if len(p) > 4 else ""
        db.execute("INSERT OR IGNORE INTO invoices (client_id,number,issue_date,due_date,amount,status,description) VALUES (?,?,?,?,?,?,?)",
            (cid, num, date.today().isoformat(), due, amt, "sent", desc))
        db.commit()
        print(f"✅ Invoice {num} created — ${amt:.2f} due {due}")
    else:
        rows = db.execute("""SELECT i.number,c.name,i.amount,i.due_date,i.status
            FROM invoices i JOIN clients c ON i.client_id=c.id
            ORDER BY i.due_date""").fetchall()
        if not rows:
            print("No invoices yet.")
        else:
            print(f"\n{'NUMBER':<15} {'CLIENT':<20} {'AMOUNT':>10} {'DUE':<12} {'STATUS'}")
            print("-" * 70)
            for r in rows:
                flag = " ⚠️ " if r[3] < date.today().isoformat() and r[4] != "paid" else ""
                print(f"{r[0]:<15} {r[1]:<20} ${r[2]:>9.2f} {r[3]:<12} {r[4]}{flag}")
    db.close()

def cmd_overdue(args):
    today = date.today().isoformat()
    db = get_db()
    rows = db.execute("""SELECT i.number,c.name,i.amount,i.due_date
        FROM invoices i JOIN clients c ON i.client_id=c.id
        WHERE i.due_date < ? AND i.status != 'paid'
        ORDER BY i.due_date""", (today,)).fetchall()
    if not rows:
        print("✅ No overdue invoices!")
    else:
        print(f"\n⚠️  OVERDUE INVOICES ({len(rows)})")
        print("-" * 55)
        total = 0
        for r in rows:
            days = (date.today() - date.fromisoformat(r[3])).days
            print(f"  {r[0]:<15} {r[1]:<20} ${r[2]:.2f}  ({days}d overdue)")
            total += r[2]
        print(f"\n  TOTAL OVERDUE: ${total:.2f}")
    db.close()

def cmd_income(args):
    db = get_db()
    if args.add:
        p = args.add.split(",")
        cid, amt = p[0].strip(), float(p[1].strip())
        notes = p[2].strip() if len(p) > 2 else ""
        db.execute("INSERT INTO income (client_id,amount,received_date,notes) VALUES (?,?,?,?)",
            (cid, amt, date.today().isoformat(), notes))
        db.commit()
        print(f"✅ Income recorded: ${amt:.2f}")
    else:
        rows = db.execute("""SELECT c.name,i.amount,i.received_date,i.notes
            FROM income i JOIN clients c ON i.client_id=c.id
            ORDER BY i.received_date DESC""").fetchall()
        total = sum(r[1] for r in rows)
        print(f"\n{'CLIENT':<25} {'AMOUNT':>10} {'DATE':<12} {'NOTES'}")
        print("-" * 65)
        for r in rows:
            print(f"{r[0]:<25} ${r[1]:>9.2f} {r[2]:<12} {r[3] or ''}")
        print(f"\n  TOTAL INCOME: ${total:.2f}")
    db.close()

def cmd_summary(args):
    db = get_db()
    clients = db.execute("SELECT COUNT(*) FROM clients").fetchone()[0]
    invoices = db.execute("SELECT COUNT(*),SUM(amount) FROM invoices").fetchone()
    paid = db.execute("SELECT COUNT(*),SUM(amount) FROM invoices WHERE status='paid'").fetchone()
    overdue = db.execute("SELECT COUNT(*),SUM(amount) FROM invoices WHERE due_date < ? AND status!='paid'",
        (date.today().isoformat(),)).fetchone()
    income = db.execute("SELECT SUM(amount) FROM income").fetchone()[0] or 0
    print(f"""
╔══════════════════════════════════════╗
║     FREELANCER PRO SUITE — SUMMARY   ║
╚══════════════════════════════════════╝
  Clients:        {clients}
  Total Invoices: {invoices[0]}  (${invoices[1] or 0:.2f})
  Paid:           {paid[0]}  (${paid[1] or 0:.2f})
  Overdue:        {overdue[0]}  (${overdue[1] or 0:.2f})  {'⚠️ ' if overdue[0] else '✅'}
  Income logged:  ${income:.2f}
""")
    db.close()

def demo():
    # Fresh DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = get_db()

    c1 = db.execute("INSERT INTO clients (name,email) VALUES (?,?)", ("Acme Corp","contact@acme.com")).lastrowid
    c2 = db.execute("INSERT INTO clients (name,email) VALUES (?,?)", ("Tech Startup","hello@techstartup.io")).lastrowid
    c3 = db.execute("INSERT INTO clients (name,email) VALUES (?,?)", ("Local Business","info@localbiz.com")).lastrowid
    db.commit()

    today = date.today().isoformat()
    db.execute("INSERT INTO invoices (client_id,number,issue_date,due_date,amount,status,description) VALUES (?,?,?,?,?,?,?)",
        (c1,"INV-001","2026-04-01","2026-04-20",1250.00,"sent","Website development"))
    db.execute("INSERT INTO invoices (client_id,number,issue_date,due_date,amount,status,description) VALUES (?,?,?,?,?,?,?)",
        (c2,"INV-002","2026-04-10","2026-04-30",850.00,"paid","Mobile app design"))
    db.execute("INSERT INTO invoices (client_id,number,issue_date,due_date,amount,status,description) VALUES (?,?,?,?,?,?,?)",
        (c3,"INV-003","2026-04-15",today,600.00,"sent","SEO optimization"))
    db.execute("INSERT INTO income (client_id,amount,received_date,notes) VALUES (?,?,?,?)",
        (c2,850.00,"2026-04-30","Payment for INV-002"))
    db.execute("INSERT INTO income (client_id,amount,received_date,notes) VALUES (?,?,?,?)",
        (c1,500.00,"2026-04-25","Partial payment INV-001"))
    db.commit()
    db.close()

def main():
    parser = argparse.ArgumentParser(description="Freelancer Pro Suite")
    parser.add_argument("--demo", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        print("✅ Demo data loaded!\n")
        # Show everything
        import types
        a = types.SimpleNamespace(add=None)
        cmd_summary(a); cmd_clients(a); cmd_invoice(a); cmd_overdue(a); cmd_income(a)
        return

    subs = parser.add_subparsers(dest="command")

    p_c = subs.add_parser("clients", help="List or add clients")
    p_c.add_argument("--add", help="'Name, email'")

    p_i = subs.add_parser("invoice", help="List or add invoices")
    p_i.add_argument("--add", help="'client_id,INV-001,2026-06-01,1500,desc'")

    p_o = subs.add_parser("overdue", help="Show overdue invoices")

    p_inc = subs.add_parser("income", help="Log or list income")
    p_inc.add_argument("--add", help="'client_id,amount,notes'")

    p_s = subs.add_parser("summary", help="Dashboard summary")

    args = parser.parse_args()
    if not args.command:
        parser.print_help(); return

    cmds = {"clients":cmd_clients,"invoice":cmd_invoice,
            "overdue":cmd_overdue,"income":cmd_income,"summary":cmd_summary}
    cmds[args.command](args)

if __name__ == "__main__":
    main()
