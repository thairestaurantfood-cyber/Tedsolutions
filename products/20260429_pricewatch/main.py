#!/usr/bin/env python3
"""PriceWatch — Track competitor prices via CLI. Stores history in SQLite."""
import os, sys, sqlite3, argparse, datetime, urllib.request, re, json, csv

DB_PATH = os.path.expanduser("~/.pricewatch.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS tracked (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT UNIQUE, label TEXT, added TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS prices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT, price REAL, raw TEXT, checked TEXT)""")
    conn.commit()
    return conn

def add_url(url, label=""):
    conn = get_db()
    try:
        conn.execute("INSERT OR IGNORE INTO tracked (url,label,added) VALUES (?,?,?)",
                     (url, label or url, datetime.datetime.now().isoformat()))
        conn.commit()
        print(f"✅ Tracking: {url}")
    except Exception as e:
        print(f"❌ {e}")
    conn.close()

def fetch_price(url):
    """Fetch page and try to extract a price with regex."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8","ignore")
        patterns = [
            r'\$\s*(\d+[\.,]\d{2})',
            r'price["\s:]+(\d+[\.,]\d{2})',
            r'(\d+[\.,]\d{2})\s*USD',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                raw = m.group(1).replace(",",".")
                return float(raw), m.group(0)[:40]
    except Exception as e:
        return None, str(e)[:60]
    return None, "no price found"

def check_all():
    conn = get_db()
    urls = conn.execute("SELECT url, label FROM tracked").fetchall()
    if not urls:
        print("No URLs tracked yet. Use --add-url first.")
        conn.close()
        return
    print(f"\n{'Label':25s} {'Price':10s} {'Change':10s} {'URL'}")
    print("─" * 70)
    for url, label in urls:
        price, raw = fetch_price(url)
        now = datetime.datetime.now().isoformat()
        # Get previous price
        prev = conn.execute(
            "SELECT price FROM prices WHERE url=? ORDER BY checked DESC LIMIT 1", (url,)
        ).fetchone()
        change = ""
        if price and prev and prev[0]:
            diff = price - prev[0]
            change = f"{'▲' if diff>0 else '▼'}{abs(diff):.2f}"
        if price:
            conn.execute("INSERT INTO prices (url,price,raw,checked) VALUES (?,?,?,?)",
                        (url, price, raw, now))
        conn.commit()
        price_str = f"${price:.2f}" if price else "n/a"
        print(f"  {label[:23]:25s} {price_str:10s} {change:10s} {url[:35]}")
    conn.close()

def show_history(url):
    conn = get_db()
    rows = conn.execute(
        "SELECT price, checked FROM prices WHERE url=? ORDER BY checked DESC LIMIT 20", (url,)
    ).fetchall()
    conn.close()
    if not rows:
        print(f"No history for {url}")
        return
    print(f"\nPrice history: {url}")
    print(f"{'Date':25s} {'Price'}")
    print("─" * 40)
    for price, checked in rows:
        print(f"  {checked[:19]:25s} ${price:.2f}")

def export_csv():
    conn = get_db()
    rows = conn.execute("SELECT url, price, raw, checked FROM prices ORDER BY checked").fetchall()
    conn.close()
    path = os.path.expanduser("~/pricewatch_export.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["url","price","raw_match","checked"])
        w.writerows(rows)
    print(f"✅ Exported {len(rows)} records to {path}")

def demo():
    """Run fully offline demo with fake data."""
    conn = get_db()
    now = datetime.datetime.now().isoformat()
    # Seed fake tracked sites
    sites = [
        ("https://shop-a.example.com", "Shop A", 29.99),
        ("https://shop-b.example.com", "Shop B", 34.50),
        ("https://shop-c.example.com", "Shop C", 27.00),
    ]
    for url, label, price in sites:
        conn.execute("INSERT OR IGNORE INTO tracked (url,label,added) VALUES (?,?,?)",
                     (url, label, now))
        conn.execute("INSERT INTO prices (url,price,raw,checked) VALUES (?,?,?,?)",
                     (url, price, f"${price}", now))
        # Add a second price point to show change
        conn.execute("INSERT INTO prices (url,price,raw,checked) VALUES (?,?,?,?)",
                     (url, price * 0.95, f"${price*0.95:.2f}",
                      (datetime.datetime.now() - datetime.timedelta(days=1)).isoformat()))
    conn.commit()
    conn.close()

    print("\n🔍 PRICEWATCH DEMO")
    print("─" * 60)
    print(f"  {'Label':20s} {'Current':10s} {'Yesterday':10s} {'Change'}")
    print("─" * 60)
    for url, label, price in sites:
        print(f"  {label:20s} ${price:>7.2f}    ${price*0.95:>7.2f}    ▲{price*0.05:.2f}")
    print()
    print("  ✅ 3 sites tracked | 1 alert triggered (Shop A +5%)")
    print("  Run --check to fetch live prices")
    print("  Run --export to get CSV report")

def main():
    p = argparse.ArgumentParser(description="PriceWatch — competitor price tracker")
    p.add_argument("--add-url", metavar="URL", help="Start tracking a URL")
    p.add_argument("--label", metavar="NAME", help="Label for the URL", default="")
    p.add_argument("--check", action="store_true", help="Check all tracked URLs now")
    p.add_argument("--history", metavar="URL", help="Show price history for URL")
    p.add_argument("--export", action="store_true", help="Export all data to CSV")
    p.add_argument("--demo", action="store_true", help="Run offline demo")
    args = p.parse_args()

    if args.demo:       demo()
    elif args.add_url:  add_url(args.add_url, args.label)
    elif args.check:    check_all()
    elif args.history:  show_history(args.history)
    elif args.export:   export_csv()
    else:               p.print_help()

if __name__ == "__main__":
    main()
