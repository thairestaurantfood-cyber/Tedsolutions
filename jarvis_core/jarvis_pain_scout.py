#!/usr/bin/env python3
"""
JARVIS Pain Scout v3 — Cutting Edge Intelligence
Scans: GitHub Trending, HN, AI news, agent ecosystem
Focus: What's hot in AI agents, what gaps exist, what can be combined
This is JARVIS's window into the real world of 2026
"""
import os, sys, json, sqlite3, urllib.request, time, re
from datetime import datetime

def load_env():
    p = os.path.expanduser("~/.env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

JARVIS = os.path.expanduser("~/jarvis")
DB_PATH = f"{JARVIS}/memory/pain_scout.db"
IDEAS_PATH = f"{JARVIS}/memory/validated_ideas.json"
LOG_PATH = f"{JARVIS}/logs/pain_scout.log"

# ── SIGNAL SOURCES — 2026 cutting edge ─────────────────────────

REDDIT_SOURCES = [
    # AI Agent ecosystem — where the world is going
    "LocalLLaMA", "ollama", "ChatGPT", "ClaudeAI",
    "artificial", "MachineLearning", "singularity",
    "LangChain", "AutoGPT", "agentsopenai",
    # Builder communities — what solo devs are shipping
    "SideProject", "indiehackers", "entrepreneur",
    "startups", "microsaas", "webdev", "Python",
    # Real world pain — global problems
    "smallbusiness", "developers, businesses, and individuals globally", "digitalnomad",
    "personalfinance", "povertyfinance", "WorkReform",
    # Emerging tech
    "selfhosted", "homeautomation", "nocode",
    "MachineLearning", "deeplearning", "datascience",
]

# GitHub trending languages to scan
GITHUB_TRENDING = [
    "https://api.github.com/search/repositories?q=created:>2026-04-01+stars:>100+topic:ai-agent&sort=stars&per_page=10",
    "https://api.github.com/search/repositories?q=created:>2026-04-01+stars:>50+topic:llm&sort=stars&per_page=10",
    "https://api.github.com/search/repositories?q=created:>2026-04-01+stars:>50+topic:mcp&sort=stars&per_page=10",
    "https://api.github.com/search/repositories?q=created:>2026-04-01+topic:ollama+stars:>30&sort=stars&per_page=10",
]

# What JARVIS should look for — 2026 opportunity signals
OPPORTUNITY_KEYWORDS = [
    # Agent gaps
    "no agent for", "wish there was an agent", "automate with llm",
    "local ai", "private ai", "self-hosted ai", "ollama",
    "mcp server", "mcp tool", "claude tool", "gpt tool",
    # Combination opportunities  
    "combine", "integrate", "connect", "bridge", "wrapper",
    "missing piece", "gap in", "nobody built",
    # Market signals
    "paying for", "would pay", "subscription", "saas for",
    "open source alternative", "replace", "cheaper than",
    # Builder signals
    "show hn", "launched", "built this", "just shipped",
    "side project", "weekend project", "solo founder",
]

# 2026 tech stack — what JARVIS CAN actually use/download
ALLOWED_TECH = {
    "local_ai": ["ollama", "llamacpp", "whisper", "sentence-transformers"],
    "data": ["sqlite3", "duckdb", "pandas", "polars"],
    "web": ["fastapi", "uvicorn", "httpx", "playwright"],
    "agents": ["langchain", "crewai", "autogen", "smolagents"],
    "tools": ["rich", "typer", "click", "pydantic"],
    "scraping": ["playwright", "beautifulsoup4", "httpx"],
}

# Categories aligned with 2026 market
CATEGORIES = {
    "ai_agent": ["agent", "llm", "ollama", "mcp", "automate", "autonomous"],
    "dev_tool": ["cli", "developer", "coding", "api", "terminal", "workflow"],
    "personal_ai": ["personal", "assistant", "memory", "second brain", "notes"],
    "data_tool": ["data", "analyze", "visualize", "dashboard", "report", "csv"],
    "automation": ["automate", "schedule", "cron", "trigger", "workflow", "n8n"],
    "ai_wrapper": ["wrapper", "interface", "frontend", "ui", "chat", "voice"],
    "open_source": ["open source", "self-hosted", "privacy", "local", "offline"],
}

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT, title TEXT, body TEXT, url TEXT,
            pain_score INTEGER DEFAULT 0,
            discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0,
            category TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS discovered_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, pain_score INTEGER, problem TEXT,
            solution TEXT, target_market TEXT,
            signal_count INTEGER DEFAULT 0,
            stripe_potential TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            category TEXT DEFAULT '',
            global_reach INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS github_trending (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT, description TEXT, stars INTEGER,
            topics TEXT, url TEXT, language TEXT,
            discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    return conn

def log(msg):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_PATH, "a") as f:
        f.write(line + "\n")

def fetch(url, timeout=10, headers=None):
    try:
        h = {"User-Agent": "JARVIS-Scout/3.0"}
        if headers:
            h.update(headers)
        req = urllib.request.Request(url, headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except:
        return None

def score_signal(text):
    text_lower = text.lower()
    score = 0
    for kw in OPPORTUNITY_KEYWORDS:
        if kw in text_lower:
            score += 2
    if any(w in text_lower for w in ["million users", "10k stars", "viral", "trending", "hot"]):
        score += 3
    if any(w in text_lower for w in ["agent", "mcp", "ollama", "llm", "gpt", "claude"]):
        score += 3
    if any(w in text_lower for w in ["open source", "free", "self-hosted", "local"]):
        score += 2
    if any(w in text_lower for w in ["python", "cli", "terminal", "api"]):
        score += 1
    return min(score, 10)

def classify(text):
    text_lower = text.lower()
    for cat, keywords in CATEGORIES.items():
        if any(k in text_lower for k in keywords):
            return cat
    return "general"

def scan_reddit(subreddit, limit=20):
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    data = fetch(url)
    if not data:
        return []
    signals = []
    try:
        for post in data["data"]["children"]:
            p = post["data"]
            title = p.get("title", "")
            body = p.get("selftext", "")[:400]
            score = score_signal(f"{title} {body}")
            if score > 0:
                signals.append({
                    "source": f"reddit/r/{subreddit}",
                    "title": title, "body": body,
                    "url": f"https://reddit.com{p.get('permalink','')}",
                    "pain_score": score,
                    "category": classify(f"{title} {body}")
                })
    except:
        pass
    return signals

def scan_hn():
    signals = []
    for story_type, url in [("ask", "https://hacker-news.firebaseio.com/v0/askstories.json"),
                             ("show", "https://hacker-news.firebaseio.com/v0/showstories.json")]:
        ids = fetch(url)
        if not ids:
            continue
        for sid in ids[:25]:
            item = fetch(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
            if not item:
                continue
            title = item.get("title", "")
            body = item.get("text", "")[:300]
            score = score_signal(f"{title} {body}")
            if story_type == "show":
                score += 2  # Show HN = proof something was built
            if score > 0:
                signals.append({
                    "source": f"hackernews/{story_type}",
                    "title": title, "body": body,
                    "url": f"https://news.ycombinator.com/item?id={sid}",
                    "pain_score": min(score, 10),
                    "category": classify(f"{title} {body}")
                })
            time.sleep(0.05)
    return signals

def scan_github_trending(db):
    """Scan GitHub for hot new AI/agent repos — these are gaps to fill or build on."""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}"} if token else {}
    new = 0
    for url in GITHUB_TRENDING:
        data = fetch(url, headers=headers)
        if not data:
            continue
        for repo in data.get("items", []):
            name = repo.get("full_name", "")
            desc = repo.get("description", "") or ""
            stars = repo.get("stargazers_count", 0)
            topics = ",".join(repo.get("topics", []))
            repo_url = repo.get("html_url", "")
            lang = repo.get("language", "")
            existing = db.execute(
                "SELECT id FROM github_trending WHERE repo_name=?", (name,)).fetchone()
            if not existing:
                db.execute("""INSERT INTO github_trending
                    (repo_name,description,stars,topics,url,language)
                    VALUES (?,?,?,?,?,?)""",
                    (name, desc[:200], stars, topics, repo_url, lang))
                new += 1
        time.sleep(1)
    db.commit()
    return new

def save_signals(db, signals):
    new = 0
    for s in signals:
        existing = db.execute(
            "SELECT id FROM signals WHERE title=? AND source=?",
            (s["title"], s["source"])).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO signals (source,title,body,url,pain_score,category) VALUES (?,?,?,?,?,?)",
                (s["source"], s["title"], s["body"], s["url"], s["pain_score"], s["category"]))
            new += 1
    db.commit()
    return new

def synthesize_ideas(db):
    sys.path.insert(0, JARVIS)
    try:
        from api import ask as llm
    except:
        log("❌ Cannot import llm"); return []

    # Get top signals
    signals = db.execute("""SELECT source,title,body,category,pain_score
        FROM signals WHERE pain_score >= 3
        ORDER BY pain_score DESC, discovered_at DESC LIMIT 50""").fetchall()

    # Get GitHub trending repos
    repos = db.execute("""SELECT repo_name,description,stars,topics
        FROM github_trending ORDER BY stars DESC LIMIT 20""").fetchall()

    signal_text = "\n".join([f"[{s[0]}] {s[1][:70]} (score:{s[4]})" for s in signals])
    repo_text = "\n".join([f"★{r[2]} {r[0]}: {r[1][:60]} [{r[3]}]" for r in repos])

    prompt = f"""You are the product strategy brain of JARVIS — an autonomous AI builder.
It is May 2026. The AI agent revolution is happening NOW.

REAL SIGNALS FROM THE INTERNET TODAY:
{signal_text}

HOT GITHUB REPOS THIS MONTH (what developers are actually building):
{repo_text}

WHAT JARVIS CAN BUILD:
- Python CLI tools using stdlib + SQLite (no heavy frameworks)
- Can pip install: ollama, rich, typer, httpx, playwright, pydantic, duckdb
- Has Mistral API, local Ollama (qwen2.5-coder, gemma3), GitHub API
- Can download and wrap existing open source tools
- Can build MCP servers (simple Python, connects to Claude/any AI)
- Can build agents that use other agents

YOUR JOB: Find 5 HIGH-IMPACT product ideas for 2026.
Think: What tool would 100,000 developers/businesses want tomorrow?
What gap exists in the AI agent ecosystem right now?
What can be built in <200 lines that wraps something powerful?

AVOID: more invoice trackers, more developers, businesses, and individuals globallyr tools, basic CRUD apps
TARGET: AI tools, agent infrastructure, developer tools, data tools,
        personal AI assistants, MCP servers, automation tools

OUTPUT — ONLY valid JSON, no other text:
[
  {{
    "title": "ToolName — sharp tagline",
    "pain_score": 9,
    "problem": "specific gap in the market right now",
    "solution": "what it does — be specific about the tech",
    "target_market": "who uses this globally",
    "category": "ai_agent|dev_tool|personal_ai|data_tool|automation|ai_wrapper",
    "global_reach": 9,
    "can_use_existing": "list any open source tools it wraps or combines"
  }}
]"""

    log("🧠 Synthesizing 2026 cutting-edge ideas with Mistral...")
    response = llm(prompt, max_tokens=2000)
    if not response:
        log("❌ No LLM response"); return []
    try:
        clean = re.sub(r'```json|```', '', response).strip()
        import re as _re
        clean = _re.sub(r",\s*([}\]])", r"\1", clean)
        if "[" not in clean or "]" not in clean:
            log("❌ No JSON array found in response"); return []
        ideas = json.loads(clean[clean.index("["):clean.rindex("]")+1])
        log(f"✅ {len(ideas)} cutting-edge ideas generated")
        return ideas
    except Exception as e:
        log(f"❌ Parse error: {e}"); return []

def save_ideas(db, ideas):
    saved = 0
    for idea in ideas:
        if not db.execute("SELECT id FROM discovered_ideas WHERE title=?",
                (idea.get("title",""),)).fetchone():
            db.execute("""INSERT INTO discovered_ideas
                (title,pain_score,problem,solution,target_market,category,global_reach)
                VALUES (?,?,?,?,?,?,?)""",
                (idea.get("title",""), idea.get("pain_score",5),
                 idea.get("problem",""), idea.get("solution",""),
                 idea.get("target_market",""), idea.get("category",""),
                 idea.get("global_reach",5)))
            saved += 1
    db.commit()
    return saved

def merge_to_validated(db):
    ideas = db.execute("""SELECT title,pain_score,problem,solution,
        target_market,category,global_reach FROM discovered_ideas
        ORDER BY pain_score DESC, global_reach DESC""").fetchall()
    existing = []
    if os.path.exists(IDEAS_PATH):
        try: existing = json.load(open(IDEAS_PATH))
        except: pass
    existing_titles = {i.get("title","").lower() for i in existing}
    added = 0
    for idea in ideas:
        if idea[0].lower() not in existing_titles:
            existing.append({
                "title": idea[0], "pain_score": idea[1],
                "problem": idea[2], "solution": idea[3],
                "target_market": idea[4], "category": idea[5],
                "global_reach": idea[6], "source": "pain_scout_v3"
            })
            existing_titles.add(idea[0].lower())
            added += 1
    existing.sort(key=lambda x: (x.get("pain_score",0), x.get("global_reach",0)), reverse=True)
    with open(IDEAS_PATH, "w") as f:
        json.dump(existing, f, indent=2)
    return added

def cmd_scan():
    load_env()
    db = get_db()
    log("=== PAIN SCOUT v3 — CUTTING EDGE SCAN ===")
    total = 0

    log(f"Scanning {len(REDDIT_SOURCES)} AI/builder subreddits...")
    for sub in REDDIT_SOURCES:
        sigs = scan_reddit(sub)
        new = save_signals(db, sigs)
        if new > 0: log(f"  r/{sub}: +{new}")
        total += new
        time.sleep(1.2)

    log("Scanning HN Ask + Show...")
    hn = scan_hn()
    new = save_signals(db, hn)
    log(f"  HN: +{new} signals")
    total += new

    log("Scanning GitHub trending AI repos...")
    gh = scan_github_trending(db)
    log(f"  GitHub: +{gh} new repos")

    # Show breakdown
    cats = db.execute("""SELECT category,COUNT(*),AVG(pain_score)
        FROM signals GROUP BY category ORDER BY COUNT(*) DESC""").fetchall()
    print("\n── Signal breakdown ──")
    for c in cats:
        print(f"  {c[0]:<20} {c[1]:>4} signals  avg:{c[2]:.1f}")

    print("\n── Hot GitHub repos ──")
    repos = db.execute("SELECT repo_name,stars,description FROM github_trending ORDER BY stars DESC LIMIT 8").fetchall()
    for r in repos:
        print(f"  ★{r[1]:<6} {r[0]:<35} {(r[2] or '')[:40]}")

    ideas = synthesize_ideas(db)
    if ideas:
        saved = save_ideas(db, ideas)
        merged = merge_to_validated(db)
        log(f"✅ {saved} ideas saved, {merged} added to pipeline")
        print("\n── New 2026 ideas ──")
        for i in ideas:
            print(f"  {i.get('pain_score')}/10 [{i.get('category')}] {i.get('title','')[:55]}")
            print(f"       uses: {i.get('can_use_existing','stdlib')[:60]}")

    db.close()
    log("=== SCAN COMPLETE ===")

def cmd_ideas():
    load_env()
    db = get_db()
    ideas = db.execute("""SELECT title,pain_score,category,global_reach
        FROM discovered_ideas ORDER BY pain_score DESC, global_reach DESC LIMIT 15""").fetchall()
    print(f"\n── Top Ideas Pipeline ({len(ideas)}) ──\n")
    for i in ideas:
        print(f"  {i[1]}/10 [{i[2]:<15}] reach:{i[3]}/10  {i[0][:55]}")
    db.close()

def demo():
    load_env()
    db = get_db()
    sig_count = db.execute("SELECT COUNT(*) FROM signals").fetchone()[0]
    idea_count = db.execute("SELECT COUNT(*) FROM discovered_ideas").fetchone()[0]
    print(f"""
╔══════════════════════════════════════════════════╗
║   JARVIS PAIN SCOUT v3 — 2026 INTELLIGENCE       ║
╚══════════════════════════════════════════════════╝
  Signals in DB:    {sig_count}
  Ideas in pipeline:{idea_count}

  SOURCES:
  • {len(REDDIT_SOURCES)} AI/builder subreddits (LocalLLaMA, indiehackers...)
  • HN Ask + Show (real builders, real problems)
  • GitHub Trending (ai-agent, llm, mcp topics)

  WHAT IT LOOKS FOR:
  • Gaps in the AI agent ecosystem
  • Hot new repos to wrap or extend
  • MCP server opportunities
  • Tools developers would pay for tomorrow

  WHAT CHANGED:
  ❌ v1: only r/developers, businesses, and individuals globally
  ❌ v2: broad but unfocused, offline bias
  ✅ v3: AI-first, 2026 ecosystem, GitHub trending,
         can suggest wrapping existing tools

  RUN: python3 jarvis_pain_scout.py --scan
""")
    db.close()

def main():
    load_env()
    import argparse
    parser = argparse.ArgumentParser(description="JARVIS Pain Scout v3")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--scan", action="store_true")
    parser.add_argument("--ideas", action="store_true")
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo(); return

    subs = parser.add_subparsers(dest="command")
    subs.add_parser("scan"); subs.add_parser("ideas")
    args = parser.parse_args()

    if args.scan or args.command == "scan": cmd_scan()
    elif args.ideas or args.command == "ideas": cmd_ideas()
    else: parser.print_help()

if __name__ == "__main__":
    main()
