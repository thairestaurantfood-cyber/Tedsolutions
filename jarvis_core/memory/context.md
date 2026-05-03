
=== WHAT TED ACTUALLY WANTS (human ratings) ===

BUILDS TED RATED GOOD (8-10/10) — build more like these:
  ✅ 20260502_freelancer_pro_suite: Clean formatted dashboard, real workflow, all 4 modules working. Best combined product. Clients invoices tax proposals in one CLI. Ready for Stripe.
  ✅ 20260429_followup: Best build so far. Demo works perfectly. Real use case for freelancers. Ready for Stripe integration.

BUILDS TED RATED BAD (1-4/10) — never build like these:
  ❌ 20260429_invoicetracker (score:3): no target No price too little too small no faces and the demo failed Not good enough
  ❌ 20260429_pricewatch (score:4): this could be valuable and could be implemented in something else that we build in the future

=== CRITICAL RULES (learned from crashes) ===
1. ALWAYS define get_db() that calls CREATE TABLE IF NOT EXISTS — call it FIRST in main()
2. ALWAYS make --demo 100% offline — hardcode all sample data, never fetch URLs in demo
3. NEVER call INSERT or SELECT before CREATE TABLE — this crashes every time
4. NEVER import: flask, requests, numpy, pandas, PIL, tensorflow, torch, bs4, tabulate, rich
5. ALWAYS use: os.makedirs(os.path.dirname(db_path), exist_ok=True) before sqlite3.connect()
6. Target: Solo freelancers, small agencies, SaaS founders in SE Asia — practical CLI tools
7. Revenue: $19-49/month subscription, simple value proposition
8. Structure: imports → get_db() → functions → main() → if __name__=='__main__'


=== CRITICAL RULES (learned from crashes) ===
1. ALWAYS define get_db() that calls CREATE TABLE IF NOT EXISTS — call it FIRST in main()
2. ALWAYS make --demo 100% offline — hardcode all sample data, never fetch URLs in demo
3. NEVER call INSERT or SELECT before CREATE TABLE — this crashes every time
4. NEVER import: flask, requests, numpy, pandas, PIL, tensorflow, torch, bs4, tabulate, rich
5. ALWAYS use: os.makedirs(os.path.dirname(db_path), exist_ok=True) before sqlite3.connect()
6. Target: Solo freelancers, small agencies, SaaS founders in SE Asia — practical CLI tools
7. Revenue: $19-49/month subscription, simple value proposition
8. Structure: imports → get_db() → functions → main() → if __name__=='__main__'


=== CRITICAL RULES (learned from crashes) ===
1. ALWAYS define get_db() that calls CREATE TABLE IF NOT EXISTS — call it FIRST in main()
2. ALWAYS make --demo 100% offline — hardcode all sample data, never fetch URLs in demo
3. NEVER call INSERT or SELECT before CREATE TABLE — this crashes every time
4. NEVER import: flask, requests, numpy, pandas, PIL, tensorflow, torch, bs4, tabulate, rich
5. ALWAYS use: os.makedirs(os.path.dirname(db_path), exist_ok=True) before sqlite3.connect()
6. Target: Solo freelancers, small agencies, SaaS founders in SE Asia — practical CLI tools
7. Revenue: $19-49/month subscription, simple value proposition
8. Structure: imports → get_db() → functions → main() → if __name__=='__main__'


=== CRITICAL RULES (learned from crashes) ===
1. ALWAYS define get_db() that calls CREATE TABLE IF NOT EXISTS — call it FIRST in main()
2. ALWAYS make --demo 100% offline — hardcode all sample data, never fetch URLs in demo
3. NEVER call INSERT or SELECT before CREATE TABLE — this crashes every time
4. NEVER import: flask, requests, numpy, pandas, PIL, tensorflow, torch, bs4, tabulate, rich
5. ALWAYS use: os.makedirs(os.path.dirname(db_path), exist_ok=True) before sqlite3.connect()
6. Target: Solo freelancers, small agencies, SaaS founders in SE Asia — practical CLI tools
7. Revenue: $19-49/month subscription, simple value proposition
8. Structure: imports → get_db() → functions → main() → if __name__=='__main__'

=== JARVIS BUILD CONTEXT — updated 2026-04-30 ===

== WHAT WORKS (build more like these) ==
✅ followup (9/10): Simple CRM — contacts + notes + follow-up dates. Clean demo, clear buyer.
✅ jarvismon (9/10): Health monitor — checks APIs/processes, reports status. Useful daily.
✅ promptbench (9/10): API benchmarker — tests multiple APIs, scores responses. Always useful.
✅ contextinject (8/10): Memory injector — reads/writes context.md. Core JARVIS tool.
✅ pricepilot (7/10): Price tracker — hardcoded demo with real DB schema. Good pattern.

