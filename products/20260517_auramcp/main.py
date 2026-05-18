import os
import sys
import json
import sqlite3
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

DB_PATH = os.path.expanduser('~/.aura_mcp/git_tools.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS git_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_path TEXT,
            branch TEXT,
            ahead INTEGER,
            behind INTEGER,
            untracked TEXT,
            modified TEXT,
            staged TEXT,
            last_updated TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS git_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_path TEXT,
            commit_hash TEXT,
            author TEXT,
            date TEXT,
            message TEXT,
            changes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_git_status(repo_path):
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'status', '--porcelain=v1', '--branch'],
            capture_output=True, text=True, check=True
        )
        status_output = result.stdout
    except subprocess.CalledProcessError as e:
        return None

    branch_line = [line for line in status_output.split('\n') if line.startswith('##')]
    if not branch_line:
        return None

    branch_info = branch_line[0].replace('## ', '').split('...')
    branch = branch_info[0]
    ahead, behind = 0, 0
    if len(branch_info) > 1:
        ahead_behind = branch_info[1].split()
        if len(ahead_behind) == 2:
            ahead = int(ahead_behind[0].replace('ahead ', ''))
            behind = int(ahead_behind[1].replace('behind ', ''))

    untracked = []
    modified = []
    staged = []
    for line in status_output.split('\n'):
        if line.startswith('?? '):
            untracked.append(line[3:])
        elif line.startswith(' M '):
            modified.append(line[3:])
        elif line.startswith('M  '):
            staged.append(line[3:])

    return {
        'repo_path': repo_path,
        'branch': branch,
        'ahead': ahead,
        'behind': behind,
        'untracked': '\n'.join(untracked),
        'modified': '\n'.join(modified),
        'staged': '\n'.join(staged),
        'last_updated': datetime.now().isoformat()
    }

def get_git_log(repo_path, limit=5):
    try:
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--pretty=format:%H|%an|%ad|%s|%b', '--date=iso', '-n', str(limit)],
            capture_output=True, text=True, check=True
        )
        log_output = result.stdout
    except subprocess.CalledProcessError as e:
        return []

    commits = []
    for block in log_output.split('\ncommit '):
        if not block.strip():
            continue
        parts = block.split('|', 4)
        if len(parts) >= 4:
            commit_hash = parts[0].strip()
            author = parts[1].strip()
            date = parts[2].strip()
            message = parts[3].strip()
            changes = parts[4].strip() if len(parts) > 4 else ''
            commits.append({
                'commit_hash': commit_hash,
                'author': author,
                'date': date,
                'message': message,
                'changes': changes
            })
    return commits

def demo():
    print("Git Status Demo (Offline)")
    print("=" * 30)
    print("This demo shows git status and log from local repositories.")
    print("No network calls are made.")
    print("=" * 30)
    print()

    # Demo with current directory
    current_dir = os.getcwd()
    print(f"Checking current directory: {current_dir}")
    status = get_git_status(current_dir)
    if status:
        print("\nGit Status:")
        print(f"Branch: {status['branch']}")
        print(f"Ahead: {status['ahead']}, Behind: {status['behind']}")
        print("\nUntracked files:")
        print(status['untracked'] if status['untracked'] else "None")
        print("\nModified files:")
        print(status['modified'] if status['modified'] else "None")
        print("\nStaged files:")
        print(status['staged'] if status['staged'] else "None")
    else:
        print("Not a git repository or git not available")

    print("\nLast 5 commits:")
    logs = get_git_log(current_dir, 5)
    for commit in logs:
        print(f"\nCommit: {commit['commit_hash'][:7]}")
        print(f"Author: {commit['author']}")
        print(f"Date: {commit['date']}")
        print(f"Message: {commit['message']}")

def main():
    parser = argparse.ArgumentParser(description='Git Status MCP Tool')
    parser.add_argument('--init-db', action='store_true', help='Initialize database')
    parser.add_argument('--demo', action='store_true', help='Run demo')
    args = parser.parse_args()

    if args.init_db:
        init_db()
        print("Database initialized")
        return

    if args.demo:
        demo()
        return

    parser.print_help()

if __name__ == '__main__':
    main()