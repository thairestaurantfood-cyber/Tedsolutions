import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.gemini_fs.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            ext TEXT,
            size INTEGER,
            mtime INTEGER,
            hash TEXT,
            indexed_at INTEGER DEFAULT (strftime('%s', 'now'))
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_path ON files(path)
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_ext ON files(ext)
    ''')
    conn.commit()
    conn.close()

def add_file(path: str):
    path = os.path.abspath(path)
    if not os.path.exists(path):
        print(f"File not found: {path}", file=sys.stderr)
        return False

    stat = os.stat(path)
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    mtime = int(stat.st_mtime)

    # Simple hash for demo (in real use would use proper hashing)
    hash_val = str(hash(path + str(stat.st_size) + str(mtime)))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO files (path, name, ext, size, mtime, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (path, name, ext, stat.st_size, mtime, hash_val))
        conn.commit()
        print(f"Added: {path}")
        return True
    except sqlite3.IntegrityError:
        print(f"Already indexed: {path}")
        return False
    finally:
        conn.close()

def list_files(ext: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if ext:
        c.execute('SELECT path, name, ext, size, mtime FROM files WHERE ext = ? ORDER BY mtime DESC', (ext,))
    else:
        c.execute('SELECT path, name, ext, size, mtime FROM files ORDER BY mtime DESC')
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No files indexed")
        return

    # Format output as raw Python list of tuples
    print("Indexed files:")
    for row in rows:
        print(row)

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()

    # Add hardcoded demo files
    demo_files = [
        ("~/Documents/project1/image.png", "image.png", ".png", 1024, 1625097600),
        ("~/Documents/notes.txt", "notes.txt", ".txt", 512, 1625097601),
        ("~/Downloads/report.pdf", "report.pdf", ".pdf", 2048, 1625097602),
        ("~/Pictures/photo.jpg", "photo.jpg", ".jpg", 4096, 1625097603),
        ("~/code/script.py", "script.py", ".py", 256, 1625097604)
    ]

    for path, name, ext, size, mtime in demo_files:
        full_path = os.path.expanduser(path)
        # Create dummy files
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w') as f:
            f.write("demo content")

        # Add to DB
        stat = os.stat(full_path)
        hash_val = str(hash(full_path + str(size) + str(mtime)))
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO files (path, name, ext, size, mtime, hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (full_path, name, ext, size, mtime, hash_val))
        conn.commit()
        conn.close()

    # Query and print formatted table
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT path, name, ext, size, mtime FROM files ORDER BY mtime DESC')
    rows = c.fetchall()
    conn.close()

    print("DEMO FILES INDEXED:")
    for row in rows:
        print(row)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        if not args.path:
            print("Error: path required for add command", file=sys.stderr)
            return
        add_file(args.path)
    elif args.command == 'list':
        list_files(getattr(args, 'ext', None))
    else:
        parser.print_help()

if __name__ == '__main__':
    init_db()
    main()