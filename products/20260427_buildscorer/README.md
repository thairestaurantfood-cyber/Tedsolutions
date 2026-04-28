# BuildScorer
Honestly scores every JARVIS build by actually running it and testing real functionality

python3 main.py --help
python3 main.py --demo

## Problem
Current scoring only checks file size and syntax. A 200 line file that crashes still scores 7.

## Features
1. Run --help and --demo on every product in products directory
2. Check if SQLite file gets created after running
3. Check if CSV export works
4. Score 0-20 based on real functionality not just file size
5. Save honest scores back to tools.json

Price: $0/month
