#!/usr/bin/env python3
"""
JARVIS Backup — pushes all key JARVIS files to GitHub nightly.
Never lose a session's work again.
"""
import os, json, base64, urllib.request, urllib.error
from datetime import datetime

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
TOKEN  = os.getenv("GITHUB_TOKEN","")
USER   = os.getenv("GITHUB_USER","thairestaurantfood-cyber")
REPO   = os.getenv("GITHUB_REPO","Tedsolutions")

# Files to back up every night
BACKUP_FILES = [
    "evolve.py",
    "api.py",
    "daily_plan.py",
    "buildguard.py",
    "jarvis_reflect.py",
    "jarvis_quality.py",
    "jarvis_inventory.py",
    "jarvis_backup.py",
    "pain_validator.py",
    "telegram_commander.py",
    "jarvis_publisher.py",
    "jarvis_learn.py",
    "memory/context.md",
    "memory/validated_ideas.json",
    "memory/daily_plan.json",
    "jarvis_crystallizer.py",
    "jarvis_pain_scout.py",
    "rate.py",
    "memory/master_skills.json",
]

def github_put(path, content, message):
    url = f"https://api.github.com/repos/{USER}/{REPO}/contents/jarvis_core/{path}"
    content_b64 = base64.b64encode(content).decode()
    # Check if file exists to get SHA
    sha = None
    try:
        req = urllib.request.Request(url,
            headers={"Authorization":f"Bearer {TOKEN}","User-Agent":"JARVIS"})
        with urllib.request.urlopen(req, timeout=10) as r:
            sha = json.loads(r.read()).get("sha")
    except: pass

    payload = {"message": message, "content": content_b64}
    if sha:
        payload["sha"] = sha

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="PUT",
        headers={"Authorization":f"Bearer {TOKEN}",
                 "Content-Type":"application/json",
                 "User-Agent":"JARVIS"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def main():
    print(f"\n{'='*50}")
    print(f"JARVIS BACKUP — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}\n")

    if not TOKEN:
        print("❌ No GitHub token"); return

    success, failed = 0, 0
    msg = f"JARVIS auto-backup {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    for rel_path in BACKUP_FILES:
        full_path = f"{JARVIS}/{rel_path}"
        if not os.path.exists(full_path):
            print(f"  ⚠️  Missing: {rel_path}")
            continue
        try:
            with open(full_path, "rb") as f:
                content = f.read()
            github_put(rel_path, content, msg)
            print(f"  ✅ {rel_path}")
            success += 1
        except Exception as e:
            print(f"  ❌ {rel_path}: {str(e)[:50]}")
            failed += 1

    print(f"\n✅ Backed up {success} files | ❌ Failed: {failed}")
    print(f"View: https://github.com/{USER}/{REPO}/tree/main/jarvis_core")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
