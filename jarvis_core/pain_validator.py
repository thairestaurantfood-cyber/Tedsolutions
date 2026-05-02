#!/usr/bin/env python3
"""
JARVIS Pain Validator — validates ideas have real market demand before building.
Scores each idea 1-10 for real pain. Only high-scoring ideas go to the builder.
"""
import os, json, sys, time
from datetime import datetime
sys.path.insert(0, os.path.expanduser("~/jarvis"))
from api import ask, ask_json

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

MEMORY    = os.path.expanduser("~/jarvis/memory")
VALIDATED = os.path.join(MEMORY, "validated_ideas.json")

SEEDS = [
    "Invoice Chaser — auto payment reminder sequences for freelancers",
    "Proposal Generator — 5 questions to professional text proposal",
    "Client Portal Tracker — file and status per client in sqlite",
    "Contract Expiry Tracker — alert before renewal deadlines",
    "Meeting Notes Processor — paste text to action items and owners",
    "Lead Qualifier — score inbound leads from CSV ranked list",
    "Freelancer Tax Estimator — income CSV to quarterly tax estimate",
    "Churn Risk Scorer — flag clients not engaged in X days",
    "Doc Chaser — remind clients for missing documents",
    "Cold Outreach Tracker — track email sequences and follow-up",
    "OTA Rate Monitor — track competitor hotel pricing daily",
    "Review Digest — weekly review summary and reply suggestions",
    "Staff Roster Scheduler — shift planner for small teams",
    "SaaS Metrics Dashboard — MRR churn LTV from CSV weekly digest",
    "Booking Double-Check — detect double bookings across CSV exports",
]

def validate_idea(title):
    prompt = f"""Market research for a solo Python CLI developer.

Idea: "{title}"
Target: Freelancers, small agencies, SaaS founders in SE Asia
Price point: $19-49/month

Score this idea on REAL market pain. Reply ONLY as JSON:
{{
  "pain_score": 8,
  "pain_evidence": "one sentence: where do people complain about this problem",
  "existing_tools": ["Tool A $X/mo", "Tool B $Y/mo"],
  "buyer_search_terms": ["exact phrase buyers google", "another phrase"],
  "sea_fit": "one sentence: how well this fits Thailand/Vietnam/Indonesia market",
  "verdict": "build",
  "reason": "one sentence why or why not"
}}

verdict must be: build (score 7+) or skip (score below 7)"""

    return ask_json(prompt)

def validate_all():
    results = []
    print(f"Validating {len(SEEDS)} ideas for real market pain...")
    print("(Using Mistral — ~3s per idea)\n")
    for i, idea in enumerate(SEEDS):
        print(f"  [{i+1}/{len(SEEDS)}] {idea[:55]}...")
        result = validate_idea(idea)
        if result:
            entry = {
                "title": idea,
                "pain_score": result.get("pain_score", 0),
                "pain_evidence": result.get("pain_evidence",""),
                "existing_tools": result.get("existing_tools",[]),
                "buyer_search_terms": result.get("buyer_search_terms",[]),
                "sea_fit": result.get("sea_fit",""),
                "verdict": result.get("verdict","skip"),
                "reason": result.get("reason",""),
                "validated_at": datetime.now().isoformat()
            }
            results.append(entry)
            score = result.get("pain_score",0)
            icon = "🔥" if score >= 8 else "✅" if score >= 6 else "⚠️"
            print(f"     {icon} {score}/10 — {result.get('pain_evidence','')[:55]}")
        else:
            print(f"     ❌ validation failed")
        time.sleep(3)

    results.sort(key=lambda x: x.get("pain_score",0), reverse=True)
    os.makedirs(MEMORY, exist_ok=True)
    with open(VALIDATED, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Saved {len(results)} validated ideas to validated_ideas.json")
    return results

def show_rankings():
    try:
        ideas = json.load(open(VALIDATED))
    except:
        print("No validated ideas yet. Run: python3 pain_validator.py --validate")
        return
    print(f"\n{'='*58}")
    print(f"PAIN-VALIDATED IDEA RANKINGS")
    print(f"{'='*58}")
    for i, idea in enumerate(ideas[:10]):
        score = idea.get("pain_score",0)
        icon  = "🔥" if score >= 8 else "✅" if score >= 6 else "⚠️"
        print(f"\n{icon} #{i+1} [{score}/10] {idea['title'][:52]}")
        print(f"   📍 {idea.get('pain_evidence','')[:65]}")
        print(f"   🌏 {idea.get('sea_fit','')[:65]}")
        tools = idea.get("existing_tools",[])
        if tools: print(f"   💰 Competitors: {', '.join(tools[:2])}")
        terms = idea.get("buyer_search_terms",[])
        if terms: print(f"   🔍 Buyers search: {terms[0]}")
        print(f"   Verdict: {idea.get('verdict','?')} — {idea.get('reason','')[:50]}")

def get_top(n=5):
    try:
        ideas = json.load(open(VALIDATED))
        return [i for i in ideas if i.get("verdict")=="build"][:n]
    except:
        return []

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="JARVIS Pain Validator")
    p.add_argument("--validate", action="store_true", help="Validate all seed ideas")
    p.add_argument("--show",     action="store_true", help="Show rankings")
    p.add_argument("--idea",     type=str,            help="Validate one idea")
    args = p.parse_args()

    if args.idea:
        r = validate_idea(args.idea)
        if r: print(json.dumps(r, indent=2))
    elif args.validate:
        validate_all()
        show_rankings()
    elif args.show:
        show_rankings()
    else:
        p.print_help()
