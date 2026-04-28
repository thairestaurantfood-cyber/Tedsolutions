import os
import sys
import json
import csv
from datetime import datetime
import argparse
import sqlite3
import subprocess
import requests

def fetch_hn_top():
    url = f"https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:10]
    else:
        raise Exception("Failed to fetch top stories from Hacker News")

def score_product(product_id):
    # Placeholder for actual scoring logic
    # This is a dummy implementation that returns a random score
    import random
    return random.randint(0, 20)

def export_to_csv(data, filename="product_scores.csv"):
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Product ID", "Score"])
        for product_id, score in data.items():
            writer.writerow([product_id, score])

def save_scores(scores):
    conn = sqlite3.connect('tools.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores
                 (product_id TEXT PRIMARY KEY, score INTEGER)''')
    for product_id, score in scores.items():
        c.execute("INSERT OR REPLACE INTO scores VALUES (?, ?)", (product_id, score))
    conn.commit()
    conn.close()

def load_scores():
    conn = sqlite3.connect('tools.db')
    c = conn.cursor()
    c.execute("SELECT * FROM scores")
    scores = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return scores

def compare_scores(scores):
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    print("\nComparison Table:")
    print("Product ID\tScore")
    for product_id, score in sorted_scores:
        print(f"{product_id}\t{score}")

def flag_broken_builds(scores):
    broken_builds = [product_id for product_id, score in scores.items() if score < 5]
    if broken_builds:
        print("\nBroken Builds:")
        for product_id in broken_builds:
            print(product_id)
    else:
        print("No broken builds found.")

def export_to_json(scores):
    with open('tools.json', 'w') as file:
        json.dump(scores, file, indent=4)

def main():
    parser = argparse.ArgumentParser(description="BuildScorer - Score products based on real test results")
    parser.add_argument("--help", action="help", help="Show this help message and exit")
    parser.add_argument("--demo", action="store_true", help="Run a demo with sample data")
    parser.add_argument("--stats", action="store_true", help="Display statistics about the scores")
    args = parser.parse_args()

    if args.demo:
        # Sample data for demonstration
        products = {
            "product1": 15,
            "product2": 8,
            "product3": 12
        }
        save_scores(products)
        export_to_json(products)
        print("Demo completed. JSON file 'tools.json' has been created.")
    else:
        # Fetch top stories from Hacker News
        try:
            top_stories = fetch_hn_top()
            scores = {story_id: score_product(story_id) for story_id in top_stories}
            save_scores(scores)
            export_to_json(scores)
            print("Product scores have been saved to 'tools.db' and exported to 'tools.json'")
        except Exception as e:
            print(f"Error: {e}")

    if args.stats:
        scores = load_scores()
        compare_scores(scores)
        flag_broken_builds(scores)

if __name__ == "__main__":
    main()