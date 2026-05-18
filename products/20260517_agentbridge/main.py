import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.jarvis/agentbridge/mcp_tools.db')

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            description TEXT,
            schema_json TEXT,
            env_vars TEXT,
            working_dir TEXT,
            timeout INTEGER,
            created_at TEXT
        )
    ''')

    tools = [
        {
            "name": "tree",
            "description": "List directory contents recursively using tree command",
            "schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path to scan"},
                    "max_depth": {"type": "integer", "description": "Maximum depth to scan"}
                },
                "required": ["path"]
            },
            "env_vars": {},
            "working_dir": "/tmp",
            "timeout": 30
        },
        {
            "name": "fd",
            "description": "Fast file finder with pattern matching",
            "schema": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Search pattern"},
                    "path": {"type": "string", "description": "Directory to search"},
                    "case_sensitive": {"type": "boolean", "description": "Case sensitive search"}
                },
                "required": ["pattern"]
            },
            "env_vars": {},
            "working_dir": "/home/user",
            "timeout": 10
        },
        {
            "name": "wc",
            "description": "Word count and line statistics",
            "schema": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "File path to analyze"},
                    "lines": {"type": "boolean", "description": "Count lines"},
                    "words": {"type": "boolean", "description": "Count words"},
                    "chars": {"type": "boolean", "description": "Count characters"}
                },
                "required": ["file"]
            },
            "env_vars": {},
            "working_dir": "/tmp",
            "timeout": 5
        }
    ]

    now = datetime.now().isoformat()
    for tool in tools:
        cursor.execute('''
            INSERT INTO tools
            (name, description, schema_json, env_vars, working_dir, timeout, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            tool["name"],
            tool["description"],
            json.dumps(tool["schema"]),
            json.dumps(tool["env_vars"]),
            tool["working_dir"],
            tool["timeout"],
            now
        ))

    conn.commit()

    print(f"{'ID':<5} {'Name':<15} {'Description':<40} {'Timeout':<8} {'Created'}")
    print("-" * 100)
    for row in cursor.execute("SELECT id, name, description, timeout, created_at FROM tools"):
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<40} {row[3]:<8} {row[4]}")

    conn.close()
    print("\nDemo complete. 3 tools registered in MCP tool registry.")

def main():
    parser = argparse.ArgumentParser(description="AgentBridge - MCP Tool Registry CLI")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample tools')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    register_parser = subparsers.add_parser('register', help='Register a new MCP tool')
    register_parser.add_argument('--name', required=True, help='Tool name')
    register_parser.add_argument('--description', required=True, help='Tool description')
    register_parser.add_argument('--schema', required=True, help='JSON schema for tool')
    register_parser.add_argument('--env-vars', default='{}', help='Environment variables JSON')
    register_parser.add_argument('--working-dir', default='/tmp', help='Working directory')
    register_parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')

    list_parser = subparsers.add_parser('list', help='List registered tools')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'register':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                description TEXT,
                schema_json TEXT,
                env_vars TEXT,
                working_dir TEXT,
                timeout INTEGER,
                created_at TEXT
            )
        ''')

        now = datetime.now().isoformat()
        try:
            cursor.execute('''
                INSERT INTO tools
                (name, description, schema_json, env_vars, working_dir, timeout, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                args.name,
                args.description,
                args.schema,
                args.env_vars,
                args.working_dir,
                args.timeout,
                now
            ))
            conn.commit()
            print(f"Tool '{args.name}' registered successfully")
        except sqlite3.IntegrityError:
            print(f"Error: Tool '{args.name}' already exists")
        conn.close()

    elif args.command == 'list':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, description, timeout, created_at FROM tools")
        tools = cursor.fetchall()
        conn.close()

        if not tools:
            print("No tools registered")
            return

        print(f"{'ID':<5} {'Name':<15} {'Description':<40} {'Timeout':<8} {'Created'}")
        print("-" * 100)
        for tool in tools:
            print(f"{tool[0]:<5} {tool[1]:<15} {tool[2]:<40} {tool[3]:<8} {tool[4]}")

if __name__ == '__main__':
    main()