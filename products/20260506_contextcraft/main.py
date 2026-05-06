import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.contextcraft.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            mtime INTEGER,
            size INTEGER,
            language TEXT,
            dependencies TEXT,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_file(path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    file_path = Path(path)
    if not file_path.exists():
        print(f"Error: File {path} does not exist", file=sys.stderr)
        conn.close()
        return

    stat = file_path.stat()
    mtime = int(stat.st_mtime)
    size = stat.st_size

    # Simple language detection
    ext = file_path.suffix.lower()
    language = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.sh': 'bash',
        '.md': 'markdown',
        '.html': 'html',
        '.css': 'css'
    }.get(ext, 'unknown')

    # Simple dependency detection (basic implementation)
    dependencies = []
    if language == 'python':
        try:
            with open(path) as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.startswith('import ') or line.startswith('from '):
                        dep = line.split()[1].split('.')[0]
                        dependencies.append(dep)
        except Exception:
            pass

    dependencies_str = json.dumps(dependencies) if dependencies else '[]'
    metadata = json.dumps({
        'language': language,
        'size': size,
        'mtime': mtime
    })

    try:
        cursor.execute('''
            INSERT OR REPLACE INTO files (path, mtime, size, language, dependencies, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(file_path), mtime, size, language, dependencies_str, metadata))
        conn.commit()
        print(f"Added: {path}")
    except sqlite3.IntegrityError:
        print(f"Updated: {path}")
    finally:
        conn.close()

def list_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT path, language, size FROM files ORDER BY path')
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No files indexed")
        return

    # Simple table formatting
    print("\nIndexed Files:")
    print("-" * 50)
    for path, lang, size in rows:
        print(f"{path} ({lang}, {size} bytes)")
    print("-" * 50)

def demo():
    init_db()
    test_file = Path(__file__).parent / "test.txt"
    test_file.write_text("test content")
    add_file(str(test_file))
    list_files()
    test_file.unlink()

def main():
    parser = argparse.ArgumentParser(description="ContextCraft - File indexing tool")
    parser.add_argument('--init', action='store_true', help='Initialize database')
    parser.add_argument('--add', type=str, help='Add file to index')
    parser.add_argument('--list', action='store_true', help='List indexed files')
    parser.add_argument('--demo', action='store_true', help='Run demo (offline)')

    args = parser.parse_args()

    if args.init:
        init_db()
    elif args.add:
        add_file(args.add)
    elif args.list:
        list_files()
    elif args.demo:
        demo()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()