== WHAT FAILS (never build like these) ==
❌ fpga_insights (1/10): Hardware/FPGA idea — not buildable in Python CLI. REJECT these.
❌ invoicer (2/10): Demo broken — Flask import crashed it. Never use Flask.
❌ buildscorer (4/10): No target buyer, no price, vague description. Always define these.
❌ pricewatch (4/10): Demo was hardcoded wrong data. Demo must show real workflow.

== PROVEN BUILD PATTERN (copy this exactly) ==
1. imports (stdlib only)
2. DB_PATH = os.path.expanduser("~/jarvis/products/PRODUCTNAME/data.db")
3. def get_db(): — CREATE TABLE IF NOT EXISTS — call this FIRST in main()
4. def add_X() / def list_X() / def report_X()
5. def demo(): — 100% hardcoded, no network, shows full workflow in 10 lines
6. def main(): get_db() first, then argparse, then route to functions
7. if __name__ == "__main__": main()

== CRITICAL RULES ==
- stdlib ONLY: os,sys,json,csv,sqlite3,argparse,datetime,pathlib,subprocess,urllib.request,re,time
- MAX 200 lines
- --demo must work 100% offline, hardcoded data, NO network calls
- NEVER: flask, requests, numpy, pandas, PIL, tensorflow, torch, bs4
- os.makedirs(os.path.dirname(DB_PATH), exist_ok=True) BEFORE sqlite3.connect()
- INSERT column count MUST match CREATE TABLE column count exactly
- Always include --help and --demo in argparse

== TARGET BUYERS (pick one per product) ==
- Freelancers: invoice tracking, follow-ups, proposals, time tracking
- Small agencies: client portals, lead tracking, contract management
- SaaS founders: churn tracking, metrics dashboards, outreach sequences
- Phuket/SE Asia bonus: hotel rate monitoring, tour agency CRM, villa booking tools

== PRICING ==
- $19/month: simple single-purpose tools
- $29/month: tools that save 2+ hours/week
- $49/month: tools that directly affect revenue

== API (confirmed working 2026-04-30) ==
- PRIMARY: Mistral (mistral-small-latest) — fast, reliable, great code quality
- FALLBACK: OpenRouter free models — slower, rate limited, use sparingly
- LOCAL: qwen2.5-coder:3b — last resort only, weak on JSON/structured output
- DEAD: Cerebras (network blocked), Groq (network blocked)

== BEST IDEAS TO BUILD NEXT ==
1. Invoice Chaser — auto payment reminder sequences ($29/mo, freelancers)
2. Proposal Generator — 5 questions → professional proposal text ($29/mo, agencies)
3. Contract Expiry Tracker — alert before renewal deadlines ($19/mo, freelancers)
4. Meeting Notes Processor — paste text → action items + owners ($19/mo, remote teams)
5. Lead Qualifier — score inbound leads from CSV → ranked list ($29/mo, agencies)
6. Churn Risk Scorer — flag clients not engaged in X days ($29/mo, SaaS founders)
7. Doc Chaser — remind clients for missing documents ($19/mo, agencies)
8. OTA Rate Monitor — track competitor hotel pricing ($39/mo, Phuket hotels)
9. Review Digest — weekly review summary + reply suggestions ($29/mo, hospitality)
10. Staff Roster Scheduler — shift planner for small teams ($19/mo, restaurants/hotels)

== DEMO PATTERN (copy exactly) ==
def demo():
    print("=== PRODUCTNAME DEMO ===")
    db = get_db()
    # Insert hardcoded sample data
    db.execute("INSERT OR IGNORE INTO items VALUES (1,'Sample Client','2026-05-01','pending')")
    db.commit()
    # Show it working
    rows = db.execute("SELECT * FROM items").fetchall()
    for r in rows:
        print(f"  {r[0]}: {r[1]} — due {r[2]} [{r[3]}]")
    print("✓ Demo complete — 3 items tracked, 1 overdue alert sent")
    db.close()


=== TED'S RATINGS (human ground truth) ===

[2026-04-30] TED RATED: 20260429_codetester = 5/10
  Feedback: The idea is good, the execution needs Mistral not local. That rating goes into brain.db and teaches the system "phase 3 needs cloud API, never accept local-only builds."
  Lesson: 20260429_codetester was ok: The idea is good, the execution needs Mistral not local. That rating goes into brain.db and teaches the system "phase 3 needs cloud API, never accept local-only builds.". Can improve.


