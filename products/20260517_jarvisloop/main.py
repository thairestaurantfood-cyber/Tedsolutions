import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/jarvis/memory/token_tamer.db')
MCP_REGISTRY_PATH = os.path.expanduser('~/.jarvis/mcp/registry.json')

def print_table(title, columns, rows):
    print(f"\n{title}")
    text_rows = [[("" if value is None else str(value)) for value in row] for row in rows]
    widths = [len(column) for column in columns]
    for row in text_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], min(len(value), 32))
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(line)
    print("| " + " | ".join(column.ljust(widths[index]) for index, column in enumerate(columns)) + " |")
    print(line)
    for row in text_rows:
        clipped = [value if len(value) <= 32 else value[:29] + "..." for value in row]
        print("| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(clipped)) + " |")
    print(line)

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE api_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        latency_ms INTEGER NOT NULL,
        status TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL
    )
    ''')

    demo_data = [
        (datetime.now().isoformat(), "llama3", 45, 120, 165, 245, "success",
         "Analyze this invoice: {invoice_data}", "Invoice processed successfully"),
        (datetime.now().isoformat(), "gemma", 32, 89, 121, 187, "success",
         "Summarize this contract: {contract_text}", "Contract summary generated"),
        (datetime.now().isoformat(), "mixtral", 78, 210, 288, 456, "failure",
         "Translate this document: {document_text}", "Translation limit exceeded")
    ]

    cursor.executemany('''
    INSERT INTO api_calls
    (timestamp, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, status, prompt, response)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_data)

    conn.commit()

    cursor.execute('''
    SELECT id, model, prompt_tokens, completion_tokens, total_tokens, latency_ms, status, prompt, response
    FROM api_calls ORDER BY id
    ''')
    rows = cursor.fetchall()
    conn.close()

    print_table(
        "TokenTamer API Call Logs",
        ["id", "model", "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms", "status", "prompt", "response"],
        rows,
    )
    print(f"Total calls logged: {len(rows)}")

def setup_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS api_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        model TEXT NOT NULL,
        prompt_tokens INTEGER NOT NULL,
        completion_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        latency_ms INTEGER NOT NULL,
        status TEXT NOT NULL,
        prompt TEXT NOT NULL,
        response TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def register_mcp_server(name, description, command, args=None):
    if args is None:
        args = []

    registry = []
    if os.path.exists(MCP_REGISTRY_PATH):
        with open(MCP_REGISTRY_PATH, 'r') as f:
            registry = json.load(f)

    server = {
        "name": name,
        "description": description,
        "command": command,
        "args": args,
        "registered_at": datetime.now().isoformat(),
        "version": "0.1.0"
    }

    registry.append(server)
    os.makedirs(os.path.dirname(MCP_REGISTRY_PATH), exist_ok=True)
    with open(MCP_REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=2)

    return server

def list_mcp_servers():
    if not os.path.exists(MCP_REGISTRY_PATH):
        print("No MCP servers registered yet.")
        return []

    with open(MCP_REGISTRY_PATH, 'r') as f:
        registry = json.load(f)

    return registry

def check_server_health(server):
    try:
        result = subprocess.run(
            [server['command']] + server['args'] + ["--health"],
            capture_output=True,
            text=True,
            timeout=5
        )
        status = "healthy" if result.returncode == 0 else "unhealthy"
        return {
            "status": status,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except Exception as e:
        return {
            "status": "error",
            "output": "",
            "error": str(e)
        }

def mcp_list():
    servers = list_mcp_servers()
    if not servers:
        print("No MCP servers registered.")
        return

    health_checks = []
    for server in servers:
        health = check_server_health(server)
        health_checks.append({
            "name": server['name'],
            "description": server['description'],
            "version": server.get('version', 'unknown'),
            "status": health['status'],
            "registered_at": server['registered_at']
        })

    print_table(
        "Registered MCP Servers",
        ["name", "description", "version", "status", "registered_at"],
        [(s['name'], s['description'], s['version'], s['status'], s['registered_at']) for s in health_checks]
    )

def mcp_register():
    name = input("Server name: ").strip()
    description = input("Description: ").strip()
    command = input("Command to run (e.g., python): ").strip()
    args = input("Arguments (space-separated, optional): ").strip().split()

    server = register_mcp_server(name, description, command, args)
    print(f"Registered MCP server: {server['name']}")

def main():
    parser = argparse.ArgumentParser(description="TokenTamer - API Call Logger and MCP Server Bridge")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    list_parser = subparsers.add_parser('mcp-list', help='List registered MCP servers')
    register_parser = subparsers.add_parser('mcp-register', help='Register a new MCP server')
    setup_parser = subparsers.add_parser('setup', help='Setup database')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'mcp-list':
        mcp_list()
    elif args.command == 'mcp-register':
        mcp_register()
    elif args.command == 'setup':
        setup_database()
        print("Database setup complete.")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()