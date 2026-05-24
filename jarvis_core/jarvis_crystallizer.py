#!/usr/bin/env python3
"""
JARVIS Crystallizer — runs daily at 17:50, after the 5pm build
Distills today's builds into a crisp summary for Hermes/Brain to use tomorrow.
Reads: quality_scores.json, build_memory.json
Writes: memory/daily_crystal.json
"""
import os, json, sys
from datetime import datetime, date

def load_env():
    p = os.path.expanduser("~/.env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

load_env()
MEMORY = os.path.expanduser("~/jarvis/memory")
LOG    = os.path.expanduser("~/jarvis/logs/crystallizer.log")

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return []

def main():
    today = date.today().isoformat()
    log(f"Crystallizer starting for {today}")

    scores = load_json(f"{MEMORY}/quality_scores.json")
    builds = load_json(f"{MEMORY}/build_memory.json").get("builds", [])

    # Today's scores
    today_scores = [s for s in scores if s.get("date","").startswith(today)]
    today_builds = [b for b in builds if b.get("date","").startswith(today)]

    if not today_scores and not today_builds:
        log("No builds today — nothing to crystallize")
        return

    # Best build today
    best = max(today_scores, key=lambda x: x.get("quality_score", 0)) if today_scores else None

    # Patterns
    sellable = [s for s in today_scores if s.get("sellable_today")]
    broken_demos = [s for s in today_scores if s.get("demo_quality") == "broken"]
    avg_score = sum(s.get("quality_score",0) for s in today_scores) / len(today_scores) if today_scores else 0

    crystal = {
        "date": today,
        "generated_at": datetime.now().isoformat(),
        "builds_today": len(today_builds),
        "scored_today": len(today_scores),
        "avg_score": round(avg_score, 1),
        "best_build": best.get("product") if best else None,
        "best_score": best.get("quality_score") if best else None,
        "best_what_works": best.get("what_works") if best else None,
        "best_what_to_fix": best.get("what_to_fix") if best else None,
        "sellable_count": len(sellable),
        "broken_demo_count": len(broken_demos),
        "broken_demo_products": [s.get("product") for s in broken_demos],
        "recommendation": (
            f"Polish {best['product']} — score {best['quality_score']}, fix: {best['what_to_fix']}"
            if best and best.get("quality_score",0) >= 7
            else "No strong build today — try a different idea tomorrow"
        ),
        "all_products_today": [s.get("product") for s in today_scores]
    }

    out = f"{MEMORY}/daily_crystal.json"
    with open(out, "w") as f:
        json.dump(crystal, f, indent=2)

    log(f"Best build: {crystal['best_build']} (score {crystal['best_score']})")
    log(f"Avg score: {crystal['avg_score']} across {crystal['builds_today']} builds")
    log(f"Sellable today: {crystal['sellable_count']}")
    log(f"Recommendation: {crystal['recommendation']}")
    log(f"Crystal saved to {out}")

if __name__ == "__main__":
    main()
