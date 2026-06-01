import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/ktx.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name TEXT NOT NULL,
        user_message TEXT NOT NULL,
        agent_response TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        context_layer TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_interaction(agent_name, user_message, agent_response, context_layer=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO interactions (agent_name, user_message, agent_response, context_layer)
    VALUES (?, ?, ?, ?)
    ''', (agent_name, user_message, agent_response, context_layer))
    conn.commit()
    conn.close()

def list_interactions():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interactions ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    # Insert demo data
    demo_data = [
        ('agent1', 'Hello, how are you?', 'I am good, thank you!', 'greeting'),
        ('agent2', 'What is the weather today?', 'It is sunny and warm.', 'weather'),
        ('agent1', 'Tell me a joke.', 'Why don\'t scientists trust atoms? Because they make up everything!', 'fun')
    ]

    for data in demo_data:
        add_interaction(*data)

    # Print formatted table
    interactions = list_interactions()
    print(f"{'ID':<5}{'Agent':<10}{'User Message':<20}{'Agent Response':<30}{'Context':<15}{'Timestamp':<20}")
    print("-" * 90)
    for row in interactions:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<20}{row[3]:<30}{row[5]:<15}{row[4]:<20}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    if '--demo' in sys.argv:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add command
    add_parser = subparsers.add_parser('add')
    add_parser.add_argument('--agent', required=True)
    add_parser.add_argument('--message', required=True)
    add_parser.add_argument('--response', required=True)
    add_parser.add_argument('--context', required=False)

    # List command
    list_parser = subparsers.add_parser('list')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        init_db()
        add_interaction(args.agent, args.message, args.response, args.context)
        print("Interaction added successfully.")
    elif args.command == 'list':
        interactions = list_interactions()
        print(f"{'ID':<5}{'Agent':<10}{'User Message':<20}{'Agent Response':<30}{'Context':<15}{'Timestamp':<20}")
        print("-" * 90)
        for row in interactions:
            print(f"{row[0]:<5}{row[1]:<10}{row[2]:<20}{row[3]:<30}{row[5]:<15}{row[4]:<20}")