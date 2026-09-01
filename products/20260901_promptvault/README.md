# PromptVault



## Problem
Developers using LLMs struggle to track prompt evolution, compare versions, and measure effectiveness without a dedicated version control system tailored for prompts.

## Solution  
A CLI tool that stores prompts in a SQLite database with versioning, diff capabilities, and scoring metrics. Includes --demo mode showing prompt save, diff, and score comparison.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-09-01
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
