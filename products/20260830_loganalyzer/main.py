import argparse
import os
import re
import sys
import sqlite3
import json
import csv
from datetime import datetime

DB_PATH = os.path.expanduser('~/loganalyzer_demo.db')

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_number INTEGER,
            timestamp TEXT,
            message TEXT,
            pattern TEXT,
            count INTEGER
        )
    ''')

    sample_logs = [
        "2023-10-01 12:00:00 ERROR: Connection failed",
        "2023-10-01 12:01:00 INFO: User logged in",
        "2023-10-01 12:02:00 WARNING: High memory usage",
        "2023-10-01 12:03:00 DEBUG: System check completed",
        "2023-10-01 12:04:00 ERROR: Database timeout",
        "2023-10-01 12:05:00 INFO: System started",
        "2023-10-01 12:06:00 WARNING: Disk space low",
        "2023-10-01 12:07:00 DEBUG: Cache cleared",
        "2023-10-01 12:08:00 ERROR: Invalid input",
        "2023-10-01 12:09:00 INFO: User logged out"
    ]

    for line_num, line in enumerate(sample_logs, 1):
        timestamp = line.split()[0] + ' ' + line.split()[1]
        message = ' '.join(line.split()[2:])
        pattern = 'ERROR' if 'ERROR' in line else 'INFO' if 'INFO' in line else 'WARNING' if 'WARNING' in line else 'DEBUG'
        cursor.execute('INSERT INTO logs (line_number, timestamp, message, pattern, count) VALUES (?, ?, ?, ?, ?)',
                  (line_num, timestamp, message, pattern, 1))

    conn.commit()

    cursor.execute('SELECT line_number, timestamp, message, pattern, count FROM logs')
    results = cursor.fetchall()

    print(f"{'Line':<10} {'Timestamp':<20} {'Message':<30} {'Pattern':<10} {'Count':<10}")
    print('-' * 80)
    for line_number, timestamp, message, pattern, count in results:
        print(f"{line_number:<10} {timestamp:<20} {message:<30} {pattern:<10} {count:<10}")

    cursor.execute('SELECT pattern, COUNT(*) as count FROM logs GROUP BY pattern')
    summary = cursor.fetchall()

    print("\nSummary Statistics:")
    print(f"{'Pattern':<10} {'Count':<10}")
    print('-' * 20)
    for pattern, count in summary:
        print(f"{pattern:<10} {count:<10}")

    conn.close()
    print("\nDemo complete.")

def analyze_logs(log_file, patterns, output_format):
    if not os.path.exists(log_file):
        print(f"Error: Log file {log_file} not found")
        return

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            line_number INTEGER,
            timestamp TEXT,
            message TEXT,
            pattern TEXT,
            count INTEGER
        )
    ''')

    with open(log_file, 'r') as file:
        for line_num, line in enumerate(file, 1):
            for pattern in patterns:
                if re.search(pattern, line):
                    timestamp = line.split()[0] + ' ' + line.split()[1]
                    message = ' '.join(line.split()[2:])
                    cursor.execute('INSERT INTO logs (line_number, timestamp, message, pattern, count) VALUES (?, ?, ?, ?, ?)',
                                  (line_num, timestamp, message, pattern, 1))

    conn.commit()

    cursor.execute('SELECT line_number, timestamp, message, pattern, count FROM logs')
    results = cursor.fetchall()

    if output_format == 'table':
        print(f"{'Line':<10} {'Timestamp':<20} {'Message':<30} {'Pattern':<10} {'Count':<10}")
        print('-' * 80)
        for line_number, timestamp, message, pattern, count in results:
            print(f"{line_number:<10} {timestamp:<20} {message:<30} {pattern:<10} {count:<10}")
    elif output_format == 'json':
        logs = []
        for line_number, timestamp, message, pattern, count in results:
            logs.append({
                'line_number': line_number,
                'timestamp': timestamp,
                'message': message,
                'pattern': pattern,
                'count': count
            })
        print(json.dumps(logs, indent=2))
    elif output_format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(['Line', 'Timestamp', 'Message', 'Pattern', 'Count'])
        for line_number, timestamp, message, pattern, count in results:
            writer.writerow([line_number, timestamp, message, pattern, count])

    cursor.execute('SELECT pattern, COUNT(*) as count FROM logs GROUP BY pattern')
    summary = cursor.fetchall()

    print("\nSummary Statistics:")
    if output_format == 'table':
        print(f"{'Pattern':<10} {'Count':<10}")
        print('-' * 20)
        for pattern, count in summary:
            print(f"{pattern:<10} {count:<10}")
    elif output_format == 'json':
        summary_data = [{'pattern': pattern, 'count': count} for pattern, count in summary]
        print(json.dumps(summary_data, indent=2))
    elif output_format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(['Pattern', 'Count'])
        for pattern, count in summary:
            writer.writerow([pattern, count])

    conn.close()

def main():
    parser = argparse.ArgumentParser(description="LogAnalyzer - Analyze log files for patterns")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    analyze_parser = subparsers.add_parser('analyze', help='Analyze log files')
    analyze_parser.add_argument('log_file', help='Path to the log file')
    analyze_parser.add_argument('--pattern', action='append', help='Pattern to search for (can be specified multiple times)')
    analyze_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Output format (table, json, csv)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'analyze':
        if not args.pattern:
            print("Error: At least one pattern must be specified")
            return
        analyze_logs(args.log_file, args.pattern, args.format)

if __name__ == "__main__":
    main()