import os
import sys
import sqlite3
import argparse
import csv
from datetime import datetime

DB_PATH = os.path.expanduser('~/signalscout.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_trend(source, title, url, score):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO trends (source, title, url, score)
        VALUES (?, ?, ?, ?)
    ''', (source, title, url, score))
    conn.commit()
    conn.close()

def list_trends():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trends ORDER BY timestamp DESC')
    trends = cursor.fetchall()
    conn.close()

    if not trends:
        print("No trends found.")
        return

    print(f"{'ID':<5}{'Source':<10}{'Title':<30}{'URL':<40}{'Score':<6}{'Timestamp':<20}")
    print("-" * 110)
    for trend in trends:
        print(f"{trend[0]:<5}{trend[1]:<10}{trend[2][:27]:<30}{trend[3][:37]:<40}{trend[4]:<6}{trend[5]:<20}")

def generate_csv_report():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trends ORDER BY timestamp DESC')
    trends = cursor.fetchall()
    conn.close()

    if not trends:
        print("No trends found to generate report.")
        return

    report_path = os.path.expanduser('~/signalscout_report.csv')
    with open(report_path, 'w', newline='') as csvfile:
        fieldnames = ['ID', 'Source', 'Title', 'URL', 'Score', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for trend in trends:
            writer.writerow({
                'ID': trend[0],
                'Source': trend[1],
                'Title': trend[2],
                'URL': trend[3],
                'Score': trend[4],
                'Timestamp': trend[5]
            })

    print(f"CSV report generated at: {report_path}")

def check_alerts(threshold):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM trends WHERE score >= ? ORDER BY timestamp DESC', (threshold,))
    alerts = cursor.fetchall()
    conn.close()

    if not alerts:
        print(f"No trends found with score above {threshold}.")
        return

    print(f"ALERTS (Score >= {threshold}):")
    print(f"{'ID':<5}{'Source':<10}{'Title':<30}{'URL':<40}{'Score':<6}{'Timestamp':<20}")
    print("-" * 110)
    for alert in alerts:
        print(f"{alert[0]:<5}{alert[1]:<10}{alert[2][:27]:<30}{alert[3][:37]:<40}{alert[4]:<6}{alert[5]:<20}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()

    trends_data = [
        ('Reddit', 'New AI tool for developers', 'https://reddit.com/ai-tool', 95),
        ('Twitter', 'Python framework gains traction', 'https://twitter.com/python-framework', 88),
        ('Product Hunt', 'Best new SaaS product', 'https://producthunt.com/saas-product', 92)
    ]

    for trend in trends_data:
        add_trend(*trend)

    print("Trends added successfully. Listing trends:")
    list_trends()

    print("\nGenerating CSV report:")
    generate_csv_report()

    print("\nChecking alerts (threshold 90):")
    check_alerts(90)

    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description='SignalScout - CLI tool for aggregating trending signals')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    add_parser = subparsers.add_parser('add', help='Add a new trend')
    add_parser.add_argument('--source', required=True, help='Source of the trend (e.g., Reddit, Twitter)')
    add_parser.add_argument('--title', required=True, help='Title of the trend')
    add_parser.add_argument('--url', required=True, help='URL of the trend')
    add_parser.add_argument('--score', type=int, required=True, help='Score of the trend (0-100)')

    list_parser = subparsers.add_parser('list', help='List all trends')

    report_parser = subparsers.add_parser('report', help='Generate CSV report of trends')
    report_parser.add_argument('--output', help='Output file path for the report (default: ~/signalscout_report.csv)')

    alert_parser = subparsers.add_parser('alert', help='Check for alerts based on score threshold')
    alert_parser.add_argument('--threshold', type=int, required=True, help='Score threshold for alerts (0-100)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'add':
        add_trend(args.source, args.title, args.url, args.score)
    elif args.command == 'list':
        list_trends()
    elif args.command == 'report':
        generate_csv_report()
    elif args.command == 'alert':
        check_alerts(args.threshold)

if __name__ == '__main__':
    main()