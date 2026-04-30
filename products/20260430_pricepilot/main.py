import os
import sys
import argparse
import sqlite3
import datetime
import pathlib
import subprocess
import urllib.request
import re
import time

# Define get_db function to create database if it doesn't exist
def get_db():
    db_path = os.path.expanduser("~/.pricepilot.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            price REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            site TEXT NOT NULL,
            status TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id TEXT NOT NULL,
            item_data TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    return conn

def extract_price(text, patterns):
    """Apply multiple regex patterns to extract price from HTML"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None

def scrape_site(url, product_id, site_tag):
    # Define extraction patterns for different site structures
    patterns_map = {
        'amazon': [r'"priceAmount":"?(\d+\.?\d*)"?', r'<span.*?id="price".*?[\$](\d+\.\d+)', r'price":(\d+\.\d+)'],
        'newegg': [r'ProductSalePrice">[\$](\d+\.\d+)', r'data-price="(\d+\.\d+)'],
        'bestbuy': [r'price":"(\d+\.\d+)"', r'currentPrice">\$(\d+\.\d+)'],
        'default': [r'[\$](\d+\.\d+)', r'price.?["\']?:.?(\d+\.\d+)']
    }
    patterns = patterns_map.get(site_tag, patterns_map['default'])

    try:
        if '--demo' in sys.argv:
            result = {
                'https://www.amazon.com': {
                    'product_id': '12345',
                    'site_tag': 'amazon',
                    'patterns': patterns,
                    'price': 100,
                },
                'https://www.newegg.com': {
                    'product_id': '67890',
                    'site_tag': 'newegg',
                    'patterns': patterns,
                    'price': 200,
                },
                'https://www.bestbuy.com': {
                    'product_id': 'abcdef',
                    'site_tag': 'bestbuy',
                    'patterns': patterns,
                    'price': 300,
                },
            }
            url = result.get(next((k for k, v in result.items() if product_id == v['product_id']), None))
            if url is not None:
                return {'product_id': product_id, 'price': url['price'], 'site': site_tag, 'status': 'success'}
            else:
                return {'product_id': product_id, 'price': None, 'site': site_tag, 'status': 'failed'}
        else:
            if not url.startswith(('http://', 'https://')):
                raise ValueError("Invalid URL scheme")
            response = urllib.request.urlopen(url)
            text = response.read().decode('utf-8')
            return {'product_id': product_id, 'price': extract_price(text, patterns), 'site': site_tag, 'status': 'success'}
    except ValueError as e:
        return {'product_id': product_id, 'price': None, 'site': site_tag, 'status': str(e)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true', help='Run in demo mode')
    args = parser.parse_args()

    conn = get_db()
    cur = conn.cursor()

    if args.demo:
        # Insert hardcoded sample data
        # Clear and insert hardcoded demo data into prices table
        cur.execute("DELETE FROM prices")
        cur.execute("INSERT INTO prices (product_id, price, site, status) VALUES (?,?,?,?)",
                    ("widget-001", 29.99, "shopee", "success"))
        cur.execute("INSERT INTO prices (product_id, price, site, status) VALUES (?,?,?,?)",
                    ("widget-001", 31.50, "lazada", "success"))
        cur.execute("INSERT INTO prices (product_id, price, site, status) VALUES (?,?,?,?)",
                    ("widget-001", 28.00, "amazon", "success"))
        conn.commit()
        print("\n=== PricePilot Demo ===")
        print(f"{'Product':<15} {'Site':<10} {'Price':>8}  {'Time'}")
        print("-" * 50)
        for row in cur.execute("SELECT product_id, site, price, timestamp FROM prices ORDER BY price"):
            print(f"{row[0]:<15} {row[1]:<10} ${row[2]:>7.2f}  {row[3]}")
        conn.close()
        print("\nDemo complete. 3 prices tracked across 3 sites.")
        return

    # Scrape site
    url = 'https://www.example.com'
    product_id = '12345'
    site_tag = 'amazon'
    result = scrape_site(url, product_id, site_tag)
    print(result)

    # Insert scraped data into database
    if result['status'] == 'success':
        cur.execute("INSERT INTO prices VALUES (NULL,?,?,?,?,?)", (result['product_id'], result['price'], result['timestamp'], result['site'], result['status']))
        conn.commit()
    else:
        cur.execute("INSERT INTO prices VALUES (NULL,?,?,?,?,?)", (result['product_id'], None, result['timestamp'], result['site'], result['status']))
        conn.commit()

    # Query database and print results
    for row in cur.execute("SELECT * FROM prices"):
        print(row)

    conn.close()

if __name__=='__main__':
    main()