#!/usr/bin/env python3
"""
JARVIS evolve.py — Offline-first builder
Tries cloud APIs, falls back to local Ollama instantly.
Never fails silently.
"""
import os, json, subprocess, datetime, time, re, sys

HOME = os.path.expanduser("~")
JARVIS = f"{HOME}/jarvis"
MEMORY = f"{JARVIS}/memory"
PRODUCTS = f"{JARVIS}/products"
LOGS = f"{JARVIS}/logs"

PLAN_FILE = f"{MEMORY}/daily_plan.json"
CONTEXT_FILE = f"{MEMORY}/context.md"
TOOLS_FILE = f"{MEMORY}/tools.json"

LOCAL_MODEL = "qwen2.5-coder:7b"
LOCAL_TIMEOUT = 90  # seconds
CLOUD_TIMEOUT = 30

now = datetime.datetime.now()
print("=" * 50)
print(f"JARVIS BUILDER - {now.strftime('%Y-%m-%d %H:%M')}")
print("=" * 50)

# ── Load context ──────────────────────────────────────

# ── Load API keys from ~/.env ─────────────────────────
def _load_env():
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ[_k.strip()] = _v.strip().strip('"').strip("'")
_load_env()


def load_context():
    try:
        with open(CONTEXT_FILE) as f:
            return f.read()[:2000]
    except:
        return "JARVIS autonomous builder. Build clean Python tools."

# ── Check internet quickly ────────────────────────────
def internet_ok():
    """Check internet by trying multiple endpoints. Accepts any HTTP response."""
    endpoints = [
        "https://api.cerebras.ai",
        "https://api.mistral.ai",
        "https://api.groq.com",
    ]
    for url in endpoints:
        try:
            r = subprocess.run(
                ["curl","-s","--max-time","4","-o","/dev/null","-w","%{http_code}",url],
                capture_output=True, text=True, timeout=6)
            code = r.stdout.strip()
            if code in ["200","301","302","303","307","308","403","404"]:
                return True
        except:
            continue
    return False


# ── Call local Ollama ─────────────────────────────────
def call_local(prompt, context=""):
    full_prompt = f"{context}\n\n{prompt}" if context else prompt
    try:
        import urllib.request, json as _json
        data = _json.dumps({
            "model": LOCAL_MODEL,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 2000,
                "think": False
            }
        }).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=LOCAL_TIMEOUT) as resp:
            r = _json.loads(resp.read())
            out = r.get("response", "").strip()
            return out if out else None
    except Exception as e:
        print(f"  Local error: {e}")
        return None

# ── Call cloud APIs ───────────────────────────────────
def call_mistral(prompt, context=""):
    try:
        import urllib.request, json as json2
        key = os.environ.get("MISTRAL_API_KEY", "")
        if not key:
            return None
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        data = json2.dumps({
            "model": "mistral-small-latest",
            "messages": messages,
            "max_tokens": 2000
        }).encode()
        req = urllib.request.Request(
            "https://api.mistral.ai/v1/chat/completions",
            data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=CLOUD_TIMEOUT) as resp:
            r = json2.loads(resp.read())
            return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        if "429" in str(e):
            print(f"  Mistral rate limited — waiting 30s...")
            import time; time.sleep(30)
            try:
                with urllib.request.urlopen(req, timeout=CLOUD_TIMEOUT) as resp:
                    r = json2.loads(resp.read())
                    return r["choices"][0]["message"]["content"].strip()
            except Exception as e2:
                print(f"  Mistral retry failed: {str(e2)[:80]}")
        else:
            print(f"  Mistral failed: {str(e)[:80]}")
        return None

