import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def get_db():
    db_path = os.path.expanduser("~/.followup.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT,
            company TEXT,
            notes TEXT,
            created DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            date DATETIME DEFAULT CURRENT_TIMESTAMP,
            summary TEXT NOT NULL,
            followup_date DATETIME,
            done BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    ''')
    conn.commit()
    return conn

def add_contact(conn, name, email):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contacts (name, email) VALUES (?, ?)
    ''', (name, email))
    conn.commit()

def log_interaction(conn, contact_id, summary):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO interactions (contact_id, summary) VALUES (?, ?)
    ''', (contact_id, summary))
    conn.commit()

def followup_contact(conn, contact_id, days):
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE contacts
        SET notes = notes || 'Follow-up scheduled for ' || datetime(followup_date, '+%d days')
        WHERE id = ?
    ''', (contact_id,))
    conn.commit()

def today_followups(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.name, i.summary, i.followup_date
        FROM contacts c
        JOIN interactions i ON c.id = i.contact_id
        WHERE i.followup_date <= datetime('now')
    ''')
    return cursor.fetchall()

def list_contacts(conn):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM contacts
    ''')
    return cursor.fetchall()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FollowUp CLI tool to manage client conversations and set follow-up reminders.')
    parser.add_argument('--add', help='Add a new contact with name and email')
    parser.add_argument('--log', help='Log an interaction for a specific contact')
    parser.add_argument('--followup', help='Set a follow-up date for a specific contact')
    parser.add_argument('--today', action='store_true', help='Show all contacts with follow-up dates due today')
    parser.add_argument('--list', action='store_true', help='List all contacts')
    parser.add_argument('--demo', action='store_true', help='Run demo mode with hardcoded data')

    args = parser.parse_args()

    conn = get_db()

    if args.demo:
        # Clear stale demo data first
        conn.execute("DELETE FROM interactions")
        conn.execute("DELETE FROM contacts")
        conn.commit()
        # Seed fresh demo data
        conn.execute("INSERT INTO contacts (name,email,phone,company,notes,created) VALUES (?,?,?,?,?,date('now'))",
            ("John Doe","john@example.com","+66-81-234-5678","Acme Co","Met at BNI Phuket"))
        conn.execute("INSERT INTO contacts (name,email,phone,company,notes,created) VALUES (?,?,?,?,?,date('now'))",
            ("Jane Smith","jane@example.com","+66-89-876-5432","Sea Tours","Referral from David"))
        conn.execute("INSERT INTO contacts (name,email,phone,company,notes,created) VALUES (?,?,?,?,?,date('now'))",
            ("David Lee","david@example.com","+66-76-123-4567","Lee Agency","Cold outreach"))
        conn.commit()
        # Add interactions using actual inserted IDs
        import datetime as _dt
        today = _dt.date.today().isoformat()
        yesterday = (_dt.date.today() - _dt.timedelta(days=1)).isoformat()
        ids = [r[0] for r in conn.execute("SELECT id FROM contacts ORDER BY id").fetchall()]
        conn.execute("INSERT INTO interactions (contact_id,date,summary,followup_date,done) VALUES (?,?,?,?,0)",
            (ids[0],yesterday,"Discussed website project budget $3,000",today))
        conn.execute("INSERT INTO interactions (contact_id,date,summary,followup_date,done) VALUES (?,?,?,?,0)",
            (ids[1],yesterday,"Demo call went well, sending proposal",today))
        conn.execute("INSERT INTO interactions (contact_id,date,summary,followup_date,done) VALUES (?,?,?,?,0)",
            (ids[2],yesterday,"Left voicemail","2026-05-15"))
        conn.commit()
        print()
        print("=== FOLLOWUP DEMO ===")
        print(f"{'Contact':20s} {'Company':15s} {'Last Note':35s} {'Due'}")
        print("-"*75)
        rows = conn.execute("""
            SELECT c.name, c.company, i.summary, i.followup_date
            FROM interactions i JOIN contacts c ON i.contact_id=c.id
            WHERE i.followup_date <= ? ORDER BY i.followup_date
        """, (today,)).fetchall()
        for r in rows:
            flag = "🔴 TODAY" if r[3] == today else "🟡"
            print(f"  {r[0]:20s} {(r[1] or ''):15s} {r[2]:35s} {flag}")
        print()
        print(f"  {len(rows)} follow-ups due today | Run --today to see live data")

    elif args.add:
        if args.add.split()[0] and args.add.split()[1]:
            add_contact(conn, *args.add.split())
        else:
            print('Usage: --add NAME EMAIL')

    elif args.log:
        if args.log.split()[0] and args.log.split()[1]:
            log_interaction(conn, int(args.log.split()[0]), args.log.split()[1])
        else:
            print('Usage: --log CONTACT_ID SUMMARY')

    elif args.followup:
        if args.followup.split()[0] and args.followup.split()[1]:
            followup_contact(conn, int(args.followup.split()[0]), int(args.followup.split()[1]))
        else:
            print('Usage: --followup CONTACT_ID DAYS')

    elif args.today:
        for contact in today_followups(conn):
            print(f'Contact: {contact[0]}, Summary: {contact[1]}, Follow-up Date: {contact[2]}')

    elif args.list:
        contacts = list_contacts(conn)
        for contact in contacts:
            print(contact)

    conn.close()