#!/usr/bin/env python3
import argparse, os, sqlite3
from pathlib import Path

DB_PATH = os.path.expanduser("~/.jarvis/ac_wallet.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    conn.commit()
    conn.close()

def wallet_create(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    pubkey = f"pubkey_{agent_id}"
    try:
        c.execute("INSERT INTO wallets (agent_id, public_key, balance, created_at) VALUES (?, ?, ?, datetime('now'))",
                  (agent_id, pubkey, 0))
        conn.commit()
        print(f"Wallet created for agent '{agent_id}' with starting balance 0 AC.")
    except sqlite3.IntegrityError:
        print(f"Wallet for agent '{agent_id}' already exists.")
    finally:
        conn.close()

def wallet_balance(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (agent_id,))
    row = c.fetchone()
    conn.close()
    if row is None:
        print(f"No wallet found for agent '{agent_id}'. Create one with 'ac-wallet create'.")
        return
    print(f"Balance for '{agent_id}': {row[0]} AC")

def wallet_send(from_agent, to_agent, amount):
    if amount <= 0:
        print("Amount must be positive.")
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        c = conn.cursor()
        c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (from_agent,))
        sender_row = c.fetchone()
        if sender_row is None:
            print(f"Sender wallet '{from_agent}' does not exist.")
            return
        sender_balance = sender_row[0]
        if sender_balance < amount:
            print(f"Insufficient balance: {sender_balance} AC < {amount} AC")
            return
        c.execute("SELECT agent_id FROM wallets WHERE agent_id = ?", (to_agent,))
        if c.fetchone() is None:
            print(f"Recipient wallet '{to_agent}' does not exist.")
            return
        c.execute("UPDATE wallets SET balance = balance - ? WHERE agent_id = ?", (amount, from_agent))
        c.execute("UPDATE wallets SET balance = balance + ? WHERE agent_id = ?", (amount, to_agent))
        c.execute("INSERT INTO transactions (from_agent, to_agent, amount, timestamp) VALUES (?, ?, ?, datetime('now'))",
                  (from_agent, to_agent, amount))
        conn.commit()
        print(f"Sent {amount} AC from '{from_agent}' to '{to_agent}'.")
    finally:
        conn.close()

def wallet_history(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT from_agent, to_agent, amount, timestamp
                 FROM transactions WHERE from_agent = ? OR to_agent = ?
                 ORDER BY id DESC""", (agent_id, agent_id))
    rows = c.fetchall()
    conn.close()
    if not rows:
        print(f"No transactions for agent '{agent_id}'.")
        return
    print(f"Transaction history for '{agent_id}':")
    print("From -> To | Amount | Timestamp")
    print("-" * 40)
    for from_a, to_a, amt, ts in rows:
        print(f"{from_a} -> {to_a} | {amt:>6} AC | {ts}")

def faucet_claim(agent_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT balance FROM wallets WHERE agent_id = ?", (agent_id,))
    row = c.fetchone()
    if row is None:
        print(f"No wallet for '{agent_id}'. Create one first.")
        conn.close()
        return
    c.execute("UPDATE wallets SET balance = balance + 100 WHERE agent_id = ?", (agent_id,))
    c.execute("INSERT INTO transactions (from_agent, to_agent, amount, timestamp) VALUES (?, ?, ?, datetime('now'))",
              ("faucet", agent_id, 100))
    conn.commit()
    conn.close()
    print(f"Faucet dispensed 100 AC to '{agent_id}'. New balance: {row[0] + 100} AC")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    alice, bob = "alice", "bob"
    wallet_create(alice); wallet_create(bob)
    faucet_claim(alice); faucet_claim(bob)
    print("\n=== Initial Balances ===")
    wallet_balance(alice); wallet_balance(bob)
    print("\n=== Sending 50 AC from Alice to Bob ===")
    wallet_send(alice, bob, 50)
    print("\n=== Balances After Transfer ===")
    wallet_balance(alice); wallet_balance(bob)
    print("\n=== Alice's Transaction History ===")
    wallet_history(alice)
    print("\n=== Bob's Transaction History ===")
    wallet_history(bob)

def main():
    parser = argparse.ArgumentParser(prog="ac-wallet", description="Agent Coin wallet CLI")
    subparsers = parser.add_subparsers(dest="command")
    p_create = subparsers.add_parser("create", help="Create a new wallet")
    p_create.add_argument("agent_id")
    p_bal = subparsers.add_parser("balance", help="Check wallet balance")
    p_bal.add_argument("agent_id")
    p_send = subparsers.add_parser("send", help="Send AC to another agent")
    p_send.add_argument("from_agent"); p_send.add_argument("to_agent"); p_send.add_argument("amount", type=int)
    p_hist = subparsers.add_parser("history", help="Show transaction history")
    p_hist.add_argument("agent_id")
    p_faucet = subparsers.add_parser("faucet", help="Claim AC from the faucet")
    p_faucet.add_argument("agent_id")
    parser.add_argument("--demo", action="store_true", help="Run a demo with two agents and print results")
    # Use parse_known_args to separate known args (like --demo) from unknown (subcommand and its args)
    args, unknown = parser.parse_known_args()
    if args.demo:
        demo()
        return
    # If not demo, we expect a subcommand. The unknown list will contain the subcommand and its args.
    # We need to parse them again with the subparsers.
    if unknown:
        # Re-parse the unknown arguments with the subparsers
        subparser = argparse.ArgumentParser()
        subparser.add_argument('command', choices=['create', 'balance', 'send', 'history', 'faucet'])
        subparser.add_argument('agent_id', nargs='?')
        subparser.add_argument('to_agent', nargs='?')
        subparser.add_argument('amount', nargs='?', type=int)
        # We cannot easily reuse the subparsers, so we'll just dispatch based on the first unknown.
        # Simpler: if unknown is not empty, treat the first as command and parse accordingly.
        # But we already have the subparsers defined; we can use parser.parse_args(unknown) if we reset.
        # Let's just do a simple dispatch.
        if not unknown:
            parser.print_help()
            return
        cmd = unknown[0]
        if cmd == "create":
            if len(unknown) < 2:
                print("error: agent_id required")
                return
            wallet_create(unknown[1])
        elif cmd == "balance":
            if len(unknown) < 2:
                print("error: agent_id required")
                return
            wallet_balance(unknown[1])
        elif cmd == "send":
            if len(unknown) < 4:
                print("error: from_agent to_agent amount required")
                return
            wallet_send(unknown[1], unknown[2], int(unknown[3]))
        elif cmd == "history":
            if len(unknown) < 2:
                print("error: agent_id required")
                return
            wallet_history(unknown[1])
        elif cmd == "faucet":
            if len(unknown) < 2:
                print("error: agent_id required")
                return
            faucet_claim(unknown[1])
        else:
            parser.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()