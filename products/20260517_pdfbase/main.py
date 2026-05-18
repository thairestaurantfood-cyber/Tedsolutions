import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.pdfbase/pdfbase.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            size INTEGER NOT NULL,
            mtime INTEGER NOT NULL,
            content_hash TEXT NOT NULL,
            indexed_at INTEGER NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding BLOB,
            FOREIGN KEY(file_id) REFERENCES files(id)
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO files (path, filename, size, mtime, content_hash, indexed_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', ('/demo/report.pdf', 'Q3_Report.pdf', 1024, int(datetime.now().timestamp()), 'abc123', int(datetime.now().timestamp())))
    conn.execute('''
        INSERT INTO chunks (file_id, chunk_index, content, embedding)
        VALUES (?, ?, ?, ?)
    ''', (1, 0, 'Revenue in Q3 was $1.2M', b'fake_embedding'))
    conn.commit()
    conn.close()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('''
        SELECT f.filename, f.size, f.mtime, c.content
        FROM files f
        JOIN chunks c ON f.id = c.file_id
        ORDER BY f.filename
    ''')
    rows = cursor.fetchall()
    conn.close()

    print("Files:")
    print("Filename       | Size | Modified    | Content")
    print("---------------|------|-------------|----------------")
    for row in rows:
        print(f"{row[0]:<15} | {row[1]:<4} | {datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d')} | {row[3]}")

def add_file(path):
    path = Path(path).resolve()
    if not path.exists():
        print(f"Error: File not found: {path}")
        return

    stat = path.stat()
    content_hash = hash(path.read_bytes())

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''
            INSERT INTO files (path, filename, size, mtime, content_hash, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (str(path), path.name, stat.st_size, int(stat.st_mtime), content_hash, int(datetime.now().timestamp())))
        conn.commit()
        print(f"Added: {path.name}")
    except sqlite3.IntegrityError:
        print(f"Already indexed: {path.name}")
    finally:
        conn.close()

def list_files():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.execute('''
        SELECT filename, size, datetime(mtime, 'unixepoch') as mtime
        FROM files
        ORDER BY filename
    ''')
    rows = cursor.fetchall()
    conn.close()

    print("Indexed Files:")
    print("Filename       | Size | Modified")
    print("---------------|------|----------")
    for row in rows:
        print(f"{row[0]:<15} | {row[1]:<4} | {row[2]}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    add_parser = subparsers.add_parser('add', help='Add a PDF file to the index')
    add_parser.add_argument('file', nargs='?')
    subparsers.add_parser('list', help='List all indexed files')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    init_db()
    if args.command == 'add':
        if not args.file:
            print("Error: File path required")
            return
        add_file(args.file)
    elif args.command == 'list':
        list_files()

if __name__ == '__main__':
    main()