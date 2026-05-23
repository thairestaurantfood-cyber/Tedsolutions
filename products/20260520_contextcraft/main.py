import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser("~/.contextcraft.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
    CREATE TABLE IF NOT EXISTS nodes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        line INTEGER NOT NULL,
        snippet TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    demo_data = [
        ('/home/user/jarvis/main.py', 'scan_project', 'function', 15, 'def scan_project(path):', '2024-01-01 10:00:00'),
        ('/home/user/jarvis/llm.py', 'LLMClient', 'class', 5, 'class LLMClient:', '2024-01-01 10:05:00'),
        ('/home/user/jarvis/main.py', 'import json', 'import', 1, 'import json', '2024-01-01 10:00:00'),
        ('/home/user/jarvis/llm.py', 'generate_response', 'function', 25, 'def generate_response(prompt):', '2024-01-01 10:10:00'),
        ('/home/user/jarvis/models.py', 'ContextNode', 'class', 8, 'class ContextNode(BaseModel):', '2024-01-01 10:15:00')
    ]

    cursor.executemany('''
    INSERT INTO nodes (path, name, type, line, snippet, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', demo_data)
    conn.commit()

    print(f"{'Path':<35} {'Name':<20} {'Type':<10} {'Line':<5} {'Snippet':<30}")
    print("-" * 110)
    cursor.execute('SELECT path, name, type, line, snippet FROM nodes ORDER BY path, line')
    for row in cursor.fetchall():
        print(f"{row[0]:<35} {row[1]:<20} {row[2]:<10} {row[3]:<5} {row[4]:<30}")
    conn.close()
    print("Demo complete.")

def build_index(args):
    path = args.path
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for py_file in Path(path).rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    line_stripped = line.strip()
                    if line_stripped.startswith('def ') and line_stripped.endswith(':'):
                        name = line_stripped[4:-1].split('(')[0].strip()
                        snippet = line_stripped
                        cursor.execute('''
                        INSERT INTO nodes (path, name, type, line, snippet)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (str(py_file), name, 'function', i, snippet))
                    elif line_stripped.startswith('class ') and line_stripped.endswith(':'):
                        name = line_stripped[6:-1].split('(')[0].strip()
                        snippet = line_stripped
                        cursor.execute('''
                        INSERT INTO nodes (path, name, type, line, snippet)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (str(py_file), name, 'class', i, snippet))
                    elif line_stripped.startswith('import ') or line_stripped.startswith('from '):
                        name = line_stripped.split()[1] if 'import' in line_stripped else line_stripped.split()[1]
                        snippet = line_stripped
                        cursor.execute('''
                        INSERT INTO nodes (path, name, type, line, snippet)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (str(py_file), name, 'import', i, snippet))
        except Exception as e:
            print(f"Error processing {py_file}: {e}", file=sys.stderr)

    conn.commit()
    print(f"Indexed {py_file} successfully")
    conn.close()

def query_llm_functions(args):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    SELECT path, name, type, line, snippet
    FROM nodes
    WHERE name LIKE '%llm%' OR name LIKE '%LLM%' OR snippet LIKE '%LLM%'
    OR name LIKE '%ai%' OR name LIKE '%AI%' OR snippet LIKE '%AI%'
    OR name LIKE '%model%' OR name LIKE '%Model%' OR snippet LIKE '%Model%'
    ORDER BY path, line
    ''')

    results = cursor.fetchall()
    if not results:
        print("No LLM-related functions found in the index")
        return

    print(f"{'Path':<35} {'Name':<20} {'Type':<10} {'Line':<5} {'Snippet':<30}")
    print("-" * 110)
    for row in results:
        print(f"{row[0]:<35} {row[1]:<20} {row[2]:<10} {row[3]:<5} {row[4]:<30}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="ContextCraft - Code context indexer and LLM function finder")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    index_parser = subparsers.add_parser('index', help='Index a Python project')
    index_parser.add_argument('path', help='Path to Python project directory')
    index_parser.set_defaults(func=build_index)

    query_parser = subparsers.add_parser('query', help='Query LLM-related functions')
    query_parser.set_defaults(func=query_llm_functions)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == "__main__":
    main()