# PromptVersion



## Problem
Teams using LLMs have no way to version-control their prompts — changes get lost, performance regressions go unnoticed, no audit trail

## Solution  
CLI tool to save, retrieve, compare and score prompt versions with metadata: model used, token count, performance score. Uses OpenClaw for local testing.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-19
Score: 0/20
Phases: [1, 2, 3]
Built offline: False
