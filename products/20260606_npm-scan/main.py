import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/npm_scan.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            description TEXT,
            license TEXT,
            homepage TEXT,
            repository TEXT,
            vulnerabilities INTEGER DEFAULT 0,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

    def demo():
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            init_db()
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            demo_data = [
            ('express', '4.17.1', 'Fast, unopinionated, minimalist web framework', 'MIT', 'https://expressjs.com', 'https://github.com/expressjs/express', 0),
            ('lodash', '4.17.21', 'A modern JavaScript utility library delivering modularity, performance & extras', 'MIT', 'https://lodash.com', 'https://github.com/lodash/lodash', 1),
            ('react', '17.0.2', 'A JavaScript library for building user interfaces', 'MIT', 'https://reactjs.org', 'https://github.com/facebook/react', 0),
            ('axios', '0.21.1', 'Promise based HTTP client for the browser and node.js', 'MIT', 'https://axios-http.com', 'https://github.com/axios/axios', 0),
            ('moment', '2.29.1', 'Parse, validate, manipulate, and display dates and times in JavaScript', 'MIT', 'https://momentjs.com', 'https://github.com/moment/moment', 2)
            ]

            cursor.executemany('''
            INSERT INTO packages (name, version, description, license, homepage, repository, vulnerabilities)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', demo_data)

            conn.commit()

            cursor.execute('SELECT name, version, vulnerabilities FROM packages')
            packages = cursor.fetchall()

            print(f"{'Name':<15}{'Version':<10}{'Vulnerabilities':<15}")
            print("-" * 40)
            for package in packages:
                print(f"{package[0]:<15}{package[1]:<10}{package[2]:<15}")

                conn.close()

                def add_package(name, version, description=None, license=None, homepage=None, repository=None, vulnerabilities=0):
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                    INSERT INTO packages (name, version, description, license, homepage, repository, vulnerabilities)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (name, version, description, license, homepage, repository, vulnerabilities))
                    conn.commit()
                    conn.close()

                    def main():
                        if '--demo' in sys.argv:
                            demo()
                            return

                        parser = argparse.ArgumentParser(description='NPM Package Scanner')
                        subparsers = parser.add_subparsers(dest='command', help='Available commands')

                        add_parser = subparsers.add_parser('add', help='Add a new package')
                        add_parser.add_argument('name', help='Package name')
                        add_parser.add_argument('version', help='Package version')
                        add_parser.add_argument('--description', help='Package description')
                        add_parser.add_argument('--license', help='Package license')
                        add_parser.add_argument('--homepage', help='Package homepage')
                        add_parser.add_argument('--repository', help='Package repository')
                        add_parser.add_argument('--vulnerabilities', type=int, default=0, help='Number of vulnerabilities')

                        args = parser.parse_args()

                        if args.command == 'add':
                            add_package(args.name, args.version, args.description, args.license, args.homepage, args.repository, args.vulnerabilities)

                            if __name__ == '__main__':
                                main()