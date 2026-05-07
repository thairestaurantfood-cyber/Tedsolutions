import os
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/srt_doctor.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS srt_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_path TEXT NOT NULL,
            fixed_path TEXT,
            errors_detected TEXT,
            fixed_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS srt_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER NOT NULL,
            error_type TEXT NOT NULL,
            line_number INTEGER,
            original_content TEXT,
            fixed_content TEXT,
            FOREIGN KEY (file_id) REFERENCES srt_files (id)
        )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        INSERT INTO srt_files (filename, original_path, fixed_path, errors_detected, fixed_count, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        "test.srt",
        "/home/user/videos/test.srt",
        "/home/user/videos/test_fixed.srt",
        "timing, numbering",
        3,
        datetime.now().isoformat()
    ))

    c.execute('''
        INSERT INTO srt_errors (file_id, error_type, line_number, original_content, fixed_content)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, "timing", 5, "00:00:05,000 --> 00:00:07,000", "00:00:05,500 --> 00:00:07,500"))

    c.execute('''
        INSERT INTO srt_errors (file_id, error_type, line_number, original_content, fixed_content)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, "numbering", 1, "1", "2"))

    c.execute('''
        INSERT INTO srt_errors (file_id, error_type, line_number, original_content, fixed_content)
        VALUES (?, ?, ?, ?, ?)
    ''', (1, "timing", 10, "00:01:05,000 --> 00:01:07,000", "00:01:05,500 --> 00:01:07,500"))

    conn.commit()
    conn.close()

    print("SRTDoctor Demo Database Contents:")
    print("=" * 50)
    print("SRT Files:")
    print("ID | Filename | Original Path | Fixed Path | Errors | Fixed Count | Created At")
    print("-" * 100)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM srt_files")
    for row in c.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {row[6]}")
    print("\nErrors:")
    print("ID | File ID | Error Type | Line | Original | Fixed")
    print("-" * 100)
    c.execute("SELECT * FROM srt_errors")
    for row in c.fetchall():
        print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description='SRT Doctor - Subtitle Repair Tool')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    parser.add_argument('--init', action='store_true', help='Initialize database')
    args = parser.parse_args()

    if args.demo:
        demo()
    elif args.init:
        init_db()
        print("Database initialized successfully")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()