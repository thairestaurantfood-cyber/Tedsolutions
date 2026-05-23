import os
import sys
import json
import sqlite3
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import re

DB_PATH = os.path.expanduser('~/.jarvis/agentbridge.db')

def ensure_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    schema TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
    conn.commit()
    return conn

def parse_cli_help(cmd_path):
    """Parses --help output to extract command name, description, and raw help text."""
    try:
        result = subprocess.run([cmd_path, '--help'], capture_output=True, text=True, check=True)
        return {
            'name': cmd_path.split('/')[-1],
            'description': result.stdout.split('\n')[0] if result.stdout else 'No description',
            'raw_help': result.stdout
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            'name': cmd_path.split('/')[-1],
            'description': 'Could not fetch help',
            'raw_help': ''
        }

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    schema TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
    conn.execute("INSERT INTO tools (name, description, schema, path) VALUES (?, ?, ?, ?)",
                 ('ls', 'List directory contents', json.dumps({'type': 'object'}), '/bin/ls'))
    conn.execute("INSERT INTO tools (name, description, schema, path) VALUES (?, ?, ?, ?)",
                 ('grep', 'Search text patterns', json.dumps({'type': 'object'}), '/bin/grep'))
    conn.execute("INSERT INTO tools (name, description, schema, path) VALUES (?, ?, ?, ?)",
                 ('curl', 'Transfer data with URLs', json.dumps({'type': 'object'}), '/usr/bin/curl'))
    conn.commit()
    print(f"{'Name':<15} {'Description':<50} {'Path'}")
    print("-" * 80)
    for row in conn.execute("SELECT name, description, path FROM tools ORDER BY name"):
        print(f"{row[0]:<15} {row[1]:<50} {row[2]}")
    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description='AgentBridge — Wrap CLI tools as MCP endpoints')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample tools')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    wrap_parser = subparsers.add_parser('wrap', help='Wrap a CLI tool')
    wrap_parser.add_argument('--tool', required=True, help='Path to CLI tool to wrap')

    serve_parser = subparsers.add_parser('serve', help='Start HTTP server')
    serve_parser.add_argument('--port', type=int, default=8000, help='Port for HTTP server')
    serve_parser.add_argument('--stdio', action='store_true', help='Use stdio for MCP')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'wrap':
        print(f"Wrapping {args.tool}...")
        conn = ensure_db()
        tool_info = parse_cli_help(args.tool)
        conn.execute(
            "INSERT OR REPLACE INTO tools (name, description, schema, path) VALUES (?, ?, ?, ?)",
            (tool_info['name'], tool_info['description'], json.dumps({'type': 'object'}), args.tool)
        )
        conn.commit()
        print(f"✓ Wrapped {tool_info['name']}")
        print(f"  Description: {tool_info['description']}")
    elif args.command == 'serve':
        print(f"Starting AgentBridge HTTP server on port {args.port}")
        if args.stdio:
            print("MCP stdio mode ready (for Claude Desktop)")
            print('{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05", "capabilities": {}}}')
        else:
            print("HTTP server mode not yet implemented")

if __name__ == "__main__":
    main()