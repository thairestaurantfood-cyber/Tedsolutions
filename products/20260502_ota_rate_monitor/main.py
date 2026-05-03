import os
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/otarate.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hotels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (hotel_id) REFERENCES hotels (id) ON DELETE CASCADE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_id INTEGER NOT NULL,
            threshold REAL NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (hotel_id) REFERENCES hotels (id) ON DELETE CASCADE
        )
    """)
    return conn

def log_rate(hotel_id, price):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO rates (hotel_id, price, date, created_at) VALUES (?, ?, ?, ?)",
        (hotel_id, price, datetime.utcnow().strftime('%Y-%m-%d'), datetime.utcnow().isoformat())
    )
    conn.commit()
    print(f"Logged rate: {price} THB for hotel ID {hotel_id}")

def demo():
    conn = get_db()
    cur = conn.cursor()

    # Clear existing data
    cur.execute("DELETE FROM alerts")
    cur.execute("DELETE FROM rates")
    cur.execute("DELETE FROM hotels")
    conn.commit()

    # Insert sample hotels
    hotels = [
        (1, "Phuket Beach Resort", "https://phuketbeach.com", datetime.utcnow().isoformat()),
        (2, "Patong Paradise Hotel", "https://patongparadise.com", datetime.utcnow().isoformat()),
        (3, "Kata Cliff Villa", "https://katacliff.com", datetime.utcnow().isoformat())
    ]
    cur.executemany("INSERT OR IGNORE INTO hotels VALUES (?, ?, ?, ?)", hotels)

    # Insert sample rates
    rates = [
        (1, 1, 1200.0, "2024-05-01", datetime.utcnow().isoformat()),
        (2, 1, 1150.0, "2024-05-02", datetime.utcnow().isoformat()),
        (3, 2, 950.0, "2024-05-01", datetime.utcnow().isoformat()),
        (4, 2, 900.0, "2024-05-02", datetime.utcnow().isoformat()),
        (5, 3, 1800.0, "2024-05-01", datetime.utcnow().isoformat()),
        (6, 3, 1750.0, "2024-05-02", datetime.utcnow().isoformat())
    ]
    cur.executemany("INSERT OR IGNORE INTO rates VALUES (?, ?, ?, ?, ?)", rates)

    # Insert sample alerts
    alerts = [
        (1, 1, 1000.0, datetime.utcnow().isoformat()),
        (2, 2, 800.0, datetime.utcnow().isoformat())
    ]
    cur.executemany("INSERT OR IGNORE INTO alerts VALUES (?, ?, ?, ?)", alerts)

    conn.commit()

    # Print formatted output
    print("HOTELS:")
    for row in cur.execute("SELECT id, name, url FROM hotels ORDER BY id"):
        print(f"  {row[0]}. {row[1]} ({row[2]})")

    print("\nRATES:")
    for row in cur.execute("""
        SELECT h.name, r.price, r.date
        FROM rates r
        JOIN hotels h ON r.hotel_id = h.id
        ORDER BY r.date DESC, h.name
    """):
        print(f"  {row[0]}: {row[1]} THB on {row[2]}")

    print("\nALERTS:")
    for row in cur.execute("""
        SELECT h.name, a.threshold
        FROM alerts a
        JOIN hotels h ON a.hotel_id = h.id
        ORDER BY h.name
    """):
        print(f"  {row[0]}: below {row[1]} THB")

def main():
    parser = argparse.ArgumentParser(description="OTA Rate Monitor")
    parser.add_argument("--demo", action="store_true", help="Run demo with sample data")
    parser.add_argument("--log", type=int, help="Log a rate for hotel ID")
    parser.add_argument("--price", type=float, help="Price to log")
    args = parser.parse_args()

    if args.demo:
        demo()
    elif args.log is not None and args.price is not None:
        log_rate(args.log, args.price)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()