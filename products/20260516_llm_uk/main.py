import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/llm_uk.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            response TEXT,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_prompt(prompt: str, response: str, model: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO prompts (prompt, response, model, created_at)
        VALUES (?, ?, ?, ?)
    ''', (prompt, response, model, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def list_prompts(limit: int = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    query = 'SELECT id, prompt, response, model, created_at FROM prompts ORDER BY created_at DESC'
    if limit:
        query += f' LIMIT {limit}'
    c.execute(query)
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No prompts found")
        return

    max_id = max(len(str(row[0])) for row in rows)
    max_prompt = max(len(row[1]) for row in rows)
    max_response = max(len(row[2]) for row in rows)
    max_model = max(len(row[3]) for row in rows)

    print(f"{'ID':<{max_id}} | {'Prompt':<{max_prompt}} | {'Response':<{max_response}} | {'Model':<{max_model}} | {'Created At'}")
    print('-' * (max_id + max_prompt + max_response + max_model + 30))
    for row in rows:
        print(f"{row[0]:<{max_id}} | {row[1][:max_prompt]:<{max_prompt}} | {row[2][:max_response]:<{max_response}} | {row[3]:<{max_model}} | {row[4]}")

def generate_report(output_format: str = 'text'):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('SELECT model, COUNT(*) as count, MIN(created_at) as earliest, MAX(created_at) as latest FROM prompts GROUP BY model')
    report_data = c.fetchall()
    conn.close()

    if not report_data:
        print("No data available for report")
        return

    if output_format == 'json':
        report = {
            'total_prompts': sum(row[1] for row in report_data),
            'models': [{
                'model': row[0],
                'count': row[1],
                'earliest': row[2],
                'latest': row[3]
            } for row in report_data]
        }
        print(json.dumps(report, indent=2))
    else:
        print("\nLLM UK Usage Report")
        print("=" * 50)
        print(f"{'Model':<15} {'Count':<10} {'Earliest':<20} {'Latest':<20}")
        print("-" * 50)
        for row in report_data:
            print(f"{row[0]:<15} {row[1]:<10} {row[2]:<20} {row[3]:<20}")

def check_alerts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM prompts WHERE created_at < datetime("now", "-7 days")')
    old_count = c.fetchone()[0]
    conn.close()

    if old_count > 0:
        print(f"ALERT: {old_count} prompts older than 7 days")
    else:
        print("No alerts")

def demo():
    DB = os.path.expanduser("~/.jarvis/llm_uk.db")
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    if os.path.exists(DB):
        os.remove(DB)

    conn = sqlite3.connect(DB)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            response TEXT,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    sample_data = [
        ("Explain quantum computing", "Quantum computing uses quantum bits...", "llama3"),
        ("Write a Python function to sort a list", "def sort_list(lst): return sorted(lst)", "mistral"),
        ("What is the capital of France?", "The capital of France is Paris.", "gemma")
    ]

    for prompt, response, model in sample_data:
        conn.execute('''
            INSERT INTO prompts (prompt, response, model, created_at)
            VALUES (?, ?, ?, ?)
        ''', (prompt, response, model, "2024-01-01T12:00:00"))

    conn.commit()

    print("\nLLM UK Demo Results")
    print("=" * 80)
    c = conn.cursor()
    c.execute('SELECT id, prompt, response, model, created_at FROM prompts ORDER BY id')
    rows = c.fetchall()

    max_id = max(len(str(row[0])) for row in rows)
    max_prompt = max(len(row[1]) for row in rows)
    max_response = max(len(row[2]) for row in rows)
    max_model = max(len(row[3]) for row in rows)

    print(f"{'ID':<{max_id}} | {'Prompt':<{max_prompt}} | {'Response':<{max_response}} | {'Model':<{max_model}} | {'Created At'}")
    print('-' * (max_id + max_prompt + max_response + max_model + 30))
    for row in rows:
        print(f"{row[0]:<{max_id}} | {row[1][:max_prompt]:<{max_prompt}} | {row[2][:max_response]:<{max_response}} | {row[3]:<{max_model}} | {row[4]}")

    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="LLM UK - Track LLM prompts and responses")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.set_defaults(func=init_db)

    add_parser = subparsers.add_parser('add', help='Add a new prompt and response')
    add_parser.add_argument('prompt', help='Prompt text')
    add_parser.add_argument('response', help='Response text')
    add_parser.add_argument('--model', default='unknown', help='Model name')
    add_parser.set_defaults(func=lambda args: add_prompt(args.prompt, args.response, args.model))

    list_parser = subparsers.add_parser('list', help='List prompts')
    list_parser.add_argument('--limit', type=int, help='Limit number of results')
    list_parser.set_defaults(func=lambda args: list_prompts(args.limit))

    report_parser = subparsers.add_parser('report', help='Generate usage report')
    report_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    report_parser.set_defaults(func=lambda args: generate_report('json' if args.json else 'text'))

    alerts_parser = subparsers.add_parser('alerts', help='Check for alerts')
    alerts_parser.set_defaults(func=check_alerts)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == '__main__':
    main()