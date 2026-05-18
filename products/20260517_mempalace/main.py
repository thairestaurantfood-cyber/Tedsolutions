import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/mempalace.db')

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
        CREATE TABLE IF NOT EXISTS memory_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_id INTEGER NOT NULL,
            accessed_at TEXT NOT NULL,
            access_count INTEGER DEFAULT 1,
            FOREIGN KEY (memory_id) REFERENCES memories (id)
        )
    ''')

    demo_memories = [
        (datetime.now().isoformat(),
         "User asked about invoice processing automation for small businesses in Phuket",
         "[0.1,0.2,0.3,0.4,0.5]",
         12,
         json.dumps({"type": "workflow", "priority": "high"})),

        (datetime.now().isoformat(),
         "Agent suggested using local Ollama models for cost-effective AI inference",
         "[0.2,0.3,0.4,0.5,0.6]",
         15,
         json.dumps({"type": "api", "model": "ollama"})),

        (datetime.now().isoformat(),
         "User wants to track token usage in real-time across multiple agents",
         "[0.3,0.4,0.5,0.6,0.7]",
         18,
         json.dumps({"type": "monitoring", "interval": "realtime"})),

        (datetime.now().isoformat(),
         "Implemented semantic search for memory retrieval using cosine similarity",
         "[0.4,0.5,0.6,0.7,0.8]",
         22,
         json.dumps({"type": "feature", "status": "completed"})),

        (datetime.now().isoformat(),
         "Memory consolidation scheduled for low-usage memories older than 30 days",
         "[0.5,0.6,0.7,0.8,0.9]",
         20,
         json.dumps({"type": "maintenance", "schedule": "monthly"}))
    ]

    cursor.executemany('''
        INSERT INTO memories (timestamp, content, embedding, token_count, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', demo_memories)

    cursor.executemany('''
        INSERT INTO memory_access (memory_id, accessed_at, access_count)
        VALUES (?, ?, ?)
    ''', [
        (1, datetime.now().isoformat(), 3),
        (2, datetime.now().isoformat(), 1),
        (3, datetime.now().isoformat(), 2),
        (1, (datetime.now().replace(day=datetime.now().day-1)).isoformat(), 2)
    ])

    conn.commit()

    print(f"{'ID':<5} {'Timestamp':<25} {'Content':<60} {'Tokens':<8} {'Type':<12}")
    print("-" * 120)
    for row in cursor.execute("SELECT id, timestamp, content, token_count, json_extract(metadata, '$.type') FROM memories"):
        print(f"{row[0]:<5} {row[1]:<25} {row[2][:57]:<60} {row[3]:<8} {row[4]:<12}")
    print("\nMemory access log:")
    print(f"{'Memory ID':<10} {'Accessed At':<25} {'Count':<8}")
    print("-" * 45)
    for row in cursor.execute("SELECT memory_id, accessed_at, access_count FROM memory_access"):
        print(f"{row[0]:<10} {row[1]:<25} {row[2]:<8}")

    conn.close()
    print("\nDemo complete. Memories stored and retrieved successfully.")

def search_memories(query, limit=5):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, timestamp, content, token_count, json_extract(metadata, '$.type') as mtype
        FROM memories
        WHERE content LIKE ?
        ORDER BY token_count DESC
        LIMIT ?
    ''', (f'%{query}%', limit))

    results = cursor.fetchall()
    conn.close()

    if not results:
        print(f"No memories found matching: {query}")
        return

    print(f"\nSearch results for: '{query}'")
    print(f"{'ID':<5} {'Timestamp':<25} {'Content':<60} {'Tokens':<8} {'Type':<12}")
    print("-" * 120)
    for row in results:
        print(f"{row[0]:<5} {row[1]:<25} {row[2][:57]:<60} {row[3]:<8} {row[4]:<12}")
    print(f"\nFound {len(results)} memories")

def add_memory(content, metadata=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if metadata is None:
        metadata = {"type": "user_input"}

    cursor.execute('''
        INSERT INTO memories (timestamp, content, embedding, token_count, metadata)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        content,
        "[]",
        len(content.split()),
        json.dumps(metadata)
    ))

    memory_id = cursor.lastrowid
    conn.commit()
    conn.close()
    print(f"\nAdded new memory with ID: {memory_id}")
    return memory_id

def main():
    parser = argparse.ArgumentParser(description="MemPalace - Lightweight Memory Storage System")
    parser.add_argument('--demo', action='store_true', help='Run interactive demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    search_parser = subparsers.add_parser('search', help='Search memories by content')
    search_parser.add_argument('query', help='Search term to find in memories')
    search_parser.add_argument('--limit', type=int, default=5, help='Maximum results to return')

    add_parser = subparsers.add_parser('add', help='Add a new memory')
    add_parser.add_argument('content', help='Content of the memory to store')
    add_parser.add_argument('--type', default='user_input', help='Type of memory (default: user_input)')

    list_parser = subparsers.add_parser('list', help='List all memories')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum memories to display')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'search':
        search_memories(args.query, args.limit)
    elif args.command == 'add':
        metadata = {"type": args.type}
        add_memory(args.content, metadata)
    elif args.command == 'list':
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, content, token_count, json_extract(metadata, '$.type') FROM memories ORDER BY id DESC LIMIT ?", (args.limit,))
        results = cursor.fetchall()
        conn.close()

        print(f"\nLast {len(results)} memories:")
        print(f"{'ID':<5} {'Timestamp':<25} {'Content':<60} {'Tokens':<8} {'Type':<12}")
        print("-" * 120)
        for row in results:
            print(f"{row[0]:<5} {row[1]:<25} {row[2][:57]:<60} {row[3]:<8} {row[4]:<12}")
        print(f"\nTotal memories in system: {len(results)}")

if __name__ == "__main__":
    main()