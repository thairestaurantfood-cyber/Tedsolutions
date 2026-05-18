#!/usr/bin/env python3
"""
Agent Registry MCP Server - under 200 lines
Exposes agent discovery as MCP server with tools:
- register_agent, list_service, discover_services, get_agent_info, leave_review, get_reviews
"""

import argparse, os, sqlite3
from pathlib import Path
import sys

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
        c.execute('''CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_id INTEGER NOT NULL,
            reviewer_agent TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (service_id) REFERENCES services(id),
            FOREIGN KEY (reviewer_agent) REFERENCES agents(agent_id))''')

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
            # Get average rating for this service
            c.execute("SELECT AVG(rating), COUNT(*) FROM reviews WHERE service_id = ?", (sid,))
            rating_result = c.fetchone()
            avg_rating = rating_result[0] if rating_result[0] is not None else 0
            review_count = rating_result[1]
            rating_display = f" ({avg_rating:.1f}★ from {review_count} reviews)" if review_count > 0 else " (no reviews)"
            out.append(f"ID: {sid} | {name} | {price} AC | by {agent_id}{rating_display}")
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
        # Get agent's average rating across all services
        c.execute("""SELECT AVG(rating), COUNT(*) 
                     FROM reviews r 
                     JOIN services s ON r.service_id = s.id 
                     WHERE s.agent_id = ?""", (agent_id,))
        rating_result = c.fetchone()
        avg_rating = rating_result[0] if rating_result[0] is not None else 0
        total_reviews = rating_result[1]
        rating_info = f"\nAverage Rating: {avg_rating:.1f}★ ({total_reviews} total reviews)" if total_reviews > 0 else "\nAverage Rating: No reviews yet"
        return f"Agent ID: {agent_id}\nPublic Key: {pubkey}\nCreated: {created}\nServices Listed: {service_count}{rating_info}"

def leave_review(service_id, reviewer_agent, rating, review_text=""):
    if rating < 1 or rating > 5:
        return "Rating must be between 1 and 5."
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        # Verify service exists
        c.execute("SELECT id FROM services WHERE id = ?", (service_id,))
        if not c.fetchone():
            return f"Service ID {service_id} not found."
        # Verify reviewer exists
        c.execute("SELECT agent_id FROM agents WHERE agent_id = ?", (reviewer_agent,))
        if not c.fetchone():
            return f"Reviewer agent '{reviewer_agent}' not registered."
        # Check if already reviewed this service (optional: allow multiple reviews)
        c.execute("INSERT INTO reviews (service_id, reviewer_agent, rating, review_text, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                  (service_id, reviewer_agent, rating, review_text))
        conn.commit()
        return f"Review left for service ID {service_id}: {rating}/5 stars"

def get_reviews(service_id):
    with sqlite3.connect(REGISTRY_DB) as conn:
        c = conn.cursor()
        c.execute("""SELECT r.rating, r.review_text, r.created_at, a.agent_id
                     FROM reviews r
                     JOIN agents a ON r.reviewer_agent = a.agent_id
                     WHERE r.service_id = ?
                     ORDER BY r.id DESC""", (service_id,))
        rows = c.fetchall()
        if not rows:
            return f"No reviews for service ID {service_id}."
        out = [f"Reviews for service ID {service_id}:", "-" * 50]
        for rating, review_text, created, reviewer in rows:
            out.append(f"{reviewer} rated {rating}/5 at {created}")
            if review_text.strip():
                out.append(f"  \"{review_text}\"")
            out.append("")
        return "\n".join(out)

def demo():
    if os.path.exists(REGISTRY_DB): os.remove(REGISTRY_DB)
    init_db()
    print("=== Agent Registry MCP Demo ===\n")
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
    print("\n--- Leave some reviews ---")
    print(leave_review(1, "translator-bot", 5, "Excellent summary, very concise!"))
    print(leave_review(1, "data-scraper", 4, "Good but missed some key points"))
    print(leave_review(2, "summarizer-bot", 3, "Basic translation, could be better"))
    print("\n--- Discover Services (now with ratings) ---")
    print(discover_services())
    print("\n--- Get Reviews for Service ID 1 ---")
    print(get_reviews(1))
    print("\n--- Agent Info ---")
    print(get_agent_info("summarizer-bot"))
    print("\n" + get_agent_info("translator-bot"))

# MCP server setup
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

def serve():
    if not MCP_AVAILABLE:
        print("Error: MCP package not installed. Run: pip install mcp", file=sys.stderr)
        return
    init_db()
    server = Server("agent-registry")
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="register_agent", description="Register a new agent",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"}},"required":["agent_id"]}),
            Tool(name="list_service", description="List a service offered by an agent",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"},"name":{"type":"string"},"description":{"type":"string"},"price":{"type":"integer"}},"required":["agent_id","name","description","price"]}),
            Tool(name="discover_services", description="Discover services with optional filters",
                 inputSchema={"type":"object","properties":{"service_name":{"type":"string"},"max_price":{"type":"integer"}}}),
            Tool(name="get_agent_info", description="Get information about an agent",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"}},"required":["agent_id"]}),
            Tool(name="leave_review", description="Leave a review for a service",
                 inputSchema={"type":"object","properties":{"service_id":{"type":"integer"},"reviewer_agent":{"type":"string"},"rating":{"type":"integer"},"review_text":{"type":"string"}},"required":["service_id","reviewer_agent","rating"]}),
            Tool(name="get_reviews", description="Get reviews for a service",
                 inputSchema={"type":"object","properties":{"service_id":{"type":"integer"}},"required":["service_id"]})
        ]
    
    @server.call_tool()
    async def call_tool(name, args):
        if name == "register_agent": 
            return [TextContent(type="text", text=register_agent(args.get("agent_id","")))]
        if name == "list_service": 
            return [TextContent(type="text", text=list_service(args.get("agent_id",""), args.get("name",""), args.get("description",""), int(args.get("price",0))))]
        if name == "discover_services": 
            return [TextContent(type="text", text=discover_services(args.get("service_name"), args.get("max_price")))]
        if name == "get_agent_info": 
            return [TextContent(type="text", text=get_agent_info(args.get("agent_id","")))]
        if name == "leave_review": 
            return [TextContent(type="text", text=leave_review(int(args.get("service_id",0)), args.get("reviewer_agent",""), int(args.get("rating",0)), args.get("review_text","")))]
        if name == "get_reviews": 
            return [TextContent(type="text", text=get_reviews(int(args.get("service_id",0))))]
        return [TextContent(type="text", text=f"Error: Unknown tool {name}")]
    
    import asyncio
    async def run():
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())
    asyncio.run(run())

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--demo", action="store_true", help="Run demo")
    p.add_argument("--serve", action="store_true", help="Start MCP server (default)")
    a = p.parse_args()
    if a.demo: demo()
    else: serve()

if __name__ == "__main__":
    main()