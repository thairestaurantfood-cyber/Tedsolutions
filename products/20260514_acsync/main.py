#!/usr/bin/env python3
"""
AC Sync - HTTP server for AC wallet ledger
Endpoints: POST /wallet/create, GET /wallet/balance, POST /wallet/send, GET /wallet/history, POST /wallet/faucet
"""

import argparse, json, os, sqlite3, threading, time, urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

DB = os.path.expanduser("~/.jarvis/ac_wallet.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB)), exist_ok=True)
    with sqlite3.connect(DB) as conn:
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

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/wallet/create': self.create_wallet()
        elif self.path == '/wallet/send': self.send_ac()
        elif self.path == '/wallet/faucet': self.faucet()
        else: self.error(404)

    def do_GET(self):
        if self.path.startswith('/wallet/balance'): self.get_balance()
        elif self.path.startswith('/wallet/history'): self.get_history()
        else: self.error(404)

    def create_wallet(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        agent = data.get('agent_id')
        if not agent: return self.error(400, 'agent_id required')
        try:
            with sqlite3.connect(DB) as conn:
                conn.execute('INSERT INTO wallets (agent_id, public_key, balance, created_at) VALUES (?, ?, ?, datetime(\'now\'))',
                             (agent, f'pubkey_{agent}', 0))
                self.respond(201, {'message': f'Wallet created for {agent} with 0 AC.'})
        except sqlite3.IntegrityError:
            self.error(409, f'Wallet for {agent} already exists')

    def send_ac(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        frm, to, amt = data.get('from_agent'), data.get('to_agent'), data.get('amount')
        if not all([frm, to, amt]): return self.error(400, 'from_agent, to_agent, amount required')
        try: amt = int(amt)
        except: return self.error(400, 'amount must be integer')
        if amt <= 0: return self.error(400, 'Amount must be positive')
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute('SELECT balance FROM wallets WHERE agent_id = ?', (frm,))
            sender = c.fetchone()
            if not sender: return self.error(404, f'Sender {frm} not found')
            if sender[0] < amt: return self.error(400, f'Insufficient: {sender[0]} < {amt}')
            c.execute('SELECT agent_id FROM wallets WHERE agent_id = ?', (to,))
            if not c.fetchone(): return self.error(404, f'Recipient {to} not found')
            c.execute('UPDATE wallets SET balance = balance - ? WHERE agent_id = ?', (amt, frm))
            c.execute('UPDATE wallets SET balance = balance + ? WHERE agent_id = ?', (amt, to))
            c.execute('INSERT INTO transactions (from_agent, to_agent, amount, timestamp) VALUES (?, ?, ?, datetime(\'now\'))',
                      (frm, to, amt))
            self.respond(200, {'message': f'Sent {amt} AC from {frm} to {to}.'})

    def faucet(self):
        length = int(self.headers.get('Content-Length', 0))
        data = json.loads(self.rfile.read(length)) if length else {}
        agent, amt = data.get('agent_id'), data.get('amount', 1000)
        if not agent: return self.error(400, 'agent_id required')
        try: amt = int(amt)
        except: return self.error(400, 'amount must be integer')
        if amt <= 0: return self.error(400, 'Amount must be positive')
        with sqlite3.connect(DB) as conn:
            conn.execute('INSERT OR IGNORE INTO wallets (agent_id, public_key, balance, created_at) VALUES (?, ?, ?, datetime(\'now\'))',
                         (agent, f'pubkey_{agent}', 0))
            conn.execute('UPDATE wallets SET balance = balance + ? WHERE agent_id = ?', (amt, agent))
            self.respond(200, {'message': f'Faucet funded {agent} with {amt} AC.'})

    def get_balance(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        agent = qs.get('agent_id', [None])[0]
        if not agent: return self.error(400, 'agent_id required')
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute('SELECT balance FROM wallets WHERE agent_id = ?', (agent,))
            row = c.fetchone()
            if not row: return self.error(404, f'No wallet for {agent}')
            self.respond(200, {'agent_id': agent, 'balance': row[0]})

    def get_history(self):
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        agent = qs.get('agent_id', [None])[0]
        if not agent: return self.error(400, 'agent_id required')
        with sqlite3.connect(DB) as conn:
            c = conn.cursor()
            c.execute('''SELECT from_agent, to_agent, amount, timestamp
                         FROM transactions WHERE from_agent = ? OR to_agent = ?
                         ORDER BY id DESC''', (agent, agent))
            rows = c.fetchall()
            self.respond(200, {'agent_id': agent, 'history': [{'from': f, 'to': t, 'amount': a, 'time': ts} for f, t, a, ts in rows]})

    def respond(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def error(self, code, msg=''):
        self.respond(code, {'error': msg} if msg else {})

    def log_message(self, fmt, *args):
        if not getattr(self.server, 'demo', False):
            return super().log_message(fmt, *args)

def run_server(port=8080, demo=False):
    init_db()
    server = HTTPServer(('localhost', port), Handler)
    server.demo = demo
    print(f'🚀 AC Sync server on http://localhost:{port}')
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

def demo():
    import subprocess, time
    def run(cmd):
        try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
        except: return 'Error'

    # Clean DB before demo
    if os.path.exists(DB):
        os.remove(DB)

    # Start server in background
    import threading
    server_thread = threading.Thread(target=run_server, args=(8080, True))
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # let server start

    base = 'http://localhost:8080'

    # Use urllib.request for reliable HTTP calls
    import urllib.request, urllib.error
    def http_request(method, path, data=None):
        url = f'{base}{path}'
        headers = {'Content-Type': 'application/json'}
        data_bytes = None
        if data is not None:
            data_bytes = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return e.read().decode('utf-8')
        except Exception as e:
            return f'Error: {e}'

    print('=== AC Sync Demo ===\n')
    print('1. Create wallets')
    print(http_request('POST', '/wallet/create', {'agent_id': 'alice'}))
    print(http_request('POST', '/wallet/create', {'agent_id': 'bob'}))
    print()
    print('2. Initial balances')
    print(http_request('GET', '/wallet/balance?agent_id=alice'))
    print(http_request('GET', '/wallet/balance?agent_id=bob'))
    print()
    print('3. Fund via faucet (100 AC each)')
    print(http_request('POST', '/wallet/faucet', {'agent_id': 'alice', 'amount': 100}))
    print(http_request('POST', '/wallet/faucet', {'agent_id': 'bob', 'amount': 100}))
    print()
    print('4. Balances after faucet')
    print(http_request('GET', '/wallet/balance?agent_id=alice'))
    print(http_request('GET', '/wallet/balance?agent_id=bob'))
    print()
    print('5. Send 30 AC from alice to bob')
    print(http_request('POST', '/wallet/send', {'from_agent': 'alice', 'to_agent': 'bob', 'amount': 30}))
    print()
    print('6. Balances after transfer')
    print(http_request('GET', '/wallet/balance?agent_id=alice'))
    print(http_request('GET', '/wallet/balance?agent_id=bob'))
    print()
    print('7. Alice history')
    print(http_request('GET', '/wallet/history?agent_id=alice'))
    print()
    print('8. Bob history')
    print(http_request('GET', '/wallet/history?agent_id=bob'))
    print()
    print('✅ Demo done. Server stopping.')
    time.sleep(2)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--demo', action='store_true', help='Run demo')
    p.add_argument('--port', type=int, default=8080, help='Port (default: 8080)')
    a = p.parse_args()
    if a.demo: demo()
    else: run_server(port=a.port)

if __name__ == '__main__': main()