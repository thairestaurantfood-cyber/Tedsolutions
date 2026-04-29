import os
import sys
import json
import csv
import sqlite3
import argparse
from datetime import datetime
import pathlib
import subprocess
import urllib.request
import re
import time

def fetch_hn_top():
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = urllib.request.urlopen(url)
    return json.loads(response.read())

def run_product(product_path, demo=False):
    args = [sys.executable, product_path]
    if demo:
        args.append("--demo")
    try:
        process = subprocess.run(args, capture_output=True, text=True, timeout=10)
        return {
            "returncode": process.returncode,
            "stdout": process.stdout,
            "stderr": process.stderr
        }
    except subprocess.TimeoutExpired:
        return {"returncode": -9, "stdout": "", "stderr": "Timeout"}

def calculate_score(result):
    score = 0
    if result["demo_runs"] == 1 and result["returncode"] == 0:
        score += 3
    if len(result["stdout"]) > 50:
        score += 2
    if not result["stderr"]:
        score += 2
    if "--help" in result["stdout"]:
        score += 2
    if len(open(str(product_path)).readlines()) > 100:
        score += 1
    return score

def update_context():
    db_path = os.path.expanduser("~/.jarvis/quality.db"); os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product, demo_runs, demo_output, demo_error, lines
            FROM quality
            ORDER BY score DESC LIMIT 3
        ''')
        top_3 = cursor.fetchall()
        cursor.execute('''
            SELECT product, demo_runs, demo_output, demo_error, lines
            FROM quality
            ORDER BY score ASC LIMIT 3
        ''')
        bottom_3 = cursor.fetchall()

    context_md = f"# PRODUCT QUALITY\n\n"
    for product, demo_runs, demo_output, demo_error, lines in top_3:
        context_md += f"### {product}\n"
        context_md += f"- Demo Runs: {demo_runs}\n"
        context_md += f"- Demo Output: {demo_output}\n"
        context_md += f"- Demo Error: {demo_error}\n"
        context_md += f"- Lines of Code: {lines}\n\n"

    for product, demo_runs, demo_output, demo_error, lines in bottom_3:
        context_md += f"### {product}\n"
        context_md += f"- Demo Runs: {demo_runs}\n"
        context_md += f"- Demo Output: {demo_output}\n"
        context_md += f"- Demo Error: {demo_error}\n"
        context_md += f"- Lines of Code: {lines}\n\n"

    with open(os.path.expanduser("~/.jarvis/memory/context.md"), "w") as f:
        f.write(context_md)

def export_to_csv():
    db_path = os.path.expanduser("~/.jarvis/quality.db"); os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT product, demo_runs, demo_output, demo_error, lines
            FROM quality
        ''')
        rows = cursor.fetchall()

    headers = ["Product", "Demo Runs", "Demo Output", "Demo Error", "Lines of Code"]
    with open(os.path.expanduser("~/.jarvis/memory/products.csv"), "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)

def main():
    parser = argparse.ArgumentParser(description="Run products and capture output for scoring.")
    parser.add_argument("--demo", action="store_true", help="Run product in demo mode with hardcoded sample data.")
    parser.add_argument("--report", action="store_true", help="Show all products ranked by score with trend arrow if score changed.")
    parser.add_argument("--worst", action="store_true", help="Show bottom 3 products with their error messages.")
    parser.add_argument("--update-context", action="store_true", help="Update context.md with top and bottom 3 products.")
    parser.add_argument("--export", action="store_true", help="Export quality data to CSV.")
    parser.add_argument("--since", type=str, help="Show only products built after date (YYYY-MM-DD).")
    args = parser.parse_args()

    db_path = os.path.expanduser("~/.jarvis/quality.db"); os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality (
                product TEXT,
                demo_runs INTEGER,
                demo_output TEXT,
                demo_error TEXT,
                lines INTEGER,
                checked BOOLEAN
            )
        ''')
        conn.commit()
        conn.close()

    products_dir = os.path.expanduser("~/.jarvis/products")
    for product_path in pathlib.Path(products_dir).glob("main.py"):
        result = run_product(product_path, demo=args.demo)
        score = calculate_score(result)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE quality
                SET returncode=?, stdout=?, stderr=?, lines=?
                WHERE product=?
            ''', (result["returncode"], result["stdout"], result["stderr"], len(open(str(product_path)).readlines()), str(product_path)))
            cursor.execute('''
                INSERT INTO quality (product, demo_runs, demo_output, demo_error, lines, checked)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (str(product_path), 1 if args.demo else 0, result["stdout"], result["stderr"], len(open(str(product_path)).readlines()), False))

    if args.report:
        # Implement report logic here
        pass

    if args.worst:
        # Implement worst logic here
        pass

    if args.update_context:
        update_context()

    if args.export:
        export_to_csv()

if __name__ == "__main__":
    main()