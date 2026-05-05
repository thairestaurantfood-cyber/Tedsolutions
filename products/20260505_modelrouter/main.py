import os
import sys
import json
import sqlite3
from pathlib import Path
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/model_router.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            provider TEXT NOT NULL,
            model_id TEXT NOT NULL,
            cost_per_1k_tokens REAL NOT NULL,
            max_tokens INTEGER NOT NULL,
            supports_json BOOLEAN NOT NULL,
            privacy_level INTEGER NOT NULL,
            enabled BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            prompt_tokens INTEGER NOT NULL,
            response_tokens INTEGER NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (model_id) REFERENCES models (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_model(name, provider, model_id, cost, max_tokens, supports_json, privacy_level):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO models (name, provider, model_id, cost_per_1k_tokens, max_tokens, supports_json, privacy_level)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, provider, model_id, cost, max_tokens, int(supports_json), privacy_level))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def list_models():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, provider, model_id, cost_per_1k_tokens, max_tokens, supports_json, privacy_level, enabled FROM models')
    rows = c.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    models = [
        ('llama3', 'ollama', 'llama3', 0.0, 8192, True, 1),
        ('mistral', 'ollama', 'mistral', 0.0, 32768, True, 1),
        ('gemma', 'ollama', 'gemma', 0.0, 8192, True, 1),
        ('mixtral', 'groq', 'mixtral-8x7b-32768', 0.24, 32768, True, 3),
        ('llama3-70b', 'groq', 'llama3-70b-8192', 0.59, 8192, True, 3),
        ('gemini-pro', 'gemini', 'gemini-pro', 0.000125, 32768, True, 3)
    ]

    for model in models:
        add_model(*model)

    rows = list_models()
    print("id | name        | provider | model_id               | cost/1k | max_tokens | json | privacy | enabled")
    print("-" * 120)
    for idx, row in enumerate(rows, 1):
        print(f"{idx} | {row[0]:<12} | {row[1]:<8} | {row[2]:<22} | {row[3]:<7} | {row[4]:<10} | {row[5]} | {row[6]} | {row[7]}")

def main():
    parser = argparse.ArgumentParser(description='Model Router - Route AI models efficiently')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample models')
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    print("Use --demo to see the model router in action")

if __name__ == '__main__':
    main()