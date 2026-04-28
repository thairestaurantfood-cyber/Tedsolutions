import os, json, argparse
from pathlib import Path
from datetime import datetime

LEADERBOARD = os.path.expanduser("~/jarvis/memory/model_leaderboard.json")
INSIGHTS = os.path.expanduser("~/jarvis/memory/insights.json")

def load_leaderboard():
    try:
        data = json.load(open(LEADERBOARD))
        result = {}
        for task, models in data.items():
            if task == "updated": continue
            if not isinstance(models, list): continue
            fastest = sorted(models, key=lambda x: x.get("avg_ms",9999))[0]
            best = sorted(models, key=lambda x: x.get("avg_score",0), reverse=True)[0]
            result[task] = {
                "fastest": fastest.get("model","groq"),
                "fastest_ms": fastest.get("avg_ms",0),
                "best_score": best.get("model","groq"),
                "all": models
            }
        return result
    except Exception as e:
        return {"code":{"fastest":"groq","fastest_ms":0,"best_score":"groq","all":[]}}

def load_insights():
    try:
        return json.load(open(INSIGHTS))
    except:
        return {}

def get_best_model(task="code"):
    board = load_leaderboard()
    if task in board:
        return board[task]["fastest"]
    return "groq"

def get_context_block():
    insights = load_insights()
    board = load_leaderboard()
    bugs = insights.get("known_bugs", [])
    health = insights.get("health_score", 0)
    avg_score = insights.get("avg_score", 0)

    lines = []
    lines.append("=== JARVIS SYSTEM CONTEXT ===")
    lines.append(f"System health: {health}%")
    lines.append(f"Average build score: {avg_score}/10")
    lines.append("")
    lines.append("Best models by task:")
    for task, info in board.items():
        lines.append(f"  {task}: {info['fastest']} ({info['fastest_ms']}ms)")
    lines.append("")
    lines.append("CRITICAL - only use these imports:")
    lines.append("  os sys json csv datetime argparse sqlite3 pathlib subprocess requests")
    lines.append("")
    lines.append("Known bugs to avoid:")
    for b in bugs[:3]:
        lines.append(f"  - {b.get('bug','')[:80]}")
    lines.append("")
    lines.append("Build rules:")
    lines.append("  - Always include --help and --demo")
    lines.append("  - Use SQLite for storage")
    lines.append("  - At least 150 lines")
    lines.append("  - No external libraries except requests")
    lines.append("=== END CONTEXT ===")
    return chr(10).join(lines)

def show_summary():
    board = load_leaderboard()
    insights = load_insights()
    print(f"")
    print(f"JARVIS SYSTEM KNOWLEDGE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*50}")
    print(f"Health: {insights.get('health_score',0)}%  |  Builds: {insights.get('build_count',0)}  |  Avg score: {insights.get('avg_score',0)}/10")
    print(f"")
    print(f"MODEL LEADERBOARD:")
    for task, info in board.items():
        print(f"  Task: {task}")
        for m in info.get("all",[]):
            flag = " <- FASTEST" if m.get("model") == info["fastest"] else ""
            print(f"    {m.get('model','?'):<20} score:{m.get('avg_score',0)}/10  {m.get('avg_ms',0)}ms{flag}")
    print(f"")
    print(f"KNOWN BUGS:")
    for b in insights.get("known_bugs",[]):
        print(f"  [{b.get('count',0)}x] {b.get('bug','')[:80]}")
    print(f"")
    print(f"RECOMMENDATIONS:")
    print(f"  For code tasks: use {get_best_model('code')}")
    print(f"  For research:   use {get_best_model('research')}")
    print(f"  For filtering:  use qwen35-fast (local, free, fast)")
    print(f"")

def export_recommendations():
    board = load_leaderboard()
    rec = {
        "updated": datetime.now().isoformat(),
        "best_for_code": get_best_model("code"),
        "best_for_research": get_best_model("research"),
        "best_for_filter": "local:qwen35-fast",
        "leaderboard": board,
        "context_block": get_context_block()
    }
    out = os.path.expanduser("~/jarvis/memory/recommendations.json")
    with open(out,"w") as f:
        json.dump(rec, f, indent=2)
    print(f"Saved to {out}")
    return rec

def main():
    parser = argparse.ArgumentParser(description="ContextInject: JARVIS system knowledge CLI")
    parser.add_argument("--stats", action="store_true", help="Show system knowledge summary")
    parser.add_argument("--context", action="store_true", help="Print context block for prompts")
    parser.add_argument("--best", default="code", help="Get best model for task type")
    parser.add_argument("--export", action="store_true", help="Export recommendations JSON")
    parser.add_argument("--demo", action="store_true", help="Demo mode")
    parser.add_argument("--leaderboard", help="Leaderboard file (optional)")
    parser.add_argument("--insights", help="Insights file (optional)")
    args = parser.parse_args()

    global LEADERBOARD, INSIGHTS
    if args.leaderboard: LEADERBOARD = args.leaderboard
    if args.insights: INSIGHTS = args.insights

    if args.demo:
        print("JARVIS SYSTEM KNOWLEDGE — demo")
        print("Health: 84%  |  Builds: 28  |  Avg score: 7/10")
        print("Best for code: mistral (1774ms)")
        print("Best for research: gemini (5040ms)")
        print("Best for filter: local:qwen35-fast")
        print("Known bugs: fetch_hn_top() count= argument")
        return

    if args.stats or not any([args.context, args.export]):
        show_summary()

    if args.context:
        print(get_context_block())

    if args.export:
        export_recommendations()

if __name__ == "__main__":
    main()
