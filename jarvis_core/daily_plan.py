#!/usr/bin/env python3
"""JARVIS Daily Planner — midnight. Picks best idea → researches it → writes daily_plan.json"""
import os, json, re, sys
from datetime import datetime
sys.path.insert(0, os.path.expanduser("~/jarvis"))
from api import ask, ask_json

QUEUE_FILE   = os.path.expanduser("~/jarvis/memory/ideas_queue.json")
PLAN_FILE    = os.path.expanduser("~/jarvis/memory/daily_plan.json")
PRODUCTS_DIR = os.path.expanduser("~/jarvis/products")
os.makedirs(PRODUCTS_DIR, exist_ok=True)

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

TG_TOKEN = os.getenv("TG_TOKEN","")
TG_CHAT  = os.getenv("TG_CHAT","")

SEED_IDEAS = [
    {"title":"Invoice Chaser — auto payment reminder sequences for freelancers","score":9},
    {"title":"Proposal Generator — 5 questions → professional text proposal","score":9},
    {"title":"Client Portal Tracker — file/message/status per client in sqlite","score":8},
    {"title":"Contract Expiry Tracker — alert before renewal deadlines","score":8},
    {"title":"Meeting Notes Processor — paste text → action items + owners","score":8},
    {"title":"Lead Qualifier — score inbound leads from CSV → ranked list","score":8},
    {"title":"Freelancer Tax Estimator — income CSV → quarterly tax estimate","score":8},
    {"title":"Churn Risk Scorer — flag clients who haven't engaged in X days","score":8},
    {"title":"Doc Chaser — auto-remind clients for missing documents","score":8},
    {"title":"Cold Outreach Tracker — track email sequences and follow-up schedule","score":8},
    {"title":"SEO Audit Reporter — URL checks → one-page actionable report","score":8},
    {"title":"Review Digest — weekly summary of reviews + reply suggestions","score":8},
    {"title":"OTA Rate Monitor — track competitor hotel pricing changes daily","score":8},
    {"title":"Staff Roster Scheduler — shift planner for small hospitality teams","score":7},
    {"title":"SaaS Metrics Dashboard — MRR churn LTV from CSV → weekly digest","score":8},
    {"title":"Testimonial Request Bot — auto-send review requests after project close","score":7},
    {"title":"Expense Categorizer — receipt CSV → categorized report + tax totals","score":7},
    {"title":"Booking Double-Check — detect double-bookings across CSV exports","score":7},
    {"title":"Project Time Tracker — start/stop timer → invoice-ready summary","score":7},
    {"title":"Competitor Price Watcher — monitor pricing pages for changes","score":7},
]

def notify(msg):
    if not TG_TOKEN: return
    try:
        import urllib.request
        data = json.dumps({"chat_id":TG_CHAT,"text":f"🧠 JARVIS PLANNER\n\n{msg}"}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data=data, headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=8)
    except: pass

def load_already_built():
    built = set()
    try:
        tools = json.load(open(os.path.expanduser("~/jarvis/memory/tools.json")))
        for t in tools: built.add(t.get("name","").lower())
    except: pass
    if os.path.exists(PRODUCTS_DIR):
        for d in os.listdir(PRODUCTS_DIR): built.add(d.lower())
    return built

def get_brain_recommendation():
    try:
        import sqlite3
        db = sqlite3.connect(os.path.expanduser("~/jarvis/memory/brain.db"))
        rows = db.execute("""
            SELECT m.problem_title, m.solution_name, m.match_score, p.buyer
            FROM matches m JOIN problems p ON m.problem_title = p.title
            WHERE m.status='pending' ORDER BY m.match_score DESC LIMIT 10
        """).fetchall()
        db.close()
        bad = ["fpga","hardware","mobile","ios","android","job post",
               "how do i","how do you","looking for work","for hire"]
        for prob, sol, score, buyer in rows:
            if any(b in prob.lower() for b in bad): continue
            return {"title":prob[:100],"source":f"brain/{sol}",
                    "score":min(10,round(score/2,1)),
                    "buyer":buyer or "small business owner"}
    except Exception as e:
        print(f"  Brain failed: {e}")
    return None

def filter_queue(ideas):
    """Use Mistral to properly filter ideas — no more 3B hallucinations."""
    if not ideas: return []
    recent = ideas[-20:]
    results = []
    print(f"  Filtering {len(recent)} queue ideas with Mistral...")

    # Batch filter — send all 20 at once, much faster than one by one
    titles = "\n".join(f"{i+1}. {x.get('title','')[:80]}" for i,x in enumerate(recent))
    prompt = f"""You are filtering startup ideas for a solo developer.
KEEP only ideas that are: a real software tool a business would pay for monthly.
REJECT: news articles, job posts, research papers, hardware, mobile apps, personal stories.

Ideas:
{titles}

Reply ONLY as JSON array of numbers to KEEP (e.g. [2,5,8,12]):"""

    raw = ask(prompt, fast=True)
    if not raw: return []
    try:
        # Extract array from response
        s = raw.find("["); e = raw.rfind("]") + 1
        if s == -1: return []
        keep_nums = json.loads(raw[s:e])
        for n in keep_nums:
            if 1 <= n <= len(recent):
                results.append({**recent[n-1], "score":7, "verdict":"build"})
        print(f"  Kept {len(results)}/{len(recent)} queue ideas")
        return results
    except Exception as ex:
        print(f"  Filter parse error: {ex} | raw: {raw[:100]}")
        return []

