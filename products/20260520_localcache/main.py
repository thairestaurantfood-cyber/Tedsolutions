import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/localcache.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            command TEXT NOT NULL,
            stdout TEXT,
            stderr TEXT,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def cache_key(key, command):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            'INSERT OR REPLACE INTO cache (key, command, stdout, stderr, timestamp) VALUES (?, ?, ?, ?, ?)',
            (key, command, None, None, datetime.now().isoformat())
        )
        conn.commit()
        print(f"Cached command for key: {key}")
    except sqlite3.IntegrityError:
        print(f"Key {key} already exists. Use 'update' or 'rm' first.")
    finally:
        conn.close()

def execute_and_store(key, command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            'UPDATE cache SET stdout=?, stderr=?, timestamp=? WHERE key=?',
            (result.stdout, result.stderr, datetime.now().isoformat(), key)
        )
        conn.commit()
        conn.close()
        print(f"Stored output for key: {key}")
    except subprocess.TimeoutExpired:
        print(f"Command timed out for key: {key}")
    except Exception as e:
        print(f"Failed to execute command: {e}")

def get_key(key):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute('SELECT command, stdout, stderr, timestamp FROM cache WHERE key=?', (key,)).fetchone()
    conn.close()
    if row:
        command, stdout, stderr, timestamp = row
        print(f"{'Key':<15}{'Timestamp':<20}{'Command':<30}")
        print(f"{key:<15}{timestamp:<20}{command[:27]:<30}")
        if stdout:
            print("\nSTDOUT:")
            print(stdout)
        if stderr:
            print("\nSTDERR:")
            print(stderr)
    else:
        print(f"Key {key} not found")

def list_keys():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute('SELECT key, command, timestamp FROM cache ORDER BY timestamp DESC').fetchall()
    conn.close()
    if rows:
        print(f"{'Key':<15}{'Timestamp':<20}{'Command':<30}")
        for key, command, timestamp in rows:
            print(f"{key:<15}{timestamp[:19]:<20}{command[:27]:<30}")
    else:
        print("No cached commands found")

def rm_key(key):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('DELETE FROM cache WHERE key=?', (key,))
    conn.commit()
    conn.close()
    print(f"Removed key: {key}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        'INSERT INTO cache (key, command, stdout, stderr, timestamp) VALUES (?, ?, ?, ?, ?)',
        ('demo1', 'sleep 0.1; echo hello', 'hello\n', '', datetime.now().isoformat())
    )
    conn.execute(
        'INSERT INTO cache (key, command, stdout, stderr, timestamp) VALUES (?, ?, ?, ?, ?)',
        ('demo2', 'date', 'Mon Jan  1 00:00:00 +0000 2026\n', '', datetime.now().isoformat())
    )
    conn.execute(
        'INSERT INTO cache (key, command, stdout, stderr, timestamp) VALUES (?, ?, ?, ?, ?)',
        ('demo3', 'ls -la', 'total 0\n', '', datetime.now().isoformat())
    )
    conn.commit()
    print(f"{'Key':<15}{'Timestamp':<20}{'Command':<30}")
    print("-" * 65)
    for row in conn.execute('SELECT key, command, timestamp FROM cache ORDER BY timestamp'):
        key, command, timestamp = row
        print(f"{key:<15}{timestamp[:19]:<20}{command[:27]:<30}")
    conn.close()
    print("Demo complete.")

def main():
    parser = argparse.ArgumentParser(description="LocalCache - CLI command caching tool")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample commands')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    cache_cmd = subparsers.add_parser('cache', help='Cache a command')
    cache_cmd.add_argument('key', help='Cache key')
    cache_cmd.add_argument('command', help='Command to cache')
    get_cmd = subparsers.add_parser('get', help='Get cached command output')
    get_cmd.add_argument('key', help='Cache key')
    list_cmd = subparsers.add_parser('list', help='List all cached commands')
    rm_cmd = subparsers.add_parser('rm', help='Remove a cached command')
    rm_cmd.add_argument('key', help='Cache key')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    if args.command == 'cache':
        cache_key(args.key, args.command)
    elif args.command == 'get':
        get_key(args.key)
    elif args.command == 'list':
        list_keys()
    elif args.command == 'rm':
        rm_key(args.key)

if __name__ == "__main__":
    import subprocess
    main()