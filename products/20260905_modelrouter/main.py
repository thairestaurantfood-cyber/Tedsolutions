import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/modelrouter.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            priority INTEGER NOT NULL,
            cost_per_token REAL NOT NULL,
            latency_ms INTEGER NOT NULL,
            quality_score REAL NOT NULL,
            last_checked TEXT,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    providers = [
        ('Ollama', 'local', 1, 0.0001, 100, 0.85, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
        ('Groq', 'cloud', 2, 0.0002, 50, 0.90, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'),
        ('Gemini', 'cloud', 3, 0.0003, 75, 0.88, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active')
    ]

    cursor.executemany('''
        INSERT INTO providers (name, type, priority, cost_per_token, latency_ms, quality_score, last_checked, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', providers)

    conn.commit()

    cursor.execute('SELECT * FROM providers')
    rows = cursor.fetchall()

    print(f"{'ID':<5}{'Name':<10}{'Type':<10}{'Priority':<10}{'Cost':<10}{'Latency':<10}{'Quality':<10}{'Last Checked':<20}{'Status':<10}")
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<10}{row[3]:<10}{row[4]:<10}{row[5]:<10}{row[6]:<10}{row[7]:<20}{row[8]:<10}")

    conn.close()
    print("Demo complete.")

def register_provider(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO providers (name, type, priority, cost_per_token, latency_ms, quality_score, last_checked, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (args.name, args.type, args.priority, args.cost, args.latency, args.quality, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'active'))
    conn.commit()
    conn.close()
    print(f"Provider {args.name} registered successfully.")

def check_provider_health(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE providers
        SET last_checked = ?, status = ?
        WHERE name = ?
    ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), args.status, args.name))
    conn.commit()
    conn.close()
    print(f"Provider {args.name} health status updated to {args.status}.")

def route_request(args):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if args.strategy == 'fastest':
        cursor.execute('''
            SELECT name, type, latency_ms
            FROM providers
            WHERE status = 'active'
            ORDER BY latency_ms ASC
            LIMIT 1
        ''')
    elif args.strategy == 'cheapest':
        cursor.execute('''
            SELECT name, type, cost_per_token
            FROM providers
            WHERE status = 'active'
            ORDER BY cost_per_token ASC
            LIMIT 1
        ''')
    elif args.strategy == 'highest_quality':
        cursor.execute('''
            SELECT name, type, quality_score
            FROM providers
            WHERE status = 'active'
            ORDER BY quality_score DESC
            LIMIT 1
        ''')
    elif args.strategy == 'fallback':
        cursor.execute('''
            SELECT name, type, priority
            FROM providers
            WHERE status = 'active'
            ORDER BY priority ASC
            LIMIT 1
        ''')
    else:
        print("Invalid routing strategy.")
        return

    result = cursor.fetchone()
    conn.close()

    if result:
        print(f"Routing to {result[0]} ({result[1]})")
    else:
        print("No available providers.")

def main():
    parser = argparse.ArgumentParser(description="ModelRouter")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Register provider command
    register_parser = subparsers.add_parser('register', help='Register a new provider')
    register_parser.add_argument('--name', required=True, help='Provider name')
    register_parser.add_argument('--type', required=True, help='Provider type (local/cloud)')
    register_parser.add_argument('--priority', type=int, required=True, help='Provider priority')
    register_parser.add_argument('--cost', type=float, required=True, help='Cost per token')
    register_parser.add_argument('--latency', type=int, required=True, help='Latency in ms')
    register_parser.add_argument('--quality', type=float, required=True, help='Quality score')
    register_parser.set_defaults(func=register_provider)

    # Check provider health command
    health_parser = subparsers.add_parser('health', help='Check provider health')
    health_parser.add_argument('--name', required=True, help='Provider name')
    health_parser.add_argument('--status', required=True, help='Provider status (active/inactive)')
    health_parser.set_defaults(func=check_provider_health)

    # Route request command
    route_parser = subparsers.add_parser('route', help='Route a request')
    route_parser.add_argument('--strategy', required=True, help='Routing strategy (fastest/cheapest/highest_quality/fallback)')
    route_parser.set_defaults(func=route_request)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == "__main__":
    main()