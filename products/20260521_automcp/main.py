import os
import sys
import argparse
import sqlite3
import json
import csv
from datetime import datetime, timedelta
import time

DB_DIR = os.path.expanduser("~/.jarvis")
DB_PATH = os.path.join(DB_DIR, 'servers.db')

def _get_db_connection():
    """Establishes a connection to the SQLite database."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if it doesn't exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = _get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    ip_address TEXT NOT NULL,
    status TEXT NOT NULL,
    last_checked TEXT NOT NULL,
    notes TEXT
    );
    ''')
    conn.commit()
    conn.close()

def add_server(name, ip_address, status="unknown", notes=""):
    """Adds a new server to the database."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    try:
        last_checked = datetime.now().isoformat()
        cursor.execute(
        "INSERT INTO servers (name, ip_address, status, last_checked, notes) VALUES (?, ?, ?, ?, ?)",
        (name, ip_address, status, last_checked, notes)
        )
        conn.commit()
        print(f"Server '{name}' added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: Server with name '{name}' already exists.")
    finally:
        conn.close()

def update_server_status(name, status):
    """Updates the status and last_checked timestamp for a server."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    last_checked = datetime.now().isoformat()
    cursor.execute(
    "UPDATE servers SET status = ?, last_checked = ? WHERE name = ?",
    (status, last_checked, name)
    )
    if cursor.rowcount == 0:
        print(f"Error: Server '{name}' not found.")
    else:
        conn.commit()
        print(f"Server '{name}' status updated to '{status}'.")
    conn.close()

def list_servers(status_filter=None):
    """Lists servers, optionally filtered by status."""
    conn = _get_db_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("SELECT * FROM servers WHERE status = ? ORDER BY name", (status_filter,))
    else:
        cursor.execute("SELECT * FROM servers ORDER BY name")
    servers = cursor.fetchall()
    conn.close()
    if not servers:
        print("No servers found.")
        return
    print(f"{'ID':<4} {'Name':<20} {'IP':<15} {'Status':<12} {'Last Checked':<20} {'Notes'}")
    print("-" * 90)
    for server in servers:
        print(f"{server['id']:<4} {server['name']:<20} {server['ip_address']:<15} {server['status']:<12} {server['last_checked']:<20} {server['notes']}")

def demo():
    """Offline demo that creates sample data and shows functionality."""
    init_db()
    add_server("web-server-1", "192.168.1.10", "online", "Main web server")
    add_server("db-server-1", "192.168.1.20", "online", "Primary database")
    add_server("backup-server", "192.168.1.30", "offline", "Backup storage")
    update_server_status("web-server-1", "maintenance")
    print("\nCurrent servers:")
    list_servers()
    print("\nOnline servers:")
    list_servers("online")

def main():\n    """Main entry point with proper argument parsing.\n""\n    parser = argparse.ArgumentParser(description=\"AutoMCP - Self-hosted MCP server orchestrator\")\n    parser.add_argument(\"--demo\", action=\"store_true\", help=\"Run demo mode\")\n    # CRITICAL: Check --demo FIRST using parse_known_args\n    pre, _ = parser.parse_known_args()\n    if pre.demo:\n        demo()\n        return\n    # If not demo, proceed with subparsers\n    subparsers = parser.add_subparsers(dest=\"command\", help=\"Available commands\")\n    \n    # init command\n    init_parser = subparsers.add_parser(\"init\", help=\"Initialize database\")\n    init_parser.set_defaults(func=init_db)\n    \n    # add command\n    add_parser = subparsers.add_parser(\"add\", help=\"Add a new server\")\n    add_parser.add_argument(\"--name\", required=True, help=\"Server name\")\n    add_parser.add_argument(\"--ip\", required=True, help=\"IP address\")\n    add_parser.add_argument(\"--status\", default=\"unknown\", help=\"Server status\")\n    add_parser.add_argument(\"--notes\", default=\"\", help=\"Additional notes\")\n    add_parser.set_defaults(func=lambda args: add_server(args.name, args.ip, args.status, args.notes))\n    \n    # update command\n    update_parser = subparsers.add_parser(\"update\", help=\"Update server status\")\n    update_parser.add_argument(\"--name\", required=True, help=\"Server name\")\n    update_parser.add_argument(\"--status\", required=True, help=\"New status\")\n    update_parser.set_defaults(func=lambda args: update_server_status(args.name, args.status))\n    \n    # list command\n    list_parser = subparsers.add_parser(\"list\", help=\"List servers\")\n    list_parser.add_argument(\"--status\", help=\"Filter by status\")\n    list_parser.set_defaults(func=lambda args: list_servers(args.status))\n    \n    # Parse arguments\n    args = parser.parse_args()\n    if hasattr(args, \"func\"):\n        args.func(args)\n    else:\n        parser.print_help()\n    \nif __name__ == \"__main__\":\n    main()\nif __name__ == "__main__":
    main()