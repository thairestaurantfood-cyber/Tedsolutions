import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
import argparse

DB_PATH = os.path.expanduser('~/.jarvis/events.db')
STATE_FILE = os.path.expanduser('~/jarvis/memory/system_state.json')

def get_default_state():
    return {
        "last_updated": None,
        "phases": {
            "plan_written": False,
            "build_started": False,
            "build_passed": False,
            "codex_fixed": False,
            "published": False
        },
        "build_history": []
    }

def read_state():
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return get_default_state()

def write_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def update_state(phase, value=True):
    state = read_state()
    state['phases'][phase] = value
    state['last_updated'] = datetime.now().isoformat()
    state['build_history'].append({
        "timestamp": state['last_updated'],
        "phase": phase,
        "value": value
    })
    write_state(state)

def get_state():
    state = read_state()
    print(f"{'Phase':<20} | {'Value':<10}")
    print("-" * 32)
    for phase, value in state['phases'].items():
        print(f"{phase:<20} | {str(value):<10}")
    print(f"\nLast updated: {state['last_updated']}")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        phase TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT
    )
    """)
    conn.commit()
    conn.close()

def log_event(phase, status, details=""):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO events (timestamp, phase, status, details) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), phase, status, details)
    )
    conn.commit()
    conn.close()

def get_events():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute("SELECT timestamp, phase, status, details FROM events ORDER BY timestamp DESC")
    print(f"{'Timestamp':<30} | {'Phase':<20} | {'Status':<10} | {'Details'}")
    print("-" * 90)
    for row in cursor.fetchall():
        print(f"{row[0]:<30} | {row[1]:<20} | {row[2]:<10} | {row[3]}")
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)

    init_db()
    update_state("plan_written", True)
    update_state("build_started", True)
    update_state("build_passed", True)
    update_state("codex_fixed", True)

    log_event("plan_written", "success", "Initial plan created")
    log_event("build_started", "success", "Build process initiated")
    log_event("build_passed", "success", "All tests passed")
    log_event("codex_fixed", "success", "Code issues resolved")

    print("System State Demo:")
    get_state()

    print("\nEvent Log Demo:")
    get_events()

    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="SystemState - Track build phases and system state")
    parser.add_argument('--demo', action='store_true', help='Run demo with hardcoded data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    state_parser = subparsers.add_parser('state', help='Show current system state')
    state_parser.set_defaults(func=get_state)

    events_parser = subparsers.add_parser('events', help='Show event log')
    events_parser.set_defaults(func=get_events)

    update_parser = subparsers.add_parser('update', help='Update a phase state')
    update_parser.add_argument('phase', help='Phase to update')
    update_parser.add_argument('--value', type=str, default='True', help='Value to set (default: True)')
    update_parser.set_defaults(func=lambda args: update_state(args.phase, args.value == 'True'))

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func()

if __name__ == "__main__":
    main()