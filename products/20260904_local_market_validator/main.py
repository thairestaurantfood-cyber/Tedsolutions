import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/local_market_validator.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            contact TEXT,
            date_added TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            demand_score INTEGER DEFAULT 0,
            alert_status TEXT DEFAULT 'none'
        )
    ''')
    conn.commit()
    conn.close()

def calculate_demand_score(description):
    keywords = ['partner', 'investor', 'collaboration', 'opportunity', 'business', 'startup', 'entrepreneur']
    score = 0
    for keyword in keywords:
        if keyword.lower() in description.lower():
            score += 1
    return score

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    demo_data = [
        ('Facebook', 'Coffee Shop', 'Looking for a coffee shop partner', 'Phuket', 'contact@email.com', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 2, 'high'),
        ('Google Maps', 'Bakery', 'New bakery opening soon', 'Phuket', 'info@bakery.com', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, 'medium'),
        ('Local Business Directory', 'Restaurant', 'Seeking restaurant investors', 'Phuket', 'restaurant@invest.com', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 3, 'high')
    ]

    cursor.executemany('''
        INSERT INTO opportunities (source, title, description, location, contact, date_added, last_updated, demand_score, alert_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', demo_data)

    conn.commit()

    cursor.execute('SELECT * FROM opportunities')
    rows = cursor.fetchall()

    print(f"{'ID':<5}{'Source':<10}{'Title':<15}{'Description':<25}{'Location':<10}{'Contact':<20}{'Date Added':<20}{'Last Updated':<20}{'Demand Score':<15}{'Alert Status':<15}")
    print("-" * 150)
    for row in rows:
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<15}{row[3]:<25}{row[4]:<10}{row[5]:<20}{row[6]:<20}{row[7]:<20}{row[8]:<15}{row[9]:<15}")

    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="Local Market Validator")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add subparsers here for other commands if needed

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

if __name__ == "__main__":
    main()