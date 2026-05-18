import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/skillswarm.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            author TEXT NOT NULL,
            version TEXT NOT NULL,
            tags TEXT NOT NULL,
            file_path TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            rating REAL DEFAULT 0.0,
            review_count INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            reviewer TEXT NOT NULL,
            rating REAL NOT NULL,
            comment TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS installations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_id INTEGER NOT NULL,
            user TEXT NOT NULL,
            installed_at TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            FOREIGN KEY (skill_id) REFERENCES skills (id)
        )
    ''')
    conn.commit()
    conn.close()

def add_skill(name, description, author, version, tags, file_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    updated_at = created_at
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, description, author, version, tags, file_path, created_at, updated_at))
    conn.commit()
    skill_id = c.lastrowid
    conn.close()
    return skill_id

def list_skills():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, author, version, tags, rating, review_count FROM skills')
    rows = c.fetchall()
    conn.close()
    return rows

def add_installation(skill_id, user, status, error_message=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    installed_at = datetime.now().isoformat()
    c.execute('''
        INSERT INTO installations (skill_id, user, installed_at, status, error_message)
        VALUES (?, ?, ?, ?, ?)
    ''', (skill_id, user, installed_at, status, error_message))
    conn.commit()
    conn.close()
    return c.lastrowid

def get_installations(skill_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if skill_id:
        c.execute('''
            SELECT id, skill_id, user, installed_at, status, error_message
            FROM installations WHERE skill_id = ?
        ''', (skill_id,))
    else:
        c.execute('SELECT id, skill_id, user, installed_at, status, error_message FROM installations')
    rows = c.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "File Organizer",
        "Automatically organizes files by date and type",
        "Ted",
        "1.0.0",
        "automation,files,organization",
        "/home/user/file_organizer.sh",
        "2024-01-15T10:00:00",
        "2024-01-15T10:00:00"
    ))
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Invoice Parser",
        "Extracts data from PDF invoices using OCR",
        "Ted",
        "1.2.0",
        "automation,invoices,ocr",
        "/home/user/invoice_parser.py",
        "2024-01-16T11:30:00",
        "2024-01-16T11:30:00"
    ))
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Telegram Bot",
        "Autonomous Telegram bot for business automation",
        "Ted",
        "0.9.5",
        "automation,telegram,bot",
        "/home/user/telegram_bot.py",
        "2024-01-17T09:15:00",
        "2024-01-17T09:15:00"
    ))
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Expense Tracker",
        "Tracks business expenses with category analysis",
        "Ted",
        "2.1.0",
        "finance,expenses,tracking",
        "/home/user/expense_tracker.py",
        "2024-01-18T14:20:00",
        "2024-01-18T14:20:00"
    ))
    c.execute('''
        INSERT INTO skills (name, description, author, version, tags, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        "Skill Swarm CLI",
        "CLI tool for managing AI skills and agents",
        "Ted",
        "0.1.0",
        "cli,automation,skills",
        "/home/user/skillswarm.py",
        "2024-01-19T08:45:00",
        "2024-01-19T08:45:00"
    ))
    conn.commit()
    conn.close()

    print("SKILL LIST:")
    print("-" * 100)
    print(f"{'ID':<5} {'Name':<20} {'Author':<15} {'Version':<10} {'Tags':<30} {'Rating':<8} {'Reviews'}")
    print("-" * 100)
    rows = list_skills()
    for row in rows:
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<15} {row[3]:<10} {row[4]:<30} {row[5]:<8} {row[6]}")
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="SkillSwarm - CLI tool for managing AI skills and agents")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    parser_list = subparsers.add_parser('list', help='List all skills')
    parser_add = subparsers.add_parser('add', help='Add a new skill')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return