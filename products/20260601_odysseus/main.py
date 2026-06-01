import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/odysseus.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_task(title, description, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO tasks (title, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, status, now, now))
    conn.commit()
    conn.close()

def add_document(title, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO documents (title, content, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', (title, content, now, now))
    conn.commit()
    conn.close()

def list_tasks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, description, status, created_at, updated_at FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    print(f"{'ID':<5}{'Title':<20}{'Description':<30}{'Status':<10}{'Created':<20}{'Updated':<20}")
    for task in tasks:
        print(f"{task[0]:<5}{task[1]:<20}{task[2]:<30}{task[3]:<10}{task[4]:<20}{task[5]:<20}")

def list_documents():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, title, content, created_at, updated_at FROM documents')
    documents = cursor.fetchall()
    conn.close()
    print(f"{'ID':<5}{'Title':<20}{'Content':<30}{'Created':<20}{'Updated':<20}")
    for document in documents:
        print(f"{document[0]:<5}{document[1]:<20}{document[2]:<30}{document[3]:<20}{document[4]:<20}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    add_task('Task 1', 'Description for Task 1', 'pending')
    add_task('Task 2', 'Description for Task 2', 'completed')
    add_document('Document 1', 'Content for Document 1')
    add_document('Document 2', 'Content for Document 2')
    print("\nTasks:")
    list_tasks()
    print("\nDocuments:")
    list_documents()

def main():
    if '--demo' in sys.argv:
        demo()
        return

    parser = argparse.ArgumentParser(description='Odysseus - Task and Document Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Add task command
    add_task_parser = subparsers.add_parser('add-task', help='Add a new task')
    add_task_parser.add_argument('--title', required=True, help='Title of the task')
    add_task_parser.add_argument('--description', help='Description of the task')
    add_task_parser.add_argument('--status', required=True, help='Status of the task')

    # Add document command
    add_doc_parser = subparsers.add_parser('add-document', help='Add a new document')
    add_doc_parser.add_argument('--title', required=True, help='Title of the document')
    add_doc_parser.add_argument('--content', required=True, help='Content of the document')

    # List tasks command
    subparsers.add_parser('list-tasks', help='List all tasks')

    # List documents command
    subparsers.add_parser('list-documents', help='List all documents')

    args = parser.parse_args()

    if args.command == 'add-task':
        add_task(args.title, args.description, args.status)
    elif args.command == 'add-document':
        add_document(args.title, args.content)
    elif args.command == 'list-tasks':
        list_tasks()
    elif args.command == 'list-documents':
        list_documents()

if __name__ == '__main__':
    main()