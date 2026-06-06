import os
import sys
import sqlite3
import argparse
from datetime import datetime
DB_PATH = os.path.expanduser("~/.jarvis/schemaspy.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schemas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            column_name TEXT NOT NULL,
            data_type TEXT NOT NULL,
            is_nullable TEXT NOT NULL,
            default_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

    def add_schema(table_name, column_name, data_type, is_nullable, default_value=None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO schemas (table_name, column_name, data_type, is_nullable, default_value)
        VALUES (?, ?, ?, ?, ?)
        ''', (table_name, column_name, data_type, is_nullable, default_value))
        conn.commit()
        conn.close()

        def list_schemas():
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT table_name, column_name, data_type, is_nullable, default_value FROM schemas')
            schemas = cursor.fetchall()
            conn.close()

            if not schemas:
                print("No schemas found.")
                return

            print(f"{'Table':<15} {'Column':<15} {'Type':<10} {'Nullable':<10} {'Default':<15}")
            print("-" * 65)
            for schema in schemas:
                print(f"{schema[0]:<15} {schema[1]:<15} {schema[2]:<10} {schema[3]:<10} {schema[4] if schema[4] else '':<15}")

                def report():
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('SELECT table_name, column_name FROM schemas')
                    reports = cursor.fetchall()
                    conn.close()

                    if not reports:
                        print("No reports found.")
                        return

                    print(f"{'Table':<15} {'Column':<15}")
                    print("-" * 30)
                    for report in reports:
                        print(f"{report[0]:<15} {report[1]:<15}")

                        def notify():
                            print("Notification: Schema reports generated.")

                            def demo():
                                if os.path.exists(DB_PATH):
                                    os.remove(DB_PATH)

                                    init_db()

                                    add_schema('users', 'id', 'INTEGER', 'NO', 'PRIMARY KEY AUTOINCREMENT')
                                    add_schema('users', 'name', 'TEXT', 'NO')
                                    add_schema('users', 'email', 'TEXT', 'NO')
                                    add_schema('users', 'created_at', 'TIMESTAMP', 'YES', 'CURRENT_TIMESTAMP')

                                    add_schema('products', 'id', 'INTEGER', 'NO', 'PRIMARY KEY AUTOINCREMENT')
                                    add_schema('products', 'name', 'TEXT', 'NO')
                                    add_schema('products', 'price', 'REAL', 'NO')
                                    add_schema('products', 'stock', 'INTEGER', 'YES', '0')

                                    list_schemas()
                                    print("\nReport:")
                                    report()
                                    notify()

                                    def main():
                                        parser = argparse.ArgumentParser(description='SchemaSpy - Lightweight database schema documentation tool')
                                        parser.add_argument('--demo', action='store_true', help='Run demo')
                                        pre, _ = parser.parse_known_args()  # check --demo FIRST
                                        if pre.demo:
                                            demo()
                                            return
                                        subparsers = parser.add_subparsers(dest='command')
                                        add_parser = subparsers.add_parser('add', help='Add a schema entry')
                                        add_parser.add_argument('table_name', help='Table name')
                                        add_parser.add_argument('column_name', help='Column name')
                                        add_parser.add_argument('data_type', help='Data type')
                                        add_parser.add_argument('is_nullable', help='Is nullable (YES/NO)')
                                        add_parser.add_argument('--default', help='Default value', default=None)
                                        list_parser = subparsers.add_parser('list', help='List all schemas')
                                        report_parser = subparsers.add_parser('report', help='Generate reports')
                                        notify_parser = subparsers.add_parser('notify', help='Send notifications')

                                        args = parser.parse_args()
                                        if not args.command:
                                            parser.print_help()

                                            if __name__ == "__main__":
                                                main()