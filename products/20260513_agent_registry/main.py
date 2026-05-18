#!/usr/bin/env python3
"""
Agent Discovery & Identity Service
Register agents and discover services. stdlib+sqlite, <200 lines.
"""

import argparse, os, sqlite3
from datetime import datetime

REGISTRY_DB = os.path.expanduser("~/.jarvis/agent_registry.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(REGISTRY_DB)), exist_ok=True)
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            public_key TEXT,
            created_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_ac INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (agent_id) REFERENCES agents(agent_id))''')

def register_agent(agent_id):
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO agents (agent_id, public_key, created_at) VALUES (?, ?, datetime('now'))",
                      (agent_id, f"pubkey_{agent_id}"))
            conn.commit()
            return f"Agent '{agent_id}' registered successfully."
        except sqlite3.IntegrityError:
            return f"Agent '{agent_id}' already exists."

def list_service(agent_id, name, description, price):
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        # Verify agent exists
        c.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (agent_id,))
        if not c.fetchone():
            return f"Agent '{agent_id}' not registered. Register first."
        c.execute("INSERT INTO services (agent_id, name, description, price_ac, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                  (agent_id, name, description, price))
        conn.commit()
        service_id = c.lastrowid
        return f"Service listed with ID {service_id}: '{name}' for {price} AC by '{agent_id}'."

def discover_services(service_name=None, max_price=None):
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        query = """SELECT s.id, s.agent_id, s.name, s.description, s.price_ac, s.created_at
                   FROM services s JOIN agents a ON s.agent_id = a.agent_id"""
        conditions = []
        params = []
        if service_name:
            conditions.append("s.name LIKE ? COLLATE NOCASE")
            params.append(f"%{service_name}%")
        if max_price is not None:
            conditions.append("s.price_ac <= ?")
            params.append(max_price)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY s.id"
        c.execute(query, params)
        rows = c.fetchall()
        if not rows:
            return "No services found matching criteria."
        out = ["Discovered Services:"]
        out.append("-" * 60)
        for row in rows:
            sid, agent_id, name, desc, price, created = row
            out.append(f"ID: {sid} | {name} | {price} AC | by {agent_id}")
            out.append(f"  {desc}")
            out.append(f"  Listed: {created}")
            out.append("")
        return "\n".join(out)

def get_agent_info(agent_id):
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT agent_id, public_key, created_at FROM agents WHERE agent_id = ?", (agent_id,))
        row = c.fetchone()
        if not row:
            return f"Agent '{agent_id}' not found."
        agent_id, pubkey, created = row
        c.execute("SELECT COUNT(*) FROM services WHERE agent_id = ?", (agent_id,))
        service_count = c.fetchone()[0]
        return f"Agent ID: {agent_id}\nPublic Key: {pubkey}\nCreated: {created}\nServices Listed: {service_count}"

def demo():
    if os.path.exists(REGISTRY_DB): os.remove(REGISTRY_DB)
    init_db()
    print("=== Agent Discovery & Identity Demo ===\n")
    # Register agents
    print(register_agent("summarizer-bot"))
    print(register_agent("translator-bot"))
    print(register_agent("data-scraper"))
    print("\n--- List Services ---")
    print(list_service("summarizer-bot", "Text Summarization", "I will summarize long texts into key points", 8))
    print(list_service("translator-bot", "Language Translation", "Translate between English and Thai", 12))
    print(list_service("data-scraper", "Web Scraping", "Extract data from websites and return as JSON", 15))
    print("\n--- Discover All Services ---")
    print(discover_services())
    print("\n--- Discover Services under 10 AC ---")
    print(discover_services(max_price=10))
    print("\n--- Discover Services containing 'translate' ---")
    print(discover_services(service_name="translate"))
    print("\n--- Agent Info ---")
    print(get_agent_info("summarizer-bot"))
    print("\n" + get_agent_info("translator-bot"))

def main():
    parser = argparse.ArgumentParser(prog="agent-registry", description="Agent Discovery & Identity Service")
    subparsers = parser.add_subparsers(dest="command")
    # register-agent
    p_reg = subparsers.add_parser("register-agent", help="Register a new agent")
    p_reg.add_argument("agent_id")
    # list-service
    p_list = subparsers.add_parser("list-service", help="List a service offered by an agent")
    p_list.add_argument("agent_id")
    p_list.add_argument("name")
    p_list.add_argument("description")
    p_list.add_argument("price", type=int)
    # discover-services
    p_disc = subparsers.add_parser("discover-services", help="Discover services")
    p_disc.add_argument("--name", help="Filter by service name (partial match)")
    p_disc.add_argument("--max-price", type=int, help="Maximum price in AC")
    # get-agent-info
    p_info = subparsers.add_parser("get-agent-info", help="Get information about an agent")
    p_info.add_argument("agent_id")
    # demo
    parser.add_argument("--demo", action="store_true", help="Run a demo")
    args = parser.parse_args()
    if args.demo:
        demo()
    elif args.command == "register-agent":
        print(register_agent(args.agent_id))
    elif args.command == "list-service":
        print(list_service(args.agent_id, args.name, args.description, args.price))
    elif args.command == "discover-services":
        print(discover_services(args.name, args.max_price))
    elif args.command == "get-agent-info":
        print(get_agent_info(args.agent_id))
    else:
        parser.parse_args(["--help"])

if __name__ == "__main__":
    main()