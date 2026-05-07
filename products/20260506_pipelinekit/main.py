import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/pipelinekit.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workflows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        config TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_workflow(name: str, config: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO workflows (name, config, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (name, json.dumps(config), datetime.now().isoformat(), datetime.now().isoformat())
        )
        conn.commit()
        print(f"Added workflow: {name}")
    except sqlite3.IntegrityError:
        print(f"Error: Workflow '{name}' already exists")
    finally:
        conn.close()

def list_workflows():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, created_at FROM workflows ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No workflows found")
        return

    print("\nWorkflows:")
    print("NAME".ljust(30) + "CREATED AT")
    print("-" * 50)
    for name, created in rows:
        print(f"{name.ljust(30)}{created}")

def demo():
    init_db()
    add_workflow("video-convert", {
        "steps": [
            {"cmd": "ffmpeg -i input.mp4 output.mp4", "timeout": 300}
        ]
    })
    add_workflow("image-resize", {
        "steps": [
            {"cmd": "convert input.jpg -resize 800x600 output.jpg", "timeout": 60}
        ]
    })
    list_workflows()

def main():
    parser = argparse.ArgumentParser(description="PipelineKit - Workflow automation tool")
    subparsers = parser.add_subparsers(dest='command', required=False)

    parser.add_argument('--demo', action='store_true', help='Run demo workflows')

    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if not args.command:
        parser.print_help()
        return

    init_db()

    if args.command == 'add':
        parser_add = subparsers.add_parser('add')
        parser_add.add_argument('name', type=str)
        parser_add.add_argument('config', type=str)
        args = parser.parse_args()
        add_workflow(args.name, json.loads(args.config))
    elif args.command == 'list':
        list_workflows()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()