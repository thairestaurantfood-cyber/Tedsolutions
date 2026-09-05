import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/gridcarbon.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS grids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        country TEXT NOT NULL,
        carbon_intensity REAL NOT NULL,
        last_updated TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sample_data = [
        ('Phuket Grid', 'Thailand', 0.5, now),
        ('Bangkok Grid', 'Thailand', 0.6, now),
        ('Singapore Grid', 'Singapore', 0.4, now),
        ('Kuala Lumpur Grid', 'Malaysia', 0.7, now),
        ('Jakarta Grid', 'Indonesia', 0.8, now)
    ]

    cursor.executemany('''
    INSERT INTO grids (name, country, carbon_intensity, last_updated)
    VALUES (?, ?, ?, ?)
    ''', sample_data)

    conn.commit()

    cursor.execute('SELECT name, country, carbon_intensity, last_updated FROM grids ORDER BY carbon_intensity')
    rows = cursor.fetchall()

    print(f"{'Grid':<20}{'Region':<15}{'Carbon Intensity (gCO2/kWh)':<30}{'Last Updated'}")
    print('-' * 80)
    for row in rows:
        print(f"{row[0]:<20}{row[1]:<15}{row[2]:<30}{row[3]}")

    conn.close()
    print("\nDemo complete.")

def list_grids(region=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = 'SELECT name, country, carbon_intensity, last_updated FROM grids'
    if region:
        query += ' WHERE country = ? ORDER BY carbon_intensity'
        cursor.execute(query, (region,))
    else:
        query += ' ORDER BY carbon_intensity'
        cursor.execute(query)

    rows = cursor.fetchall()

    print(f"{'Grid':<20}{'Region':<15}{'Carbon Intensity (gCO2/kWh)':<30}{'Last Updated'}")
    print('-' * 80)
    for row in rows:
        print(f"{row[0]:<20}{row[1]:<15}{row[2]:<30}{row[3]}")

    conn.close()

def show_tips():
    tips = [
        "Use renewable energy sources when possible",
        "Unplug devices when not in use",
        "Use energy-efficient appliances",
        "Adjust your thermostat to save energy",
        "Use LED bulbs instead of incandescent bulbs",
        "Wash clothes with cold water",
        "Air dry your clothes instead of using a dryer",
        "Take shorter showers",
        "Use a programmable thermostat",
        "Insulate your home to reduce heating and cooling costs"
    ]

    print("Carbon Footprint Reduction Tips:")
    print("-" * 30)
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")

def main():
    parser = argparse.ArgumentParser(description="GridCarbon - Carbon Intensity Tracker")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')

    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    list_parser = subparsers.add_parser('list', help='List grids')
    list_parser.add_argument('--region', type=str, help='Filter by region')

    tips_parser = subparsers.add_parser('tips', help='Show carbon footprint reduction tips')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        list_grids(args.region)
    elif args.command == 'tips':
        show_tips()

if __name__ == "__main__":
    main()