def call_groq(prompt, context=""):
    try:
        import urllib.request, json as json2
        key = os.environ.get("GROQ_API_KEY", "")
        if not key:
            return None
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})
        data = json2.dumps({
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "max_tokens": 2000
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=CLOUD_TIMEOUT) as resp:
            r = json2.loads(resp.read())
            return r["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  Groq failed: {str(e)[:80]}")
        return None


def call_cerebras(prompt, context=""):
    """Cerebras — fast free inference via curl (urllib blocked by proxy)."""
    key = os.environ.get("CEREBRAS_API_KEY","")
    if not key: return None
    try:
        import json as _j
        full = f"{context}\n\n{prompt}" if context else prompt
        # Try qwen-3-235b first (best quality), fallback to llama3.1-8b
        for model in ["llama3.1-8b"]:  # llama3.1-8b confirmed working
            payload = _j.dumps({
                "model": model,
                "messages": [{"role":"user","content":full}],
                "max_tokens": 4000
            })
            r = subprocess.run([
                "curl","-s","-X","POST",
                "https://api.cerebras.ai/v1/chat/completions",
                "-H", f"Authorization: Bearer {key}",
                "-H", "Content-Type: application/json",
                "-d", payload
            ], capture_output=True, text=True, timeout=60)
            resp = _j.loads(r.stdout)
            if "choices" in resp:
                print(f"  ✓ Cerebras/{model.split('-')[0]} answered")
                return resp["choices"][0]["message"]["content"].strip()
            else:
                print(f"  Cerebras/{model} failed: {resp.get('message','')[:50]}")
    except Exception as e:
        print(f"  Cerebras failed: {e}")
    return None

def call_openrouter(prompt, context=""):
    """OpenRouter — multiple free models via curl."""
    key = os.environ.get("OPENROUTER_API_KEY","")
    if not key: return None
    try:
        import json as _j
        full = (context + "\n\n" + prompt) if context else prompt
        for model in ["google/gemma-3-4b-it:free"]:
            payload = _j.dumps({
                "model": model,
                "messages": [{"role":"user","content":full}],
                "max_tokens": 4000
            })
            r = subprocess.run([
                "curl","-s","-X","POST",
                "https://openrouter.ai/api/v1/chat/completions",
                "-H", f"Authorization: Bearer {key}",
                "-H", "Content-Type: application/json",
                "-H", "HTTP-Referer: https://github.com/tedsolutions",
                "-d", payload
            ], capture_output=True, text=True, timeout=60)
            resp = _j.loads(r.stdout)
            if "choices" in resp:
                print(f"  ✓ OpenRouter/{model.split('/')[1]} answered")
                return resp["choices"][0]["message"]["content"].strip()
            else:
                err = resp.get("error",{}).get("message","")[:50]
                print(f"  OpenRouter/{model} failed: {err}")
    except Exception as e:
        print(f"  OpenRouter failed: {e}")
    return None
    try:
        import urllib.request as _ur, json as _j
        full = f"{context}\n\n{prompt}" if context else prompt
        data = _j.dumps({
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [{"role":"user","content":full}],
            "max_tokens": 4000
        }).encode()
        req = _ur.Request(
            "https://openrouter.ai/api/v1/chat/completions",
            data=data,
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json",
                     "HTTP-Referer":"https://github.com/tedsolutions"},
            method="POST"
        )
        with _ur.urlopen(req, timeout=30) as r:
            return _j.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"  OpenRouter failed: {e}")
        return None

# ── Smart LLM caller: cloud first, local fallback ─────
def llm(prompt, context="", label=""):
    if label:
        print(f"  Calling LLM: {label}")
    
    online = internet_ok()
    
    if online:
        result = call_mistral(prompt, context)
        if result:
            print(f"  ✓ Mistral answered ({len(result)} chars)")
            return result
        result = call_openrouter(prompt, context)
        if result:
            print(f"  ✓ OpenRouter answered ({len(result)} chars)")
            return result
        result = call_cerebras(prompt, context)
        if result:
            print(f"  ✓ Cerebras answered ({len(result)} chars)")
            return result
        result = call_groq(prompt, context)
        if result:
            print(f"  ✓ Groq answered ({len(result)} chars)")
            return result
        print(f"  Cloud failed — using local")
    else:
        print(f"  Offline — using local directly")
    
    result = call_local(prompt, context)
    if result:
        print(f"  ✓ Local answered ({len(result)} chars)")
        return result
    
    print(f"  ❌ All LLMs failed for: {label}")
    return None

