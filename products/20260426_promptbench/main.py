import os, json, sqlite3, argparse, requests, time
from datetime import datetime
from pathlib import Path

for _line in open(os.path.expanduser("~/.env")):
    _k,_,_v = _line.strip().partition("=")
    if _k and _v: os.environ[_k] = _v

DB = os.path.expanduser("~/jarvis/memory/promptbench.db")
LEADERBOARD = os.path.expanduser("~/jarvis/memory/model_leaderboard.json")

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS results
        (id INTEGER PRIMARY KEY, model TEXT, task TEXT, prompt TEXT,
         response TEXT, ms INTEGER, score INTEGER, ts TEXT)""")
    conn.commit()
    return conn

def call_model(name, prompt):
    start = time.time()
    try:
        if name == "groq":
            key = os.getenv("GROQ_API_KEY","")
            if not key: return None, 0
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization":f"Bearer {key}"},
                json={"model":"llama-3.3-70b-versatile",
                      "messages":[{"role":"user","content":prompt}],
                      "max_tokens":500},timeout=20)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
        elif name == "mistral":
            key = os.getenv("MISTRAL_API_KEY","")
            if not key: return None, 0
            r = requests.post("https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization":f"Bearer {key}"},
                json={"model":"mistral-small-latest",
                      "messages":[{"role":"user","content":prompt}],
                      "max_tokens":500},timeout=20)
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"].strip()
        elif name == "gemini":
            key = os.getenv("GEMINI_API_KEY","")
            if not key: return None, 0
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
                json={"contents":[{"parts":[{"text":prompt}]}],
                      "generationConfig":{"maxOutputTokens":500}},timeout=20)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        elif name.startswith("local:"):
            model = name.split(":",1)[1]
            r = requests.post("http://localhost:11434/api/generate",
                json={"model":model,"prompt":prompt,"stream":False,
                      "options":{"num_predict":300,"think":False}},timeout=60)
            text = r.json().get("response","").strip()
        else:
            return None, 0
        ms = int((time.time()-start)*1000)
        return text, ms
    except Exception as e:
        ms = int((time.time()-start)*1000)
        print(f"    {name} failed: {str(e)[:60]}")
        return None, ms

def score_response(text, task):
    if not text: return 0
    score = 0
    length = len(text)
    if length > 100: score += 3
    if length > 300: score += 2
    if task == "code":
        if "def " in text or "```" in text: score += 3
        if "return" in text: score += 2
    elif task == "research":
        if any(w in text.lower() for w in ["because","therefore","however","market","user"]): score += 3
        if len(text.split()) > 50: score += 2
    elif task == "filter":
        if any(w in text for w in ["{","[","score","verdict"]): score += 3
    return min(score, 10)

def save_result(conn, model, task, prompt, response, ms, score):
    conn.execute("INSERT INTO results VALUES (NULL,?,?,?,?,?,?,?)",
        (model, task, prompt[:100], (response or "")[:500], ms, score,
         datetime.now().isoformat()))
    conn.commit()

def update_leaderboard(conn):
    rows = conn.execute("""
        SELECT model, task, AVG(score) as avg_score, AVG(ms) as avg_ms, COUNT(*) as runs
        FROM results WHERE response IS NOT NULL AND response != ""
        GROUP BY model, task ORDER BY avg_score DESC
    """).fetchall()
    board = {}
    for model, task, avg_score, avg_ms, runs in rows:
        if task not in board: board[task] = []
        board[task].append({
            "model": model,
            "avg_score": round(avg_score,1),
            "avg_ms": int(avg_ms),
            "runs": runs
        })
    board["updated"] = datetime.now().isoformat()
    with open(LEADERBOARD,"w") as f:
        json.dump(board, f, indent=2)
    return board

def print_comparison(results, task):
    print(f"")
    print(f"PROMPTBENCH RESULTS — task: {task}")
    print(f"{'Model':<20} {'Score':>6} {'Time':>8} {'Preview'}")
    print(f"{'-'*70}")
    for r in sorted(results, key=lambda x: x['score'], reverse=True):
        preview = str(r['response'] or 'FAILED')[:40]
        status = f"{r['score']:>6}/10" if r['response'] else "  FAIL"
        print(f"{r['model']:<20} {status} {r['ms']:>6}ms   {preview}")
    print(f"")

def main():
    parser = argparse.ArgumentParser(description="PromptBench: Test prompt across all models")
    parser.add_argument("--prompt", help="Prompt to test")
    parser.add_argument("--task", choices=["code","research","filter"], default="code")
    parser.add_argument("--models", default="groq,mistral,gemini,local:qwen35-fast")
    parser.add_argument("--stats", action="store_true", help="Show leaderboard")
    parser.add_argument("--demo", action="store_true", help="Demo mode")
    args = parser.parse_args()

    conn = init_db()

    if args.demo:
        print("PROMPTBENCH DEMO")
        print(f"{'Model':<20} {'Score':>6} {'Time':>8} {'Preview'}")
        print(f"{'-'*70}")
        demo = [
            ("groq",20,9,"def add(a, b): return a + b"),
            ("gemini",3200,8,"Here is a Python function..."),
            ("mistral",1800,7,"def add_numbers(a, b):"),
            ("local:qwen35-fast",4800,6,"def add(a,b): # adds two"),
        ]
        for model,ms,score,preview in demo:
            print(f"{model:<20} {score:>6}/10 {ms:>6}ms   {preview}")
        return

    if args.stats:
        board = update_leaderboard(conn)
        for task, models in board.items():
            if task == "updated": continue
            print(f"\nTask: {task}")
            for m in models:
                print(f"  {m['model']:<20} avg:{m['avg_score']}/10  {m['avg_ms']}ms  ({m['runs']} runs)")
        return

    if not args.prompt:
        print("Provide --prompt or use --demo or --stats")
        return

    models = args.models.split(",")
    print(f"Testing {len(models)} models on task: {args.task}")
    print(f"Prompt: {args.prompt[:60]}...")
    print(f"")

    results = []
    for model in models:
        print(f"  Testing {model}...")
        response, ms = call_model(model.strip(), args.prompt)
        score = score_response(response, args.task)
        save_result(conn, model, args.task, args.prompt, response, ms, score)
        results.append({"model":model,"response":response,"ms":ms,"score":score})

    print_comparison(results, args.task)
    board = update_leaderboard(conn)
    print(f"Leaderboard saved to {LEADERBOARD}")
    best = results[0] if results else None
    if best:
        winner = sorted(results, key=lambda x: x['score'], reverse=True)[0]
        print(f"Winner: {winner['model']} (score:{winner['score']}/10, {winner['ms']}ms)")

if __name__ == "__main__":
    main()
