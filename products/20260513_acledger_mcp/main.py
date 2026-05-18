#!/usr/bin/env python3
"""
AC Ledger MCP Server - under 200 lines
Exposes AC wallet ledger as MCP server with tools:
- create_wallet, get_balance, send_ac, get_history
"""

import argparse, os, sqlite3
from pathlib import Path

DB_PATH = os.path.expanduser("~/.jarvis/ac_wallet.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS wallets (
            agent_id TEXT PRIMARY KEY, balance INTEGER NOT NULL DEFAULT 0,
            public_key TEXT, created_at TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT, to_agent TEXT, amount INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (from_agent) REFERENCES wallets(agent_id),
            FOREIGN KEY (to_agent) REFERENCES wallets(agent_id))''')

def wallet_create(agent_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO wallets (agent_id, public_key, balance, created_at) VALUES (?, ?, ?, datetime('now'))",
                      (agent_id, f"pubkey_{agent_id}", 0))
            conn.commit()
            return f"Wallet created for agent '{agent_id}' with starting balance 0 AC."
        except sqlite3.IntegrityError:
            return f"Wallet for agent '{agent_id}' already exists."

def wallet_get_balance(agent_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (agent_id,))
        row = c.fetchone()
        return f"Balance for '{agent_id}': {row[0]} AC" if row else f"No wallet found for agent '{agent_id}'. Create one with 'create_wallet'."

def wallet_send_ac(from_agent, to_agent, amount):
    if amount <= 0: return "Amount must be positive."
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (from_agent,))
        sender = c.fetchone()
        if not sender: return f"Sender wallet '{from_agent}' does not exist."
        if sender[0] < amount: return f"Insufficient balance: {sender[0]} AC < {amount} AC"
        c.execute("SELECT agent_id FROM wallets WHERE agent_id = ?", (to_agent,))
        if not c.fetchone(): return f"Recipient wallet '{to_agent}' does not exist."
        c.execute("UPDATE wallets SET balance = balance - ? WHERE agent_id = ?", (amount, from_agent))
        c.execute("UPDATE wallets SET balance = balance + ? WHERE agent_id = ?", (amount, to_agent))
        c.execute("INSERT INTO transactions (from_agent, to_agent, amount, timestamp) VALUES (?, ?, ?, datetime('now'))",
                  (from_agent, to_agent, amount))
        conn.commit()
        return f"Sent {amount} AC from '{from_agent}' to '{to_agent}'."

def wallet_get_history(agent_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""SELECT from_agent, to_agent, amount, timestamp
                     FROM transactions WHERE from_agent = ? OR to_agent = ?
                     ORDER BY id DESC""", (agent_id, agent_id))
        rows = c.fetchall()
        if not rows: return f"No transactions for agent '{agent_id}'."
        out = [f"Transaction history for '{agent_id}':", "From -> To | Amount | Timestamp", "-" * 40]
        out += [f"{f} -> {t} | {a:>6} AC | {ts}" for f, t, a, ts in rows]
        return "\n".join(out)

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    init_db()
    # Create a faucet agent and fund it directly for demo (since create_wallet starts at 0)
    wallet_create("faucet")
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE wallets SET balance = 10000 WHERE agent_id = ?", ("faucet",))
        conn.commit()
    alice, bob = "alice", "bob"
    print(wallet_create(alice)); print(wallet_create(bob))
    print(wallet_send_ac("faucet", alice, 100)); print(wallet_send_ac("faucet", bob, 100))
    print("\n=== Initial Balances ==="); print(wallet_get_balance(alice)); print(wallet_get_balance(bob))
    print("\n=== Sending 50 AC from Alice to Bob ==="); print(wallet_send_ac(alice, bob, 50))
    print("\n=== Balances After Transfer ==="); print(wallet_get_balance(alice)); print(wallet_get_balance(bob))
    print("\n=== Alice's Transaction History ==="); print(wallet_get_history(alice))
    print("\n=== Bob's Transaction History ==="); print(wallet_get_history(bob))

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
    server = Server("ac-ledger")
    
    @server.list_tools()
    async def list_tools():
        return [
            Tool(name="create_wallet", description="Create a new wallet",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"}},"required":["agent_id"]}),
            Tool(name="get_balance", description="Get wallet balance",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"}},"required":["agent_id"]}),
            Tool(name="send_ac", description="Send AC between agents",
                 inputSchema={"type":"object","properties":{"from_agent":{"type":"string"},"to_agent":{"type":"string"},"amount":{"type":"integer"}},"required":["from_agent","to_agent","amount"]}),
            Tool(name="get_history", description="Get transaction history",
                 inputSchema={"type":"object","properties":{"agent_id":{"type":"string"}},"required":["agent_id"]})
        ]
    
    @server.call_tool()
    async def call_tool(name, args):
        if name == "create_wallet": return [TextContent(type="text", text=wallet_create(args.get("agent_id","")))]
        if name == "get_balance": return [TextContent(type="text", text=wallet_get_balance(args.get("agent_id","")))]
        if name == "send_ac": return [TextContent(type="text", text=wallet_send_ac(args.get("from_agent",""), args.get("to_agent",""), int(args.get("amount",0))))]
        if name == "get_history": return [TextContent(type="text", text=wallet_get_history(args.get("agent_id","")))]
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