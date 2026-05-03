#!/usr/bin/env python3
"""
JARVIS Rate — Ted's morning review tool
Quick rating of latest builds → feeds lessons.db
"""
import os, sys, sqlite3, json, subprocess
from datetime import datetime

JARVIS = os.path.expanduser("~/jarvis")
LESSONS_DB = f"{JARVIS}/memory/lessons.db"
PRODUCTS_DIR = f"{JARVIS}/products"

def get_latest_products(n=5):
    dirs = sorted([d for d in os.listdir(PRODUCTS_DIR)
        if os.path.isdir(f"{PRODUCTS_DIR}/{d}")], reverse=True)
    return dirs[:n]

def run_demo(product_dir):
    main = f"{PRODUCTS_DIR}/{product_dir}/main.py"
    if not os.path.exists(main):
        return "no main.py found"
    try:
        result = subprocess.run(
            ["python3", main, "--demo"],
            capture_output=True, text=True, timeout=10)
        out = result.stdout + result.stderr
        return out[:600] if out else "no output"
    except Exception as e:
        return f"error: {e}"

def save_rating(product, score, feedback):
    db = sqlite3.connect(LESSONS_DB)
    pattern = "good_pattern" if score >= 7 else "bad_pattern"
    prefix = "ALWAYS" if score >= 8 else ("IMPROVE" if score >= 5 else "NEVER")
    lesson = f"{prefix}: {feedback}"
    db.execute("""INSERT INTO lessons (date, source, lesson_type, pattern, reflection, times_seen, score_impact)
        VALUES (?,?,?,?,?,?,?)""",
        (datetime.now().isoformat(), product, pattern,
         f"{product} scored {score}/10", lesson, 1, float(score-5)))
    db.commit()
    db.close()
    print(f"✅ Saved: {product} = {score}/10")

def main():
    print(f"""
╔══════════════════════════════════════╗
║       JARVIS RATE — BUILD REVIEW     ║
╚══════════════════════════════════════╝

RATING GUIDE:
  9-10  Sellable today — real value, clean demo, clear use case
   7-8  Good — works well, needs one more phase or polish
   5-6  OK — core idea valid, demo weak or incomplete  
   3-4  Poor — idea ok but broken or useless demo
   1-2  Fail — wrong idea or completely broken

""")
    products = get_latest_products(5)
    if not products:
        print("No products found.")
        return

    for i, p in enumerate(products):
        print(f"  {i+1}. {p}")
    print()

    try:
        choice = input("Which product to rate? (number or name, Enter for latest): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return

    if not choice:
        product = products[0]
    elif choice.isdigit():
        idx = int(choice) - 1
        product = products[idx] if 0 <= idx < len(products) else products[0]
    else:
        product = choice

    print(f"\n── Running demo: {product} ──\n")
    demo_out = run_demo(product)
    print(demo_out)

    print(f"""
── Rate this build ──
What to look for:
  • Does the demo actually show the core feature?
  • Is the output clear and readable?
  • Would someone pay for this?
  • Does it solve a real problem?
""")

    try:
        score_str = input("Score (1-10): ").strip()
        score = int(score_str)
        score = max(1, min(10, score))
    except (ValueError, EOFError, KeyboardInterrupt):
        print("Invalid score — cancelled.")
        return

    try:
        feedback = input("One line feedback (what to fix or keep): ").strip()
    except (EOFError, KeyboardInterrupt):
        feedback = "no feedback"

    if not feedback:
        feedback = "no feedback provided"

    save_rating(product, score, feedback)

    print(f"""
── Saved ──
  Product: {product}
  Score:   {score}/10
  Lesson:  {feedback}

JARVIS will learn from this tonight.
""")

if __name__ == "__main__":
    main()
