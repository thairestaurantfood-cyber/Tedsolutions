import os
import sys
import sqlite3
import argparse
import datetime
import pathlib
import json

# --- Constants ---
JARVIS_BASE_DIR = os.path.expanduser('~/.jarvis')
RAGLITE_APP_SUBDIR = 'raglite'
DB_FILE_NAME = 'raglite.db'

def _get_app_dir():
    """Returns the path to the RagLite application directory."""
    app_dir = os.path.join(JARVIS_BASE_DIR, RAGLITE_APP_SUBDIR)
    return app_dir

def _get_db_path():
    """Returns the full path to the SQLite database file."""
    app_dir = _get_app_dir()
    db_path = os.path.join(app_dir, DB_FILE_NAME)
    return db_path

def _ensure_app_dir_exists():
    """Ensures the application directory exists."""
    app_dir = _get_app_dir()
    os.makedirs(app_dir, exist_ok=True)

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    _ensure_app_dir_exists()
    db_path = _get_db_path()
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    embedding TEXT NOT NULL,
    FOREIGN KEY(doc_id) REFERENCES documents(id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_type TEXT NOT NULL,
    data TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
    )
    ''')
    conn.commit()
    conn.close()

def demo():
    """Offline demo that creates test data and shows reports functionality."""
    db_path = _get_db_path()
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert test documents with all fields populated
    cursor.execute('INSERT INTO documents (content, metadata) VALUES (?, ?)',
                  ("Invoice #INV-001 from ABC Corp", json.dumps({"source": "invoice", "amount": 1250.00})))
    cursor.execute('INSERT INTO documents (content, metadata) VALUES (?, ?)',
                  ("Meeting notes from client call", json.dumps({"source": "meeting", "client": "XYZ Ltd"})))
    cursor.execute('INSERT INTO documents (content, metadata) VALUES (?, ?)',
                  ("Product specs for Widget X", json.dumps({"source": "specs", "version": "1.2"})))

    # Insert test embeddings
    cursor.execute('INSERT INTO embeddings (doc_id, embedding) VALUES (?, ?)',
                  (1, json.dumps([0.1, 0.2, 0.3])))
    cursor.execute('INSERT INTO embeddings (doc_id, embedding) VALUES (?, ?)',
                  (2, json.dumps([0.4, 0.5, 0.6])))
    cursor.execute('INSERT INTO embeddings (doc_id, embedding) VALUES (?, ?)',
                  (3, json.dumps([0.7, 0.8, 0.9])))

    # Generate test reports
    cursor.execute('INSERT INTO reports (report_type, data, status) VALUES (?, ?, ?)',
                  ("term_frequency", json.dumps({"terms": {"invoice": 1, "meeting": 1, "specs": 1}}), "completed"))
    cursor.execute('INSERT INTO reports (report_type, data, status) VALUES (?, ?, ?)',
                  ("document_summary", json.dumps({"total_docs": 3, "sources": ["invoice", "meeting", "specs"]}), "completed"))

    conn.commit()

    # Print formatted table for documents
    print(f"{'ID':<5} {'Content':<40} {'Source':<15} {'Amount':<10}")
    print("-" * 80)
    for row in cursor.execute("SELECT id, content, metadata FROM documents"):
        metadata = json.loads(row[2])
        source = metadata.get("source", "unknown")
        amount = metadata.get("amount", "")
        print(f"{row[0]:<5} {row[1][:37]:<40} {source:<15} {str(amount):<10}")

    # Print formatted table for reports
    print("\n" + f"{'ID':<5} {'Report Type':<20} {'Status':<12} {'Total Docs':<12}")
    print("-" * 60)
    for row in cursor.execute("SELECT id, report_type, status, data FROM reports"):
        data = json.loads(row[3])
        total_docs = data.get("total_docs", "N/A")
        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<12} {str(total_docs):<12}")

    conn.close()
    print("\nDemo complete.")

def main():
    if '--demo' in sys.argv:
        demo()
        return

    parser = argparse.ArgumentParser(description="RagLite - Lightweight RAG system for document processing")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')
    parser_init = subparsers.add_parser('init', help='Initialize database')
    parser_add = subparsers.add_parser('add', help='Add document to database')
    parser_add.add_argument('file', nargs='?', help='File to add (optional)')
    parser_search = subparsers.add_parser('search', help='Search documents')
    parser_search.add_argument('query', nargs='?', help='Search query')
    parser_report = subparsers.add_parser('report', help='Generate report')
    parser_report.add_argument('type', nargs='?', help='Report type (term_frequency, document_summary)')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'init':
        init_db()
        print("Database initialized.")
    elif args.command == 'add':
        _ensure_app_dir_exists()
        init_db()
        db_path = _get_db_path()
        if args.file and os.path.exists(args.file):
            with open(args.file, 'r', encoding='utf-8') as f:
                content = f.read()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO documents (content, metadata) VALUES (?, ?)',
                          (content, json.dumps({"source": os.path.basename(args.file)})))
            conn.commit()
            conn.close()
            print(f"Added {args.file} to database.")
        else:
            print("No file provided or file not found.")
    elif args.command == 'search':
        db_path = _get_db_path()
        if not os.path.exists(db_path):
            print("Database not found. Run 'raglite init' first.")
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if args.query:
            cursor.execute("SELECT id, content, metadata FROM documents WHERE content LIKE ?", 
                          (f"%{args.query}%",))
        else:
            cursor.execute("SELECT id, content, metadata FROM documents")
        rows = cursor.fetchall()
        if rows:
            print(f"{'ID':<5} {'Content':<50} {'Source':<15}")
            print("-" * 80)
            for row in rows:
                metadata = json.loads(row[2])
                source = metadata.get("source", "unknown")
                content = row[1][:47] + "..." if len(row[1]) > 50 else row[1]
                print(f"{row[0]:<5} {content:<50} {source:<15}")
        else:
            print("No documents found.")
        conn.close()
    elif args.command == 'report':
        db_path = _get_db_path()
        if not os.path.exists(db_path):
            print("Database not found. Run 'raglite init' first.")
            return
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if args.type:
            cursor.execute("SELECT id, report_type, data, status, generated_at FROM reports WHERE report_type = ?", 
                          (args.type,))
        else:
            cursor.execute("SELECT id, report_type, data, status, generated_at FROM reports")
        rows = cursor.fetchall()
        if rows:
            print(f"{'ID':<5} {'Type':<20} {'Status':<12} {'Generated':<20}")
            print("-" * 60)
            for row in rows:
                print(f"{row[0]:<5} {row[1]:<20} {row[2]:<12} {row[4]:<20}")
        else:
            print("No reports found.")
        conn.close()
    else:
        print(f"Unknown command: {args.command}")

if __name__ == "__main__":
    main()