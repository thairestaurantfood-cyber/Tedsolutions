import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/model_router.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            model TEXT NOT NULL,
            tokens INTEGER NOT NULL,
            cost REAL NOT NULL,
            duration_ms INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS models (
            name TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            cost_per_token REAL NOT NULL,
            max_tokens INTEGER NOT NULL,
            is_local BOOLEAN NOT NULL
        )
    """)
    # Seed models
    models = [
        ('llama3', 'ollama', 0.00, 8192, True),
        ('mistral', 'ollama', 0.00, 32768, True),
        ('gemma', 'ollama', 0.00, 8192, True),
        ('llama3-groq-70b-8192-tool-use-preview', 'groq', 0.0000008, 8192, False),
        ('llama3-70b-8192', 'groq', 0.0000008, 8192, False),
        ('mistralai-7b-instruct-v0.3', 'groq', 0.0000001, 8192, False),
        ('mistral-large-latest', 'mistral', 0.000003, 32768, False)
    ]
    cur.executemany("INSERT OR IGNORE INTO models VALUES (?,?,?,?,?)", models)
    conn.commit()
    conn.close()

def get_models():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, provider, cost_per_token, max_tokens, is_local FROM models")
    models = cur.fetchall()
    conn.close()
    return models

def calculate_cost(model_name, tokens):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT cost_per_token FROM models WHERE name=?", (model_name,))
    cost_per_token = cur.fetchone()[0]
    conn.close()
    return tokens * cost_per_token

def log_usage(prompt, model_name, tokens, duration_ms):
    cost = calculate_cost(model_name, tokens)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usage (prompt, model, tokens, cost, duration_ms)
        VALUES (?,?,?,?,?)
    """, (prompt, model_name, tokens, cost, duration_ms))
    conn.commit()
    conn.close()

def route_prompt(prompt, max_tokens=2048):
    models = get_models()
    local_models = [m for m in models if m[4]]
    cloud_models = [m for m in models if not m[4]]

    # Simple routing: short prompts to local, long to cloud
    if len(prompt.split()) <= 50 and len(prompt) <= 2000:
        return local_models[0][0]  # Default to first local model
    else:
        return cloud_models[0][0]  # Default to first cloud model

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Insert sample usage data
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usage (prompt, model, tokens, cost, duration_ms)
        VALUES (?,?,?,?,?)
    """, ("Demo prompt", "llama3", 100, 0.0, 500))
    conn.commit()
    conn.close()

def main():
    if '--demo' in sys.argv:
        demo()
        return

    parser = argparse.ArgumentParser(description='Model Router CLI')
    subparsers = parser.add_subparsers(dest='command')

    route_parser = subparsers.add_parser('route', help='Route a prompt to best model')
    route_parser.add_argument('prompt', type=str, help='Prompt to route')
    route_parser.add_argument('--max-tokens', type=int, default=2048, help='Max tokens for response')

    args = parser.parse_args()

    if args.command == 'route':
        model = route_prompt(args.prompt, args.max_tokens)
        print(f"Route to: {model}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()