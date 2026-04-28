# ContextInject
Reads system memory and injects live insights into every build prompt

python3 main.py --help
python3 main.py --demo

## Problem
evolve.py builds blindly without knowing what APIs are fastest, what bugs to avoid, or what has already been tried

## Features
1. Read model_leaderboard.json and return fastest model per task type
2. Read insights.json for known bugs and lessons
3. Generate a context block string to prepend to prompts
4. CLI to show current system knowledge summary
5. Output best model recommendation as JSON

Price: $0/month
