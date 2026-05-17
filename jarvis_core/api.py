#!/usr/bin/env python3
"""
JARVIS API — single source of truth for all LLM calls.
Priority: Gemini → Mistral → OpenAI → NVIDIA → OpenRouter → Local
Import this in every JARVIS script.
"""
import os, json, time, urllib.request, urllib.error

def _load_env():
    env_path = os.path.expanduser('~/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip().strip('"').strip("'")
_load_env()

def _post(url, payload, headers={}, timeout=30):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data,
        headers={"Content-Type":"application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())

def _retry(fn, retries=2, delay=3):
    for i in range(retries):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = delay * (i + 1)
                print(f"    rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    return None

# ── Individual providers ──────────────────────────────

def call_mistral(prompt, model="mistral-small-latest", max_tokens=2000):
    key = os.getenv("MISTRAL_API_KEY","")
    if not key: return None
    try:
        def fn():
            r = _post("https://api.mistral.ai/v1/chat/completions",
                {"model":model,
                 "messages":[{"role":"user","content":prompt}],
                 "max_tokens":max_tokens,"temperature":0.3},
                {"Authorization":f"Bearer {key}"},
                timeout=60)
            return r["choices"][0]["message"]["content"].strip()
        return _retry(fn)
    except Exception as e:
        print(f"  Mistral failed: {e}"); return None

def call_gemini(prompt, max_tokens=2000):
    key = os.getenv("GEMINI_API_KEY","")
    if not key: return None
    try:
        def fn():
            r = _post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
                {"contents":[{"parts":[{"text":prompt}]}],
                 "generationConfig":{"maxOutputTokens":max_tokens,"temperature":0.3}},
                timeout=60)
            return r["candidates"][0]["content"]["parts"][0]["text"].strip()
        return _retry(fn, retries=2, delay=5)
    except Exception as e:
        print(f"  Gemini failed: {e}"); return None

def call_openai(prompt, max_tokens=2000):
    key = os.getenv("OPENAI_API_KEY","")
    if not key: return None
    try:
        def fn():
            r = _post("https://api.openai.com/v1/chat/completions",
                {"model":"gpt-4o-mini",
                 "messages":[{"role":"user","content":prompt}],
                 "max_tokens":max_tokens,"temperature":0.3},
                {"Authorization":f"Bearer {key}"},
                timeout=60)
            return r["choices"][0]["message"]["content"].strip()
        return _retry(fn, retries=2, delay=5)
    except Exception as e:
        print(f"  OpenAI failed: {e}"); return None

def call_nvidia(prompt, max_tokens=2000):
    key = os.getenv("NVIDIA_API_KEY","")
    if not key: return None
    try:
        def fn():
            r = _post("https://integrate.api.nvidia.com/v1/chat/completions",
                {"model":"meta/llama-3.3-70b-instruct",
                 "messages":[{"role":"user","content":prompt}],
                 "max_tokens":max_tokens,"temperature":0.3},
                {"Authorization":f"Bearer {key}"},
                timeout=60)
            return r["choices"][0]["message"]["content"].strip()
        return _retry(fn, retries=2, delay=5)
    except Exception as e:
        print(f"  NVIDIA failed: {e}"); return None

def call_openrouter(prompt, max_tokens=2000):
    key = os.getenv("OPENROUTER_API_KEY","")
    if not key: return None
    models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-4b-it:free",
    ]
    for model in models:
        try:
            def fn():
                r = _post("https://openrouter.ai/api/v1/chat/completions",
                    {"model":model,
                     "messages":[{"role":"user","content":prompt}],
                     "max_tokens":max_tokens},
                    {"Authorization":f"Bearer {key}",
                     "HTTP-Referer":"https://github.com/jarvis",
                     "X-Title":"JARVIS"},
                    timeout=60)
                return r["choices"][0]["message"]["content"].strip()
            result = _retry(fn, retries=2, delay=5)
            if result: return result
        except Exception as e:
            print(f"  OpenRouter {model}: {e}")
    return None

def call_local(prompt, model="gemma3:4b"):
    try:
        data = json.dumps({"model":model,"prompt":prompt,"stream":False,
            "options":{"temperature":0.3,"num_predict":800}}).encode()
        req = urllib.request.Request("http://localhost:11434/api/generate",
            data=data, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read()).get("response","").strip()
    except Exception as e:
        print(f"  Local failed: {e}"); return None

# ── Main entry point used by all scripts ─────────────

def call_local_coder(prompt):
    """Use qwen2.5-coder:7b for code generation — better than gemma3:4b for code."""
    return call_local(prompt, model="qwen2.5-coder:7b")

def ask(prompt, max_tokens=2000, fast=False):
    """
    Ask the best available LLM.
    fast=True: use smaller/faster models for simple tasks like filtering.
    Returns text or None.
    """
    if fast:
        # Fast path: Gemini flash → Mistral small → OpenAI → NVIDIA → coder local
        return (call_gemini(prompt, max_tokens=500)
                or call_mistral(prompt, model="mistral-small-latest", max_tokens=500)
                or call_openai(prompt, max_tokens=500)
                or call_nvidia(prompt, max_tokens=500)
                or call_local_coder(prompt))
    # Full path: Gemini → Mistral → OpenAI → NVIDIA → OpenRouter → coder local
    return (call_gemini(prompt, max_tokens=max_tokens)
            or call_mistral(prompt, max_tokens=max_tokens)
            or call_openai(prompt, max_tokens=max_tokens)
            or call_nvidia(prompt, max_tokens=max_tokens)
            or call_openrouter(prompt, max_tokens=max_tokens)
            or call_local_coder(prompt))

def ask_json(prompt, max_tokens=2000):
    """Ask for JSON response. Strips markdown fences. Returns dict or None."""
    raw = ask(prompt, max_tokens=max_tokens)
    if not raw: return None
    try:
        raw = raw.strip()
        # Strip markdown fences
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        if raw.endswith("```"):
            raw = "\n".join(raw.split("\n")[:-1])
        s = raw.find("{"); e = raw.rfind("}") + 1
        if s == -1: return None
        return json.loads(raw[s:e])
    except Exception as ex:
        print(f"  JSON parse failed: {ex}")
        return None

if __name__ == "__main__":
    # Self-test
    print("Testing JARVIS API layer...")
    result = ask("Say the word WORKING and nothing else.", fast=True)
    print(f"Fast test: {result}")
    result2 = ask_json('Return this exact JSON: {"status":"ok","score":9}')
    print(f"JSON test: {result2}")