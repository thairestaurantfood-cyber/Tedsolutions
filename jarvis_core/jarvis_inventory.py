#!/usr/bin/env python3
"""
JARVIS Tool Inventory — scans all products, maps capabilities,
suggests combinations. JARVIS sees what it's built and builds on it.
"""
import os, json, sqlite3, subprocess, sys, re
from datetime import datetime
sys.path.insert(0, os.path.expanduser("~/jarvis"))
from api import ask_json

def _load_env():
    p = os.path.expanduser('~/.env')
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                line=line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k,v=line.split('=',1)
                    os.environ[k.strip()]=v.strip().strip('"').strip("'")
_load_env()

JARVIS   = os.path.expanduser("~/jarvis")
PRODUCTS = f"{JARVIS}/products"
MEMORY   = f"{JARVIS}/memory"

def scan_product(name, product_dir):
    main = f"{product_dir}/main.py"
    if not os.path.exists(main):
        return None
    with open(main) as f:
        code = f.read()
    commands = re.findall(r"add_parser\(['\"](\w+)['\"]", code)
    tables   = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", code)
    lines    = len(code.split("\n"))
    try:
        r = subprocess.run(["python3", main, "--demo"],
            capture_output=True, text=True, timeout=10)
        demo_works  = r.returncode == 0 and len(r.stdout.strip()) > 10
        demo_output = r.stdout.strip()[:300]
    except:
        demo_works  = False
        demo_output = ""
    return {
        "name": name, "commands": commands, "tables": tables,
        "lines": lines, "demo_works": demo_works, "demo_output": demo_output
    }

def build_inventory():
    products = sorted([
        p for p in os.listdir(PRODUCTS)
        if p.startswith("202") and os.path.isdir(f"{PRODUCTS}/{p}")
    ])
    scores = {}
    try:
        db = sqlite3.connect(f"{MEMORY}/brain.db")
        for prod, score in db.execute(
            "SELECT product, ted_score FROM human_ratings").fetchall():
            scores[prod] = score
        db.close()
    except: pass

    inventory = []
    print(f"Scanning {len(products)} products...\n")
    for prod in products:
        caps = scan_product(prod, f"{PRODUCTS}/{prod}")
        if not caps: continue
        entry = {**caps, "ted_score": scores.get(prod)}
        inventory.append(entry)
        status = "✅" if caps["demo_works"] else "❌"
        score  = f"{scores[prod]}/10" if prod in scores else "unrated"
        print(f"{status} {prod} | {score} | {caps['lines']}L | tables:{caps['tables']}")

    with open(f"{MEMORY}/tool_inventory.json","w") as f:
        json.dump(inventory, f, indent=2)
    return inventory

def find_combinations(inventory):
    working = [t for t in inventory if t["demo_works"]]
    if len(working) < 2:
        print("Need 2+ working tools"); return

    summary = "\n".join([
        f"- {t['name']}: tables={t['tables']} commands={t['commands'][:3]}"
        for t in working[:8]
    ])

    result = ask_json(f"""Product architect for a solo Python CLI developer.

These tools are built and working:
{summary}

Suggest 3 powerful COMBINATIONS that create more value than each tool alone.
Think: what would a freelancer pay $49-99/month for as an all-in-one suite?

Reply ONLY as JSON array:
[{{
  "name": "FreelancerOS",
  "combines": ["tool1","tool2"],
  "tagline": "one sentence",
  "why_valuable": "why worth more than parts",
  "monthly_price": 49,
  "build_approach": "how to combine in one CLI"
}}]""")

    if not result:
        print("Combination research failed"); return

    combos = result if isinstance(result, list) else [result]
    print(f"\n{'='*55}")
    print("🔧 COMBINATION OPPORTUNITIES")
    print(f"{'='*55}\n")
    for c in combos:
        print(f"💡 {c.get('name')} — ${c.get('monthly_price')}/mo")
        print(f"   {c.get('tagline')}")
        print(f"   Combines: {', '.join(c.get('combines',[]))}")
        print(f"   Why: {c.get('why_valuable','')[:70]}")
        print(f"   Build: {c.get('build_approach','')[:70]}")
        print()

    # Add to validated ideas so planner builds them next
    try:
        existing = json.load(open(f"{MEMORY}/validated_ideas.json"))
    except:
        existing = []
    new_ideas = [{"title": f"{c.get('name')} — {c.get('tagline','')}",
                  "source":"tool_combination","score":9,"pain_score":9,
                  "verdict":"build","pain_evidence":c.get("why_valuable",""),
                  "validated_at":datetime.now().isoformat()} for c in combos]
    with open(f"{MEMORY}/validated_ideas.json","w") as f:
        json.dump(new_ideas + existing, f, indent=2)
    print(f"✅ {len(new_ideas)} combination ideas added to build queue")

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--scan",    action="store_true")
    p.add_argument("--combine", action="store_true")
    p.add_argument("--status",  action="store_true")
    args = p.parse_args()

    if args.status:
        try:
            inv = json.load(open(f"{MEMORY}/tool_inventory.json"))
            working = [t for t in inv if t["demo_works"]]
            rated   = [t for t in inv if t.get("ted_score")]
            good    = [t for t in rated if t["ted_score"] >= 7]
            print(f"\nTotal: {len(inv)} | Working: {len(working)} | Good(7+): {len(good)}")
            for t in sorted(inv, key=lambda x: x.get("ted_score") or 0, reverse=True):
                icon = "✅" if t["demo_works"] else "❌"
                score = f"{t['ted_score']}/10" if t.get("ted_score") else "?"
                print(f"  {icon} {score:>4} {t['name']}")
        except: print("Run --scan first")
    elif args.combine:
        try: inv = json.load(open(f"{MEMORY}/tool_inventory.json"))
        except: inv = build_inventory()
        find_combinations(inv)
    else:
        inv = build_inventory()
        find_combinations(inv)

if __name__ == "__main__":
    main()
