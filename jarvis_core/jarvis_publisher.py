#!/usr/bin/env python3
"""
JARVIS Publisher — Auto-publishes every finished build.

What it does:
  1. Pushes product code to GitHub tedsolutions repo
  2. Generates HTML landing page for the product
  3. Sends email summary to Ted with GitHub link
  4. Marks product as published in brain.db

Run after every build:
  python3 ~/jarvis/jarvis_publisher.py --product 20260428_fpga_insights
  python3 ~/jarvis/jarvis_publisher.py --all        (publish everything unpublished)
  python3 ~/jarvis/jarvis_publisher.py --status     (show what's published)
"""

import os, json, re, smtplib, urllib.request, urllib.parse
import base64, sqlite3, argparse, subprocess

def ask_hermes(prompt):
    """Use local Ollama model instead of Hermes."""
    try:
        import requests
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5-coder:7b",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        return r.json().get("response", "").strip()
    except Exception as e:
        return f"LOCAL LLM ERROR: {e}"

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

HOME     = os.path.expanduser("~")
JARVIS   = f"{HOME}/jarvis"
PRODUCTS = f"{JARVIS}/products"
MEMORY   = f"{JARVIS}/memory"
LOG      = f"{JARVIS}/logs/publisher.log"

# Load .env
for line in open(f"{HOME}/.env", errors="replace"):
    k, _, v = line.strip().partition("=")
    if k and v: os.environ[k] = v

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USER  = os.getenv("GITHUB_USER", "thairestaurantfood-cyber")
GITHUB_REPO  = os.getenv("GITHUB_REPO", "Tedsolutions")
SMTP_USER    = os.getenv("SMTP_USER", "")
SMTP_PASS    = os.getenv("SMTP_PASS", "")
TG_TOKEN     = os.getenv("TG_TOKEN", "")
TG_CHAT      = os.getenv("TG_CHAT", "")

os.makedirs(f"{JARVIS}/logs", exist_ok=True)


def trigger_vercel():
    """Ping Vercel deploy hook after every publish."""
    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.vercel.com/v1/integrations/deploy/prj_Nv9lifD6j0mLmRWZpUAbwuPWoqwc/vn3T6kbNfm",
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            log(f"🚀 Vercel deploy triggered: {r.status}")
            return True
    except Exception as e:
        log(f"⚠️  Vercel trigger failed: {e}")
        return False

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")

# ── GITHUB API ────────────────────────────────────────
def github_api(method, path, data=None):
    url = f"https://api.github.com{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    req.add_header("User-Agent", "JARVIS")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/vnd.github.v3+json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {}, e.code

def file_exists_on_github(path):
    result, status = github_api("GET",
        f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path}")
    return status == 200, result.get("sha", "")

def push_file(repo_path, content, commit_msg):
    """Push a single file to GitHub."""
    encoded = base64.b64encode(content.encode()).decode()
    exists, sha = file_exists_on_github(repo_path)
    data = {
        "message": commit_msg,
        "content": encoded,
    }
    if exists and sha:
        data["sha"] = sha
    result, status = github_api("PUT",
        f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{repo_path}",
        data)
    return status in (200, 201)

