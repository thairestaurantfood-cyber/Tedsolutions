import os
import sqlite3
import argparse
from datetime import datetime
import subprocess
import json
from pathlib import Path

def fetch_hn_top():
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url)
    return json.loads(response.text)

def process_story(story_id):
    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
    response = requests.get(url)
    story = json.loads(response.text)
    return {
        "id": story["id"],
        "title": story["title"],
        "url": story["url"],
        "points": story["score"],
        "comments_count": story["descendants"] if "descendants" in story else 0,
        "time": datetime.fromtimestamp(story["time"]).strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    parser = argparse.ArgumentParser(description="Fetch and process Hacker News top stories.")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode with hardcoded sample data.")
    parser.add_argument("--help", action="help", help="Show this message and exit.")
    args = parser.parse_args()

    if args.demo:
        # Demo data
        stories = [
            {"id": 123, "title": "Demo Title 1", "url": "https://example.com/demo1", "points": 50, "comments_count": 100, "time": "2026-04-27 12:00:00"},
            {"id": 456, "title": "Demo Title 2", "url": "https://example.com/demo2", "points": 30, "comments_count": 80, "time": "2026-04-27 11:00:00"}
        ]
    else:
        stories = fetch_hn_top()

    # Process and store stories in SQLite database
    conn = sqlite3.connect(os.path.expanduser("~/.hn.db"))
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS hn_stories (id INTEGER PRIMARY KEY, title TEXT, url TEXT, points INTEGER, comments_count INTEGER, time TEXT)")
    for story in stories:
        cursor.execute("INSERT INTO hn_stories VALUES (?, ?, ?, ?, ?, ?)", (story["id"], story["title"], story["url"], story["points"], story["comments_count"], story["time"]))
    conn.commit()
    conn.close()

    print(f"Processed {len(stories)} stories and stored them in the database.")

if __name__ == "__main__":
    main()