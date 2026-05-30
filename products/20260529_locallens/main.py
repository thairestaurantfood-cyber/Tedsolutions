import os
import sys
import sqlite3
import argparse
import json
import csv
from datetime import datetime

DB_PATH = os.path.expanduser('~/locallens.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scrapes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            analyzed BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.commit()
    conn.close()

def add_scrape(url, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scrapes (url, content)
        VALUES (?, ?)
    ''', (url, content))
    conn.commit()
    conn.close()

def list_scrapes():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, url, timestamp, analyzed FROM scrapes')
    scrapes = cursor.fetchall()
    conn.close()

    print(f"{'ID':<5}{'URL':<30}{'TIMESTAMP':<20}{'ANALYZED':<10}")
    print('-' * 65)
    for scrape in scrapes:
        print(f"{scrape[0]:<5}{scrape[1][:27]:<30}{scrape[2]:<20}{'Yes' if scrape[3] else 'No':<10}")

def generate_report(format_type='csv'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, url, timestamp, analyzed FROM scrapes')
    scrapes = cursor.fetchall()
    conn.close()

    if format_type == 'csv':
        with open('scrapes_report.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'URL', 'TIMESTAMP', 'ANALYZED'])
            for scrape in scrapes:
                writer.writerow([scrape[0], scrape[1], scrape[2], 'Yes' if scrape[3] else 'No'])
        print("CSV report generated: scrapes_report.csv")
    elif format_type == 'json':
        report = []
        for scrape in scrapes:
            report.append({
                'id': scrape[0],
                'url': scrape[1],
                'timestamp': scrape[2],
                'analyzed': 'Yes' if scrape[3] else 'No'
            })
        with open('scrapes_report.json', 'w') as jsonfile:
            json.dump(report, jsonfile, indent=4)
        print("JSON report generated: scrapes_report.json")

def send_alert(message):
    print(f"ALERT: {message}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()

    add_scrape('https://example.com/page1', 'Sample content for page 1')
    add_scrape('https://example.com/page2', 'Sample content for page 2')
    add_scrape('https://example.com/page3', 'Sample content for page 3')

    list_scrapes()

    generate_report('csv')
    generate_report('json')

    send_alert("Demo completed successfully")

def main():
    parser = argparse.ArgumentParser(description="LocalLens")
    parser.add_argument('--demo', action='store_true', help='Run demo mode')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subs = parser.add_subparsers(dest='command')

    add_parser = subs.add_parser('add', help='Add a new scrape')
    add_parser.add_argument('url', help='URL of the scrape')
    add_parser.add_argument('content', help='Content of the scrape')

    list_parser = subs.add_parser('list', help='List all scrapes')

    report_parser = subs.add_parser('report', help='Generate a report')
    report_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Output format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_scrape(args.url, args.content)
        print("Scrape added successfully")
    elif args.command == 'list':
        list_scrapes()
    elif args.command == 'report':
        generate_report(args.format)

if __name__ == "__main__":
    main()