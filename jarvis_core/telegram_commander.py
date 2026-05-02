#!/usr/bin/env python3
"""
JARVIS Telegram Commander — control JARVIS from your phone
Commands: /status /build /rate /plan /top /log /reflect /demo
"""
import os, json, subprocess, time, urllib.request, urllib.parse
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

TOKEN   = os.getenv("TG_TOKEN","")
CHAT_ID = os.getenv("TG_CHAT","")
JARVIS  = os.path.expanduser("~/jarvis")
last_update_id = None

def send(text):
    try:
        data = json.dumps({
            "chat_id": CHAT_ID,
            "text": str(text)[:4000],
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data=data, headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req, timeout=8)
    except Exception as e:
        print(f"Send failed: {e}")

def run(cmd, timeout=120):
    try:
        r = subprocess.check_output(cmd, shell=True,
            stderr=subprocess.STDOUT, timeout=timeout,
            cwd=JARVIS)
        return r.decode("utf-8","ignore")[:3500]
    except subprocess.CalledProcessError as e:
        return f"ERROR: {e.output.decode('utf-8','ignore')[:500]}"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"

def get_updates():
    global last_update_id
    params = {"timeout": 30}
    if last_update_id:
        params["offset"] = last_update_id + 1
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getUpdates?" + \
              urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=35) as r:
            return json.loads(r.read())
    except:
        return {"result": []}

def cmd_status():
    """System health snapshot."""
    try:
        plan = json.load(open(f"{JARVIS}/memory/daily_plan.json"))
        product = plan.get("plan",{}).get("product_name","?")
        phases  = plan.get("phases_complete",[])
        idea_src= plan.get("idea",{}).get("source","?")
    except:
        product, phases, idea_src = "none", [], "?"

    try:
        validated = json.load(open(f"{JARVIS}/memory/validated_ideas.json"))
        top_idea = validated[0]["title"][:40] if validated else "none"
    except:
        top_idea = "none"

    try:
        mem = json.load(open(f"{JARVIS}/memory/build_memory.json"))
        builds = mem.get("builds",[])
        recent = builds[-1] if builds else {}
        last_score = recent.get("score","?")
        last_product = recent.get("product","?")
    except:
        last_score, last_product = "?", "?"

    # API check
    try:
        import sys
        sys.path.insert(0, JARVIS)
        from api import call_mistral
        api_ok = "✅ Mistral" if call_mistral("say OK", max_tokens=5) else "❌ Mistral down"
    except:
        api_ok = "⚠️ API unknown"

    uptime = run("uptime -p").strip()
    return (f"🤖 *JARVIS STATUS*\n"
            f"⏱ {uptime}\n"
            f"🏗 Building: {product} (phases {phases})\n"
            f"💡 Source: {idea_src}\n"
            f"⭐ Last score: {last_score}/10 ({last_product})\n"
            f"🔥 Next idea: {top_idea}\n"
            f"🌐 {api_ok}")

def cmd_plan():
    """Show tonight's build plan."""
    try:
        plan = json.load(open(f"{JARVIS}/memory/daily_plan.json"))
        p = plan.get("plan",{})
        name    = p.get("product_name","?")
        tagline = p.get("tagline","?")
        market  = p.get("target_market","?")[:60]
        price   = p.get("monthly_price_usd","?")
        score   = p.get("overall_score","?")
        phases  = plan.get("phases_complete",[])
        features= p.get("mvp_features",[])[:3]
        phuket  = p.get("phuket_angle","")[:80]
        msg = (f"📋 *TONIGHT'S PLAN*\n\n"
               f"🏗 {name}\n"
               f"💡 {tagline}\n\n"
               f"🎯 {market}\n"
               f"💰 ${price}/mo | ⭐ {score}/10\n"
               f"✅ Phases done: {phases}\n\n"
               f"Features:\n" + "\n".join(f"• {f}" for f in features))
        if phuket and phuket.lower() != "none":
            msg += f"\n\n🇹🇭 {phuket}"
        return msg
    except Exception as e:
        return f"❌ No plan found: {e}"

def cmd_top():
    """Show top 5 validated ideas."""
    try:
        ideas = json.load(open(f"{JARVIS}/memory/validated_ideas.json"))
        build = [i for i in ideas if i.get("verdict")=="build"][:5]
        msg = "🔥 *TOP VALIDATED IDEAS*\n\n"
        for i, idea in enumerate(build):
            score = idea.get("pain_score",0)
            msg += f"{i+1}. [{score}/10] {idea['title'][:50]}\n"
            msg += f"   {idea.get('pain_evidence','')[:55]}\n\n"
        return msg
    except Exception as e:
        return f"❌ No validated ideas: {e}"

def cmd_log():
    """Last 25 lines of most recent build log."""
    logs = []
    for name in ["build_8am","build_12pm","build_5pm"]:
        p = f"{JARVIS}/logs/{name}.log"
        if os.path.exists(p):
            logs.append((os.path.getmtime(p), p, name))
    if not logs:
        return "❌ No build logs found"
    logs.sort(reverse=True)
    _, path, name = logs[0]
    lines = open(path).readlines()[-25:]
    return f"📋 *{name}* (last 25 lines)\n\n```\n{''.join(lines)[-2000:]}\n```"

def cmd_rate(args):
    """Rate last product: /rate 8 great demo clean code"""
    parts = args.strip().split(" ", 1)
    if not parts or not parts[0].isdigit():
        return "Usage: /rate 8 your feedback here"
    score    = int(parts[0])
    feedback = parts[1] if len(parts) > 1 else ""
    if not 1 <= score <= 10:
        return "Score must be 1-10"
    try:
        plan = json.load(open(f"{JARVIS}/memory/daily_plan.json"))
        product = plan.get("plan",{}).get("product_name","unknown")
        import sqlite3
        db = sqlite3.connect(f"{JARVIS}/memory/brain.db")
        db.execute("""INSERT INTO human_ratings
                      (date, product, ted_score, feedback, runs_demo)
                      VALUES (?,?,?,?,1)""",
                   (datetime.now().isoformat(), product, score, feedback))
        db.commit()
        db.close()
        # Trigger reflexion
        subprocess.Popen(["python3", f"{JARVIS}/jarvis_reflect.py"],
                        cwd=JARVIS)
        return (f"✅ *Rated!*\n"
                f"Product: {product}\n"
                f"Score: {score}/10\n"
                f"Feedback: {feedback}\n"
                f"🪞 Reflexion running...")
    except Exception as e:
        return f"❌ Rating failed: {e}"

def cmd_build():
    """Trigger a build right now."""
    try:
        plan = json.load(open(f"{JARVIS}/memory/daily_plan.json"))
        product = plan.get("plan",{}).get("product_name","?")
        phases  = plan.get("phases_complete",[])
        subprocess.Popen(["python3", f"{JARVIS}/evolve.py"], cwd=JARVIS)
        return (f"🔨 *Build triggered!*\n"
                f"Product: {product}\n"
                f"Phases done: {phases}\n"
                f"Next phase building now...")
    except Exception as e:
        return f"❌ Build failed to start: {e}"

def cmd_demo():
    """Run demo of latest product."""
    try:
        products = sorted(os.listdir(f"{JARVIS}/products"))
        products = [p for p in products if p.startswith("202")]
        if not products:
            return "❌ No products found"
        latest = products[-1]
        output = run(f"python3 {JARVIS}/products/{latest}/main.py --demo")
        return f"🎬 *Demo: {latest}*\n\n```\n{output[:1500]}\n```"
    except Exception as e:
        return f"❌ Demo failed: {e}"

def cmd_reflect():
    """Run reflexion engine now."""
    send("🪞 Running reflexion...")
    output = run(f"python3 {JARVIS}/jarvis_reflect.py", timeout=60)
    return f"🪞 *Reflexion complete*\n```\n{output[-1000:]}\n```"

def cmd_help():
    return (f"🤖 *JARVIS COMMANDS*\n\n"
            f"/status — system health\n"
            f"/plan — tonight's build plan\n"
            f"/top — top validated ideas\n"
            f"/build — trigger build now\n"
            f"/demo — run latest product demo\n"
            f"/log — last build log\n"
            f"/rate 8 feedback — rate last product\n"
            f"/reflect — run learning engine\n"
            f"/help — this message")

def handle(msg):
    text = msg.get("text","").strip()
    if not text:
        return
    print(f"CMD: {text}")

    if text == "/status":
        send(cmd_status())
    elif text == "/plan":
        send(cmd_plan())
    elif text == "/top":
        send(cmd_top())
    elif text == "/build":
        send(cmd_build())
    elif text == "/demo":
        send(cmd_demo())
    elif text == "/log":
        send(cmd_log())
    elif text.startswith("/rate "):
        send(cmd_rate(text[6:]))
    elif text == "/reflect":
        send(cmd_reflect())
    elif text in ["/help", "/start"]:
        send(cmd_help())
    elif text.startswith("/ask ") or text.startswith("/do "):
        query = text.split(" ",1)[1]
        send("🧠 Thinking...")
        result = run(f'python3 {JARVIS}/agent.py "{query}"', timeout=60)
        if result and "ERROR" not in result:
            send(result)
    else:
        send(f"Unknown command. Try /help")

def main():
    global last_update_id
    print(f"JARVIS Telegram Commander started — {datetime.now()}")
    send("🤖 JARVIS online. Type /help for commands.")
    while True:
        try:
            updates = get_updates()
            for u in updates.get("result",[]):
                last_update_id = u["update_id"]
                if "message" in u:
                    handle(u["message"])
        except Exception as e:
            print(f"Loop error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    main()
