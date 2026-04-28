import os
import sys
import json
import csv
import datetime
import argparse
import sqlite3
import pathlib
import subprocess
import requests

# Define the BuildScorer class
class BuildScorer:
    def __init__(self):
        self.products_dir = os.path.expanduser('~/jarvis/products')
        self.sqlite_file = 'build_scores.db'
        self.help_output = {}
        self.demo_output = {}
        self.errors = {}

    # Create the SQLite database and table
    def create_db(self):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS build_scores
                     (product text, score integer, timestamp text)''')
        conn.commit()
        conn.close()

    # Run --help and --demo on each product
    def run_products(self):
        for filename in os.listdir(self.products_dir):
            if filename.endswith(".py"):
                product_path = os.path.join(self.products_dir, filename)
                try:
                    # Run --help
                    output = subprocess.check_output([sys.executable, product_path, '--help'])
                    self.help_output[filename] = output.decode('utf-8')
                except subprocess.CalledProcessError as e:
                    self.errors[filename] = f'--help failed with error code {e.returncode}'

                try:
                    # Run --demo
                    output = subprocess.check_output([sys.executable, product_path, '--demo'])
                    self.demo_output[filename] = output.decode('utf-8')
                except subprocess.CalledProcessError as e:
                    self.errors[filename] = f'--demo failed with error code {e.returncode}'

    # Check if SQLite file gets created after running
    def check_sqlite_file(self):
        return os.path.exists(self.sqlite_file)

    # Calculate the build score
    def calculate_score(self):
        # For now, just return a score of 5
        return 5

    # Save the build score to the SQLite database
    def save_score(self, product, score):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        c.execute("INSERT INTO build_scores VALUES (?, ?, ?)",
                   (product, score, str(datetime.datetime.now())))
        conn.commit()
        conn.close()

    # Get the build score from the SQLite database
    def get_score(self, product):
        conn = sqlite3.connect(self.sqlite_file)
        c = conn.cursor()
        c.execute("SELECT score FROM build_scores WHERE product=?", (product,))
        row = c.fetchone()
        conn.close()
        if row:
            return row[0]
        else:
            return None

# Define the main function
def main():
    parser = argparse.ArgumentParser(description='Build Scorer')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    args = parser.parse_args()

    scorer = BuildScorer()
    scorer.create_db()
    scorer.run_products()

    if args.demo:
        print('Demo mode:')
        for product, output in scorer.help_output.items():
            print(f'{product} --help:')
            print(output)
        for product, output in scorer.demo_output.items():
            print(f'{product} --demo:')
            print(output)
    else:
        print('Running products:')
        for product, output in scorer.help_output.items():
            print(f'{product} --help:')
            print(output)
        for product, output in scorer.demo_output.items():
            print(f'{product} --demo:')
            print(output)

    if scorer.check_sqlite_file():
        print('SQLite file created successfully')
    else:
        print('Failed to create SQLite file')

    score = scorer.calculate_score()
    scorer.save_score('product.py', score)
    print(f'Build score: {score}')

    if scorer.get_score('product.py'):
        print(f'Score retrieved from database: {scorer.get_score("product.py")}')
    else:
        print('Failed to retrieve score from database')

if __name__ == '__main__':
    main()