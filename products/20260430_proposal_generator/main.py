import os
import sqlite3
import argparse
from datetime import datetime

# Path configuration
DB_PATH = os.path.expanduser("~/.jarvis/proposal_generator/data.db")

def get_db():
    """Initialize database with required tables if they don't exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create proposals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            client_name TEXT NOT NULL,
            project_description TEXT,
            budget TEXT,
            deadline TEXT,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'draft'
        )
    """)

    # Create reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            report_type TEXT NOT NULL,
            content TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (proposal_id) REFERENCES proposals (id)
        )
    """)

    # Create alerts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (proposal_id) REFERENCES proposals (id)
        )
    """)

    conn.commit()
    return conn

def add_proposal(title, client_name, project_description, budget, deadline):
    """Add a new proposal to the database."""
    conn = get_db()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO proposals
        (title, client_name, project_description, budget, deadline, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, client_name, project_description, budget, deadline, created_at))

    conn.commit()
    proposal_id = cursor.lastrowid
    conn.close()
    return proposal_id

def list_proposals(limit=None):
    """List all proposals with optional limit."""
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT id, title, client_name, budget, status FROM proposals"
    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return results

def generate_report(proposal_id, report_type):
    """Generate a report for a specific proposal."""
    conn = get_db()
    cursor = conn.cursor()

    created_at = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO reports
        (proposal_id, report_type, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (proposal_id, report_type, f"Report content for {report_type}", created_at))

    conn.commit()
    report_id = cursor.lastrowid
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Proposal Generator")
    parser.add_argument("--demo", action="store_true", help="Run demo mode with hardcoded data.")
    args = parser.parse_args()

    if args.demo:
        conn = get_db()
        cur = conn.cursor()
        # Insert hardcoded sample data
        cur.execute("INSERT OR IGNORE INTO proposals (title, client_name, project_description, budget, deadline) VALUES (?, ?, ?, ?, ?)", ("Proposal 1", "Client A", "Project Description 1", "$5000", "2026-12-31"))
        conn.commit()
        cur.execute("INSERT OR IGNORE INTO reports (proposal_id, report_type, content, created_at) VALUES (?, ?, ?, ?)", (1, "Technical Report", "Report content for Technical Report", datetime.now().isoformat()))
        conn.commit()
        # Query and print
        for row in cur.execute("SELECT * FROM proposals LIMIT 5"):
            print(row)
        for row in cur.execute("SELECT * FROM reports LIMIT 5"):
            print(row)
        conn.close()
        print("Demo complete.")
        return

    # Main logic goes here

if __name__ == "__main__":
    main()