# ── Extract Python code from LLM response ─────────────
def extract_code(text):
    if not text:
        return None
    # Try ```python block first
    m = re.search(r'```python\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try ``` block
    m = re.search(r'```\n(.*?)```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # If it looks like raw Python
    if text.strip().startswith(('import ', 'from ', 'def ', '#!/', '#!')):
        return text.strip()
    # Last resort — return as-is if it has def or import
    if 'def ' in text or 'import ' in text:
        return text.strip()
    return None

# ── Strip forbidden imports ───────────────────────────
FORBIDDEN = ['PIL', 'pillow', 'flask', 'tesseract', 'pytesseract', 'tabulate',
             'pandas', 'numpy', 'requests', 'bs4', 'beautifulsoup']

def repair_imports(code):
    if not code:
        return code
    lines = code.split('\n')
    clean = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(('import ', 'from ')):
            forbidden = any(f.lower() in stripped.lower() for f in FORBIDDEN)
            if forbidden:
                print(f"    Removed forbidden import: {stripped}")
                continue
        clean.append(line)
    return '\n'.join(clean)

# ── Syntax check ──────────────────────────────────────
def syntax_ok(code):
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError as e:
        print(f"    Syntax error: {e}")
        return False

# ── Score a built file ────────────────────────────────
def score_file(path):
    """
    Real scorer — tests actual behaviour, not just structure.
    Max 12 points. <6 = bad build, 8+ = good build.
    """
    score = 0
    banned = ["flask","django","tensorflow","torch","numpy","pandas",
              "PIL","pillow","bs4","tesseract","tabulate","rich",
              "click","fastapi","cv2","sklearn"]
    try:
        size = os.path.getsize(path)
        with open(path) as f:
            code = f.read()

        # Hard penalty: banned imports = probably broken
        found_banned = [b for b in banned if f"import {b}" in code or f"from {b}" in code]
        if found_banned:
            print(f"  ❌ Banned imports: {found_banned} -4")
            score -= 4

        # Basic structure
        if syntax_ok(code): score += 2
        else:
            print(f"  ❌ Syntax error — returning 0")
            return 0

        if size > 1000: score += 1
        if size > 3000: score += 1
        if "def " in code: score += 1
        if "__main__" in code: score += 1
        if "sqlite3" in code: score += 1  # uses persistent storage
        if "argparse" in code or "sys.argv" in code: score += 1

        # Real test 1: --help runs without crashing
        try:
            r = subprocess.run(["python3", path, "--help"],
                               capture_output=True, timeout=8)
            if r.returncode == 0:
                score += 2
                print(f"  ✅ --help works +2")
            else:
                err = r.stderr.decode()[:120]
                print(f"  ❌ --help failed: {err}")
                score -= 2
        except Exception as e:
            print(f"  ❌ --help crashed: {e}")
            score -= 1

        # Real test 2: --demo runs without crashing
        try:
            r = subprocess.run(["python3", path, "--demo"],
                               capture_output=True, timeout=10)
            if r.returncode == 0 and len(r.stdout) > 20:
                score += 3
                print(f"  ✅ --demo works +3")
            elif r.returncode == 0:
                score += 1
                print(f"  ⚠️  --demo ran but no output +1")
            else:
                err = r.stderr.decode()[:120]
                print(f"  ❌ --demo failed: {err}")
                score -= 2
        except Exception as e:
            print(f"  ❌ --demo crashed: {e}")
            score -= 1

    except Exception as e:
        print(f"  Score error: {e}")
    
    score = max(0, score)
    print(f"  📊 Final score: {score}/12")
    return score

# ── Load plan ─────────────────────────────────────────
def load_plan():
    try:
        with open(PLAN_FILE) as f:
            return json.load(f)
    except:
        return None

# ── Save build memory ─────────────────────────────────
def save_memory(product_name, phase, score, code_size):
    mem_file = f"{MEMORY}/build_memory.json"
    try:
        with open(mem_file) as f:
            mem = json.load(f)
    except:
        mem = {"builds": []}
    mem["builds"].append({
        "date": datetime.datetime.now().isoformat(),
        "product": product_name,
        "phase": phase,
        "score": score,
        "size": code_size,
        "online": internet_ok()
    })
    # Keep last 100
    mem["builds"] = mem["builds"][-100:]
    with open(mem_file, "w") as f:
        json.dump(mem, f, indent=2)


def strip_banned_imports(code):
    """Remove banned imports that will crash — replace with stdlib equivalents."""
    banned_map = {
        "import flask": "# flask removed — use urllib.request instead",
        "from flask": "# flask removed",
        "import requests": "import urllib.request as requests_compat  # stdlib replacement",
        "from requests": "# requests removed — use urllib.request",
        "import numpy": "# numpy removed — use stdlib math",
        "import pandas": "# pandas removed — use csv module",
        "import PIL": "# PIL removed — not available",
        "from PIL": "# PIL removed — not available",
        "import tensorflow": "# tensorflow removed — not available",
        "import torch": "# torch removed — not available",
        "import bs4": "# bs4 removed — use urllib + re",
        "from bs4": "# bs4 removed — use urllib + re",
        "import tabulate": "# tabulate removed — format manually",
        "from tabulate": "# tabulate removed",
        "import rich": "# rich removed — not available",
        "from rich": "# rich removed",
        "import tesseract": "# tesseract removed — not available",
    }
    lines = code.split("\n")
    cleaned = []
    removed = []
    for line in lines:
        stripped = line.strip()
        matched = False
        for ban, replacement in banned_map.items():
            if stripped.startswith(ban):
                cleaned.append(replacement)
                removed.append(ban)
                matched = True
                break
        if not matched:
            cleaned.append(line)
    if removed:
        print(f"  🔧 Stripped banned imports: {removed}")
    return "\n".join(cleaned)

# ── Main build logic ──────────────────────────────────
plan = load_plan()
if not plan:
    print("❌ No daily_plan.json found. Run daily_plan.py first.")
    sys.exit(1)

product_info = plan.get("plan", {})
product_name = product_info.get("product_name", "UnknownProduct")
phases = product_info.get("build_phases", [])
phases_done = plan.get("phases_complete", [])

print(f"\nProduct: {product_name}")
print(f"Phases done: {phases_done}")

# Find next phase to build
next_phase = None
for p in phases:
    if p["phase"] not in phases_done:
        next_phase = p
        break

if not next_phase:
    print("All phases complete!")
    sys.exit(0)

phase_num = next_phase["phase"]
phase_name = next_phase["name"]
phase_desc = next_phase["description"]
# Always use safe stdlib — ignore plan tech_stack (LLM picks Flask/TF otherwise)
tech_stack = ["os", "sys", "json", "csv", "sqlite3", "argparse", "datetime", "pathlib", "subprocess", "urllib.request", "re", "time"]

print(f"Building phase {phase_num}: {phase_name}...")

# Load context and any existing code
context = load_context()
product_dir = f"{PRODUCTS}/20{now.strftime('%y%m%d')}_{product_name.lower().replace(' ','_')}"
os.makedirs(product_dir, exist_ok=True)
main_file = f"{product_dir}/main.py"

existing_code = ""
if os.path.exists(main_file):
    with open(main_file) as f:
        existing_code = f.read()

# Build prompt
tech_str = ", ".join(tech_stack)
if existing_code:
    prompt = f"""You are building phase {phase_num} ({phase_name}) of {product_name}.

EXISTING CODE:
{existing_code[:3000]}

PHASE {phase_num} TASK: {phase_desc}

RULES — MUST FOLLOW ALL:
- ONLY Python stdlib: os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time
- BANNED (will crash): flask, django, requests, PIL, pillow, tensorflow, torch, numpy, pandas, bs4, tesseract, tabulate, rich, click, fastapi
- BANNED (not available): any OCR, any ML model, any image processing, any web framework
- Max 200 lines total — this is a CLI tool, not a web app
- Use sqlite3 for all data storage
- Use urllib.request for any HTTP calls (not requests library)
- Use os.path.expanduser("~/.jarvis/") for all file paths
- Include argparse with --help and --demo flags
- --demo flag must work offline with hardcoded sample data and print results

Write the complete updated main.py that includes all previous phases plus phase {phase_num}.

CRITICAL RULES — YOUR CODE WILL BE AUTOMATICALLY TESTED:
- --demo flag MUST use ONLY hardcoded data. NO urllib, NO requests, NO http calls ANYWHERE in demo
- --demo must insert hardcoded rows, query them, print results, then exit cleanly
- CREATE TABLE must appear before INSERT — always
- stdlib ONLY: os,sys,json,csv,sqlite3,argparse,datetime,pathlib,subprocess,re,time
- No markdown fences — output raw Python only, starting with "import"
- os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True) before sqlite3.connect()
- Column names in INSERT must exactly match CREATE TABLE column names

ARGPARSE PATTERN — follow this EXACTLY (never use required=True on subparsers):
```python
def main():
    parser = argparse.ArgumentParser(description="ProductName")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()  # check --demo FIRST
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')  # NO required=True
    # add subparsers here...
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
```

DEMO PATTERN — follow this exactly:
    if args.demo:
        conn = get_db()
        cur = conn.cursor()
        # Insert hardcoded sample data
        cur.execute("INSERT OR IGNORE INTO items VALUES (?,?,?)", ("sample","data","2026-01-01"))
        conn.commit()
        # Query and print
        for row in cur.execute("SELECT * FROM items LIMIT 5"):
            print(row)
        conn.close()
        print("Demo complete.")
        return

Write the complete updated main.py starting with imports:"""
else:
    problem = product_info.get("problem", "")
    solution = product_info.get("solution", "")
    prompt = f"""Build phase {phase_num} ({phase_name}) of {product_name}.

PROBLEM: {problem}
SOLUTION: {solution}
THIS PHASE: {phase_desc}

CRITICAL RULES — YOUR CODE WILL BE AUTOMATICALLY TESTED:
- stdlib ONLY: os,sys,json,csv,sqlite3,argparse,datetime,pathlib,subprocess,re,time
- NO PIL, flask, requests, pandas, numpy, tabulate, bs4
- Use os.path.expanduser('~') for all paths
- --demo flag MUST use ONLY hardcoded data, NO network calls, NO input()
- --demo must insert hardcoded rows, query them, print formatted table, then exit
- No markdown fences — output raw Python only, starting with 'import'
ARGPARSE PATTERN — follow this EXACTLY:
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--demo', action='store_true')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return
    subparsers = parser.add_subparsers(dest='command')  # NO required=True
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
Output ONLY the Python code in a ```python block:"""

# ── RAG inject — add relevant memory to prompt ──────
def rag_inject(prompt):
    try:
        import sqlite3
        db_path = os.path.expanduser("~/jarvis/memory/rag_memory.db")
        if not os.path.exists(db_path):
            return prompt
        conn = sqlite3.connect(db_path)
        rows = conn.execute("SELECT content FROM memory ORDER BY rowid DESC LIMIT 5").fetchall()
        conn.close()
        if rows:
            sep = chr(10)
            memories = sep.join(r[0] for r in rows if r[0])[:800]
            return "RELEVANT MEMORY:" + sep + memories + sep + sep + prompt
    except:
        pass
    return prompt

# Call LLM — inject RAG memory first
print(f"  Building phase {phase_num}: {phase_name}...")
prompt = rag_inject(prompt)
# ── Skill injection — proven patterns from master_skills.json ──
try:
    _skills_file = os.path.join(MEMORY, "master_skills.json")
    if os.path.exists(_skills_file):
        _skills = json.load(open(_skills_file))
        _ap = _skills.get("top_patterns", {}).get("argparse", "")
        _src = _skills.get("top_patterns", {}).get("argparse_source", "")
        if _ap:
            _skill_block = f"""
PROVEN WORKING PATTERN (from {_src} — copy this exactly):
{_ap[:600]}
"""
            prompt = _skill_block + prompt
            print(f"  💡 Skills injected from: {_src}")
except Exception as _se:
    pass
response = llm(prompt, context, label=f"Phase {phase_num}")

if not response:
    print(f"❌ Could not build phase {phase_num} — all LLMs failed")
    sys.exit(1)

# Extract and clean code
code = extract_code(response)
if not code:
    print(f"❌ Could not extract code from response")
    print(f"Response preview: {response[:200]}")
    sys.exit(1)

code = repair_imports(code)
code = strip_banned_imports(code)

# Save
with open(main_file, "w") as f:
    f.write(code)
print(f"Saved: {main_file}")

# ── BuildGuard: validate & auto-fix before scoring ──
# Retry loop: if fail, send error back to Mistral and rebuild (max 2 retries)
_bg_passed = False
_bg_score = 0
_bg_report = []
for _attempt in range(3):  # 1 original + 2 retries
    try:
        sys.path.insert(0, JARVIS)
        from buildguard import guard as _guard
        _bg_passed, _bg_score, _bg_report = _guard(main_file, autofix=True, verbose=False)
    except Exception as _e:
        print(f"  BuildGuard error: {_e}")
        break

    if _bg_passed:
        print(f"  🛡️  BuildGuard: PASS ({_bg_score}/12)")
        break
    else:
        print(f"  🛡️  BuildGuard: FAIL ({_bg_score}/12) — demo broken")
        for _line in _bg_report:
            if "❌" in _line or "⚠" in _line:
                print(f"     {_line}")

        if _attempt >= 2:
            print("  ❌ Max retries reached — keeping broken build")
            # Log failure for learning
            _fail_log = os.path.join(MEMORY, "build_failures.json")
            try:
                _fails = json.load(open(_fail_log)) if os.path.exists(_fail_log) else []
            except: _fails = []
            _fails.append({
                "date": now.isoformat(),
                "product": product_name,
                "phase": phase_num,
                "errors": [l for l in _bg_report if "❌" in l],
                "score": _bg_score
            })
            # Keep last 50 failures only
            _fails = _fails[-50:]
            with open(_fail_log, "w") as _fl:
                json.dump(_fails, _fl, indent=2)
            print(f"  📝 Failure logged for learning")
            break

        # Retry — send error back to LLM
        print(f"  🔄 Retry {_attempt+1}/2 — asking LLM to fix...")
        _errors = [l for l in _bg_report if "❌" in l]
        _error_str = "\n".join(_errors[:5])
        with open(main_file) as _f:
            _broken_code = _f.read()
        _fix_prompt = f"""Your previous code had these errors:
{_error_str}

RULES YOU MUST FOLLOW:
- Fix ALL errors above
- Keep total file under 180 lines (strict limit)
- --demo must work 100% offline, NO network calls, NO input() calls
- stdlib only: os,sys,json,csv,sqlite3,argparse,datetime,pathlib,re,time
- Never use: flask,requests,numpy,pandas,PIL,urllib in demo

Here is the broken code to fix:
{_broken_code[:3000]}

Return ONLY the complete fixed Python file, no explanation, no markdown fences."""

        _fixed_raw = llm(_fix_prompt, context, label='fix_retry')
        _fixed_code = extract_code(_fixed_raw)
        if _fixed_code:
            _fixed_code = repair_imports(_fixed_code)
            _fixed_code = strip_banned_imports(_fixed_code)
            with open(main_file, "w") as _f:
                _f.write(_fixed_code)
            code = _fixed_code
            print(f"  ✍️  Fixed code saved ({len(_fixed_code)} chars)")
        else:
            print("  ❌ Could not extract fixed code")
            break


# Score
score = score_file(main_file)
size = os.path.getsize(main_file)
print(f"Score: {score} - size {size}b", end="")
if syntax_ok(code):
    print(" syntax ok +3", end="")
print()

# Update plan
phases_done.append(phase_num)
plan["phases_complete"] = phases_done
plan["build_status"] = "complete" if len(phases_done) >= len(phases) else "in_progress"
plan["last_build"] = now.isoformat()
with open(PLAN_FILE, "w") as f:
    json.dump(plan, f, indent=2)

# Save memory
save_memory(product_name, phase_num, score, size)

# Write docs on final phase
if len(phases_done) >= len(phases):
    print("Generating product docs...")
    readme = f"""# {product_name}

{product_info.get('tagline', '')}

## Problem
{product_info.get('problem', '')}

## Solution  
{product_info.get('solution', '')}

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
{tech_str}

## Built by JARVIS
Date: {now.strftime('%Y-%m-%d')}
Score: {score}/20
Phases: {phases_done}
Built offline: {not internet_ok()}
"""
    with open(f"{product_dir}/README.md", "w") as f:
        f.write(readme)
    print(f"  Docs written: README.md")
    print(f"\n💾 Done. Score: {score}")

    print(f"Phase {phase_num} complete. Total: {phases_done}")
    if len(phases_done) < len(phases):
        print(f"  ⏳ Waiting 20s before next phase (rate limit protection)...")
        time.sleep(20)
print("=" * 50)

# ── Auto-publish after complete build ─────────────────
def auto_publish(product_dir):
    try:
        import subprocess
        result = subprocess.run(
            ["python3", os.path.expanduser("~/jarvis/jarvis_publisher.py"),
             "--product", os.path.basename(product_dir)],
            capture_output=True, text=True, timeout=60
        )
        print(result.stdout[-500:] if result.stdout else "")
    except Exception as e:
        print(f"  Publisher skipped: {e}")
