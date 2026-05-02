#!/usr/bin/env python3
"""
JARVIS Quality Scorer — asks Mistral to evaluate builds the way Ted would.
Runs after every build. Catches weak demos before Ted sees them.
Writes quality_score to build memory so the system learns what Ted likes.
"""
import os, json, sys, sqlite3, subprocess
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

JARVIS = os.path.expanduser("~/jarvis")

def get_demo_output(product_dir):
    """Run --demo and capture output."""
    main = os.path.join(product_dir, "main.py")
    if not os.path.exists(main):
        return None
    try:
        r = subprocess.run(
            ["python3", main, "--demo"],
            capture_output=True, text=True, timeout=15
        )
        out = r.stdout.strip()
        return out if out else None
    except:
        return None

def score_with_mistral(product_name, demo_output, code_path):
    """Ask Mistral to score this build the way Ted would."""
    try:
        with open(code_path) as f:
            code = f.read()[:2000]
    except:
        code = "unavailable"

    prompt = f"""You are Ted, a solo developer in Phuket evaluating a CLI tool.
Rate this product honestly 1-10. Be strict — only give 8+ if it's genuinely impressive.

Product: {product_name}
Demo output:
---
{demo_output[:500] if demo_output else "NO OUTPUT"}
---
Code preview (first 2000 chars):
{code}
---

Ted's standards:
- 9-10: Demo shows real workflow, formatted output, solves obvious pain, could sell today
- 7-8: Demo works, output is readable, idea is solid, needs minor polish
- 5-6: Demo runs but output is weak/raw/confusing, or idea is vague
- 3-4: Demo broken or useless output or wrong idea
- 1-2: Doesn't work or completely wrong direction

Reply ONLY as JSON:
{{
  "quality_score": 7,
  "demo_quality": "good/weak/broken",
  "what_works": "one sentence",
  "what_to_fix": "one sentence — the most important thing to improve",
  "sellable_today": false,
  "ted_would_say": "one sentence casual reaction like Ted would say"
}}"""

    return ask_json(prompt)

def evaluate_latest():
    """Evaluate the most recently built product."""
    products = sorted([
        p for p in os.listdir(f"{JARVIS}/products")
        if p.startswith("202") and os.path.isdir(f"{JARVIS}/products/{p}")
    ])
    if not products:
        print("No products found")
        return

    latest = products[-1]
    product_dir = f"{JARVIS}/products/{latest}"
    main_path   = f"{product_dir}/main.py"

    print(f"\n{'='*50}")
    print(f"JARVIS QUALITY CHECK — {latest}")
    print(f"{'='*50}")

    demo_out = get_demo_output(product_dir)
    if demo_out:
        print(f"Demo output ({len(demo_out)} chars):")
        print(demo_out[:300])
    else:
        print("❌ No demo output")

    print("\nAsking Mistral to score...")
    result = score_with_mistral(latest, demo_out, main_path)

    if not result:
        print("❌ Mistral scoring failed")
        return

    score    = result.get("quality_score", 0)
    demo_q   = result.get("demo_quality","?")
    works    = result.get("what_works","?")
    fix      = result.get("what_to_fix","?")
    sellable = result.get("sellable_today", False)
    ted_says = result.get("ted_would_say","?")

    icon = "🔥" if score >= 8 else "✅" if score >= 6 else "⚠️" if score >= 4 else "❌"
    print(f"\n{icon} Quality Score: {score}/10")
    print(f"   Demo: {demo_q}")
    print(f"   Works: {works}")
    print(f"   Fix: {fix}")
    print(f"   Sellable: {'YES 💰' if sellable else 'not yet'}")
    print(f"   Ted would say: \"{ted_says}\"")

    # Save to quality log
    quality_log = f"{JARVIS}/memory/quality_scores.json"
    try:
        log = json.load(open(quality_log))
    except:
        log = []

    log.append({
        "date": datetime.now().isoformat(),
        "product": latest,
        "quality_score": score,
        "demo_quality": demo_q,
        "what_works": works,
        "what_to_fix": fix,
        "sellable_today": sellable,
        "ted_would_say": ted_says
    })
    log = log[-50:]
    with open(quality_log, "w") as f:
        json.dump(log, f, indent=2)

    # If quality score is low — write to build failures for reflexion
    if score < 6:
        failures_log = f"{JARVIS}/memory/build_failures.json"
        try:
            fails = json.load(open(failures_log))
        except:
            fails = []
        fails.append({
            "date": datetime.now().isoformat(),
            "product": latest,
            "phase": 3,
            "errors": [f"Quality score {score}/10: {fix}"],
            "score": score
        })
        fails = fails[-50:]
        with open(failures_log, "w") as f:
            json.dump(fails, f, indent=2)
        print(f"\n📝 Low quality logged — reflexion will address this tonight")

    # If sellable — flag it
    if sellable:
        print(f"\n💰 SELLABLE PRODUCT DETECTED — consider adding Stripe!")

    print(f"\n{'='*50}\n")
    return result

def show_history():
    """Show quality score history."""
    try:
        log = json.load(open(f"{JARVIS}/memory/quality_scores.json"))
    except:
        print("No quality history yet")
        return
    print(f"\n{'='*50}")
    print("QUALITY SCORE HISTORY")
    print(f"{'='*50}")
    for entry in log[-10:]:
        score = entry.get("quality_score",0)
        icon = "🔥" if score>=8 else "✅" if score>=6 else "⚠️"
        print(f"{icon} {score}/10 {entry['product'][:35]}")
        print(f"   {entry.get('ted_would_say','')[:65]}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--latest", action="store_true", help="Score latest product")
    p.add_argument("--history", action="store_true", help="Show score history")
    p.add_argument("--all", action="store_true", help="Score all products")
    args = p.parse_args()

    if args.history:
        show_history()
    elif args.all:
        products = sorted([
            x for x in os.listdir(f"{JARVIS}/products")
            if x.startswith("202")
        ])
        for prod in products[-5:]:
            product_dir = f"{JARVIS}/products/{prod}"
            demo_out = get_demo_output(product_dir)
            result = score_with_mistral(prod, demo_out, f"{product_dir}/main.py")
            if result:
                print(f"{result.get('quality_score')}/10 {prod} — {result.get('ted_would_say','')[:50]}")
    else:
        evaluate_latest()
