import os
import sys
import json
import sqlite3
import argparse
import datetime
import re
import difflib

DB_PATH = os.path.expanduser("~/.promptvault/prompts.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version INTEGER NOT NULL,
            prompt_text TEXT NOT NULL,
            score INTEGER,
            timestamp TEXT NOT NULL,
            UNIQUE(name, version)
        )
    """)
    conn.commit()
    conn.close()

def save_prompt(name, prompt_text):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    version = 1 if not c.execute('SELECT * FROM prompts WHERE name=?', (name,)).fetchone() else c.execute('SELECT MAX(version) FROM prompts WHERE name=?', (name,)).fetchone()[0] + 1
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('INSERT INTO prompts (name, version, prompt_text, score, timestamp) VALUES (?, ?, ?, NULL, ?)', (name, version, prompt_text, timestamp))
    conn.commit()
    conn.close()

def list_prompts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, COUNT(*) AS versions, MAX(score) AS best_score, prompt_text FROM prompts GROUP BY name ORDER BY best_score DESC')
    rows = c.fetchall()
    conn.close()
    return rows

def show_prompt(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM prompts WHERE name=? ORDER BY version DESC LIMIT 1', (name,))
    row = c.fetchone()
    conn.close()
    if row:
        print(f"NAME: {row[0]}")
        print(f"PROMPT: {row[2]}")
    else:
        print("Prompt not found.")

def diff_prompts(name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM prompts WHERE name=? ORDER BY version DESC LIMIT 2', (name,))
    rows = c.fetchall()
    conn.close()
    if len(rows) == 2:
        diff = difflib.ndiff(rows[0][2].splitlines(), rows[1][2].splitlines())
        print('\n'.join(diff))
    else:
        print("Not enough versions to compare.")

def score_prompt(name, score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE prompts SET score=? WHERE name=? AND version=(SELECT MAX(version) FROM prompts WHERE name=?)', (score, name, name))
    conn.commit()
    conn.close()

def best_prompts():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, MAX(score) AS score, prompt_text FROM prompts GROUP BY name ORDER BY score DESC LIMIT 5')
    rows = c.fetchall()
    conn.close()
    return rows

def demo_mode():
    import os as _os
    _db = os.path.expanduser("~/.promptvault/prompts.db")
    if _os.path.exists(_db): _os.remove(_db)
    init_db()
    save_prompt("classifier", "Classify this text as positive, negative or neutral.")
    save_prompt("classifier", "Classify the following text as positive, negative or neutral.")
    save_prompt("summarizer", "Summarize the following text in 3 bullet points.")
    save_prompt("summarizer", "Summarize the following text in 5 sentences.")
    save_prompt("extractor", "Extract all named entities from this text.")
    save_prompt("extractor", "Extract key phrases and their relevance scores.")

    print("\n=== PROMPTVAULT DEMO ===\n")
    
    print("Saved prompts:")
    rows = list_prompts()
    for row in rows:
        print(f"{row[0]:<15} {row[1]:<10} {row[2]}/10 {' '.join(row[3].split()[:4]) + '...' if len(row[3].split()) > 4 else row[3]}")
    
    print("\nBest prompts:")
    rows = best_prompts()
    for row in rows:
        print(f"{row[0]:<15} {row[1]}/10 {' '.join(row[2].split()[:4]) + '...' if len(row[2].split()) > 4 else row[2]}")

def main():
    parser = argparse.ArgumentParser(description="PromptVault - Version control for LLM prompts")
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    
    subparsers = parser.add_subparsers(dest='command')

    save_parser = subparsers.add_parser('save', help='Save a prompt version')
    save_parser.add_argument('name', type=str, help='Prompt name')
    save_parser.add_argument('prompt_text', type=str, help='Prompt text')

    list_parser = subparsers.add_parser('list', help='List all prompts with scores')

    show_parser = subparsers.add_parser('show', help='Show latest version of a prompt')
    show_parser.add_argument('name', type=str, help='Prompt name')

    diff_parser = subparsers.add_parser('diff', help='Show diff between last 2 versions of a prompt')
    diff_parser.add_argument('name', type=str, help='Prompt name')

    score_parser = subparsers.add_parser('score', help='Rate a prompt version')
    score_parser.add_argument('name', type=str, help='Prompt name')
    score_parser.add_argument('score', type=int, choices=range(1, 11), help='Score (1-10)')

    best_parser = subparsers.add_parser('best', help='Show highest scored prompts')

    args, unknown_args = parser.parse_known_args()

    if args.demo:
        demo_mode()
    elif args.command == 'save':
        save_prompt(args.name, args.prompt_text)
    elif args.command == 'list':
        rows = list_prompts()
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<10} {row[2]}/10 {' '.join(row[3].split()[:4]) + '...' if len(row[3].split()) > 4 else row[3]}")
    elif args.command == 'show':
        show_prompt(args.name)
    elif args.command == 'diff':
        diff_prompts(args.name)
    elif args.command == 'score':
        score_prompt(args.name, args.score)
    elif args.command == 'best':
        rows = best_prompts()
        for row in rows:
            print(f"{row[0]:<15} {row[1]}/10 {' '.join(row[2].split()[:4]) + '...' if len(row[2].split()) > 4 else row[2]}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()