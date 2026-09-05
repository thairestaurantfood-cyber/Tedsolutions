import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta

DB_PATH = os.path.expanduser('~/ecogrid.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            region TEXT,
            timezone TEXT NOT NULL,
            carbon_intensity REAL,
            last_updated TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grid_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            kwh REAL NOT NULL,
            cost REAL,
            FOREIGN KEY(grid_id) REFERENCES grids(id)
        )
    ''')
    conn.commit()
    conn.close()

def suggest_optimal_times(grid_id, duration_hours):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT timezone, carbon_intensity
        FROM grids
        WHERE id = ?
    ''', (grid_id,))
    grid_info = cursor.fetchone()

    if not grid_info:
        print("Grid not found.")
        conn.close()
        return

    timezone, carbon_intensity = grid_info

    now = datetime.now()
    optimal_times = []

    for i in range(24):
        hour = (now.hour + i) % 24
        simulated_intensity = carbon_intensity * (0.8 + 0.4 * (hour / 24))

        optimal_times.append({
            'hour': hour,
            'carbon_intensity': simulated_intensity,
            'cost': simulated_intensity * 0.1
        })

    optimal_times.sort(key=lambda x: x['carbon_intensity'])

    print(f"\nOptimal times for grid {grid_id} (next {duration_hours} hours):")
    print(f"{'Hour':<10}{'Carbon Intensity':<20}{'Estimated Cost ($)':<20}")
    print('-' * 50)
    for time in optimal_times[:duration_hours]:
        print(f"{time['hour']:02d}:00    {time['carbon_intensity']:.2f} gCO2/kWh    {time['cost']:.2f}")

    conn.close()

def track_usage(grid_id, start_time, end_time, kwh):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT carbon_intensity
        FROM grids
        WHERE id = ?
    ''', (grid_id,))
    result = cursor.fetchone()

    if not result:
        print("Grid not found.")
        conn.close()
        return

    carbon_intensity = result[0]
    cost = carbon_intensity * 0.1 * kwh

    cursor.execute('''
        INSERT INTO usage (grid_id, start_time, end_time, kwh, cost)
        VALUES (?, ?, ?, ?, ?)
    ''', (grid_id, start_time, end_time, kwh, cost))

    conn.commit()
    conn.close()

    print(f"Usage tracked successfully. Estimated cost: ${cost:.2f}")

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    conn = sqlite3.connect(DB_PATH)

    # Insert sample data
    conn.execute("INSERT INTO grids (name, country, region, timezone, carbon_intensity, last_updated) VALUES ('Phuket Grid', 'Thailand', 'Southern', 'Asia/Bangkok', 45.2, '2023-01-01 12:00:00')")
    conn.execute("INSERT INTO grids (name, country, region, timezone, carbon_intensity, last_updated) VALUES ('Bangkok Grid', 'Thailand', 'Central', 'Asia/Bangkok', 52.8, '2023-01-01 12:00:00')")
    conn.execute("INSERT INTO grids (name, country, region, timezone, carbon_intensity, last_updated) VALUES ('Chiang Mai Grid', 'Thailand', 'Northern', 'Asia/Bangkok', 38.5, '2023-01-01 12:00:00')")

    conn.execute("INSERT INTO usage (grid_id, start_time, end_time, kwh, cost) VALUES (1, '2023-01-01 08:00:00', '2023-01-01 10:00:00', 15.5, 7.26)")
    conn.execute("INSERT INTO usage (grid_id, start_time, end_time, kwh, cost) VALUES (2, '2023-01-01 14:00:00', '2023-01-01 16:00:00', 12.3, 6.45)")
    conn.execute("INSERT INTO usage (grid_id, start_time, end_time, kwh, cost) VALUES (3, '2023-01-01 20:00:00', '2023-01-01 22:00:00', 8.7, 3.37)")

    conn.commit()

    # Print grids table
    print("\nGrids:")
    print(f"{'ID':<5}{'Name':<20}{'Country':<15}{'Region':<15}{'Timezone':<15}{'Carbon Intensity':<20}{'Last Updated'}")
    print("-" * 90)
    for row in conn.execute("SELECT * FROM grids"):
        print(f"{row[0]:<5}{row[1]:<20}{row[2]:<15}{row[3]:<15}{row[4]:<15}{row[5]:<20}{row[6]}")

    # Print usage table
    print("\nUsage:")
    print(f"{'ID':<5}{'Grid ID':<10}{'Start Time':<25}{'End Time':<25}{'kWh':<10}{'Cost'}")
    print("-" * 80)
    for row in conn.execute("SELECT * FROM usage"):
        print(f"{row[0]:<5}{row[1]:<10}{row[2]:<25}{row[3]:<25}{row[4]:<10}{row[5]}")

    conn.close()
    print("\nDemo complete.")

def main():
    parser = argparse.ArgumentParser(description="EcoGrid CLI")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Add subparsers for existing commands
    suggest_parser = subparsers.add_parser('suggest', help='Suggest optimal times for energy usage')
    suggest_parser.add_argument('grid_id', type=int, help='Grid ID')
    suggest_parser.add_argument('duration', type=int, help='Duration in hours')

    track_parser = subparsers.add_parser('track', help='Track energy usage')
    track_parser.add_argument('grid_id', type=int, help='Grid ID')
    track_parser.add_argument('start_time', help='Start time (YYYY-MM-DD HH:MM:SS)')
    track_parser.add_argument('end_time', help='End time (YYYY-MM-DD HH:MM:SS)')
    track_parser.add_argument('kwh', type=float, help='kWh used')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'suggest':
        suggest_optimal_times(args.grid_id, args.duration)
    elif args.command == 'track':
        track_usage(args.grid_id, args.start_time, args.end_time, args.kwh)

if __name__ == "__main__":
    main()