import os
import sqlite3
import argparse
import json
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/agentgit.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            output_path TEXT NOT NULL,
            snapshot_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            metadata TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            field TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_at TEXT NOT NULL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_snapshot(agent_name, output_path, snapshot_hash, metadata=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute('''
        INSERT INTO snapshots (agent_name, output_path, snapshot_hash, created_at, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (agent_name, output_path, snapshot_hash, created_at, json.dumps(metadata) if metadata else None))
    conn.commit()
    snapshot_id = c.lastrowid
    conn.close()
    return snapshot_id

def list_snapshots(agent_name=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if agent_name:
        c.execute('SELECT * FROM snapshots WHERE agent_name = ? ORDER BY created_at DESC', (agent_name,))
    else:
        c.execute('SELECT * FROM snapshots ORDER BY created_at DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def add_change(snapshot_id, field, old_value, new_value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    changed_at = datetime.now().isoformat()
    c.execute('''
        INSERT INTO changes (snapshot_id, field, old_value, new_value, changed_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (snapshot_id, field, old_value, new_value, changed_at))
    conn.commit()
    conn.close()

def generate_diff_report(snapshot_id1, snapshot_id2):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id1,))
    snap1 = c.fetchone()
    c.execute('SELECT * FROM snapshots WHERE id = ?', (snapshot_id2,))
    snap2 = c.fetchone()

    if not snap1 or not snap2:
        print("Invalid snapshot IDs")
        return

    c.execute('''
        SELECT field, old_value, new_value
        FROM changes
        WHERE snapshot_id = ?
    ''', (snapshot_id1,))
    changes1 = c.fetchall()

    c.execute('''
        SELECT field, old_value, new_value
        FROM changes
        WHERE snapshot_id = ?
    ''', (snapshot_id2,))
    changes2 = c.fetchall()

    print(f"\nDiff Report: {snap1[1]} vs {snap2[1]}")
    print("="*80)
    print(f"Snapshot 1: {snap1[2]} (ID: {snap1[0]})")
    print(f"Snapshot 2: {snap2[2]} (ID: {snap2[0]})")
    print("\nChanges in Snapshot 1:")
    for field, old, new in changes1:
        print(f"  {field}: {old} -> {new}")

    print("\nChanges in Snapshot 2:")
    for field, old, new in changes2:
        print(f"  {field}: {old} -> {new}")
    print("="*80)

    conn.close()

def check_alerts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        SELECT s.id, s.agent_name, s.output_path, c.field, c.new_value
        FROM snapshots s
        JOIN changes c ON s.id = c.snapshot_id
        WHERE c.new_value LIKE '%ERROR%' OR c.new_value LIKE '%FAILED%'
        ORDER BY c.changed_at DESC
    ''')
    alerts = c.fetchall()

    if alerts:
        print("\nALERTS:")
        print("-"*80)
        for alert in alerts:
            print(f"Agent: {alert[1]}, Path: {alert[2]}, Field: {alert[3]}, Value: {alert[4]}")
        print("-"*80)
    else:
        print("\nNo alerts found")

    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Insert hardcoded demo data
    snap1 = add_snapshot(
        agent_name="code-generator",
        output_path="/tmp/code_v1.py",
        snapshot_hash="abc123",
        metadata={"version": "1.0", "lines": 42}
    )
    snap2 = add_snapshot(
        agent_name="code-generator",
        output_path="/tmp/code_v2.py",
        snapshot_hash="def456",
        metadata={"version": "2.0", "lines": 56}
    )
    snap3 = add_snapshot(
        agent_name="report-builder",
        output_path="/tmp/report.pdf",
        snapshot_hash="ghi789",
        metadata={"pages": 12}
    )

    # Add some changes
    add_change(snap1, "metadata", '{"version": "1.0", "lines": 42}', '{"version": "1.1", "lines": 45}')
    add_change(snap2, "output_path", "/tmp/code_v2.py", "/tmp/code_v3.py")
    add_change(snap3, "metadata", '{"pages": 12}', '{"pages": 15, "errors": 0}')

    # Query and print formatted table
    snapshots = list_snapshots()
    print("id | agent_name       | output_path       | snapshot_hash | created_at")
    print("-" * 70)
    for row in snapshots:
        print(f"{row[0]} | {row[1]:<16} | {row[2]:<17} | {row[3]:<13} | {row[4]}")

    # Generate diff report
    generate_diff_report(snap1, snap2)

    # Check alerts
    check_alerts()

    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="AgentGit - Track agent outputs and changes")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    # list command
    list_parser = subparsers.add_parser('list', help='List snapshots')
    list_parser.add_argument('--agent', help='Filter by agent name')

    # diff command
    diff_parser = subparsers.add_parser('diff', help='Generate diff report')
    diff_parser.add_argument('id1', type=int, help='First snapshot ID')
    diff_parser.add_argument('id2', type=int, help='Second snapshot ID')

    # alerts command
    subparsers.add_parser('alerts', help='Check for alerts')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        snapshots = list_snapshots(args.agent)
        print("id | agent_name       | output_path       | snapshot_hash | created_at")
        print("-" * 70)
        for row in snapshots:
            print(f"{row[0]} | {row[1]:<16} | {row[2]:<17} | {row[3]:<13} | {row[4]}")

    elif args.command == 'diff':
        generate_diff_report(args.id1, args.id2)

    elif args.command == 'alerts':
        check_alerts()