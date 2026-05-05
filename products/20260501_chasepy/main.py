import os, sys, sqlite3, argparse
from datetime import datetime, timedelta, date

DB_PATH = os.path.expanduser("~/.chasepy/invoices.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client TEXT NOT NULL,
            email TEXT DEFAULT '',
            amount REAL NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'unpaid',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            sent_at TEXT,
            days_overdue INTEGER,
            stage TEXT,
            message TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        );
    """)
    conn.commit()
    return conn

# ── Escalation engine ──────────────────────────────────────────
STAGES = {
    "day1":  {"days": 1,  "tone": "friendly",     "label": "👋 Friendly nudge"},
    "day7":  {"days": 7,  "tone": "firm",          "label": "📋 Firm reminder"},
    "day14": {"days": 14, "tone": "final",         "label": "🚨 Final notice"},
}

def get_stage(days_overdue):
    if days_overdue >= 14: return "day14"
    if days_overdue >= 7:  return "day7"
    if days_overdue >= 1:  return "day1"
    return None

def build_message(stage, client, amount, due_date, invoice_id):
    tone = STAGES[stage]["tone"]
    amt = f"${amount:.2f}"
    if tone == "friendly":
        return (f"Hi {client},\n\n"
                f"Just a friendly reminder that invoice #{invoice_id} for {amt} "
                f"was due on {due_date}.\n"
                f"Please let us know if you have any questions.\n\n"
                f"Thanks for your business!")
    elif tone == "firm":
        return (f"Dear {client},\n\n"
                f"This is a follow-up regarding invoice #{invoice_id} for {amt}, "
                f"which is now 7 days overdue (due {due_date}).\n"
                f"Please arrange payment at your earliest convenience.\n\n"
                f"If payment has already been sent, please disregard this notice.")
    else:  # final
        return (f"FINAL NOTICE — {client}\n\n"
                f"Invoice #{invoice_id} for {amt} is now 14+ days overdue.\n"
                f"Due date was: {due_date}\n\n"
                f"Immediate payment is required to avoid further action.\n"
                f"Please contact us within 48 hours to resolve this matter.")

def already_sent(conn, invoice_id, stage):
    row = conn.execute(
        "SELECT id FROM reminders WHERE invoice_id=? AND stage=?",
        (invoice_id, stage)).fetchone()
    return row is not None

# ── Commands ───────────────────────────────────────────────────
def cmd_add(args):
    db = get_db()
    db.execute("INSERT INTO invoices (client,email,amount,due_date,notes) VALUES (?,?,?,?,?)",
        (args.client, args.email or "", args.amount, args.due, args.notes or ""))
    db.commit()
    db.close()
    print(f"✅ Invoice added: {args.client} ${args.amount:.2f} due {args.due}")

def cmd_list(args):
    db = get_db()
    q = "SELECT id,client,amount,due_date,status FROM invoices"
    params = []
    if args.status:
        q += " WHERE status=?"; params.append(args.status)
    q += " ORDER BY due_date"
    rows = db.execute(q, params).fetchall()
    today = date.today().isoformat()
    if not rows:
        print("No invoices."); return
    print(f"\n{'ID':<5} {'CLIENT':<22} {'AMOUNT':>10} {'DUE':<12} {'STATUS':<10} {'OVERDUE'}")
    print("-" * 72)
    for r in rows:
        days_od = (date.today() - date.fromisoformat(r[3])).days if r[3] < today else 0
        flag = f"  {days_od}d" if days_od > 0 and r[4] != "paid" else ""
        print(f"{r[0]:<5} {r[1]:<22} ${r[2]:>9.2f} {r[3]:<12} {r[4]:<10}{flag}")
    db.close()

def cmd_chase(args):
    """Core escalation engine — checks all unpaid overdue invoices."""
    db = get_db()
    today = date.today().isoformat()
    invoices = db.execute(
        "SELECT id,client,email,amount,due_date FROM invoices WHERE status='unpaid' AND due_date < ?",
        (today,)).fetchall()

    if not invoices:
        print("✅ No overdue invoices to chase.")
        db.close(); return

    print(f"\n🎯 CHASEPY — Escalation Run {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Found {len(invoices)} overdue invoice(s)\n")

    acted = 0
    for inv_id, client, email, amount, due_date in invoices:
        days_od = (date.today() - date.fromisoformat(due_date)).days
        stage = get_stage(days_od)
        if not stage:
            continue

        label = STAGES[stage]["label"]

        if already_sent(db, inv_id, stage):
            print(f"  ⏭️  #{inv_id} {client:<20} {days_od}d overdue — {label} already sent")
            continue

        msg = build_message(stage, client, amount, due_date, inv_id)

        # Log reminder
        db.execute("INSERT INTO reminders (invoice_id,sent_at,days_overdue,stage,message) VALUES (?,?,?,?,?)",
            (inv_id, datetime.now().isoformat(), days_od, stage, msg))
        db.commit()

        print(f"  ✅ #{inv_id} {client:<20} {days_od}d overdue — {label}")
        if args.verbose:
            print(f"\n{'─'*50}")
            print(msg)
            print(f"{'─'*50}\n")
        acted += 1

    print(f"\n  Sent: {acted} reminders | Skipped (already sent): {len(invoices)-acted}")
    db.close()

def cmd_history(args):
    db = get_db()
    rows = db.execute("""SELECT r.sent_at,i.client,i.amount,r.days_overdue,r.stage,r.message
        FROM reminders r JOIN invoices i ON r.invoice_id=i.id
        ORDER BY r.sent_at DESC LIMIT 20""").fetchall()
    if not rows:
        print("No reminder history yet."); return
    print(f"\n{'DATE':<20} {'CLIENT':<20} {'AMOUNT':>10} {'DAYS':>6} {'STAGE':<8}")
    print("-" * 68)
    for r in rows:
        print(f"{r[0][:16]:<20} {r[1]:<20} ${r[2]:>9.2f} {r[3]:>6}d {r[4]:<8}")
    db.close()

def cmd_paid(args):
    db = get_db()
    db.execute("UPDATE invoices SET status='paid' WHERE id=?", (args.id,))
    db.commit()
    row = db.execute("SELECT client,amount FROM invoices WHERE id=?", (args.id,)).fetchone()
    db.close()
    if row:
        print(f"✅ Invoice #{args.id} marked PAID — {row[0]} ${row[1]:.2f}")
    else:
        print(f"❌ Invoice #{args.id} not found")

def cmd_summary(args):
    db = get_db()
    today = date.today().isoformat()
    total = db.execute("SELECT COUNT(*),SUM(amount) FROM invoices WHERE status='unpaid'").fetchone()
    overdue = db.execute("SELECT COUNT(*),SUM(amount) FROM invoices WHERE status='unpaid' AND due_date<?", (today,)).fetchone()
    reminders = db.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]
    stage_counts = db.execute("SELECT stage,COUNT(*) FROM reminders GROUP BY stage").fetchall()
    print(f"""
