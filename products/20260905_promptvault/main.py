import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/promptvault.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            version INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt_id INTEGER NOT NULL,
            version INTEGER NOT NULL,
            score INTEGER NOT NULL,
            notes TEXT,
            run_at TIMESTAMP NOT NULL,
            FOREIGN KEY (prompt_id) REFERENCES prompts(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_prompt(name, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO prompts (name, content, version, created_at, updated_at)
        VALUES (?, ?, 1, ?, ?)
    ''', (name, content, now, now))
    conn.commit()
    conn.close()

def update_prompt(id, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE prompts
        SET content = ?, version = version + 1, updated_at = ?
        WHERE id = ?
    ''', (content, now, id))
    conn.commit()
    conn.close()

def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, version, created_at FROM prompts')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_prompt_history(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, name, content, version, created_at, updated_at
        FROM prompts
        WHERE id = ?
        ORDER BY version DESC
    ''', (id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def rollback_prompt(id, version):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT content FROM prompts
        WHERE id = ? AND version = ?
    ''', (id, version))
    result = cursor.fetchone()
    if result:
        content = result[0]
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            UPDATE prompts
            SET content = ?, version = version + 1, updated_at = ?
            WHERE id = ?
        ''', (content, now, id))
        conn.commit()
        conn.close()

def log_prompt_run(prompt_id, version, score, notes):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO prompt_runs (prompt_id, version, score, notes, run_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (prompt_id, version, score, notes, now))
    conn.commit()
    conn.close()

def get_prompt_performance(prompt_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT version, AVG(score) as avg_score, COUNT(*) as run_count
        FROM prompt_runs
        WHERE prompt_id = ?
        GROUP BY version
        ORDER BY version DESC
    ''', (prompt_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Add sample prompts
    add_prompt('greeting', 'Hello, how can I help you today?')
    add_prompt('farewell', 'Goodbye! Have a great day!')
    add_prompt('question', 'What is your favorite programming language?')

    # Update prompts to create versions
    update_prompt(1, 'Hi there! How can I assist you today?')
    update_prompt(2, 'See you later! Have a wonderful day!')
    update_prompt(3, 'What programming language do you prefer?')

    # Log sample prompt runs
    log_prompt_run(1, 1, 8, 'Good but needs improvement')
    log_prompt_run(1, 2, 9, 'Better response')
    log_prompt_run(2, 1, 7, 'Needs more warmth')
    log_prompt_run(2, 2, 8, 'More professional')
    log_prompt_run(3, 1, 6, 'Too technical')
    log_prompt_run(3, 2, 7, 'More approachable')

    # Print prompt performance
    print(f'{"Prompt ID":<10} {"Version":<10} {"Avg Score":<10} {"Run Count"}')
    print("-" * 40)
    for prompt_id in [1, 2, 3]:
        performance = get_prompt_performance(prompt_id)
        for row in performance:
            print(f"{prompt_id:<10} {row[0]:<10} {row[1]:<10.2f} {row[2]}")

def main():
    parser = argparse.ArgumentParser(description="PromptVault")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')

    # Add subparsers for other commands here...
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # Handle commands here...

if __name__ == "__main__":
    main()