=== TED'S RATINGS (human ground truth) ===

[2026-04-30] TED RATED: 20260429_invoicetracker = 3/10
  Feedback: no target No price too little too small no faces and the demo failed Not good enough
  Lesson: 20260429_invoicetracker failed: no target No price too little too small no faces and the demo failed Not good enough. Avoid this pattern.


=== TED'S RATINGS (human ground truth) ===

[2026-04-30] TED RATED: 20260430_proposal_generator = 5/10
  Feedback: no comment
  Lesson: 20260430_proposal_generator was ok: no comment. Can improve.


=== WHAT I HAVE LEARNED (updated 2026-05-03 22:00) ===
Health Score: 93%
Total builds: 20
Average build score: 11
Best API so far: Cerebras (llama3.1-8b confirmed working)
Online builds: 20/20

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

=== BUILDS TO COPY (score 8-10) ===
  ✅ 20260426_jarvismon (9/10): demo works
     Lesson: 20260426_jarvismon worked: you need this to be working so please work on it. Build more like this.
  ✅ 20260426_promptbench (9/10): demo works
     Lesson: 20260426_promptbench worked: this is very useful for you and you should always use it. Build more like this.
  ✅ 20260429_followup (9/10): demo works
     Lesson: FollowUp is the template for good builds: simple problem, clean demo, clear buyer. Build more like this.
  ✅ 20260426_contextinject (8/10): demo works
     Lesson: 20260426_contextinject worked: this is very useful for your own knowledge. Build more like this.
  ✅ 20260502_freelancer_pro_suite (8/10): demo works
=== BUILDS TO NEVER REPEAT (score 1-3) ===
  ❌ 20260429_invoicetracker (3/10)
     Why bad: no target No price too little too small no faces and the demo failed Not good enough
  ❌ 20260426_invoicer (2/10)
     Why bad: the demo is not working The idea is OK
  ❌ 20260428_fpga_insights (1/10)
     Why bad: this is not a valid build Please don't build things like this
