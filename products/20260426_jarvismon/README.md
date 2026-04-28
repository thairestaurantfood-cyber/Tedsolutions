# JarvisMon
Daily health report for the JARVIS system — what worked, what broke, what to fix

python3 main.py --help
python3 main.py --demo

## Problem
JARVIS runs overnight but Ted has no easy way to see what succeeded, what failed, and why without reading raw logs

## Features
1. Read and parse all logs in ~/jarvis/logs/
2. Count successes vs failures per script
3. Show last 5 builds with scores
4. Detect common errors like DNS failures and API timeouts
5. Print clean summary and send to Telegram

Price: $0/month
