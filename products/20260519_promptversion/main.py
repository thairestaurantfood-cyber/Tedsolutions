import os
import sys
import sqlite3
import argparse
import datetime
from pathlib import Path
import json

# --- Constants ---
APP_NAME = "promptversion"
JARVIS_DIR = Path.home() / ".jarvis"
DB_PATH = JARVIS_DIR / f"{APP_NAME}.db"

# --- Database Functions ---
def _init_db():
    """Initializes the database and creates the prompts table if it doesn't exist."""
    os.makedirs(JARVIS_DIR, exist_ok=True) # Ensure JARVIS_DIR exists
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(name, version)
    );
    ''')
    conn.commit()
    conn.close()

def _get_db_connection():
    os.makedirs(JARVIS_DIR, exist_ok=True) # Ensure JARVIS_DIR exists for the db path
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def _format_version(version):
    version = str(version)
    return version if version.startswith('v') else f'v{version}'

def add_prompt(name, version, content):
    conn = _get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        cursor.execute("INSERT INTO prompts (name, version, content, created_at) VALUES (?, ?, ?, ?)",
        (name, version, content, created_at))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Error: Prompt '{name}' version '{version}' already exists.", file=sys.stderr)
        return False
    finally:
        conn.close()

def get_prompt(name, version=None):
    conn = _get_db_connection()
    cursor = conn.cursor()
    if version:
        cursor.execute("SELECT * FROM prompts WHERE name = ? AND version = ?", (name, version))
    else: # Get the latest version if none specified
        cursor.execute("""
        SELECT * FROM prompts WHERE name = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """, (name,))
    prompt = cursor.fetchone()
    conn.close()
    return prompt

def list_prompts(name_filter=None):
    conn = _get_db_connection()
    cursor = conn.cursor()
    if name_filter:
        cursor.execute("SELECT name, version, created_at FROM prompts WHERE name LIKE ? ORDER BY name, version DESC", (f"%{name_filter}%",))
    else:
        cursor.execute("SELECT name, version, created_at FROM prompts ORDER BY name, version DESC")
    prompts = cursor.fetchall()
    conn.close()
    return prompts

def demo():
    print("Running offline demo for promptversion tool...")
    if DB_PATH.exists():
        DB_PATH.unlink()
    _init_db() # Ensure DB is initialized for demo
    print(f"Database initialized at: {DB_PATH}")
    # Add some demo prompts
    add_prompt("greeting", "v1.0", "Hello there!")
    add_prompt("greeting", "v1.1", "Greetings, human!")
    add_prompt("farewell", "v1.0", "Goodbye!")
    add_prompt("farewell", "v1.1", "See you later!")
    add_prompt("greeting", "v1.2", "Hi!") # Add a newer version
    print("\n--- Listing all prompts ---")
    all_prompts = list_prompts()
    if all_prompts:
        for p in all_prompts:
            print(f"  {p['name']} ({_format_version(p['version'])}) created: {p['created_at']}")
    else:
        print("  No prompts found in demo.")
    print("\n--- Getting 'greeting' v1.1 ---")
    greet_v1_1 = get_prompt("greeting", "v1.1")
    if greet_v1_1:
        print(f"  Content: {greet_v1_1['content']}")
    else:
        print("  'greeting' v1.1 not found (this shouldn't happen in a successful demo).")
    print("\n--- Getting latest 'greeting' ---")
    latest_greet = get_prompt("greeting")
    if latest_greet:
        print(f"  Latest greeting ({_format_version(latest_greet['version'])}): {latest_greet['content']}")
    else:
        print("  Latest 'greeting' not found.")
    print("\n--- Listing prompts filtered by 'fare' ---")
    fare_prompts = list_prompts(name_filter="fare")
    if fare_prompts:
        for p in fare_prompts:
            print(f"  {p['name']} ({_format_version(p['version'])}) created: {p['created_at']}")
    else:
        print("  No prompts found matching 'fare'.")
    print("\nDemo finished.")

def main():
    if '--demo' in sys.argv:
        demo()
        return
    parser = argparse.ArgumentParser(description="Manage prompt versions for Jarvis.")
    subparsers = parser.add_subparsers(dest="command")
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new prompt version.")
    add_parser.add_argument("name", help="Name of the prompt.")
    add_parser.add_argument("version", help="Version string (e.g., v1.0).")
    add_parser.add_argument("content", help="Content of the prompt.")
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a prompt version.")
    get_parser.add_argument("name", help="Name of the prompt.")
    get_parser.add_argument("--version", help="Specific version to retrieve (latest if not specified).")
    # List command
    list_parser = subparsers.add_parser("list", help="List all prompt versions.")
    list_parser.add_argument("--name", help="Filter by prompt name (case-insensitive substring match).")
    args = parser.parse_args()
    # Initialize DB for all commands (it's safe, creates if not exists)
    _init_db()
    if args.command == "add":
        if add_prompt(args.name, args.version, args.content):
            print(f"Prompt '{args.name}' {_format_version(args.version)} added successfully.")
    elif args.command == "get":
        prompt = get_prompt(args.name, args.version)
        if prompt:
            print(f"Prompt: {prompt['name']} ({_format_version(prompt['version'])})")
            print(f"Created: {prompt['created_at']}")
            print("Content:")
            print(prompt['content'])
        else:
            print(f"Prompt '{args.name}' not found" + (f" with version '{args.version}'" if args.version else " (latest)."), file=sys.stderr)
            sys.exit(1)
    elif args.command == "list":
        prompts = list_prompts(args.name)
        if prompts:
            print("--- Prompts ---")
            for p in prompts:
                print(f"  {p['name']} ({_format_version(p['version'])}) created: {p['created_at']}")
        else:
            print("No prompts found.")

if __name__ == "__main__":
    main()