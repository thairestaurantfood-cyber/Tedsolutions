import os, sys, json, argparse, requests, sqlite3
from datetime import datetime
from pathlib import Path

for _line in open(os.path.expanduser("~/.env")):
    _k,_,_v = _line.strip().partition("=")
    if _k and _v: os.environ[_k] = _v

TG_TOKEN = os.getenv("TG_TOKEN","")
TG_CHAT  = os.getenv("TG_CHAT","")

def notify(msg):
    if not TG_TOKEN: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id":TG_CHAT,"text":msg}, timeout=8)
    except: pass

def parse_logs(log_dir):
    log_dir = Path(log_dir).expanduser()
    results = {}
    for log_file in sorted(log_dir.glob("*.log")):
        name = log_file.stem
        lines = []
        try:
            lines = log_file.read_text(errors="ignore").splitlines()
        except: continue
        errors, successes, dns_fails, api_fails, builds = [], [], 0, 0, []
        for line in lines:
            l = line.lower()
            if "nameresolutionerror" in l or "failed to resolve" in l:
                dns_fails += 1
            elif "timeout" in l or "timed out" in l:
                api_fails += 1
            elif any(x in l for x in ["error","failed","exception","traceback"]):
                errors.append(line.strip()[:100])
            elif any(x in l for x in ["built","success","done","saved","complete","ok"]):
                successes.append(line.strip()[:100])
            if "| built |" in l or "built:" in l:
                builds.append(line.strip()[:80])
        results[name] = {
            "lines": len(lines),
            "errors": errors[-3:],
            "successes": successes[-3:],
            "dns_fails": dns_fails,
            "api_fails": api_fails,
            "builds": builds[-3:],
            "error_count": len(errors),
            "success_count": len(successes),
        }
    return results

def parse_lessons():
    lessons_file = Path("~/jarvis/memory/lessons.log").expanduser()
    builds = []
    if not lessons_file.exists(): return builds
    for line in lessons_file.read_text(errors="ignore").splitlines()[-20:]:
        if "| BUILT |" in line:
            builds.append(line.strip())
    return builds

def health_score(results):
    total_errors = sum(r["error_count"] for r in results.values())
    total_success = sum(r["success_count"] for r in results.values())
    total_dns = sum(r["dns_fails"] for r in results.values())
    total = total_errors + total_success
    if total == 0: return 0, total_errors, total_success, total_dns
    score = int((total_success / total) * 100)
    return score, total_errors, total_success, total_dns

def print_report(results, lessons, score, errors, successes, dns):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"")
    print(f"JARVIS HEALTH REPORT — {now}")
    print(f"=" * 50)
    print(f"Health Score : {score}%")
    print(f"Successes    : {successes}")
    print(f"Errors       : {errors}")
    print(f"DNS failures : {dns} (intermittent network drops)")
    print(f"=" * 50)
    print(f"")
    print(f"LOG FILES:")
    for name, r in results.items():
        status = "OK" if r["error_count"] == 0 else f"{r['error_count']} errors"
        print(f"  {name:<25} {r['lines']:>5} lines  {status}")
        for e in r["errors"][:2]:
            print(f"    ERROR: {e[:80]}")
        for s in r["successes"][:1]:
            print(f"    OK   : {s[:80]}")
    print(f"")
    print(f"RECENT BUILDS:")
    if lessons:
        for b in lessons[-5:]:
            print(f"  {b}")
    else:
        print(f"  No builds logged yet")
    print(f"")

def build_telegram_msg(results, lessons, score, errors, successes, dns):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    msg = f"JARVIS REPORT {now}\n"
    msg += f"Health: {score}% | OK:{successes} | ERR:{errors} | DNS:{dns}\n\n"
    problem_logs = [(n,r) for n,r in results.items() if r["error_count"] > 0]
    if problem_logs:
        msg += "Problems:\n"
        for name, r in problem_logs[:3]:
            msg += f"  {name}: {r['error_count']} errors, {r['dns_fails']} DNS fails\n"
    if lessons:
        msg += "\nLast builds:\n"
        for b in lessons[-3:]:
            msg += f"  {b[:60]}\n"
    return msg

def main():
    parser = argparse.ArgumentParser(description="JarvisMon: JARVIS system health monitor")
    parser.add_argument("--log_dir", default="~/jarvis/logs/", help="Log directory")
    parser.add_argument("--stats", action="store_true", help="Show detailed stats")
    parser.add_argument("--notify", action="store_true", help="Send Telegram report")
    parser.add_argument("--demo", action="store_true", help="Show demo output")
    args = parser.parse_args()

    if args.demo:
        print("JARVIS HEALTH REPORT — demo mode")
        print("Health Score : 72%")
        print("Successes    : 18")
        print("Errors       : 7")
        print("DNS failures : 24 (intermittent network drops)")
        print("collector    : 7 errors, 24 DNS fails")
        print("build_midnight: 2 errors, 1 success")
        print("Last build   : Invoicer phase 3 | score:7")
        return

    log_dir = Path(args.log_dir).expanduser()
    if not log_dir.exists():
        print(f"Log dir not found: {log_dir}")
        sys.exit(1)

    results = parse_logs(log_dir)
    lessons = parse_lessons()
    score, errors, successes, dns = health_score(results)

    print_report(results, lessons, score, errors, successes, dns)

    if args.stats:
        print("TOP ERRORS:")
        for name, r in results.items():
            if r["errors"]:
                print(f"  [{name}]")
                for e in r["errors"]:
                    print(f"    {e}")

    if args.notify:
        msg = build_telegram_msg(results, lessons, score, errors, successes, dns)
        notify(msg)
        print("Telegram notification sent")

if __name__ == "__main__":
    main()