def deep_research(idea):
    prompt = f"""You are a product strategist for a solo Python CLI developer.

Idea: "{idea['title']}"

Constraints:
- Python stdlib ONLY: os,sys,json,csv,sqlite3,argparse,datetime,pathlib,subprocess,urllib.request,re,time
- Max 200 lines. NO Flask, requests, numpy, pandas, PIL, tensorflow
- Must have --demo mode that works 100% offline with hardcoded data
- Target buyers: freelancers, small agencies, SaaS founders in SE Asia
- Price: $19-49/month

Return ONLY valid JSON (no markdown):
{{
  "product_name": "short name",
  "tagline": "one sentence what it does",
  "problem": "specific pain point",
  "solution": "what it does step by step",
  "target_market": "specific buyer description",
  "monthly_price_usd": 29,
  "mvp_features": ["feat1","feat2","feat3","feat4","feat5"],
  "build_phases": [
    {{"phase":1,"name":"Core DB + add","description":"sqlite schema + add/list commands","hours":2}},
    {{"phase":2,"name":"Reports + alerts","description":"report generation + notification","hours":2}},
    {{"phase":3,"name":"Demo + polish","description":"--demo mode + --help + edge cases","hours":1}}
  ],
  "demo_script": "5-line description of what --demo shows",
  "market_score": 8,
  "buildability_score": 9,
  "overall_score": 8,
  "verdict": "build",
  "phuket_angle": "specific use case for Phuket/Thailand businesses, or none"
}}"""
    return ask_json(prompt)

def get_validated_seeds():
    """Load pain-validated ideas — ranked by real market evidence."""
    try:
        ideas = json.load(open(os.path.expanduser("~/jarvis/memory/validated_ideas.json")))
        return [{"title":i["title"],"score":i["pain_score"],
                 "source":"pain_validated",
                 "buyer_search":i.get("buyer_search_terms",[""])[0],
                 "sea_fit":i.get("sea_fit",""),
                 "competitors":i.get("existing_tools",[])}
                for i in ideas if i.get("verdict")=="build"]
    except:
        return []

def pick_candidate(queue_ideas, brain, already_built):
    candidates = []
    if brain: candidates.append(brain)
    filtered = filter_queue(queue_ideas)
    candidates.extend(filtered[:3])
    # Use pain-validated ideas first, fall back to static seeds
    validated = get_validated_seeds()
    v_unused = [v for v in validated
                if not any(w in " ".join(already_built)
                          for w in v["title"].lower().split()[:2])]
    if v_unused:
        candidates.extend(v_unused[:3])
        print(f"  📊 {len(v_unused)} pain-validated ideas available")
    else:
        seeds = [s for s in SEED_IDEAS
                 if not any(w in " ".join(already_built)
                           for w in s["title"].lower().split()[:2])]
        if seeds:
            idx = datetime.now().timetuple().tm_yday % len(seeds)
            candidates.append({**seeds[idx], "source":"seed"})
    candidates.append({"title":"Invoice Chaser for Freelancers","source":"fallback","score":8})
    # Return first not already built
    for c in candidates:
        words = c["title"].lower().split()[:3]
        if not any(w in " ".join(already_built) for w in words):
            return c
    return candidates[0]

def main():
    print(f"\n{'='*55}")
    print(f"JARVIS PLANNER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}\n")

    queue = []
    try: queue = json.load(open(QUEUE_FILE))
    except: print("  No queue file.")

    built = load_already_built()
    brain = get_brain_recommendation()

    print(f"📚 Queue: {len(queue)} | 🏗️ Built: {len(built)} | 🧠 Brain: {'yes' if brain else 'no'}")

    top = pick_candidate(queue, brain, built)
    print(f"\n🎯 Tonight's idea: {top['title']}")
    print(f"   Source: {top.get('source','?')} | Score: {top.get('score','?')}")

    print(f"\n🔬 Researching with Mistral...")
    plan = deep_research(top)

    if not plan:
        print("  Research failed — trying again...")
        plan = deep_research({"title": "Invoice Chaser for Freelancers"})

    if not plan:
        print("❌ No plan. Exiting.")
        notify("❌ Planner failed tonight.")
        return

    daily_plan = {
        "date": datetime.now().isoformat(),
        "idea": top, "plan": plan,
        "build_status": "pending", "phases_complete": []
    }
    with open(PLAN_FILE, "w") as f:
        json.dump(daily_plan, f, indent=2)

    name    = plan.get("product_name","?")
    tagline = plan.get("tagline","?")
    market  = plan.get("target_market","?")
    price   = plan.get("monthly_price_usd",0)
    score   = plan.get("overall_score","?")
    phuket  = plan.get("phuket_angle","")
    features= plan.get("mvp_features",[])
    phases  = plan.get("build_phases",[])

    print(f"\n✅ {name} — {tagline}")
    print(f"   {market} | ${price}/mo | {score}/10")
    if phuket and phuket.lower() != "none":
        print(f"   🇹🇭 {phuket}")

    msg  = f"📋 TONIGHT'S BUILD\n\n🏗️ {name}\n💡 {tagline}\n\n"
    msg += f"🎯 {market}\n💰 ${price}/mo | ⭐ {score}/10\n\n"
    msg += "Features:\n" + "\n".join(f"  • {f}" for f in features[:5])
    msg += "\n\nPhases:\n" + "\n".join(
        f"  {p.get('phase')}: {p.get('name')} ({p.get('hours')}h)" for p in phases)
    if phuket and phuket.lower() != "none":
        msg += f"\n\n🇹🇭 Phuket: {phuket}"
    notify(msg)
    print(f"\n📱 Notified. Done.\n{'='*55}\n")

if __name__ == "__main__":
    main()
