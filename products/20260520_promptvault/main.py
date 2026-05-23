import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/promptvault.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            tags TEXT
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

    # Insert hardcoded data with all fields populated
    c.execute("INSERT INTO prompts (name, version, content, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
              ("greeting", 1, "Hello, {user}!", "2024-01-01 10:00:00", "basic,common"))
    c.execute("INSERT INTO prompts (name, version, content, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
              ("greeting", 2, "Hi there, {user}! How are you today?", "2024-01-02 11:00:00", "basic,common"))
    c.execute("INSERT INTO prompts (name, version, content, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
              ("summarize", 1, "Summarize the following text in 3 bullet points:", "2024-01-03 12:00:00", "work,productivity"))
    c.execute("INSERT INTO prompts (name, version, content, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
              ("translate", 1, "Translate the following text to {target_language}:", "2024-01-04 13:00:00", "work,translation"))
    conn.commit()

    # Print formatted table showing all prompts and version differences
    c.execute("SELECT name, version, content, timestamp, tags FROM prompts ORDER BY name, version")
    rows = c.fetchall()
    print(f"{'Name':<15}{'Version':<10}{'Tags':<20}{'Timestamp':<20}")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]:<15}{row[1]:<10}{row[4]:<20}{row[3]:<20}")

    # Show diff between versions of same prompt
    print("\nVersion differences for 'greeting':")
    c.execute("SELECT version, content FROM prompts WHERE name = ? ORDER BY version", ("greeting",))
    versions = c.fetchall()
    for i in range(len(versions)-1):
        print(f"\nVersion {versions[i][0]} → {versions[i+1][0]}:")
        print(f"  {versions[i][1]}")
        print(f"  → {versions[i+1][1]}")

    conn.close()
    print("\nDemo complete.")

def save_prompt(name, content, tags=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT COALESCE(MAX(version), 0) FROM prompts WHERE name = ?", (name,))
    current_version = c.fetchone()[0] + 1

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tags_str = tags or ""

    c.execute("INSERT INTO prompts (name, version, content, timestamp, tags) VALUES (?, ?, ?, ?, ?)",
              (name, current_version, content, timestamp, tags_str))
    conn.commit()
    conn.close()
    print(f"Saved prompt '{name}' version {current_version}")

def get_prompt(name, version=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    if version:
        c.execute("SELECT content FROM prompts WHERE name = ? AND version = ?", (name, version))
    else:
        c.execute("SELECT content FROM prompts WHERE name = ? ORDER BY version DESC LIMIT 1", (name,))

    result = c.fetchone()
    conn.close()

    if result:
        print(result[0])
    else:
        print(f"Prompt '{name}' not found")

def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT name, version, tags, timestamp FROM prompts ORDER BY name, version")
    rows = c.fetchall()
    print(f"{'Name':<15}{'Version':<10}{'Tags':<20}{'Timestamp':<20}")
    print("-" * 70)
    for row in rows:
        print(f"{row[0]:<15}{row[1]:<10}{row[2]:<20}{row[3]:<20}")
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="PromptVault - Versioned prompt storage and retrieval")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample prompts')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    save_parser = subparsers.add_parser('save', help='Save a new prompt version')
    save_parser.add_argument('name', help='Prompt name')
    save_parser.add_argument('content', help='Prompt content/template')
    save_parser.add_argument('--tags', help='Comma-separated tags')

    get_parser = subparsers.add_parser('get', help='Get latest or specific version of a prompt')
    get_parser.add_argument('name', help='Prompt name')
    get_parser.add_argument('--version', type=int, help='Specific version number')

    list_parser = subparsers.add_parser('list', help='List all prompts')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'save':
        save_prompt(args.name, args.content, args.tags)
    elif args.command == 'get':
        get_prompt(args.name, args.version)
    elif args.command == 'list':
        list_prompts()

if __name__ == "__main__":
    main()