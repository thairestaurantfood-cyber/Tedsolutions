#!/usr/bin/env python3
"""
JARVIS Reflexion Engine — runs after every build + after ratings
Implements the Reflexion pattern: failure → reflection → stored lesson → better next build
This is what separates a system that repeats mistakes from one that genuinely learns.
"""
import os, json, sqlite3, sys
from datetime import datetime
sys.path.insert(0, os.path.expanduser("~/jarvis"))
from api import ask

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

MEMORY   = os.path.expanduser("~/jarvis/memory")
FAILURES = os.path.join(MEMORY, "build_failures.json")
LESSONS  = os.path.join(MEMORY, "lessons.db")
CONTEXT  = os.path.join(MEMORY, "context.md")

def get_db():
    os.makedirs(MEMORY, exist_ok=True)
    db = sqlite3.connect(LESSONS)
    db.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        source TEXT,
        lesson_type TEXT,
        pattern TEXT,
        reflection TEXT,
        times_seen INTEGER DEFAULT 1,
        score_impact REAL DEFAULT 0
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS reflections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        product TEXT,
        phase INTEGER,
        error TEXT,
        reflection TEXT,
        applied INTEGER DEFAULT 0
    )""")
    db.commit()
    return db

def reflect_on_failure(product, phase, error, broken_code=""):
    """
    Core Reflexion: given a failure, ask Mistral to generate
    a specific actionable lesson — not generic advice.
    """
    print(f"  🪞 Reflecting on: {product} phase {phase}...")
    prompt = f"""You are analyzing a failed Python CLI build to extract a specific lesson.

Product: {product}
Phase: {phase}
Error: {error}
Code length: {len(broken_code)} chars

Write a SPECIFIC lesson in this exact format:
PATTERN: [what specific coding pattern caused this — e.g. "adding multiple functions in phase 2 exceeds 200 line limit"]
REFLECTION: [one sentence: what went wrong and the exact rule to follow next time]
RULE: [one imperative sentence starting with NEVER or ALWAYS — e.g. "NEVER add more than 2 new functions in a single phase"]

Be specific. Not "write better code" — but the exact mistake and exact fix."""

    raw = ask(prompt, fast=True)
    if not raw:
        return None

    pattern, reflection, rule = "", "", ""
    for line in raw.strip().split("\n"):
        if line.startswith("PATTERN:"): pattern = line.replace("PATTERN:","").strip()
        elif line.startswith("REFLECTION:"): reflection = line.replace("REFLECTION:","").strip()
        elif line.startswith("RULE:"): rule = line.replace("RULE:","").strip()

    if not reflection:
        return None

    db = get_db()
    # Check if we've seen this pattern before — if so increment times_seen
    existing = db.execute(
        "SELECT id, times_seen FROM lessons WHERE pattern LIKE ? AND lesson_type='build_failure'",
        (f"%{pattern[:50]}%",)
    ).fetchone()

    if existing:
        db.execute("UPDATE lessons SET times_seen=times_seen+1, date=? WHERE id=?",
                   (datetime.now().isoformat(), existing[0]))
        print(f"  📈 Pattern seen {existing[1]+1}x: {pattern[:60]}")
    else:
        db.execute("""INSERT INTO lessons (date, source, lesson_type, pattern, reflection)
                      VALUES (?,?,?,?,?)""",
                   (datetime.now().isoformat(), product, "build_failure", pattern, reflection))
        print(f"  💡 New lesson: {reflection[:70]}")

    # Store full reflection
    db.execute("""INSERT INTO reflections (date, product, phase, error, reflection)
                  VALUES (?,?,?,?,?)""",
               (datetime.now().isoformat(), product, phase, error[:200],
                f"{reflection} {rule}"))
    db.commit()
    db.close()
    return reflection

def reflect_on_rating(product, score, feedback):
    """After Ted rates a build, extract lessons from the feedback."""
    if not feedback or score == 0:
        return
    print(f"  🪞 Reflecting on rating: {product} ({score}/10)...")

    prompt = f"""A Python CLI product was rated {score}/10 by a human reviewer.
Product: {product}
Reviewer feedback: "{feedback}"
Score: {score}/10