=== BUILDS THAT NEED IMPROVEMENT (score 4-7) ===
  ⚠️  20260427_buildscorer (7/10)
     Fix: 20260427_buildscorer was ok: it's very important that when you test something that it actually works
  ⚠️  20260430_pricepilot (7/10)
     Fix: PricePilot pattern works: hardcoded demo with real DB schema. Price tracker is a strong product for 
  ⚠️  20260502_taxcruncher_cli (7/10)
     Fix: 20260502_taxcruncher_cli was ok: clean demo, formatted output, real use case, but needs the actual r
  ⚠️  20260501_chasepy (6/10)
     Fix: 20260501_chasepy was ok: demo works, shows real data, but Q2/Q3/Q4 all zero (only one quarter popula
  ⚠️  20260429_codetester (5/10)
     Fix: 20260429_codetester was ok: The idea is good, the execution needs Mistral not local. That rating goe
  ⚠️  20260430_proposal_generator (5/10)
     Fix: 20260430_proposal_generator was ok: no comment. Can improve.
  ⚠️  20260502_ota_rate_monitor (5/10)
     Fix: 20260502_ota_rate_monitor was ok: hey it's a good idea but it needs much more work to be polished re
  ⚠️  20260426_buildscorer (4/10)
     Fix: 20260426_buildscorer failed: needs a target needs a price and more descriptions. Avoid this pattern.
  ⚠️  20260429_pricewatch (4/10)
     Fix: 20260429_pricewatch failed: this could be valuable and could be implemented in something else that w

Last 5 builds:
  - 2026-05-03 | DoubleCheck CLI phase 2 | score:13
  - 2026-05-03 | DoubleCheck CLI phase 3 | score:13
  - 2026-05-03 | AgentBridge phase 1 | score:13
  - 2026-05-03 | AgentBridge phase 2 | score:8
  - 2026-05-03 | AgentBridge phase 3 | score:13
=== BUILDS TO COPY (score 8-10) ===
  ✅ 20260426_jarvismon (9/10): demo works
     Lesson: 20260426_jarvismon worked: you need this to be working so please work on it. Build more like this.
  ✅ 20260426_promptbench (9/10): demo works
     Lesson: 20260426_promptbench worked: this is very useful for you and you should always use it. Build more like this.
  ✅ 20260429_followup (9/10): demo works
     Lesson: FollowUp is the template for good builds: simple problem, clean demo, clear buyer. Build more like this.
  ✅ 20260426_contextinject (8/10): demo works
     Lesson: 20260426_contextinject worked: this is very useful for your own knowledge. Build more like this.
  ✅ 20260502_freelancer_pro_suite (8/10): demo works
=== BUILDS TO NEVER REPEAT (score 1-3) ===
  ❌ 20260429_invoicetracker (3/10)
     Why bad: no target No price too little too small no faces and the demo failed Not good enough
  ❌ 20260426_invoicer (2/10)
     Why bad: the demo is not working The idea is OK
  ❌ 20260428_fpga_insights (1/10)
     Why bad: this is not a valid build Please don't build things like this
=== BUILDS THAT NEED IMPROVEMENT (score 4-7) ===
  ⚠️  20260427_buildscorer (7/10)
     Fix: 20260427_buildscorer was ok: it's very important that when you test something that it actually works
  ⚠️  20260430_pricepilot (7/10)
     Fix: PricePilot pattern works: hardcoded demo with real DB schema. Price tracker is a strong product for 
  ⚠️  20260502_taxcruncher_cli (7/10)
     Fix: 20260502_taxcruncher_cli was ok: clean demo, formatted output, real use case, but needs the actual r
  ⚠️  20260501_chasepy (6/10)
     Fix: 20260501_chasepy was ok: demo works, shows real data, but Q2/Q3/Q4 all zero (only one quarter popula
  ⚠️  20260429_codetester (5/10)
     Fix: 20260429_codetester was ok: The idea is good, the execution needs Mistral not local. That rating goe
  ⚠️  20260430_proposal_generator (5/10)
     Fix: 20260430_proposal_generator was ok: no comment. Can improve.
  ⚠️  20260502_ota_rate_monitor (5/10)
     Fix: 20260502_ota_rate_monitor was ok: hey it's a good idea but it needs much more work to be polished re
  ⚠️  20260426_buildscorer (4/10)
     Fix: 20260426_buildscorer failed: needs a target needs a price and more descriptions. Avoid this pattern.
  ⚠️  20260429_pricewatch (4/10)
     Fix: 20260429_pricewatch failed: this could be valuable and could be implemented in something else that w

Last 5 builds:
  - 2026-05-02 | TaxCruncher CLI phase 2 | score:13
  - 2026-05-02 | Freelancer Pro Suite phase 1 | score:8
  - 2026-05-02 | Freelancer Pro Suite phase 2 | score:10
  - 2026-05-02 | Freelancer Pro Suite phase 3 | score:13
  - 2026-05-02 | OTA Rate Monitor phase 1 | score:13
=== BUILDS TO COPY (score 8-10) ===
  ✅ 20260426_jarvismon (9/10): demo works
     Lesson: 20260426_jarvismon worked: you need this to be working so please work on it. Build more like this.
  ✅ 20260426_promptbench (9/10): demo works
     Lesson: 20260426_promptbench worked: this is very useful for you and you should always use it. Build more like this.
  ✅ 20260429_followup (9/10): demo works
     Lesson: FollowUp is the template for good builds: simple problem, clean demo, clear buyer. Build more like this.
  ✅ 20260426_contextinject (8/10): demo works
     Lesson: 20260426_contextinject worked: this is very useful for your own knowledge. Build more like this.
=== BUILDS TO NEVER REPEAT (score 1-3) ===
  ❌ 20260429_invoicetracker (3/10)
     Why bad: no target No price too little too small no faces and the demo failed Not good enough
  ❌ 20260426_invoicer (2/10)
     Why bad: the demo is not working The idea is OK
  ❌ 20260428_fpga_insights (1/10)
     Why bad: this is not a valid build Please don't build things like this
=== BUILDS THAT NEED IMPROVEMENT (score 4-7) ===
  ⚠️  20260427_buildscorer (7/10)
     Fix: 20260427_buildscorer was ok: it's very important that when you test something that it actually works
  ⚠️  20260430_pricepilot (7/10)
     Fix: PricePilot pattern works: hardcoded demo with real DB schema. Price tracker is a strong product for 
  ⚠️  20260429_codetester (5/10)
     Fix: 20260429_codetester was ok: The idea is good, the execution needs Mistral not local. That rating goe
  ⚠️  20260430_proposal_generator (5/10)
     Fix: 20260430_proposal_generator was ok: no comment. Can improve.
  ⚠️  20260426_buildscorer (4/10)
     Fix: 20260426_buildscorer failed: needs a target needs a price and more descriptions. Avoid this pattern.
  ⚠️  20260429_pricewatch (4/10)
     Fix: 20260429_pricewatch failed: this could be valuable and could be implemented in something else that w

Last 5 builds:
  - 2026-04-30 | Proposal Generator phase 1 | score:13
  - 2026-04-30 | Proposal Generator phase 2 | score:0
  - 2026-04-30 | Proposal Generator phase 2 | score:10
  - 2026-04-30 | Proposal Generator phase 3 | score:13
  - 2026-05-01 | ChasePy phase 1 | score:8
=== BUILDS TO COPY (score 8-10) ===
  ✅ 20260426_jarvismon (9/10): demo works
     Lesson: 20260426_jarvismon worked: you need this to be working so please work on it. Build more like this.
  ✅ 20260426_promptbench (9/10): demo works
     Lesson: 20260426_promptbench worked: this is very useful for you and you should always use it. Build more like this.
  ✅ 20260429_followup (9/10): demo works
     Lesson: FollowUp is the template for good builds: simple problem, clean demo, clear buyer. Build more like this.
  ✅ 20260426_contextinject (8/10): demo works
     Lesson: 20260426_contextinject worked: this is very useful for your own knowledge. Build more like this.
=== BUILDS TO NEVER REPEAT (score 1-3) ===
  ❌ 20260429_invoicetracker (3/10)
     Why bad: no target No price too little too small no faces and the demo failed Not good enough
  ❌ 20260426_invoicer (2/10)
     Why bad: the demo is not working The idea is OK
  ❌ 20260428_fpga_insights (1/10)
     Why bad: this is not a valid build Please don't build things like this
=== BUILDS THAT NEED IMPROVEMENT (score 4-7) ===
  ⚠️  20260427_buildscorer (7/10)
     Fix: 20260427_buildscorer was ok: it's very important that when you test something that it actually works
  ⚠️  20260430_pricepilot (7/10)
     Fix: PricePilot pattern works: hardcoded demo with real DB schema. Price tracker is a strong product for 
  ⚠️  20260429_codetester (5/10)
     Fix: 20260429_codetester was ok: The idea is good, the execution needs Mistral not local. That rating goe
  ⚠️  20260430_proposal_generator (5/10)
     Fix: 20260430_proposal_generator was ok: no comment. Can improve.
  ⚠️  20260426_buildscorer (4/10)
     Fix: 20260426_buildscorer failed: needs a target needs a price and more descriptions. Avoid this pattern.
  ⚠️  20260429_pricewatch (4/10)
     Fix: 20260429_pricewatch failed: this could be valuable and could be implemented in something else that w

Last 5 builds:
  - 2026-04-30 | PricePilot phase 3 | score:8
  - 2026-04-30 | Proposal Generator phase 1 | score:13
  - 2026-04-30 | Proposal Generator phase 2 | score:0
  - 2026-04-30 | Proposal Generator phase 2 | score:10
  - 2026-04-30 | Proposal Generator phase 3 | score:13

=== TED'S RATINGS (human ground truth) ===

[2026-05-02] TED RATED: 20260501_chasepy = 6/10
  Feedback: demo works, shows real data, but Q2/Q3/Q4 all zero (only one quarter populated). Feedback: "demo needs data in all 4 quarters, good concept"
  Lesson: 20260501_chasepy was ok: demo works, shows real data, but Q2/Q3/Q4 all zero (only one quarter populated). Feedback: "demo needs data in all 4 quarters, good concept". Can improve.


=== TED'S RATINGS (human ground truth) ===

[2026-05-02] TED RATED: 20260502_taxcruncher_cli = 7/10
  Feedback: clean demo, formatted output, real use case, but needs the actual reminder sending in phase 2. Feedback: "good demo format, needs reminder sequences built in phase 2"
  Lesson: 20260502_taxcruncher_cli was ok: clean demo, formatted output, real use case, but needs the actual reminder sending in phase 2. Feedback: "good demo format, needs reminder sequences built in phase 2". Can improve.

== REFLEXION LESSONS (auto-generated, do not edit) ==
These are patterns learned from actual build failures and Ted's ratings:

NEVER DO (caused build failures):
  ❌ [1x] NEVER use required=True on subparsers — check --demo with parse_known_args() first
  ❌ [1x] NEVER write more than 2 new functions per phase — stay under 150 lines total

ALWAYS DO (caused good ratings):
  ✅ ALWAYS: Best build so far. Demo works perfectly. Real use case for freelancers. Ready for Stripe integration.
  ✅ ALWAYS: this is very useful for you and you should always use it
  ✅ ALWAYS: you need this to be working so please work on it

AVOID (caused bad ratings):
  ⚠️  NEVER build hardware/FPGA/ML training ideas — only data tools and automations
  ⚠️  NEVER: this is not a valid build Please don't build things like this
  ⚠️  NEVER: the demo is not working The idea is OK