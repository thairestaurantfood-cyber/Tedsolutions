#!/usr/bin/env python3
"""
AC Market - Agent Service Marketplace
List, browse, buy services with AC payments. stdlib+sqlite, <200 lines.
"""

import argparse, os, sqlite3
WALLET_DB = os.path.expanduser("~/.jarvis/ac_wallet.db")
MARKET_DB = os.path.expanduser("~/.jarvis/ac_market.db")

def init_wallet():
    os.makedirs(os.path.dirname(os.path.abspath(WALLET_DB)), exist_ok=True)
    with sqlite3.connect(WALLET_DB) as conn:
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

def init_market():
    os.makedirs(os.path.dirname(os.path.abspath(MARKET_DB)), exist_ok=True)
    with sqlite3.connect(MARKET_DB) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_agent TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            price_ac INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            sold_to TEXT,
            sold_at TEXT,
            FOREIGN KEY (seller_agent) REFERENCES wallets(agent_id),
            FOREIGN KEY (sold_to) REFERENCES wallets(agent_id))''')

def wallet_create(agent):
    with sqlite3.connect(WALLET_DB) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO wallets (agent_id, public_key, balance, created_at) VALUES (?, ?, ?, datetime('now'))",
                      (agent, f"pubkey_{agent}", 0))
            conn.commit()
            return f"Wallet created for agent '{agent}' with starting balance 0 AC."
        except sqlite3.IntegrityError:
            return f"Wallet for agent '{agent}' already exists."

def wallet_balance(agent):
    with sqlite3.connect(WALLET_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (agent,))
        r = c.fetchone()
        return f"Balance for '{agent}': {r[0]} AC" if r else f"No wallet for '{agent}'. Create one."

def wallet_send(fr, to, amt):
    if amt <= 0: return "Amount must be positive."
    with sqlite3.connect(WALLET_DB) as conn:
        c = conn.cursor()
        c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (fr,))
        s = c.fetchone()
        if not s: return f"Sender '{fr}' does not exist."
        if s[0] < amt: return f"Insufficient: {s[0]} AC < {amt} AC"
        c.execute("SELECT agent_id FROM wallets WHERE agent_id = ?", (to,))
        if not c.fetchone(): return f"Recipient '{to}' does not exist."
        c.execute("UPDATE wallets SET balance = balance - ? WHERE agent_id = ?", (amt, fr))
        c.execute("UPDATE wallets SET balance = balance + ? WHERE agent_id = ?", (amt, to))
        c.execute("INSERT INTO transactions (from_agent, to_agent, amount, timestamp) VALUES (?, ?, ?, datetime('now'))",
                  (fr, to, amt))
        conn.commit()
        return f"Sent {amt} AC from '{fr}' to '{to}'."

def list_svc(seller, name, desc, price):
    with sqlite3.connect(MARKET_DB) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO services (seller_agent, name, description, price_ac, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                  (seller, name, desc, price))
        conn.commit()
        return f"Service listed ID {c.lastrowid}: '{name}' for {price} AC by '{seller}'."

def browse_svc(unsold=True):
    with sqlite3.connect(MARKET_DB) as conn:
        c = conn.cursor()
        if unsold:
            c.execute("""SELECT id, seller_agent, name, description, price_ac, created_at
                         FROM services WHERE sold_to IS NULL ORDER BY id""")
        else:
            c.execute("""SELECT id, seller_agent, name, description, price_ac, created_at, sold_to, sold_at
                         FROM services ORDER BY id""")
        rows = c.fetchall()
        if not rows: return "No services." if unsold else "No services listed."
        out = ["Available Services:" if unsold else "All Services:", "-"*60]
        for r in rows:
            if unsold:
                sid, seller, name, desc, price, created = r
                out.append(f"ID:{sid} {name} | {price} AC | by {seller}")
                out.append(f"  {desc}")
                out.append(f"  Listed: {created}")
            else:
                sid, seller, name, desc, price, created, sold_to, sold_at = r
                status = "SOLD" if sold_to else "AVAILABLE"
                out.append(f"ID:{sid} {name} | {price} AC | {status} | by {seller}")
                out.append(f"  {desc}")
                out.append(f"  Listed: {created}")
                if sold_to: out.append(f"  Sold to: {sold_to} at {sold_at}")
            out.append("")
        return "\n".join(out)

def buy_svc(buyer, sid):
    with sqlite3.connect(WALLET_DB) as wconn, sqlite3.connect(MARKET_DB) as mconn:
        wc = wconn.cursor()
        mc = mconn.cursor()
        mc.execute("SELECT seller_agent, name, price_ac FROM services WHERE id = ? AND sold_to IS NULL", (sid,))
        svc = mc.fetchone()
        if not svc: return f"Service ID {sid} not found or sold."
        seller, name, price = svc
        wc.execute("SELECT balance FROM wallets WHERE agent_id = ?", (buyer,))
        b = wc.fetchone()
        if not b: return f"Buyer '{buyer}' does not exist."
        if b[0] < price: return f"Insufficient: {b[0]} AC < {price} AC"
        wc.execute("SELECT agent_id FROM wallets WHERE agent_id = ?", (seller,))
        if not wc.fetchone(): return f"Seller '{seller}' does not exist."
        pay = wallet_send(buyer, seller, price)
        if not pay.startswith("Sent"): return pay
        mc.execute("UPDATE services SET sold_to = ?, sold_at = datetime('now') WHERE id = ?", (buyer, sid))
        mconn.commit()
        return f"Service '{name}' bought for {price} AC. {pay}"

def demo():
    for db in (WALLET_DB, MARKET_DB):
        if os.path.exists(db): os.remove(db)
    init_wallet(); init_market()
    print("=== AC Market Demo ===\n")
    print(wallet_create("alice")); print(wallet_create("bob"))
    with sqlite3.connect(WALLET_DB) as conn:
        c = conn.cursor()
        c.execute("UPDATE wallets SET balance = 50 WHERE agent_id = ?", ("alice",))
        c.execute("UPDATE wallets SET balance = 30 WHERE agent_id = ?", ("bob",))
        conn.commit()
    print("\n--- Initial Balances ---")
    print(wallet_balance("alice")); print(wallet_balance("bob"))
    print("\n--- Alice Lists Service ---")
    print(list_svc("alice", "Text Summarization", "I summarize text", 10))
    print("\n--- Browse Services ---")
    print(browse_svc())
    print("\n--- Bob Buys Service ---")
    print(buy_svc("bob", 1))
    print("\n--- Balances After ---")
    print(wallet_balance("alice")); print(wallet_balance("bob"))
    print("\n--- Market After ---")
    print(browse_svc(False))

def main():
    p = argparse.ArgumentParser(prog="ac-market")
    s = p.add_subparsers(dest="cmd")
    # list
    ls = s.add_parser("list-service", help="List a service")
    ls.add_argument("seller"); ls.add_argument("name"); ls.add_argument("description"); ls.add_argument("price", type=int)
    # browse
    bs = s.add_parser("browse-services", help="Browse services")
    bs.add_argument("--all", action="store_true", help="Show all")
    # buy
    by = s.add_parser("buy-service", help="Buy a service")
    by.add_argument("buyer"); by.add_argument("service_id", type=int)
    p.add_argument("--demo", action="store_true", help="Run demo")
    a = p.parse_args()
    if a.demo: demo()
    elif a.cmd == "list-service": print(list_svc(a.seller, a.name, a.description, a.price))
    elif a.cmd == "browse-services": print(browse_svc(not a.all))
    elif a.cmd == "buy-service": print(buy_svc(a.buyer, a.service_id))
    else: p.parse_args(["--help"])

if __name__ == "__main__":
    main()