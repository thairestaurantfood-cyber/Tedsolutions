import os
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser("~/.jarvis/aura_crawler.db")

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS repos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT NOT NULL UNIQUE,
            owner TEXT NOT NULL,
            description TEXT,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id INTEGER NOT NULL,
            agent_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            points INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (repo_id) REFERENCES repos (id)
        )
    ''')
    conn.commit()
    conn.close()

def calculate_ratings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Calculate rating for each repo (stars * 0.5 + forks * 0.3 + avg_points * 0.2)
    c.execute('''
        SELECT
            r.id,
            r.repo_name,
            r.owner,
            r.stars,
            r.forks,
            r.description,
            r.last_updated,
            r.created_at,
            COALESCE(AVG(rew.points), 0) as avg_points,
            (r.stars * 0.5 + r.forks * 0.3 + COALESCE(AVG(rew.points), 0) * 0.2) as rating
        FROM repos r
        LEFT JOIN rewards rew ON r.id = rew.repo_id
        GROUP BY r.id
        ORDER BY rating DESC
    ''')

    repos_with_ratings = c.fetchall()
    conn.commit()
    conn.close()
    return repos_with_ratings

def print_repo_ratings(repos):
    print("\nRepo Ratings:")
    print("ID | Repo Name    | Owner  | Stars | Forks | AvgPts | Rating | Description")
    print("---|--------------|--------|-------|-------|--------|--------|------------")
    for row in repos:
        print(f"{row[0]:<2} | {row[1]:<12} | {row[2]:<6} | {row[3]:<5} | {row[4]:<5} | {row[8]:<6} | {row[9]:<6.1f} | {row[5]}")

def print_leaderboard(repos):
    print("\nLeaderboard (Top 3 Agents):")
    print("Rank | Agent ID  | Total Points")
    print("-----|-----------|-------------")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT agent_id, SUM(points) as total_points
        FROM rewards
        GROUP BY agent_id
        ORDER BY total_points DESC
        LIMIT 3
    ''')
    leaderboard = c.fetchall()
    conn.close()

    for i, row in enumerate(leaderboard, 1):
        print(f"{i:<4} | {row[0]:<9} | {row[1]}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Insert sample repos with realistic data
    repos = [
        ('aura-crawler', 'ted-ai', 'CLI tool for GitHub repo management with reward system', 42, 8, '2024-05-20T10:00:00Z', '2024-01-01T00:00:00Z'),
        ('local-lens', 'ted-ai', 'Tourism-focused AI tools for Phuket businesses', 123, 25, '2024-05-19T15:30:00Z', '2024-02-15T00:00:00Z'),
        ('invoice-bot', 'ted-ai', 'Automated invoice processing for Thai businesses', 87, 12, '2024-05-18T12:15:00Z', '2024-03-01T00:00:00Z'),
        ('ai-emailer', 'ted-ai', 'AI-powered email automation for small businesses', 65, 18, '2024-05-17T08:45:00Z', '2024-01-15T00:00:00Z'),
        ('file-org', 'ted-ai', 'Automated file organization tool for developers', 34, 5, '2024-05-16T14:20:00Z', '2024-04-01T00:00:00Z')
    ]
    c.executemany('INSERT INTO repos (repo_name, owner, description, stars, forks, last_updated, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)', repos)

    # Insert sample rewards with realistic points
    rewards = [
        (1, 'agent-1', 'star', 10, '2024-05-20T09:00:00Z'),
        (1, 'agent-2', 'fork', 15, '2024-05-20T09:15:00Z'),
        (1, 'agent-3', 'star', 8, '2024-05-20T09:30:00Z'),
        (2, 'agent-1', 'contribution', 25, '2024-05-19T14:00:00Z'),
        (2, 'agent-2', 'star', 12, '2024-05-19T14:15:00Z'),
        (3, 'agent-3', 'star', 10, '2024-05-18T11:00:00Z'),
        (3, 'agent-1', 'fork', 20, '2024-05-18T11:30:00Z'),
        (4, 'agent-2', 'contribution', 30, '2024-05-17T08:00:00Z'),
        (5, 'agent-3', 'star', 5, '2024-05-16T13:00:00Z'),
        (5, 'agent-1', 'fork', 10, '2024-05-16T13:45:00Z')
    ]
    c.executemany('INSERT INTO rewards (repo_id, agent_id, action_type, points, timestamp) VALUES (?, ?, ?, ?, ?)', rewards)

    conn.commit()
    conn.close()

    # Print repos table
    print("Sample Repositories:")
    print("ID | Repo Name    | Owner  | Stars | Forks | Description")
    print("---|--------------|--------|-------|-------|------------")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, repo_name, owner, stars, forks, description FROM repos')
    for row in c.fetchall():
        print(f"{row[0]:<2} | {row[1]:<12} | {row[2]:<6} | {row[3]:<5} | {row[4]:<5} | {row[5]}")
    conn.close()

    # Print rewards table
    print("\nSample Rewards:")
    print("ID | Repo ID | Agent ID | Action   | Points | Timestamp")
    print("---|---------|----------|----------|--------|-----------")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, repo_id, agent_id, action_type, points, timestamp FROM rewards')
    for row in c.fetchall():
        print(f"{row[0]:<2} | {row[1]:<7} | {row[2]:<8} | {row[3]:<8} | {row[4]:<6} | {row[5]}")
    conn.close()

    # Calculate and print ratings
    repos_with_ratings = calculate_ratings()
    print_repo_ratings(repos_with_ratings)