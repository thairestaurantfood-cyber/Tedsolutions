# PromptBench
Test any prompt against all available models and rank results by speed and quality

python3 main.py --help
python3 main.py --demo

## Problem
JARVIS picks APIs blindly with no data on which model performs best for which task type

## Features
1. Send prompt to Groq, Mistral, Gemini, Novita and local ollama models
2. Time each response in milliseconds
3. Save results to SQLite leaderboard
4. Show side by side comparison in terminal
5. Export leaderboard to JSON for evolve.py to read

Price: $0/month
