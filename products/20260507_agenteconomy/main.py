import os, sys, json, sqlite3, argparse, secrets, uuid, threading
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

CONFIG_DIR = Path(os.path.expanduser("~")) / ".agent_economy"
CONFIG_FILE = CONFIG_DIR / "config.json"
DB_PATH = CONFIG_DIR / "agenteconomy.db"

def get_db():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("CREATE TABLE IF NOT EXISTS agents (agent_id TEXT PRIMARY KEY, secret_token TEXT NOT NULL, balance INTEGER NOT NULL DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS transactions (tx_id TEXT PRIMARY KEY, from_agent TEXT, to_agent TEXT, amount INTEGER NOT NULL, memo TEXT, timestamp TEXT NOT NULL)")
    conn.commit()
    return conn

def demo():
    if DB_PATH.exists(): DB_PATH.unlink()
    if CONFIG_FILE.exists(): CONFIG_FILE.unlink()
    conn = get_db()
    a1_id, a1_tok = str(uuid.uuid4()), secrets.token_hex(16)
    a2_id, a2_tok = str(uuid.uuid4()), secrets.token_hex(16)
    conn.execute("INSERT INTO agents VALUES (?,?,?)", (a1_id, a1_tok, 1000))
    conn.execute("INSERT INTO agents VALUES (?,?,?)", (a2_id, a2_tok, 500))
    conn.commit()
    # Do a transfer
    amount = 200
    tx_id = str(uuid.uuid4())
    conn.execute("UPDATE agents SET balance=balance-? WHERE agent_id=?", (amount, a1_id))
    conn.execute("UPDATE agents SET balance=balance+? WHERE agent_id=?", (amount, a2_id))
    conn.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?)",
        (tx_id, a1_id, a2_id, amount, "demo payment", datetime.now().isoformat()))
    conn.commit()
    print("\n=== AgentEconomy Demo ===")
    print(f"\n{'Agent':<12} {'Balance':>10}")
    print("-" * 25)
    for aid, bal in conn.execute("SELECT agent_id, balance FROM agents"):
        label = "Agent-A" if aid == a1_id else "Agent-B"
        print(f"{label:<12} {bal:>10} credits")
    print(f"\n{'TX':<10} {'From':<10} {'To':<10} {'Amount':>8} {'Memo'}")
    print("-" * 50)
    for tx in conn.execute("SELECT tx_id, from_agent, to_agent, amount, memo FROM transactions"):
        print(f"{tx[0][:6]}...  {'Agent-A':<10} {'Agent-B':<10} {tx[3]:>8}  {tx[4]}")
    print("\n✅ Demo complete — ledger, transfer, and tx log all working.")
    conn.close()

def init_agent():
    conn = get_db()
    agent_id, secret_token = str(uuid.uuid4()), secrets.token_hex(16)
    conn.execute("INSERT INTO agents VALUES (?,?,?)", (agent_id, secret_token, 0))
    conn.commit()
    config = {"agent_id": agent_id, "secret_token": secret_token}
    with open(CONFIG_FILE, "w") as f: json.dump(config, f, indent=2)
    print(f"✅ Agent created: {agent_id}")
    print(f"   Token: {secret_token}")
    print(f"   Config: {CONFIG_FILE}")
    conn.close()

def show_balance():
    if not CONFIG_FILE.exists():
        print("No agent configured. Run: agent-economy init"); return
    config = json.load(open(CONFIG_FILE))
    conn = get_db()
    row = conn.execute("SELECT balance FROM agents WHERE agent_id=?", (config["agent_id"],)).fetchone()
    print(f"Balance: {row[0] if row else 0} AgentCredits")
    conn.close()

def send_credits(to_agent, amount, memo):
    if not CONFIG_FILE.exists():
        print("No agent configured. Run: agent-economy init"); return
    config = json.load(open(CONFIG_FILE))
    conn = get_db()
    row = conn.execute("SELECT balance, secret_token FROM agents WHERE agent_id=?", (config["agent_id"],)).fetchone()
    if not row: print("Agent not found."); return
    balance, token = row
    if token != config["secret_token"]: print("❌ Auth failed."); return
    if balance < amount: print(f"❌ Insufficient balance: {balance} credits"); return
    to = conn.execute("SELECT agent_id FROM agents WHERE agent_id=?", (to_agent,)).fetchone()
    if not to: print(f"❌ Recipient not found: {to_agent}"); return
    tx_id = str(uuid.uuid4())
    conn.execute("UPDATE agents SET balance=balance-? WHERE agent_id=?", (amount, config["agent_id"]))
    conn.execute("UPDATE agents SET balance=balance+? WHERE agent_id=?", (amount, to_agent))
    conn.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?)",
        (tx_id, config["agent_id"], to_agent, amount, memo, datetime.now().isoformat()))
    conn.commit()
    print(f"✅ Sent {amount} credits to {to_agent[:8]}...")
    print(f"   TX: {tx_id}")
    conn.close()

class LedgerHandler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    def do_GET(self):
        conn = get_db()
        agents = conn.execute("SELECT agent_id, balance FROM agents").fetchall()
        txs = conn.execute("SELECT tx_id, from_agent, to_agent, amount, memo, timestamp FROM transactions ORDER BY timestamp DESC LIMIT 10").fetchall()
        conn.close()
        data = {
            "agents": [{"id": a[0], "balance": a[1]} for a in agents],
            "transactions": [{"tx": t[0], "from": t[1], "to": t[2], "amount": t[3], "memo": t[4], "time": t[5]} for t in txs]
        }
        body = json.dumps(data, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

def start_server(port=8765):
    server = HTTPServer(("0.0.0.0", port), LedgerHandler)
    print(f"🌐 Ledger API running on http://localhost:{port}")
    server.serve_forever()

def main():
    parser = argparse.ArgumentParser(description="AgentEconomy — Agent-to-agent credit ledger")
    parser.add_argument("--demo", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo: demo(); return

    subs = parser.add_subparsers(dest="command")
    subs.add_parser("init")
    subs.add_parser("balance")

    send_p = subs.add_parser("send")
    send_p.add_argument("to_agent")
    send_p.add_argument("amount", type=int)
    send_p.add_argument("--memo", default="payment")

    server_p = subs.add_parser("server")
    server_p.add_argument("--port", type=int, default=8765)

    args = parser.parse_args()
    if args.command == "init": init_agent()
    elif args.command == "balance": show_balance()
    elif args.command == "send": send_credits(args.to_agent, args.amount, args.memo)
    elif args.command == "server": start_server(args.port)
    else: parser.print_help()

if __name__ == "__main__":
    main()
