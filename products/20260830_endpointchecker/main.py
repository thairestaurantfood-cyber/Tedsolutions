import argparse
import os
import sqlite3
import sys
import time
import json
import csv
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError

DB_PATH = os.path.expanduser('~/.jarvis/endpoint_checker.db')

def create_table():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS endpoints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            method TEXT NOT NULL,
            headers TEXT,
            auth TEXT,
            status_code INTEGER,
            response_time REAL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def insert_endpoint(url, method, headers, auth, status_code, response_time):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO endpoints (url, method, headers, auth, status_code, response_time, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (url, method, headers, auth, status_code, response_time, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_endpoints():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT url, method, headers, auth, status_code, response_time, timestamp FROM endpoints')
    endpoints = cursor.fetchall()
    conn.close()
    return endpoints

def check_endpoint(url, method='GET', headers=None, auth=None):
    try:
        req = Request(url, method=method)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        if auth:
            req.add_header('Authorization', f'Basic {auth}')

        start_time = time.time()
        with urlopen(req) as response:
            response_time = time.time() - start_time
            return response.getcode(), response_time
    except URLError as e:
        if hasattr(e, 'code'):
            return e.code, 0
        else:
            return 0, 0

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    create_table()

    demo_data = [
        ('https://www.google.com', 'GET', None, None, 200, 0.45),
        ('https://www.github.com', 'GET', None, None, 200, 0.62),
        ('https://www.python.org', 'GET', None, None, 200, 0.38),
        ('https://nonexistent.example.com', 'GET', None, None, 404, 1.2),
        ('https://httpbin.org/status/500', 'GET', None, None, 500, 0.8),
        ('https://httpbin.org/post', 'POST', {'Content-Type': 'application/json'}, None, 200, 0.5),
        ('https://httpbin.org/basic-auth/user/pass', 'GET', None, 'dXNlcjpwYXNz', 200, 0.7),
    ]

    for url, method, headers, auth, status_code, response_time in demo_data:
        headers_json = json.dumps(headers) if headers else None
        insert_endpoint(url, method, headers_json, auth, status_code, response_time)

    endpoints = get_endpoints()
    total_response_time = sum(endpoint[5] for endpoint in endpoints)
    avg_response_time = total_response_time / len(endpoints) if endpoints else 0
    successful_checks = sum(1 for endpoint in endpoints if endpoint[4] == 200)
    uptime_percentage = (successful_checks / len(endpoints)) * 100 if endpoints else 0

    print(f"{'Endpoint':<40} {'Method':<10} {'Status':<10} {'Response Time':<15} {'Last Checked'}")
    print('-' * 90)
    for endpoint in endpoints:
        headers = json.loads(endpoint[2]) if endpoint[2] else {}
        print(f"{endpoint[0]:<40} {endpoint[1]:<10} {endpoint[4]:<10} {endpoint[5]:<15.2f} {endpoint[6]}")

    print("\nSummary Statistics:")
    print(f"Total Endpoints: {len(endpoints)}")
    print(f"Average Response Time: {avg_response_time:.2f}s")
    print(f"Uptime Percentage: {uptime_percentage:.2f}%")

def print_json(endpoints):
    data = []
    for endpoint in endpoints:
        headers = json.loads(endpoint[2]) if endpoint[2] else {}
        data.append({
            'url': endpoint[0],
            'method': endpoint[1],
            'headers': headers,
            'auth': endpoint[3],
            'status_code': endpoint[4],
            'response_time': endpoint[5],
            'timestamp': endpoint[6]
        })
    print(json.dumps(data, indent=2))

def print_csv(endpoints):
    writer = csv.writer(sys.stdout)
    writer.writerow(['URL', 'Method', 'Headers', 'Auth', 'Status Code', 'Response Time', 'Timestamp'])
    for endpoint in endpoints:
        headers = json.loads(endpoint[2]) if endpoint[2] else {}
        writer.writerow([endpoint[0], endpoint[1], headers, endpoint[3], endpoint[4], endpoint[5], endpoint[6]])

def main():
    parser = argparse.ArgumentParser(description="EndpointChecker")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add command for checking an endpoint
    check_parser = subparsers.add_parser('check', help='Check an endpoint')
    check_parser.add_argument('url', help='URL to check')
    check_parser.add_argument('--method', default='GET', help='HTTP method (default: GET)')
    check_parser.add_argument('--headers', nargs='+', help='Custom headers (key=value)')
    check_parser.add_argument('--auth', help='Basic authentication (username:password)')
    check_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Output format')

    # Add command for listing endpoints
    list_parser = subparsers.add_parser('list', help='List all endpoints')
    list_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Output format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'check':
        headers = {}
        if args.headers:
            for header in args.headers:
                key, value = header.split('=')
                headers[key] = value

        auth = None
        if args.auth:
            auth = args.auth.encode('utf-8').decode('ascii')

        status_code, response_time = check_endpoint(args.url, args.method, headers, auth)
        insert_endpoint(args.url, args.method, json.dumps(headers), auth, status_code, response_time)

        endpoints = get_endpoints()
        if args.format == 'json':
            print_json(endpoints)
        elif args.format == 'csv':
            print_csv(endpoints)
        else:
            print(f"{'Endpoint':<40} {'Method':<10} {'Status':<10} {'Response Time':<15} {'Last Checked'}")
            print('-' * 90)
            for endpoint in endpoints:
                headers = json.loads(endpoint[2]) if endpoint[2] else {}
                print(f"{endpoint[0]:<40} {endpoint[1]:<10} {endpoint[4]:<10} {endpoint[5]:<15.2f} {endpoint[6]}")

    elif args.command == 'list':
        endpoints = get_endpoints()
        if args.format == 'json':
            print_json(endpoints)
        elif args.format == 'csv':
            print_csv(endpoints)
        else:
            print(f"{'Endpoint':<40} {'Method':<10} {'Status':<10} {'Response Time':<15} {'Last Checked'}")
            print('-' * 90)
            for endpoint in endpoints:
                headers = json.loads(endpoint[2]) if endpoint[2] else {}
                print(f"{endpoint[0]:<40} {endpoint[1]:<10} {endpoint[4]:<10} {endpoint[5]:<15.2f} {endpoint[6]}")

if __name__ == "__main__":
    main()