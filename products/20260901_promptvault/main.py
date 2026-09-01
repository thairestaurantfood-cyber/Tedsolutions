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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prompt_tags (
            prompt_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (prompt_id, tag_id),
            FOREIGN KEY (prompt_id) REFERENCES prompts(id),
            FOREIGN KEY (tag_id) REFERENCES tags(id)
        )
    ''')
    conn.commit()
    conn.close()

def add_prompt(name, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prompts (name, content, version)
        VALUES (?, ?, 1)
    ''', (name, content))
    conn.commit()
    conn.close()

def add_tag(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO tags (name)
        VALUES (?)
    ''', (name,))
    conn.commit()
    conn.close()

def tag_prompt(prompt_id, tag_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM tags WHERE name = ?
    ''', (tag_name,))
    tag = cursor.fetchone()
    if not tag:
        cursor.execute('''
            INSERT INTO tags (name)
            VALUES (?)
        ''', (tag_name,))
        tag_id = cursor.lastrowid
    else:
        tag_id = tag[0]
    cursor.execute('''
        INSERT OR IGNORE INTO prompt_tags (prompt_id, tag_id)
        VALUES (?, ?)
    ''', (prompt_id, tag_id))
    conn.commit()
    conn.close()

def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.version, p.created_at, p.score, GROUP_CONCAT(t.name, ', ')
        FROM prompts p
        LEFT JOIN prompt_tags pt ON p.id = pt.prompt_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        GROUP BY p.id
    ''')
    prompts = cursor.fetchall()
    conn.close()
    return prompts

def get_prompt_version(prompt_id, version):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.content, p.version, p.created_at, p.updated_at, p.score, GROUP_CONCAT(t.name, ', ')
        FROM prompts p
        LEFT JOIN prompt_tags pt ON p.id = pt.prompt_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        WHERE p.id = ? AND p.version = ?
        GROUP BY p.id
    ''', (prompt_id, version))
    prompt = cursor.fetchone()
    conn.close()
    return prompt

def diff_versions(prompt_id, version1, version2):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT content FROM prompts
        WHERE id = ? AND version = ?
    ''', (prompt_id, version1))
    content1 = cursor.fetchone()[0]
    cursor.execute('''
        SELECT content FROM prompts
        WHERE id = ? AND version = ?
    ''', (prompt_id, version2))
    content2 = cursor.fetchone()[0]
    conn.close()

    lines1 = content1.split('\n')
    lines2 = content2.split('\n')
    max_len = max(len(lines1), len(lines2))

    print(f"Diff between version {version1} and version {version2}:")
    print("-" * 50)
    for i in range(max_len):
        line1 = lines1[i] if i < len(lines1) else ""
        line2 = lines2[i] if i < len(lines2) else ""
        if line1 != line2:
            print(f"Version {version1}: {line1}")
            print(f"Version {version2}: {line2}")
            print("-" * 50)

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Add prompts
    add_prompt('Greeting', 'Hello, how can I help you today?')
    add_prompt('Farewell', 'Goodbye! Have a great day!')
    add_prompt('Question', 'What is your favorite programming language?')

    # Add tags
    add_tag('greeting')
    add_tag('farewell')
    add_tag('question')
    add_tag('programming')

    # Tag prompts
    tag_prompt(1, 'greeting')
    tag_prompt(2, 'farewell')
    tag_prompt(3, 'question')
    tag_prompt(3, 'programming')

    # Update a prompt to create a new version
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE prompts
        SET content = ?, version = 2, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', ('Hello! How can I assist you today?',))
    conn.commit()

    # Add another version
    cursor.execute('''
        INSERT INTO prompts (name, content, version, created_at, updated_at, score)
        SELECT name, 'Hello! How may I help you today?', 3, created_at, CURRENT_TIMESTAMP, score
        FROM prompts
        WHERE id = 1
    ''')
    conn.commit()

    # Update scores
    cursor.execute('''
        UPDATE prompts
        SET score = 4.5
        WHERE id = 1 AND version = 1
    ''')
    cursor.execute('''
        UPDATE prompts
        SET score = 4.8
        WHERE id = 1 AND version = 2
    ''')
    cursor.execute('''
        UPDATE prompts
        SET score = 5.0
        WHERE id = 1 AND version = 3
    ''')
    conn.commit()

    # Print all prompts with tags
    print(f"{'ID':<5} {'Name':<15} {'Version':<8} {'Created':<20} {'Score':<6} {'Tags'}")
    print("-" * 70)
    for row in cursor.execute('''
        SELECT p.id, p.name, p.version, p.created_at, p.score, GROUP_CONCAT(t.name, ', ')
        FROM prompts p
        LEFT JOIN prompt_tags pt ON p.id = pt.prompt_id
        LEFT JOIN tags t ON pt.tag_id = t.id
        GROUP BY p.id, p.version
    '''):
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<8} {row[3]:<20} {row[4]:<6} {row[5]}")

    conn.close()
    print("Demo complete.")

def main():
    parser = argparse.ArgumentParser(description="PromptVault")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

if __name__ == "__main__":
    main()