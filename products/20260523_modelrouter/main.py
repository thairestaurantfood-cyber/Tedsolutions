import os, sys, sqlite3, argparse, json
from datetime import datetime

# --- Constants ---
DB_ROOT = os.path.expanduser('~/.jarvis/')
DB_DIR = os.path.join(DB_ROOT, 'modelrouter')
DB_PATH = os.path.join(DB_DIR, 'modelrouter.db')

# --- DB Helpers ---
def _db_conn():
    os.makedirs(DB_DIR, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = _db_conn()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, url TEXT NOT NULL, provider TEXT NOT NULL, context_window INTEGER, capabilities TEXT, description TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS routes (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, model_name TEXT NOT NULL, priority INTEGER DEFAULT 0, FOREIGN KEY (model_name) REFERENCES models(name) ON DELETE CASCADE)')
    conn.commit()
    conn.close()

def add_model(name, url, provider, context_window=None, capabilities=None, description=None):
    conn = _db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO models (name, url, provider, context_window, capabilities, description) VALUES (?, ?, ?, ?, ?, ?)',
                 (name, url, provider, context_window, capabilities, description))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def list_models():
    conn = _db_conn()
    c = conn.cursor()
    c.execute('SELECT name, provider, context_window, capabilities, description FROM models')
    rows = c.fetchall()
    conn.close()
    return rows

def add_route(name, model_name, priority=0):
    conn = _db_conn()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO routes (name, model_name, priority) VALUES (?, ?, ?)',
                 (name, model_name, priority))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()

def list_routes():
    conn = _db_conn()
    c = conn.cursor()
    c.execute('''SELECT r.name, r.priority, m.name, m.provider
                 FROM routes r JOIN models m ON r.model_name = m.name
                 ORDER BY r.priority DESC''')
    rows = c.fetchall()
    conn.close()
    return rows

def analyze_prompt(prompt):
    conn = _db_conn()
    c = conn.cursor()

    c.execute('SELECT name, capabilities FROM models')
    models = c.fetchall()

    keywords = ['code', 'text', 'chat', 'reasoning']
    scores = []
    for model_name, caps in models:
        score = 0
        if caps:
            for kw in keywords:
                if kw in caps.lower():
                    score += 1
        scores.append((model_name, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    top_models = [name for name, score in scores[:3]]
    conn.close()
    return top_models

def demo():
    init_db()
    add_model('llama3', 'http://localhost:11434', 'ollama', 8192, 'chat reasoning', 'General purpose model')
    add_model('phi3', 'http://localhost:11434', 'ollama', 4096, 'code text', 'Small efficient model')
    add_route('default', 'llama3', 10)
    add_route('fast', 'phi3', 5)

    print("\n=== Models ===")
    for row in list_models():
        print(f"{row[0]:<15} {row[1]:<15} {str(row[2]):<10} {row[3] or '':<20} {row[4] or ''}")

    print("\n=== Routes ===")
    for row in list_routes():
        print(f"{row[0]:<15} {str(row[1]):<5} {row[2]:<15} {row[3]:<15}")

    print("\n=== Top Models for Prompt ===")
    top = analyze_prompt("Explain quantum computing")
    print("Suggested:", ", ".join(top))

def main():
    if '--demo' in sys.argv:
        demo()
        return

    parser = argparse.ArgumentParser(description='Model Router CLI')
    subparsers = parser.add_subparsers(dest='command')

    models_parser = subparsers.add_parser('models', help='Manage models')
    models_parser.add_argument('action', choices=['list'])
    models_parser.add_argument('--add', nargs=3, metavar=('NAME', 'URL', 'PROVIDER'))

    routes_parser = subparsers.add_parser('routes', help='Manage routes')
    routes_parser.add_argument('action', choices=['list'])
    routes_parser.add_argument('--add', nargs=2, metavar=('NAME', 'MODEL'))

    args = parser.parse_args()

    if args.command == 'models':
        if args.action == 'list':
            for row in list_models():
                print(f"{row[0]:<15} {row[1]:<15} {str(row[2]):<10} {row[3] or '':<20} {row[4] or ''}")
    elif args.command == 'routes':
        if args.action == 'list':
            for row in list_routes():
                print(f"{row[0]:<15} {str(row[1]):<5} {row[2]:<15} {row[3]:<15}")
        elif args.add:
            add_route(args.add[0], args.add[1])

if __name__ == '__main__':
    main()