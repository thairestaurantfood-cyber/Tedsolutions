#!/usr/bin/env python3
"""
BuildGuard — validates and auto-fixes LLM-generated code before saving.
Kills the recurring demo bugs. Run after every phase build.

Usage: python3 buildguard.py <path/to/main.py>
Returns: exit 0 = pass, exit 1 = unfixable
"""
import sys, os, re, subprocess, ast, tempfile

BANNED = [
    "import flask","from flask",
    "import requests","from requests",
    "import numpy","import pandas",
    "import PIL","import tensorflow",
    "import torch","from torch",
    "import bs4","from bs4",
    "import tabulate","from tabulate",
    "import rich","from rich",
]

STDLIB_SUBS = {
    "import requests": "import urllib.request",
    "from requests import": "# requests removed — use urllib.request",
}

def load(path):
    with open(path) as f:
        return f.read()

def save(path, code):
    with open(path, "w") as f:
        f.write(code)

def fix_markdown_fence(code):
    """Remove ```python or ``` fences LLM sometimes leaves."""
    lines = code.splitlines()
    if lines and lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines)

def fix_banned_imports(code):
    """Replace or remove banned imports."""
    fixed = []
    changed = []
    for line in code.splitlines():
        stripped = line.strip()
        replaced = False
        for sub_old, sub_new in STDLIB_SUBS.items():
            if stripped.startswith(sub_old):
                fixed.append(line.replace(sub_old, sub_new))
                changed.append(f"  replaced: {stripped[:60]}")
                replaced = True
                break
        if not replaced:
            banned = any(stripped.startswith(b) for b in BANNED)
            if banned:
                fixed.append(f"# REMOVED: {line}")
                changed.append(f"  removed: {stripped[:60]}")
            else:
                fixed.append(line)
    return "\n".join(fixed), changed

def fix_makedirs(code):
    """Ensure os.makedirs before sqlite3.connect calls."""
    if "sqlite3.connect(" not in code:
        return code, []
    if "os.makedirs" in code:
        return code, []
    # Insert makedirs pattern after get_db or before sqlite3.connect
    old = "conn = sqlite3.connect("
    if old in code:
        # Find the db path variable
        idx = code.find(old)
        line_start = code.rfind("\n", 0, idx) + 1
        indent = len(code[line_start:idx]) - len(code[line_start:idx].lstrip())
        ind = " " * indent
        fix = f"{ind}os.makedirs(os.path.dirname(os.path.abspath({code[idx+len(old):code.find(')',idx)+1]})), exist_ok=True)\n"
        code = code[:idx] + fix + code[idx:]
        return code, ["  added os.makedirs before sqlite3.connect"]
    return code, []

def check_syntax(code):
    """Return (ok, error_msg)."""
    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError line {e.lineno}: {e.msg}"

def check_create_table(code):
    """Warn if INSERT appears before CREATE TABLE."""
    insert_pos = code.find("INSERT")
    create_pos = code.find("CREATE TABLE")
    if insert_pos != -1 and create_pos != -1 and insert_pos < create_pos:
        return False, "INSERT before CREATE TABLE"
    return True, None

def check_demo_offline(code):
    """Warn if --demo tries to fetch URLs."""
    if "--demo" not in code and "demo" not in code.lower():
        return True, None
    url_patterns = ["http://","https://","urllib.request.urlopen","requests.get"]
    demo_start = code.lower().find("demo")
    if demo_start == -1:
        return True, None
    demo_block = code[demo_start:demo_start+2000]
    for p in url_patterns:
        if p in demo_block:
            return False, f"Demo fetches URLs ({p}) — must use hardcoded data"
    return True, None

def run_demo(path):
    """Actually run --demo and return (ok, output)."""
    try:
        r = subprocess.run(
            ["python3", path, "--demo"],
            capture_output=True, text=True, timeout=15
        )
        if r.returncode == 0:
            return True, r.stdout[:200]
        else:
            return False, r.stderr[:300]
    except subprocess.TimeoutExpired:
        return False, "Demo timed out (>15s)"
    except Exception as e:
        return False, str(e)

def run_help(path):
    """Run --help and return (ok, output)."""
    try:
        r = subprocess.run(
            ["python3", path, "--help"],
            capture_output=True, text=True, timeout=10
        )
        return r.returncode == 0, r.stderr[:100] if r.returncode != 0 else ""
    except Exception as e:
        return False, str(e)

def guard(path, autofix=True, verbose=True):
    """
    Main guard function. Returns (passed, score, report).
    passed = True means safe to save/use.
    """
    report = []
    fixes = []
    code = load(path)
    original = code

    def log(msg): report.append(msg)

    # Auto-fixes
    if autofix:
        code2 = fix_markdown_fence(code)
        if code2 != code:
            fixes.append("  removed markdown fence")
            code = code2

        code2, changed = fix_banned_imports(code)
        if changed:
            fixes.extend(changed)
            code = code2

        code2, changed = fix_makedirs(code)
        if changed:
            fixes.extend(changed)
            code = code2

        if code != original:
            save(path, code)
            log(f"🔧 Auto-fixed {len(fixes)} issues:")
            for f in fixes:
                log(f)

    # Checks
    passed = True
    score = 0

    ok, err = check_syntax(code)
    if ok:
        log("✅ Syntax OK")
        score += 3
    else:
        log(f"❌ {err}")
        passed = False

    ok, err = check_create_table(code)
    if ok:
        log("✅ Table order OK")
        score += 1
    else:
        log(f"⚠️  {err}")

    ok, err = check_demo_offline(code)
    if ok:
        log("✅ Demo appears offline")
        score += 1
    else:
        log(f"⚠️  {err}")

    ok, _ = run_help(path)
    if ok:
        log("✅ --help works")
        score += 2
    else:
        log("❌ --help failed")
        passed = False

    ok, out = run_demo(path)
    if ok:
        # Quality check — not just "did it run" but "is output useful"
        out_stripped = out.strip()
        has_numbers  = any(c.isdigit() for c in out_stripped)
        has_newlines = out_stripped.count("\n") >= 2
        has_dollar   = "$" in out_stripped or "%" in out_stripped
        useful = has_numbers and has_newlines
        
        if useful:
            log(f"✅ --demo works ({len(out)} chars output)")
            score += 3
        elif len(out_stripped) > 20:
            log(f"⚠️  --demo ran but output looks weak (no table/numbers) +1")
            score += 1
        else:
            log(f"❌ --demo ran but no meaningful output")
        score += 5
    else:
        log(f"❌ --demo failed: {out[:150]}")
        passed = False

    log(f"\n{'✅ PASS' if passed else '❌ FAIL'} — BuildGuard score: {score}/12")

    if verbose:
        print("\n".join(report))

    return passed, score, report

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: buildguard.py <path/to/main.py> [--nofix]")
        sys.exit(1)
    path = sys.argv[1]
    autofix = "--nofix" not in sys.argv
    if not os.path.exists(path):
        print(f"❌ File not found: {path}")
        sys.exit(1)
    passed, score, _ = guard(path, autofix=autofix)
    sys.exit(0 if passed else 1)