╔══════════════════════════════════════╗
║       CHASEPY — DASHBOARD            ║
╚══════════════════════════════════════╝
  Unpaid invoices: {total[0]}  (${total[1] or 0:.2f})
  Overdue:         {overdue[0]}  (${overdue[1] or 0:.2f})
  Reminders sent:  {reminders}""")
    for s, c in stage_counts:
        print(f"    {STAGES.get(s,{}).get('label','?')}: {c}")
    print()
    db.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = get_db()
    today = date.today()
    invoices = [
        ("Acme Corp",        "acme@corp.com",    1500.00, (today - timedelta(days=2)).isoformat(),  "Project A"),
        ("Globex Inc",       "globex@inc.com",   2300.50, (today - timedelta(days=8)).isoformat(),  "Project B"),
        ("Initech",          "init@ech.com",      950.75, (today - timedelta(days=15)).isoformat(), "Project C"),
        ("Wayne Enterprises","wayne@ent.com",    5000.00, (today - timedelta(days=1)).isoformat(),  "Project D"),
        ("Stark Industries", "stark@ind.com",    7500.50, (today + timedelta(days=5)).isoformat(),  "Project E"),
    ]
    for c, e, a, d, n in invoices:
        db.execute("INSERT INTO invoices (client,email,amount,due_date,notes) VALUES (?,?,?,?,?)",
            (c, e, a, d, n))
    db.commit()
    db.close()

    print("✅ Demo data loaded!\n")
    import types
    a = types.SimpleNamespace(status=None, verbose=True, id=None)
    cmd_summary(a)
    cmd_list(a)
    print("\n── Running escalation engine ──\n")
    cmd_chase(a)
    print("\n── Reminder history ──")
    cmd_history(a)

def main():
    parser = argparse.ArgumentParser(description="ChasePy — Escalating invoice reminders")
    parser.add_argument("--demo", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo(); return

    subs = parser.add_subparsers(dest="command")

    p = subs.add_parser("add", help="Add invoice")
    p.add_argument("--client", required=True)
    p.add_argument("--email", default="")
    p.add_argument("--amount", type=float, required=True)
    p.add_argument("--due", required=True, help="YYYY-MM-DD")
    p.add_argument("--notes", default="")

    p = subs.add_parser("list", help="List invoices")
    p.add_argument("--status", default=None)

    p = subs.add_parser("chase", help="Run escalation engine")
    p.add_argument("--verbose", action="store_true", help="Show full message text")

    p = subs.add_parser("paid", help="Mark invoice paid")
    p.add_argument("--id", type=int, required=True)

    subs.add_parser("history", help="Show reminder history")
    subs.add_parser("summary", help="Dashboard")

    args = parser.parse_args()
    if not args.command:
        parser.print_help(); return

    cmds = {"add":cmd_add, "list":cmd_list, "chase":cmd_chase,
            "paid":cmd_paid, "history":cmd_history, "summary":cmd_summary}
    cmds[args.command](args)

if __name__ == "__main__":
    main()