Extract the core lesson. Reply in this format:
PATTERN: [what specific thing caused this score — good or bad]
REFLECTION: [what to do more or less of next time]
RULE: [one ALWAYS or NEVER rule]"""

    raw = ask(prompt, fast=True)
    if not raw: return

    pattern, reflection, rule = "", "", ""
    for line in raw.strip().split("\n"):
        if line.startswith("PATTERN:"): pattern = line.replace("PATTERN:","").strip()
        elif line.startswith("REFLECTION:"): reflection = line.replace("REFLECTION:","").strip()
        elif line.startswith("RULE:"): rule = line.replace("RULE:","").strip()

    if not reflection: return

    lesson_type = "good_pattern" if score >= 7 else "bad_pattern"
    db = get_db()
    db.execute("""INSERT INTO lessons (date, source, lesson_type, pattern, reflection, score_impact)
                  VALUES (?,?,?,?,?,?)""",
               (datetime.now().isoformat(), product, lesson_type, pattern,
                f"{reflection} {rule}", score - 5))
    db.commit()
    db.close()
    print(f"  💡 Rating lesson saved: {reflection[:70]}")

def get_top_lessons(n=8):
    """Get the most important lessons — high frequency failures + high impact patterns."""
    db = get_db()
    rows = db.execute("""
        SELECT lesson_type, pattern, reflection, times_seen, score_impact
        FROM lessons
        ORDER BY times_seen DESC, ABS(score_impact) DESC
        LIMIT ?
    """, (n,)).fetchall()
    db.close()
    return rows

def update_context_with_lessons():
    """
    Rewrite the LESSONS section of context.md with current top lessons.
    This is what makes each build smarter than the last.
    """
    lessons = get_top_lessons(10)
    if not lessons:
        print("  No lessons yet.")
        return

    # Build lessons block
    lines = ["\n== REFLEXION LESSONS (auto-generated, do not edit) =="]
    lines.append("These are patterns learned from actual build failures and Ted's ratings:\n")

    failures = [(l,p,r,t,s) for l,p,r,t,s in lessons if l=="build_failure"]
    goods    = [(l,p,r,t,s) for l,p,r,t,s in lessons if l=="good_pattern"]
    bads     = [(l,p,r,t,s) for l,p,r,t,s in lessons if l=="bad_pattern"]

    if failures:
        lines.append("NEVER DO (caused build failures):")
        for _,pattern,reflection,times,_ in failures[:4]:
            lines.append(f"  ❌ [{times}x] {reflection}")

    if goods:
        lines.append("\nALWAYS DO (caused good ratings):")
        for _,pattern,reflection,_,impact in goods[:3]:
            lines.append(f"  ✅ {reflection}")

    if bads:
        lines.append("\nAVOID (caused bad ratings):")
        for _,pattern,reflection,_,impact in bads[:3]:
            lines.append(f"  ⚠️  {reflection}")

    lessons_block = "\n".join(lines)

    # Read current context.md
    try:
        with open(CONTEXT) as f:
            ctx = f.read()
    except:
        ctx = ""

    # Replace or append the lessons block
    marker_start = "\n== REFLEXION LESSONS"
    marker_end   = "\n== "
    if marker_start in ctx:
        # Find end of lessons block
        start_idx = ctx.index(marker_start)
        end_idx   = ctx.find(marker_end, start_idx + len(marker_start))
        if end_idx == -1:
            ctx = ctx[:start_idx] + lessons_block
        else:
            ctx = ctx[:start_idx] + lessons_block + "\n" + ctx[end_idx:]
    else:
        ctx = ctx.rstrip() + "\n" + lessons_block

    with open(CONTEXT, "w") as f:
        f.write(ctx)
    print(f"  ✅ context.md updated with {len(lessons)} lessons")

def process_pending_failures():
    """Read build_failures.json and reflect on any unprocessed failures."""
    if not os.path.exists(FAILURES):
        print("  No failures log found.")
        return 0
    try:
        fails = json.load(open(FAILURES))
    except:
        return 0

    db = get_db()
    processed = 0
    for f in fails[-10:]:  # Last 10 only
        product = f.get("product","unknown")
        phase   = f.get("phase", 0)
        errors  = f.get("errors", [])
        if not errors: continue

        # Check not already reflected on
        existing = db.execute(
            "SELECT id FROM reflections WHERE product=? AND phase=?",
            (product, phase)
        ).fetchone()
        if existing: continue

        error_str = " | ".join(errors[:3])
        reflect_on_failure(product, phase, error_str)
        processed += 1

    db.close()
    return processed

def process_recent_ratings():
    """Read human_ratings from brain.db and reflect on recent ones."""
    try:
        brain_db = sqlite3.connect(os.path.expanduser("~/jarvis/memory/lessons.db"))
        rows = brain_db.execute("""
            SELECT product, score, feedback
            FROM human_ratings
            WHERE date >= date('now', '-7 days')
            ORDER BY date DESC LIMIT 20
        """).fetchall()
        brain_db.close()
    except Exception as e:
        print(f"  brain.db read failed: {e}")
        return 0

    db = get_db()
    processed = 0
    for product, score, feedback in rows:
        if not feedback: continue
        existing = db.execute(
            "SELECT id FROM lessons WHERE source=? AND lesson_type IN ('good_pattern','bad_pattern')",
            (product,)
        ).fetchone()
        if existing: continue
        reflect_on_rating(product, score, feedback)
        processed += 1
    db.close()
    return processed

def main():
    print(f"\n{'='*50}")
    print(f"JARVIS REFLEXION — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    print("📋 Processing build failures...")
    f_count = process_pending_failures()
    print(f"   {f_count} failures reflected on")

    print("\n⭐ Processing ratings...")
    r_count = process_recent_ratings()
    print(f"   {r_count} ratings reflected on")

    print("\n📝 Updating context.md with lessons...")
    update_context_with_lessons()

    lessons = get_top_lessons(5)
    if lessons:
        print(f"\n🧠 Top lessons so far:")
        for ltype, pattern, reflection, times, impact in lessons:
            icon = "✅" if ltype == "good_pattern" else "❌"
            print(f"   {icon} [{times}x] {reflection[:65]}")

    print(f"\n✅ Reflexion complete.\n{'='*50}\n")

if __name__ == "__main__":
    main()