# ── LANDING PAGE GENERATOR ────────────────────────────
def generate_landing_page(product_name, tagline, problem,
                           solution, tech_stack, github_url):
    clean_name = product_name.replace("_", " ").title()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{clean_name}</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background:#0a0a0a; color:#e0e0e0; }}
  .hero {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
           padding: 80px 20px; text-align:center; }}
  .hero h1 {{ font-size:2.8rem; font-weight:800; color:#fff;
              margin-bottom:16px; letter-spacing:-1px; }}
  .hero p  {{ font-size:1.2rem; color:#94a3b8; max-width:600px;
              margin:0 auto 32px; line-height:1.6; }}
  .badge {{ display:inline-block; background:#0f3460; color:#60a5fa;
            padding:6px 16px; border-radius:999px; font-size:0.85rem;
            border:1px solid #1e40af; margin-bottom:24px; }}
  .btn {{ display:inline-block; background:#3b82f6; color:#fff;
          padding:14px 32px; border-radius:8px; text-decoration:none;
          font-weight:600; font-size:1rem; margin:8px;
          transition:background 0.2s; }}
  .btn:hover {{ background:#2563eb; }}
  .btn.secondary {{ background:transparent; border:1px solid #374151; color:#9ca3af; }}
  .section {{ max-width:800px; margin:0 auto; padding:60px 20px; }}
  .section h2 {{ font-size:1.6rem; font-weight:700; margin-bottom:16px; color:#fff; }}
  .section p  {{ color:#94a3b8; line-height:1.8; margin-bottom:16px; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
            gap:16px; margin-top:24px; }}
  .card {{ background:#111; border:1px solid #1f2937; border-radius:12px;
           padding:24px; }}
  .card h3 {{ color:#60a5fa; font-size:1rem; margin-bottom:8px; }}
  .card p  {{ color:#6b7280; font-size:0.9rem; line-height:1.6; }}
  .tech {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }}
  .tech span {{ background:#1f2937; color:#9ca3af; padding:4px 12px;
                border-radius:6px; font-size:0.8rem; font-family:monospace; }}
  .footer {{ text-align:center; padding:40px 20px; color:#374151;
             font-size:0.85rem; border-top:1px solid #111; }}
  .jarvis-badge {{ color:#3b82f6; font-weight:600; }}
</style>
</head>
<body>
<div class="hero">
  <div class="badge">🤖 Built by JARVIS</div>
  <h1>{clean_name}</h1>
  <p>{tagline}</p>
  <a href="{github_url}" class="btn">View on GitHub</a>
  <a href="#about" class="btn secondary">Learn More</a>
</div>

<div class="section" id="about">
  <h2>The Problem</h2>
  <p>{problem}</p>

  <h2 style="margin-top:40px">The Solution</h2>
  <p>{solution}</p>

  <div class="cards" style="margin-top:40px">
    <div class="card">
      <h3>🚀 Open Source</h3>
      <p>Full source code available on GitHub. Fork it, modify it, deploy it.</p>
    </div>
    <div class="card">
      <h3>🐍 Pure Python</h3>
      <p>No heavy dependencies. Runs anywhere Python runs.</p>
    </div>
    <div class="card">
      <h3>💾 Local First</h3>
      <p>Your data stays on your machine. SQLite storage, no cloud required.</p>
    </div>
  </div>

  <h2 style="margin-top:48px">Tech Stack</h2>
  <div class="tech">
    {"".join(f"<span>{t.strip()}</span>" for t in tech_stack.split(","))}
  </div>
</div>

<div class="footer">
  Built autonomously by <span class="jarvis-badge">JARVIS</span> —
  {datetime.now().strftime("%B %Y")} ·
  <a href="https://github.com/{GITHUB_USER}/{GITHUB_REPO}"
     style="color:#3b82f6">tedsolutions</a>
</div>
</body>
</html>"""

# ── EMAIL SENDER ──────────────────────────────────────
def send_email(subject, body_html):
    if not SMTP_USER or not SMTP_PASS:
        log("  Email skipped — no SMTP config")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = SMTP_USER
        msg["To"]      = SMTP_USER
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as s:
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, SMTP_USER, msg.as_string())
        log(f"  ✅ Email sent to {SMTP_USER}")
        return True
    except Exception as e:
        log(f"  ❌ Email failed: {e}")
        return False

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return False
    try:
        data = json.dumps({
            "chat_id": TG_CHAT,
            "text": msg,
            "parse_mode": "HTML"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=8):
            return True
    except:
        return False

# ── GET PUBLISHED STATUS DB ───────────────────────────
def get_pub_db():
    db = sqlite3.connect(f"{MEMORY}/published.db")
    db.execute("""CREATE TABLE IF NOT EXISTS published (
        product TEXT PRIMARY KEY,
        github_url TEXT, page_url TEXT,
        date TEXT, score INTEGER
    )""")
    db.commit()
    return db

# ── PUBLISH ONE PRODUCT ───────────────────────────────
def publish_product(product_dir):
    folder = os.path.basename(product_dir)
    main_py = f"{product_dir}/main.py"
    readme  = f"{product_dir}/README.md"

    if not os.path.exists(main_py):
        log(f"  ✗ No main.py in {folder}")
        return False

    log(f"\n📦 Publishing: {folder}")

    # Read files
    with open(main_py) as f:
        code = f.read()

    readme_content = ""
    if os.path.exists(readme):
        with open(readme) as f:
            readme_content = f.read()

    # Parse product info from README
    tagline  = ""
    problem  = ""
    solution = ""
    tech     = "python,sqlite3,json,os"

    for line in readme_content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not tagline:
            tagline = line
        if line.startswith("## Problem"):
            pass
        if "Problem" in readme_content:
            m = re.search(r"## Problem\n(.+?)(?=##|$)", readme_content, re.DOTALL)
            if m: problem = m.group(1).strip()[:300]
        if "Solution" in readme_content:
            m = re.search(r"## Solution\n(.+?)(?=##|$)", readme_content, re.DOTALL)
            if m: solution = m.group(1).strip()[:300]
        if "Tech Stack" in readme_content:
            m = re.search(r"## Tech Stack\n(.+?)(?=##|$)", readme_content, re.DOTALL)
            if m: tech = m.group(1).strip().replace("\n",",")[:200]

    if not tagline:
        tagline = f"A tool built by JARVIS on {datetime.now().strftime('%Y-%m-%d')}"
    if not problem:
        problem = "Automates a common business task."
    if not solution:
        solution = "A clean Python tool with demo mode and full documentation."

    github_url = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/tree/main/products/{folder}"
    page_url   = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/products/{folder}/"

    # Push to GitHub
    log("  Pushing to GitHub...")
    ok1 = push_file(
        f"products/{folder}/main.py",
        code,
        f"🤖 JARVIS: publish {folder}"
    )
    ok2 = push_file(
        f"products/{folder}/README.md",
        readme_content or f"# {folder}\n\n{tagline}\n",
        f"🤖 JARVIS: readme {folder}"
    )

    # Generate and push landing page
    log("  Generating landing page...")
    page_html = generate_landing_page(
        folder, tagline, problem, solution, tech, github_url
    )
    ok3 = push_file(
        f"products/{folder}/index.html",
        page_html,
        f"🤖 JARVIS: landing page {folder}"
    )

    if not (ok1 or ok2):
        log(f"  ❌ GitHub push failed")
        return False

    # Save to published db
    db = get_pub_db()
    db.execute("""INSERT OR REPLACE INTO published
        (product, github_url, page_url, date, score)
        VALUES (?,?,?,?,?)""",
        (folder, github_url, page_url,
         datetime.now().isoformat(), 0))
    db.commit()
    db.close()

    return {
        "folder": folder,
        "tagline": tagline,
        "github_url": github_url,
        "page_url": page_url,
        "code": code # Return code for LLM summarization
    }

def get_llm_summary(product_name, code):
    log(f"  🤖 Requesting LLM summary for {product_name}...")
    summary = ask_hermes(f"Summarize the following Python product in one short sentence, suitable for a landing page tagline:\n\n```python\n{code}\n```")
    if not summary:
        summary = f"An autonomous Python tool built by JARVIS for {product_name.replace('_', ' ').title().split(' ')[0]}."
    log(f"  🤖 LLM summary for {product_name}: {summary}")
    return summary

def send_product_notifications(product_info, summary):
    folder = product_info["folder"]
    tagline = product_info["tagline"]
    github_url = product_info["github_url"]
    page_url = product_info["page_url"]

    clean_name = folder.replace("_", " ").title()
    email_html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:32px;">
      <h1 style="color:#3b82f6">🤖 JARVIS Published: {clean_name}</h1>
      <p style="color:#666;font-size:1.1rem">{tagline}</p>
      <p style="color:#666;font-size:1.1rem">Summary: {summary}</p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p><strong>GitHub:</strong>
         <a href="{github_url}">{github_url}</a></p>
      <p><strong>Landing page:</strong>
         <a href="{page_url}">{page_url}</a></p>
      <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
      <p style="color:#999;font-size:0.85rem">
        Built autonomously by JARVIS · {datetime.now().strftime("%Y-%m-%d %H:%M")}
      </p>
    </div>"""

    send_email(f"🤖 JARVIS Published: {clean_name}", email_html)

    send_telegram(
        f"🚀 <b>Published: {clean_name}</b>\n\n"
        f"<i>{summary}</i>\n\n"
        f"{tagline}\n\n"
        f"<a href='{github_url}'>View on GitHub</a>"
    )
    trigger_vercel() # Trigger Vercel after notifications

# ── MAIN ──────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", type=str, help="Publish specific product folder name")
    parser.add_argument("--all",     action="store_true", help="Publish all unpublished")
    parser.add_argument("--status",  action="store_true", help="Show published products")
    args = parser.parse_args()

    log("=" * 50)
    log(f"JARVIS PUBLISHER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 50)

    if args.status:
        db = get_pub_db()
        rows = db.execute(
            "SELECT product, github_url, date FROM published ORDER BY date DESC"
        ).fetchall()
        print(f"\n📦 PUBLISHED PRODUCTS: {len(rows)}\n")
        for product, url, date in rows:
            print(f"  {date[:10]} — {product}")
            print(f"             {url}\n")
        db.close()

    elif args.product:
        product_path = f"{PRODUCTS}/{args.product}"
        if not os.path.exists(product_path):
            log(f"❌ Not found: {product_path}")
        else:
            product_info = publish_product(product_path)
            if product_info:
                summary = get_llm_summary(product_info["folder"], product_info["code"])
                send_product_notifications(product_info, summary)
            else:
                log(f"❌ Failed to publish {product_path}")


    elif args.all:
        import concurrent.futures # Moved here to be specific to this branch

        db = get_pub_db()
        published = {r[0] for r in db.execute(
            "SELECT product FROM published"
        ).fetchall()}
        db.close()

        dirs = sorted([
            d for d in os.listdir(PRODUCTS)
            if os.path.isdir(f"{PRODUCTS}/{d}")
            and d not in published
        ])
        log(f"Found {len(dirs)} unpublished products")

        products_to_summarize = []
        for d in dirs:
            log(f"Preparing to publish {d} (GitHub push, landing page)...")
            product_info = publish_product(f"{PRODUCTS}/{d}")
            if product_info:
                products_to_summarize.append(product_info)
            else:
                log(f"❌ Failed to prepare {d} for publishing.")
            import time; time.sleep(2)  # Be polite to GitHub API for each product's initial push

        llm_futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor: # Use a pool for parallel LLM calls
            for product_info in products_to_summarize:
                future = executor.submit(get_llm_summary, product_info["folder"], product_info["code"])
                llm_futures.append((product_info, future))

            log(f"Waiting for {len(llm_futures)} LLM summaries in parallel...")
            for product_info, future in llm_futures:
                summary = future.result() # This will block until the summary is ready
                log(f"  ✅ LLM summary received for {product_info['folder']}")
                send_product_notifications(product_info, summary) # Send notifications after summary is ready
        log("All products processed.")

    else:
        log("Use --all, --product NAME, or --status")
