import os
import sqlite3
from argparse import ArgumentParser
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

        def demo():
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)

                init_db()

                add_schema('users', 'id', 'INTEGER', 'NO', 'PRIMARY KEY AUTOINCREMENT')
                add_schema('users', 'name', 'TEXT', 'NO')
                add_schema('users', 'email', 'TEXT', 'NO')

                print(f"{'Table':<15} {'Column':<15} {'Type':<10} {'Nullable':<10} {'Default':<15}")
                print("-" * 65)

                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT table_name, column_name, data_type, is_nullable, default_value FROM schemas')
                schemas = cursor.fetchall()
                conn.close()

                for schema in schemas:
                    print(f"{schema[0]:<15} {schema[1]:<15} {schema[2]:<10} {schema[3]:<10} {schema[4] if schema[4] else '':<15}")

                    def main():
                        parser = ArgumentParser(description="SchemaSpy")
                        parser.add_argument('--demo', action='store_true', help='Run demo')
                        pre, _ = parser.parse_known_args()  # check --demo FIRST
                        if pre.demo:
                            demo()
                            return

                        subparsers = parser.add_subparsers(dest='command')  # NO required=True

    # Add subparsers here...

                        args = parser.parse_args()
                        if not args.command:
                            parser.print_help()
                            return

                        if __name__ == "__main__":
                            main()