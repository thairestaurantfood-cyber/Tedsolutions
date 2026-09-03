import argparse
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/pipelinekit.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pipelines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pipeline_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        command TEXT NOT NULL,
        args TEXT NOT NULL,
        input TEXT,
        output TEXT,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (pipeline_id) REFERENCES pipelines (id)
    )
    """)
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    conn = sqlite3.connect(DB_PATH)

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert demo pipeline
    conn.execute("""
    INSERT INTO pipelines (name, status, created_at, updated_at)
    VALUES (?, ?, ?, ?)
    """, ('demo_pipeline', 'created', now, now))

    pipeline_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert demo steps
    steps = [
        ('scrape', 'curl', json.dumps(["https://example.com"]), None, None, 'created', now, now),
        ('score', 'grep', json.dumps(["score"]), None, None, 'created', now, now),
        ('build', 'make', json.dumps(["all"]), None, None, 'created', now, now),
        ('publish', 'rsync', json.dumps(["-avz", "./dist/", "user@example.com:~/public_html/"]), None, None, 'created', now, now)
    ]

    for step in steps:
        conn.execute("""
        INSERT INTO steps (pipeline_id, name, command, args, input, output, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pipeline_id, *step))

    conn.commit()

    # Print pipelines
    print("Pipelines:")
    print(f"{'ID':<5} {'Name':<15} {'Status':<10} {'Created':<20} {'Updated':<20}")
    print("-" * 65)
    for row in conn.execute("SELECT id, name, status, created_at, updated_at FROM pipelines"):
        print(f"{row[0]:<5} {row[1]:<15} {row[2]:<10} {row[3]:<20} {row[4]:<20}")

    # Print steps
    print("\nSteps:")
    print(f"{'ID':<5} {'Pipeline ID':<12} {'Name':<10} {'Command':<15} {'Status':<10} {'Created':<20} {'Updated':<20}")
    print("-" * 85)
    for row in conn.execute("SELECT id, pipeline_id, name, command, status, created_at, updated_at FROM steps"):
        print(f"{row[0]:<5} {row[1]:<12} {row[2]:<10} {row[3]:<15} {row[4]:<10} {row[5]:<20} {row[6]:<20}")

    conn.close()
    print("\nDemo complete.")

def run_pipeline(pipeline_file, max_retries=3):
    with open(pipeline_file) as f:
        pipeline = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert pipeline
    conn.execute("""
    INSERT INTO pipelines (name, status, created_at, updated_at)
    VALUES (?, ?, ?, ?)
    """, (pipeline['name'], 'running', now, now))

    pipeline_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert steps
    for step in pipeline['steps']:
        conn.execute("""
        INSERT INTO steps (pipeline_id, name, command, args, input, output, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pipeline_id, step['name'], step['command'], json.dumps(step['args']),
              step.get('input'), step.get('output'), 'pending', now, now))

    conn.commit()

    # Execute steps
    for step in conn.execute("SELECT id, command, args FROM steps WHERE pipeline_id = ?", (pipeline_id,)):
        step_id, command, args = step
        args_list = json.loads(args)

        try:
            result = subprocess.run([command] + args_list, capture_output=True, text=True)
            status = 'completed' if result.returncode == 0 else 'failed'
            output = result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            status = 'failed'
            output = str(e)

        conn.execute("""
        UPDATE steps
        SET status = ?, output = ?, updated_at = ?
        WHERE id = ?
        """, (status, output, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), step_id))

        conn.commit()

    # Update pipeline status
    conn.execute("""
    UPDATE pipelines
    SET status = ?, updated_at = ?
    WHERE id = ?
    """, ('completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), pipeline_id))

    conn.commit()
    conn.close()

def main():
    parser = argparse.ArgumentParser(description="PipelineKit")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add run command
    run_parser = subparsers.add_parser('run', help='Run a pipeline')
    run_parser.add_argument('pipeline_file', help='Path to pipeline JSON file')
    run_parser.add_argument('--max-retries', type=int, default=3, help='Maximum number of retries for failed steps')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'run':
        run_pipeline(args.pipeline_file, args.max_retries)

if __name__ == "__main__":
    main()