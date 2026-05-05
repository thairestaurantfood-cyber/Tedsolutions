import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/agentos.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            command TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            output TEXT,
            error TEXT,
            duration_ms INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents (id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    """)
    conn.commit()
    conn.close()

def add_agent(name: str, description: str, command: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO agents (name, description, command, created_at) VALUES (?, ?, ?, ?)",
        (name, description, command, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def list_agents():
    conn = get_db()
    rows = conn.execute("SELECT id, name, description, command, created_at FROM agents ORDER BY created_at DESC").fetchall()
    conn.close()
    return rows

def run_agent(agent_id: int):
    conn = get_db()
    agent = conn.execute("SELECT command FROM agents WHERE id = ?", (agent_id,)).fetchone()
    conn.close()

    if not agent:
        print(f"Agent {agent_id} not found")
        return None

    command = agent[0]
    start_time = datetime.utcnow()
    result = {"output": "", "error": "", "duration_ms": 0}

    try:
        start = datetime.utcnow()
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        duration = (datetime.utcnow() - start).total_seconds() * 1000
        result["output"] = proc.stdout
        result["error"] = proc.stderr
        result["duration_ms"] = int(duration)
        status = "success" if proc.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        result["error"] = "Command timed out after 300 seconds"
        status = "timeout"
    except Exception as e:
        result["error"] = str(e)

    conn = get_db()
    conn.execute(
        "INSERT INTO reports (agent_id, status, output, error, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (agent_id, status, result["output"], result["error"], result["duration_ms"], datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

    return result

def demo():
    DB_PATH = os.path.expanduser("~/.jarvis/agentos.db")
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    init_db()
    add_agent("Demo Agent", "A demo agent for testing purposes.", "echo 'Hello, World!'")
    agents = list_agents()
    print(f"{'ID':<5} {'Name':<15} {'Description':<20} {'Command'}")
    print("-" * 45)
    for agent in agents:
        print(f"{agent[0]:<5} {agent[1]:<15} {agent[2]:<20} {agent[3]}")

def main():
    parser = argparse.ArgumentParser(description="AgentOS")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()  # check --demo FIRST
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')  # NO required=True
    subparsers.add_parser('add', help='Add a new agent').set_defaults(func=add_agent)
    list_parser = subparsers.add_parser('list', help='List all agents').set_defaults(func=list_agents)
    run_parser = subparsers.add_parser('run', help='Run an agent by ID').add_argument('id', type=int).set_defaults(func=run_agent)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.func == add_agent:
        args.func(args.name, args.description, args.command)
    elif args.func == list_agents:
        agents = args.func()
        print(f"{'ID':<5} {'Name':<15} {'Description':<20} {'Command'}")
        print("-" * 45)
        for agent in agents:
            print(f"{agent[0]:<5} {agent[1]:<15} {agent[2]:<20} {agent[3]}")
    elif args.func == run_agent:
        result = args.func(args.id)
        if result:
            print(f"Status: {result['status']}")
            print(f"Output: {result['output']}")
            print(f"Error: {result['error']}")
            print(f"Duration: {result['duration_ms']} ms")

if __name__ == "__main__":
    main()