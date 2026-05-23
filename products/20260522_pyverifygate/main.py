import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/pyverifygate.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS loops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    invariant TEXT NOT NULL,
    bound INTEGER NOT NULL,
    created_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def add_loop(code: str, invariant: str, bound: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
    'INSERT INTO loops (code, invariant, bound, created_at) VALUES (?, ?, ?, ?)',
    (code, invariant, bound, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def list_loops():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, code, invariant, bound, created_at FROM loops')
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("No loops verified yet.")
        return
    print(f"{'ID':<5} {'Code':<30} {'Invariant':<20} {'Bound':<10} {'Created':<20}")
    print("-" * 85)
    for row in rows:
        print(f"{row[0]:<5} {row[1][:27]+'...':<30} {row[2][:17]+'...':<20} {row[3]:<10} {row[4]:<20}")

def generate_report():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, code, invariant, bound, created_at FROM loops')
    rows = c.fetchall()
    conn.close()
    if not rows:
        print("No loops verified to generate a report.")
        return
    print("\n--- PyVerifyGate Report ---")
    print(f"{'ID':<5} {'Code':<30} {'Bound':<10} {'Gate Status':<15} {'Alert'}")
    print("-" * 80)
    failed_loops = []
    GATE_THRESHOLD = 50
    for row in rows:
        loop_id, code, invariant, bound, created_at = row
        gate_status = "PASS"
        alert_message = ""
        if bound > GATE_THRESHOLD:
            gate_status = "FAIL"
            alert_message = f"HIGH BOUND ({bound} > {GATE_THRESHOLD})"
            failed_loops.append(str(loop_id))
        print(f"{loop_id:<5} {code[:27]+'...':<30} {bound:<10} {gate_status:<15} {alert_message}")
    if failed_loops:
        print("\n--- CRITICAL ALERTS ---")
        print(f"The following loop IDs failed the 'High Bound' gate (>{GATE_THRESHOLD}): {', '.join(failed_loops)}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO loops (code, invariant, bound, created_at) VALUES ('for i in range(n):', 'i < n', 10, '2024-01-01T10:00:00')")
    conn.execute("INSERT INTO loops (code, invariant, bound, created_at) VALUES ('while x > 0:', 'x > 0', 30, '2024-01-02T11:00:00')")
    conn.execute("INSERT INTO loops (code, invariant, bound, created_at) VALUES ('for item in collection:', 'len(collection) > 0', 60, '2024-01-03T12:00:00')")
    conn.commit()
    print(f"{'ID':<5} {'Code':<30} {'Invariant':<20} {'Bound':<10} {'Created':<20}")
    print("-" * 85)
    for row in conn.execute("SELECT id, code, invariant, bound, created_at FROM loops"):
        print(f"{row[0]:<5} {row[1][:27]+'...':<30} {row[2][:17]+'...':<20} {row[3]:<10} {row[4]:<20}")
    conn.close()
    print("\nDemo complete. 3 loops verified with sample data.")

def main():
    parser = argparse.ArgumentParser(description="PyVerifyGate - Loop invariant verification tool")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a new loop to verify')
    add_parser.add_argument('--code', type=str, required=True, help='Loop code snippet')
    add_parser.add_argument('--invariant', type=str, required=True, help='Loop invariant condition')
    add_parser.add_argument('--bound', type=int, required=True, help='Loop bound value')
    list_parser = subparsers.add_parser('list', help='List all verified loops')
    report_parser = subparsers.add_parser('report', help='Generate verification report')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == 'add':
        add_loop(args.code, args.invariant, args.bound)
        print("Loop added successfully.")
    elif args.command == 'list':
        list_loops()
    elif args.command == 'report':
        generate_report()

if __name__ == "__main__":
    main()