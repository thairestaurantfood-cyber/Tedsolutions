import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.memtoken/memtoken.db')

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding TEXT,
        token_count INTEGER,
        metadata TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS token_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        agent_name TEXT NOT NULL,
        model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost_usd REAL NOT NULL,
        conversation_id TEXT NOT NULL,
        task_description TEXT NOT NULL
    )
    ''')

    demo_data = [
        (datetime.now().isoformat(), "User asked about invoice processing automation", "embedding1", 12, json.dumps({"type": "workflow"})),
        (datetime.now().isoformat(), "Agent suggested using Groq API for fast inference", "embedding2", 15, json.dumps({"type": "api"})),
        (datetime.now().isoformat(), "User wants to track token usage in real-time", "embedding3", 18, json.dumps({"type": "monitoring"}))
    ]

    cursor.executemany('INSERT INTO memories (timestamp, content, embedding, token_count, metadata) VALUES (?, ?, ?, ?, ?)', demo_data)

    token_data = [
        (datetime.now().isoformat(), "invoice-agent", "llama3-70b-8192", 500, 1200, 1700, 0.085, "conv-1001", "Process invoice PDF"),
        (datetime.now().isoformat(), "invoice-agent", "llama3-70b-8192", 300, 800, 1100, 0.055, "conv-1001", "Extract vendor details"),
        (datetime.now().isoformat(), "chat-assistant", "mixtral-8x7b-32768", 200, 500, 700, 0.035, "conv-1002", "Answer general question"),
        (datetime.now().isoformat(), "summarizer", "gemma-7b-it", 800, 300, 1100, 0.022, "conv-1003", "Summarize long document"),
        (datetime.now().isoformat(), "invoice-agent", "llama3-70b-8192", 450, 1100, 1550, 0.0775, "conv-1004", "Validate invoice data")
    ]

    cursor.executemany('''
    INSERT INTO token_usage
    (timestamp, agent_name, model, input_tokens, output_tokens, total_tokens, cost_usd, conversation_id, task_description)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', token_data)

    conn.commit()

    print("\nDemo Memories:")
    print("-" * 80)
    print(f"{'ID':<3} {'Timestamp':<25} {'Content':<40} {'Tokens':<6}")
    print("-" * 80)
    for row in cursor.execute('SELECT id, timestamp, content, token_count FROM memories ORDER BY id'):
        print(f"{row[0]:<3} {row[1]:<25} {row[2][:40]:<40} {row[3]:<6}")

    print("\n\nToken Usage Analytics:")
    print("-" * 80)
    print(f"{'ID':<3} {'Agent':<15} {'Model':<20} {'Total Tokens':<12} {'Cost USD':<10} {'Task':<30}")
    print("-" * 80)
    for row in cursor.execute('SELECT id, agent_name, model, total_tokens, cost_usd, task_description FROM token_usage ORDER BY id'):
        print(f"{row[0]:<3} {row[1]:<15} {row[2]:<20} {row[3]:<12} {row[4]:<10.3f} {row[5][:30]:<30}")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description='MemToken - Memory and Token Tracking System')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    args = parser.parse_args()

    if args.demo:
        demo()
        return

    print("MemToken - Memory and Token Tracking System")
    print("Use --demo to run a demonstration")

if __name__ == '__main__':
    main()