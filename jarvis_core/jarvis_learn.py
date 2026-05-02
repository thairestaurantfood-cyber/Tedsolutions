#!/usr/bin/env python3
"""
JARVIS Learning Loop — runs at 10pm daily.
Reads human ratings + build history → updates context.md with lessons.
"""
import os, json, sqlite3, subprocess
from datetime import datetime
from pathlib import Path

# Load API keys
def _load_env():
    env_path = os.path.expanduser('~/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
_load_env()

JARVIS   = os.path.expanduser('~/jarvis')
MEMORY   = f'{JARVIS}/memory'
CONTEXT  = f'{MEMORY}/context.md'
DB       = f'{MEMORY}/brain.db'
TG_TOKEN = os.getenv('TG_TOKEN','')
TG_CHAT  = os.getenv('TG_CHAT','')

def notify(msg):
    if not TG_TOKEN: return
    try:
        import urllib.request as _ur
        data = json.dumps({'chat_id':TG_CHAT,'text':msg}).encode()
        req = _ur.Request(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage',
            data=data, headers={'Content-Type':'application/json'})
        _ur.urlopen(req, timeout=8)
    except: pass

def get_ratings():
    """Load all human ratings from brain.db."""
    try:
        db = sqlite3.connect(DB)
        rows = db.execute('''SELECT product, ted_score, feedback, lesson, runs_demo
            FROM human_ratings ORDER BY ted_score DESC''').fetchall()
        db.close()
        return rows
    except Exception as e:
        print(f'  ratings error: {e}')
        return []

def get_build_memory():
    """Load recent build history."""
    try:
        mem_file = f'{MEMORY}/build_memory.json'
        with open(mem_file) as f:
            mem = json.load(f)
        return mem.get('builds', [])[-20:]
    except:
        return []

def extract_lessons(ratings):
    """Turn ratings into concrete lessons."""
    good = [r for r in ratings if r[1] >= 8]
    bad  = [r for r in ratings if r[1] <= 3]
    ok   = [r for r in ratings if 4 <= r[1] <= 7]

    lessons = []

    if good:
        lessons.append('=== BUILDS TO COPY (score 8-10) ===')
        for r in good:
            lessons.append(f'  ✅ {r[0]} ({r[1]}/10): {r[4] and "demo works" or "demo unknown"}')
            if r[3]: lessons.append(f'     Lesson: {r[3]}')

    if bad:
        lessons.append('=== BUILDS TO NEVER REPEAT (score 1-3) ===')
        for r in bad:
            lessons.append(f'  ❌ {r[0]} ({r[1]}/10)')
            if r[2]: lessons.append(f'     Why bad: {r[2][:100]}')

    if ok:
        lessons.append('=== BUILDS THAT NEED IMPROVEMENT (score 4-7) ===')
        for r in ok:
            lessons.append(f'  ⚠️  {r[0]} ({r[1]}/10)')
            if r[3]: lessons.append(f'     Fix: {r[3][:100]}')

    return lessons

def update_context(lessons, builds):
    """Rewrite the LEARNED section of context.md."""
    with open(CONTEXT) as f:
        content = f.read()

    # Build stats
    scores = [b.get('score', 0) for b in builds if b.get('score')]
    avg = sum(scores) / len(scores) if scores else 0
    online_builds = sum(1 for b in builds if b.get('online'))
    total = len(builds)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    new_section = f'''=== WHAT I HAVE LEARNED (updated {now}) ===
Health Score: {min(100, int(avg*8))}%
Total builds: {total}
Average build score: {int(avg)}
Best API so far: Cerebras (llama3.1-8b confirmed working)
Online builds: {online_builds}/{total}

Build lessons:
  - Do NOT use PIL, tensorflow, flask, tesseract, numpy — not available
  - ONLY use: os sys json csv datetime argparse sqlite3 pathlib subprocess urllib.request re time
  - Cerebras produces best code fastest (llama3.1-8b)
  - Keep builds under 200 lines for reliability
  - Always include --demo mode with hardcoded sample data — NO network calls in demo
  - Always include --help
  - os.makedirs before sqlite3.connect — always
  - INSERT column names must exactly match CREATE TABLE columns
  - Never use requests, flask, numpy, pandas

''' + '\n'.join(lessons) + '''

Last 5 builds:'''

    for b in builds[-5:]:
        new_section += f"\n  - {b.get('date','?')[:10]} | {b.get('product','?')} phase {b.get('phase','?')} | score:{b.get('score','?')}"

    # Replace existing learned section
    import re
    pattern = r'=== WHAT I HAVE LEARNED.*?(?=\n===|\Z)'
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(pattern, new_section, content, flags=re.DOTALL)
    else:
        content += '\n\n' + new_section

    with open(CONTEXT, 'w') as f:
        f.write(content)

    return new_section

def run_monitor():
    """Run jarvismon and return health summary."""
    try:
        mon = f'{JARVIS}/products/20260426_jarvismon/main.py'
        if not os.path.exists(mon): return 'monitor not found'
        r = subprocess.run(['python3', mon, '--log_dir', f'{JARVIS}/logs/'],
            capture_output=True, text=True, timeout=30)
        return r.stdout[:500]
    except Exception as e:
        return f'monitor error: {e}'

def main():
    print(f'\n{"="*50}')
    print(f'JARVIS LEARNING LOOP — {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print('='*50)

    # 1. Load ratings
    ratings = get_ratings()
    print(f'\n📊 Human ratings loaded: {len(ratings)}')
    for r in ratings[:5]:
        print(f'  {r[1]}/10 | {r[0]}')

    # 2. Load builds
    builds = get_build_memory()
    print(f'\n🏗️  Recent builds: {len(builds)}')

    # 3. Extract lessons
    lessons = extract_lessons(ratings)
    print(f'\n📚 Lessons extracted: {len(lessons)}')

    # 4. Update context.md
    section = update_context(lessons, builds)
    print(f'\n✅ context.md updated')

    # 5. Run health monitor
    print('\n🔍 Running health monitor...')
    health = run_monitor()
    if health and 'Health' in health:
        for line in health.splitlines():
            if any(x in line for x in ['Health','Score','DNS','Error']):
                print(f'  {line.strip()}')

    # 6. Summary stats
    good = sum(1 for r in ratings if r[1] >= 8)
    bad  = sum(1 for r in ratings if r[1] <= 3)
    print(f'\n📈 Summary: {good} great builds, {bad} failures, {len(ratings)-good-bad} ok')
    print(f'   Best products: {", ".join(r[0] for r in ratings if r[1]>=8)}')

    # 7. Notify
    msg = (f'🧠 JARVIS learned from {len(ratings)} rated builds\n'
           f'✅ Best: {ratings[0][0]} ({ratings[0][1]}/10)\n' if ratings else
           f'🧠 JARVIS learning loop ran — no ratings yet\n')
    notify(msg)

    print('\n✅ Learning loop complete')

if __name__ == '__main__':
    main()
