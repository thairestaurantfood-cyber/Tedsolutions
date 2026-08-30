import argparse
import json
import os
import sqlite3
import sys
import yaml
import toml
from pathlib import Path
import csv
from datetime import datetime

DB_PATH = os.path.expanduser('~/config_validator.db')

def demo():
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    create_table()

    # Insert demo errors with all fields populated
    insert_error('demo_config.json', 1, 'MissingField', 'Missing required field: api_key', 'high')
    insert_error('demo_schema.json', 2, 'TypeMismatch', 'Expected string, got integer for field: timeout', 'medium')
    insert_error('demo_config.yaml', 3, 'InvalidFormat', 'Invalid YAML format', 'high')
    insert_error('demo_schema.toml', 4, 'MissingField', 'Missing required field: version', 'medium')

    # Print formatted table output
    print(f"{'ID':<5} {'File Path':<20} {'Line':<5} {'Type':<15} {'Message':<30} {'Severity':<10} {'Timestamp':<20}")
    print("-" * 100)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM validation_errors ORDER BY timestamp DESC')
    for error in cursor.fetchall():
        print(f"{error[0]:<5} {error[1]:<20} {error[2]:<5} {error[3]:<15} {error[4]:<30} {error[5]:<10} {error[6]:<20}")
    conn.close()
    print("Demo complete.")

def create_table():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS validation_errors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            line_number INTEGER,
            error_type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_error(file_path, line_number, error_type, message, severity='medium'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO validation_errors (file_path, line_number, error_type, message, severity)
        VALUES (?, ?, ?, ?, ?)
    ''', (file_path, line_number, error_type, message, severity))
    conn.commit()
    conn.close()

def load_file(file_path):
    if file_path.endswith('.json'):
        with open(file_path, 'r') as f:
            return json.load(f)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    elif file_path.endswith('.toml'):
        with open(file_path, 'r') as f:
            return toml.load(f)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def validate_config(config_path, schema_path):
    try:
        config = load_file(config_path)
    except Exception as e:
        insert_error(config_path, 0, 'FileError', str(e), 'high')
        return False

    try:
        schema = load_file(schema_path)
    except Exception as e:
        insert_error(schema_path, 0, 'FileError', str(e), 'high')
        return False

    if not isinstance(config, dict):
        insert_error(config_path, 0, 'ValidationError', 'Config must be a JSON object', 'high')
        return False

    if not isinstance(schema, dict):
        insert_error(schema_path, 0, 'ValidationError', 'Schema must be a JSON object', 'high')
        return False

    for key, value in schema.items():
        if 'required' in value and value['required'] and key not in config:
            insert_error(config_path, 0, 'ValidationError', f'Missing required field: {key}', 'medium')

    return True

def list_errors(output_format='table'):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM validation_errors ORDER BY timestamp DESC')
    errors = cursor.fetchall()
    conn.close()

    if not errors:
        print("No validation errors found.")
        return

    if output_format == 'table':
        print(f"{'ID':<5} {'File Path':<20} {'Line':<5} {'Type':<15} {'Message':<30} {'Severity':<10} {'Timestamp':<20}")
        print("-" * 100)
        for error in errors:
            print(f"{error[0]:<5} {error[1]:<20} {error[2]:<5} {error[3]:<15} {error[4]:<30} {error[5]:<10} {error[6]:<20}")
    elif output_format == 'json':
        print(json.dumps([dict(zip(['id', 'file_path', 'line_number', 'error_type', 'message', 'severity', 'timestamp'], error)) for error in errors], indent=2))
    elif output_format == 'csv':
        writer = csv.writer(sys.stdout)
        writer.writerow(['ID', 'File Path', 'Line', 'Type', 'Message', 'Severity', 'Timestamp'])
        writer.writerows(errors)
    else:
        print(f"Unsupported output format: {output_format}")

def main():
    parser = argparse.ArgumentParser(description="ConfigValidator")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    validate_parser = subparsers.add_parser('validate', help='Validate config against schema')
    validate_parser.add_argument('config_path', help='Path to config file')
    validate_parser.add_argument('schema_path', help='Path to schema file')

    list_parser = subparsers.add_parser('list', help='List validation errors')
    list_parser.add_argument('--format', choices=['table', 'json', 'csv'], default='table', help='Output format')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'validate':
        validate_config(args.config_path, args.schema_path)
    elif args.command == 'list':
        list_errors(args.format)

if __name__ == "__main__":
    main()