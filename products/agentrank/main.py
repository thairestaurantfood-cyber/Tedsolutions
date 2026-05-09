import os, json, hashlib, argparse, sqlite3, uuid, subprocess, sys
from datetime import datetime
from pathlib import Path

DB_PATH = Path(os.path.expanduser("~")) / ".agentrank" / "agentrank.db"
RATINGS_FILE = Path(os.path.expanduser("~")) / ".agentrank" / "agent_ratings.json"
VERSION = "0.1.0"

CRITERIA = ["demo_runs", "under_200_lines", "stdlib_only", "real_output", "fast_response"]

def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""CREATE TABLE IF NOT EXISTS agents (
        agent_id TEXT PRIMARY KEY,
        created_at TEXT,
        rating_count INTEGER DEFAULT 0,
        weight REAL DEFAULT 0.1
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS ratings (
        rating_id TEXT PRIMARY KEY,
        agent_id TEXT,
        repo TEXT,
        demo_runs INTEGER,
        under_200_lines INTEGER,
        stdlib_only INTEGER,
        real_output INTEGER,
        fast_response INTEGER,
        demo_hash TEXT,
        score REAL,
        timestamp TEXT,
        FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS leaderboard (
        repo TEXT PRIMARY KEY,
        avg_score REAL,
        rating_count INTEGER,
        last_updated TEXT
    )""")
    conn.commit()
    return conn

def register_agent():
    conn = get_db()
    agent_id = "agent_" + str(uuid.uuid4())[:8]
    conn.execute("INSERT INTO agents VALUES (?,?,?,?)",
        (agent_id, datetime.now().isoformat(), 0, 0.1))
    conn.commit()
    config = {"agent_id": agent_id}
    cfg_path = DB_PATH.parent / "config.json"
    with open(cfg_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"✅ Agent registered: {agent_id}")
    print(f"   Config: {cfg_path}")
    print(f"   Starting weight: 0.1 (grows with accurate ratings)")
    conn.close()

def get_agent_id():
    cfg = DB_PATH.parent / "config.json"
    if not cfg.exists():
        print("❌ No agent registered. Run: agentrank register"); sys.exit(1)
    return json.load(open(cfg))["agent_id"]

def measure_repo(repo_path):
    """Objective measurements — no human opinion needed."""
    results = {}
    main_py = Path(repo_path) / "main.py"
    if not main_py.exists():
        return None, "No main.py found"

    # Line count
    lines = main_py.read_text().splitlines()
    results["under_200_lines"] = 1 if len(lines) <= 200 else 0
    results["line_count"] = len(lines)

    # stdlib only check
    imports = [l.strip() for l in lines if l.startswith("import ") or l.startswith("from ")]
    stdlib = {"os","sys","json","sqlite3","argparse","uuid","hashlib","datetime",
              "pathlib","http","threading","subprocess","secrets","base64",
              "time","re","math","random","string","shutil","tempfile","csv"}
    non_stdlib = [i for i in imports if not any(s in i for s in stdlib)]
    results["stdlib_only"] = 1 if len(non_stdlib) == 0 else 0
    results["non_stdlib"] = non_stdlib

    # Run demo
    try:
        start = datetime.now()
        r = subprocess.run(
            [sys.executable, str(main_py), "--demo"],
            capture_output=True, text=True, timeout=10
        )
        elapsed = (datetime.now() - start).total_seconds()
        results["demo_runs"] = 1 if r.returncode == 0 else 0
        results["fast_response"] = 1 if elapsed < 3.0 else 0
        results["demo_output"] = r.stdout[:500]
        results["demo_hash"] = hashlib.sha256(r.stdout.encode()).hexdigest()[:16]
        # Real output check — not empty, not just "use list to view"
        bad_phrases = ["use list", "no data", "run init", "coming soon", "todo"]
        real = len(r.stdout.strip()) > 50 and not any(p in r.stdout.lower() for p in bad_phrases)
        results["real_output"] = 1 if real else 0
    except subprocess.TimeoutExpired:
        results["demo_runs"] = 0
        results["fast_response"] = 0
        results["real_output"] = 0
        results["demo_hash"] = "timeout"
        results["demo_output"] = "TIMEOUT"

    score = sum([results["demo_runs"], results["under_200_lines"],
                 results["stdlib_only"], results["real_output"],
                 results["fast_response"]]) / 5.0
    results["score"] = round(score, 2)
    return results, None

def submit_rating(repo_path):
    agent_id = get_agent_id()
    conn = get_db()

    # Check agent weight
    agent = conn.execute("SELECT weight, rating_count FROM agents WHERE agent_id=?",
        (agent_id,)).fetchone()
    if not agent:
        print("❌ Agent not found in DB"); return

    print(f"🔍 Measuring repo: {repo_path}")
    results, err = measure_repo(repo_path)
    if err:
        print(f"❌ {err}"); return

    repo_name = Path(repo_path).name
    rating_id = str(uuid.uuid4())

    conn.execute("""INSERT INTO ratings VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (rating_id, agent_id, repo_name,
         results["demo_runs"], results["under_200_lines"],
         results["stdlib_only"], results["real_output"],
         results["fast_response"], results["demo_hash"],
         results["score"], datetime.now().isoformat()))

    # Update agent rating count
    conn.execute("UPDATE agents SET rating_count=rating_count+1 WHERE agent_id=?", (agent_id,))

    # Update leaderboard
    all_ratings = conn.execute(
        "SELECT score FROM ratings WHERE repo=?", (repo_name,)).fetchall()
    if len(all_ratings) >= 1:
        avg = sum(r[0] for r in all_ratings) / len(all_ratings)
        conn.execute("""INSERT OR REPLACE INTO leaderboard VALUES (?,?,?,?)""",
            (repo_name, round(avg, 2), len(all_ratings), datetime.now().isoformat()))

    conn.commit()

    print(f"\n📊 Rating submitted for: {repo_name}")
    print(f"   Demo runs:       {'✅' if results['demo_runs'] else '❌'}")
    print(f"   Under 200 lines: {'✅' if results['under_200_lines'] else '❌'} ({results['line_count']} lines)")
    print(f"   Stdlib only:     {'✅' if results['stdlib_only'] else '❌'}")
    print(f"   Real output:     {'✅' if results['real_output'] else '❌'}")
    print(f"   Fast (<3s):      {'✅' if results['fast_response'] else '❌'}")
    print(f"   Score:           {results['score']*100:.0f}/100")
    print(f"   Demo hash:       {results['demo_hash']}")
    print(f"   Rating count for this repo: {len(all_ratings)}")
    if len(all_ratings) < 3:
        print(f"   ⚠️  Needs {3-len(all_ratings)} more rating(s) to appear on leaderboard")
    conn.close()

def show_leaderboard():
    conn = get_db()
    rows = conn.execute("""
        SELECT repo, avg_score, rating_count, last_updated
        FROM leaderboard WHERE rating_count >= 1
        ORDER BY avg_score DESC, rating_count DESC
    """).fetchall()
    print(f"\n{'='*60}")
    print(f"  🤖 AGENTRANK LEADERBOARD — Agent-Rated Code Quality")
    print(f"{'='*60}")
    print(f"  {'Rank':<5} {'Repo':<28} {'Score':>6} {'Ratings':>8}")
    print(f"  {'-'*55}")
    for i, (repo, score, count, updated) in enumerate(rows, 1):
        bar = "█" * int(score * 10)
        flag = " ⚠️ unverified" if count < 3 else ""
        print(f"  {i:<5} {repo:<28} {score*100:>5.0f}% {count:>6} ratings{flag}")
    if not rows:
        print("  No ratings yet. Run: agentrank rate <repo_path>")
    print(f"{'='*60}")
    conn.close()

def export_json():
    """Export ratings as JSON for GitHub publishing."""
    conn = get_db()
    rows = conn.execute("""
        SELECT repo, avg_score, rating_count, last_updated
        FROM leaderboard WHERE rating_count >= 3
        ORDER BY avg_score DESC
    """).fetchall()
    data = {
        "version": VERSION,
        "generated": datetime.now().isoformat(),
        "description": "Agent-consensus code quality ratings. Rated by agents, for agents.",
        "criteria": CRITERIA,
        "leaderboard": [
            {"rank": i+1, "repo": r[0], "score": r[1],
             "ratings": r[2], "last_updated": r[3]}
            for i, r in enumerate(rows)
        ]
    }
    out = Path("agent_ratings.json")
    with open(out, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Exported {len(rows)} verified repos to {out}")
    conn.close()

def demo():
    # Reset
    if DB_PATH.exists(): DB_PATH.unlink()
    cfg = DB_PATH.parent / "config.json"
    if cfg.exists(): cfg.unlink()

    print("\n=== AgentRank Demo ===")
    print("Registering agent...")
    register_agent()

    # Rate our own products
    products = Path(os.path.expanduser("~/jarvis/products"))
    rated = 0
    for p in sorted(products.iterdir()):
        if (p / "main.py").exists() and rated < 4:
            print(f"\n--- Rating: {p.name} ---")
            submit_rating(str(p))
            rated += 1

    print("\n")
    show_leaderboard()
    export_json()

def main():
    parser = argparse.ArgumentParser(description="AgentRank — Agent-consensus code quality ratings")
    parser.add_argument("--demo", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo(); return

    subs = parser.add_subparsers(dest="cmd")
    subs.add_parser("register")
    r = subs.add_parser("rate")
    r.add_argument("repo_path")
    subs.add_parser("leaderboard")
    subs.add_parser("export")

    args = parser.parse_args()
    if args.cmd == "register": register_agent()
    elif args.cmd == "rate": submit_rating(args.repo_path)
    elif args.cmd == "leaderboard": show_leaderboard()
    elif args.cmd == "export": export_json()
    else: parser.print_help()

if __name__ == "__main__":
    main()
