import os
import sys
import sqlite3
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser("~/.jarvis/promptvault.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            version INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            tags TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_prompt(content: str, version: int = 1, tags: str = ''):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO prompts (content, version, created_at, tags) VALUES (?, ?, ?, ?)',
        (content, version, datetime.now().isoformat(), tags)
    )
    conn.commit()
    conn.close()

def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT id, content, version, created_at, tags FROM prompts ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_prompt(prompt_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('SELECT id, content, version, created_at, tags FROM prompts WHERE id = ?', (prompt_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def diff_prompts(prompt_id1: int, prompt_id2: int):
    p1 = get_prompt(prompt_id1)
    p2 = get_prompt(prompt_id2)
    if not p1 or not p2:
        return None

    diff = []
    diff.append(f"Diff between prompt {prompt_id1} and {prompt_id2}:")
    diff.append("-" * 80)
    diff.append(f"ID {prompt_id1}:")
    diff.append(f"  Content: {p1[1]}")
    diff.append(f"  Version: {p1[2]}")
    diff.append(f"  Tags: {p1[4]}")
    diff.append("-" * 80)
    diff.append(f"ID {prompt_id2}:")
    diff.append(f"  Content: {p2[1]}")
    diff.append(f"  Version: {p2[2]}")
    diff.append(f"  Tags: {p2[4]}")
    return "\n".join(diff)

def search_prompts(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('''
        SELECT id, content, version, created_at, tags
        FROM prompts
        WHERE content LIKE ? OR tags LIKE ?
        ORDER BY created_at DESC
    ''', (f'%{query}%', f'%{query}%'))
    rows = cursor.fetchall()
    conn.close()
    return rows

def improve_prompt(prompt_id: int):
    p = get_prompt(prompt_id)
    if not p:
        return None
    return f"Improved version of prompt {prompt_id}:\n{p[1]}"

def demo():
    print("=== PromptVault Demo ===")
    print("1. Initializing database...")
    init_db()

    print("\n2. Saving test prompts...")
    save_prompt("Write a Python function to calculate Fibonacci sequence", tags="python,algorithm")
    save_prompt("Create a React component for a weather app", tags="react,frontend")
    save_prompt("Explain quantum computing in simple terms", tags="education,science")

    print("\n3. Listing all prompts...")
    prompts = list_prompts()
    for p in prompts:
        print(f"ID {p[0]}: {p[1][:50]}... (v{p[2]})")

    print("\n4. Getting specific prompt...")
    prompt = get_prompt(1)
    print(f"Prompt 1: {prompt[1]}")

    print("\n5. Searching prompts...")
    results = search_prompts("python")
    print(f"Found {len(results)} results for 'python'")

    print("\n6. Comparing prompts...")
    diff = diff_prompts(1, 2)
    print(diff)

    print("\n7. Improving a prompt...")
    improved = improve_prompt(3)
    print(improved)

    print("\nDemo completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='PromptVault - Local prompt management')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    
    subparsers = parser.add_subparsers(dest='command')
    
    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.set_defaults(func=lambda args: init_db())

    save_parser = subparsers.add_parser('save', help='Save a new prompt')
    save_parser.add_argument('content', type=str, help='Prompt content')
    save_parser.add_argument('--version', type=int, default=1, help='Version number')
    save_parser.add_argument('--tags', type=str, default='', help='Comma-separated tags')
    save_parser.set_defaults(func=lambda args: save_prompt(args.content, args.version, args.tags))

    list_parser = subparsers.add_parser('list', help='List all prompts')
    list_parser.set_defaults(func=lambda args: [print(f"ID {p[0]}: {p[1][:50]}... (v{p[2]}, {p[4]})") for p in list_prompts()])

    get_parser = subparsers.add_parser('get', help='Get a specific prompt')
    get_parser.add_argument('id', type=int, help='Prompt ID')
    get_parser.set_defaults(func=lambda args: print(get_prompt(args.id)[1] if get_prompt(args.id) else "Not found"))

    diff_parser = subparsers.add_parser('diff', help='Compare two prompts')
    diff_parser.add_argument('id1', type=int, help='First prompt ID')
    diff_parser.add_argument('id2', type=int, help='Second prompt ID')
    diff_parser.set_defaults(func=lambda args: print(diff_prompts(args.id1, args.id2) or "Error: One or both prompts not found"))

    search_parser = subparsers.add_parser('search', help='Search prompts')
    search_parser.add_argument('query', type=str, help='Search term')
    search_parser.set_defaults(func=lambda args: [print(f"ID {p[0]}: {p[1][:50]}... (v{p[2]}, {p[4]})") for p in search_prompts(args.query)])

    improve_parser = subparsers.add_parser('improve', help='Improve a prompt')
    improve_parser.add_argument('id', type=int, help='Prompt ID')
    improve_parser.set_defaults(func=lambda args: print(improve_prompt(args.id) or "Error: Prompt not found"))

    args = parser.parse_args()
    
    if args.demo:
        demo()
        return
        
    if not hasattr(args, 'func'):
        parser.print_help()
        sys.exit(1)

    args.func(args)

if __name__ == "__main__":
    main()