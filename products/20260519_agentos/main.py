import argparse
import sqlite3
from datetime import datetime
import os
import json
import time

DB_PATH = os.path.expanduser('~/.jarvis/product.db')
SKILL_DIR = os.path.expanduser('~/jarvis/products/')

def create_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            agent_id INTEGER,
            task_name TEXT NOT NULL,
            priority INTEGER NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY,
            agent_id INTEGER,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        )
    ''')
    conn.commit()
    conn.close()

def discover_skills():
    skills = {}
    if not os.path.exists(SKILL_DIR):
        os.makedirs(SKILL_DIR, exist_ok=True)
        return skills

    for item in os.listdir(SKILL_DIR):
        path = os.path.join(SKILL_DIR, item)
        if os.path.isfile(path) and path.endswith('.skill'):
            try:
                with open(path, 'r') as f:
                    skill_data = json.load(f)
                    skills[item] = skill_data
            except:
                continue
    return skills

def print_dashboard(conn):
    print("\n" + "="*50)
    print("AGENTOS STATUS DASHBOARD")
    print("="*50)

    # Agents table
    print("\nAgents:")
    print(f"{'ID':<5} {'Name':<15} {'Status':<10}")
    print("-" * 35)
    c = conn.cursor()
    c.execute('SELECT id, name, status FROM agents ORDER BY id')
    agents = c.fetchall()
    for agent in agents:
        print(f"{agent[0]:<5} {agent[1]:<15} {agent[2]:<10}")

    # Tasks summary
    print("\nTask Queue:")
    c.execute('''
        SELECT agent_id, COUNT(*) as count, AVG(priority) as avg_priority
        FROM tasks
        GROUP BY agent_id
        ORDER BY agent_id
    ''')
    tasks = c.fetchall()
    print(f"{'AgentID':<10} {'Count':<8} {'AvgPriority':<12}")
    print("-" * 35)
    for task in tasks:
        print(f"{task[0]:<10} {task[1]:<8} {task[2]:<12.1f}")

    # Memory usage
    print("\nMemory Usage:")
    c.execute('''
        SELECT agent_id, COUNT(*) as entries
        FROM memory
        GROUP BY agent_id
        ORDER BY agent_id
    ''')
    memory = c.fetchall()
    print(f"{'AgentID':<10} {'Entries':<10}")
    print("-" * 35)
    for mem in memory:
        print(f"{mem[0]:<10} {mem[1]:<10}")

    # Skills
    print("\nActive Skills:")
    skills = discover_skills()
    if skills:
        print(f"{'Skill':<20} {'Description':<30}")
        print("-" * 55)
        for name, data in skills.items():
            print(f"{name:<20} {data.get('description','')[:30]:<30}")
    else:
        print("No skills found")

    print("\n" + "="*50)

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    create_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Insert hardcoded agents
    c.execute("INSERT INTO agents (name, status) VALUES (?, ?)", ('WebScraper', 'idle'))
    c.execute("INSERT INTO agents (name, status) VALUES (?, ?)", ('EmailParser', 'busy'))
    c.execute("INSERT INTO agents (name, status) VALUES (?, ?)", ('InvoiceBot', 'idle'))

    # Insert hardcoded tasks
    c.execute("INSERT INTO tasks (agent_id, task_name, priority) VALUES (?, ?, ?)", (1, 'Scrape ecommerce site', 8))
    c.execute("INSERT INTO tasks (agent_id, task_name, priority) VALUES (?, ?, ?)", (2, 'Parse 50 emails', 5))
    c.execute("INSERT INTO tasks (agent_id, task_name, priority) VALUES (?, ?, ?)", (3, 'Process invoice PDF', 7))
    c.execute("INSERT INTO tasks (agent_id, task_name, priority) VALUES (?, ?, ?)", (1, 'Scrape travel site', 6))
    c.execute("INSERT INTO tasks (agent_id, task_name, priority) VALUES (?, ?, ?)", (2, 'Parse booking confirmations', 4))

    # Insert hardcoded memory
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (1, 'last_run', '2024-01-15T14:30:00', '2024-01-15T14:30:00'))
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (2, 'last_run', '2024-01-15T15:00:00', '2024-01-15T15:00:00'))
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (3, 'last_run', '2024-01-15T14:45:00', '2024-01-15T14:45:00'))
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (1, 'config', '{"rate_limit": 10}', '2024-01-15T14:30:00'))
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (2, 'config', '{"timeout": 30}', '2024-01-15T15:00:00'))
    c.execute("INSERT INTO memory (agent_id, key, value, timestamp) VALUES (?, ?, ?, ?)", (3, 'config', '{"ocr_engine": "tesseract"}', '2024-01-15T14:45:00'))

    conn.commit()
    conn.close()

    # Print formatted dashboard
    conn = sqlite3.connect(DB_PATH)
    print_dashboard(conn)
    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="AgentOS - Autonomous Agent System")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')
    parser.set_defaults(func=lambda _: parser.print_help())

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)

if __name__ == "__main__":
    main()