import os
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import sys

DB_PATH = os.path.expanduser('~/.modelrouter.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL,
    cost REAL NOT NULL,
    speed REAL NOT NULL,
    privacy INTEGER NOT NULL,
    created_at TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

    def add_model(name, provider, cost, speed, privacy):
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
        INSERT INTO models (name, provider, cost, speed, privacy, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, provider, cost, speed, privacy, datetime.now().isoformat()))
        conn.commit()
        conn.close()

        def list_models():
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT name, provider, cost, speed, privacy FROM models')
            rows = c.fetchall()
            conn.close()
            if not rows:
                print("No models registered.")
                return
            print(f"{'Name':<15}{'Provider':<15}{'Cost':<10}{'Speed':<10}{'Privacy':<10}")
            print("-" * 55)
            for row in rows:
                print(f"{row[0]:<15}{row[1]:<15}{row[2]:<10.4f}{row[3]:<10.2f}{row[4]:<10}")

                def demo():
                    if os.path.exists(DB_PATH):
                        os.remove(DB_PATH)
                        init_db()
                        add_model('llama3', 'ollama', 0.0, 2.5, 1)
                        add_model('mistral-tiny', 'mistral', 0.01, 1.2, 0)
                        add_model('mixtral-8x7b', 'mistral', 0.05, 0.8, 0)
                        add_model('llama3-70b', 'groq', 0.08, 0.5, 0)
                        add_model('gemma-7b', 'groq', 0.06, 0.7, 0)
                        list_models()

                        def main():
                            if '--demo' in sys.argv:
                                demo()
                                return

                            parser = argparse.ArgumentParser(
                            description='Model Router CLI for managing AI models.',
                            formatter_class=argparse.RawTextHelpFormatter
                            )
                            parser.add_argument('--demo', action='store_true', help='Run a demonstration of the model router (offline).')
                            subparsers = parser.add_subparsers(dest='command', help='Available commands')

                            add_parser = subparsers.add_parser('add', help='Add a new model to the router.')
                            add_parser.add_argument('--name', type=str, required=True, help='Name of the model (e.g., llama3).')
                            add_parser.add_argument('--provider', type=str, required=True, help='Provider of the model (e.g., ollama, mistral, groq).')
                            add_parser.add_argument('--cost', type=float, required=True, help='Cost per unit (e.g., per 1M tokens), 0.0 for free.')
                            add_parser.add_argument('--speed', type=float, required=True, help='Speed rating (lower is faster).')
                            add_parser.add_argument('--privacy', type=int, required=True, choices=[0,1], help='Privacy score (1=private, 0=public).')

                            args = parser.parse_args()
                            if args.command == 'add':
                                add_model(args.name, args.provider, args.cost, args.speed, args.privacy)
                                print(f"Added model: {args.name}")

                                if __name__ == '__main__':
                                    main()