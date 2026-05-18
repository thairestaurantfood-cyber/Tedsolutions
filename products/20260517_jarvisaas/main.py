import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import time
import re
import subprocess

DB_PATH = os.path.expanduser('~/.jarvis/users.db')
SCHEDULE_PATH = os.path.expanduser('~/.jarvis/build_schedule.json')
LOG_PATH = os.path.expanduser('~/.jarvis/build_logs.db')
PRODUCT_DB = os.path.expanduser('~/.jarvis/products.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_token TEXT NOT NULL,
            niche TEXT NOT NULL,
            daily_budget REAL NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def init_logs_db():
    os.makedirs(os.path.dirname(os.path.abspath(LOG_PATH)), exist_ok=True)
    conn = sqlite3.connect(LOG_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS build_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            build_name TEXT NOT NULL,
            status TEXT NOT NULL,
            score REAL,
            output TEXT,
            scheduled_at TEXT NOT NULL,
            completed_at TEXT,
            error TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def init_products_db():
    os.makedirs(os.path.dirname(os.path.abspath(PRODUCT_DB)), exist_ok=True)
    conn = sqlite3.connect(PRODUCT_DB)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            product_code TEXT NOT NULL,
            status TEXT NOT NULL,
            score REAL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def print_table(title, columns, rows):
    print(f"\n{title}")
    if not rows:
        print("(no rows)")
        return

    str_rows = [[("" if value is None else str(value)) for value in row] for row in rows]
    widths = [
        max(len(column), *(len(row[index]) for row in str_rows))
        for index, column in enumerate(columns)
    ]
    separator = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    header = "| " + " | ".join(column.ljust(widths[index]) for index, column in enumerate(columns)) + " |"

    print(separator)
    print(header)
    print(separator)
    for row in str_rows:
        print("| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(row)) + " |")
    print(separator)

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    if os.path.exists(LOG_PATH): os.remove(LOG_PATH)
    if os.path.exists(PRODUCT_DB): os.remove(PRODUCT_DB)

    init_db()
    init_logs_db()
    init_products_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO users (telegram_token, niche, daily_budget, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
              ("123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11", "AI tools for indie hackers", 10.0, "2024-01-01T00:00:00", "2024-01-01T00:00:00"))
    c.execute("INSERT INTO users (telegram_token, niche, daily_budget, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
              ("654321:XYZ-DEF5678ghIkl-zyx57W2v123ew11", "Tourism automation in Phuket", 25.0, "2024-01-02T00:00:00", "2024-01-02T00:00:00"))
    conn.commit()
    conn.close()

    log_conn = sqlite3.connect(LOG_PATH)
    log_c = log_conn.cursor()
    log_c.execute("INSERT INTO build_logs (user_id, build_name, status, score, output, scheduled_at, completed_at, error) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (1, "demo_build", "success", 12.0, "Build successful", datetime.now().isoformat(), datetime.now().isoformat(), None))
    log_conn.commit()
    log_conn.close()

    products_conn = sqlite3.connect(PRODUCT_DB)
    products_c = products_conn.cursor()
    products_c.execute("INSERT INTO products (user_id, product_name, product_code, status, score, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                       (1, "Jarvis CLI", "jarvis-cli-v1", "active", 12.0, datetime.now().isoformat()))
    products_conn.commit()
    products_conn.close()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, niche, daily_budget, created_at, updated_at FROM users ORDER BY id")
    users = c.fetchall()
    conn.close()

    log_conn = sqlite3.connect(LOG_PATH)
    log_c = log_conn.cursor()
    log_c.execute("SELECT id, user_id, build_name, status, score, output, scheduled_at, completed_at, error FROM build_logs ORDER BY id")
    build_logs = log_c.fetchall()
    log_conn.close()

    products_conn = sqlite3.connect(PRODUCT_DB)
    products_c = products_conn.cursor()
    products_c.execute("SELECT id, user_id, product_name, product_code, status, score, created_at FROM products ORDER BY id")
    products = products_c.fetchall()
    products_conn.close()

    print("Demo inserted data")
    print_table("Users", ["id", "niche", "daily_budget", "created_at", "updated_at"], users)
    print_table("Build Logs", ["id", "user_id", "build_name", "status", "score", "output", "scheduled_at", "completed_at", "error"], build_logs)
    print_table("Products", ["id", "user_id", "product_name", "product_code", "status", "score", "created_at"], products)

def main():
    parser = argparse.ArgumentParser(description='Jarvis AI Build System')
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    parser.add_argument('--init', action='store_true', help='Initialize databases')
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    if args.init:
        init_db()
        init_logs_db()
        init_products_db()
        print("Databases initialized")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
