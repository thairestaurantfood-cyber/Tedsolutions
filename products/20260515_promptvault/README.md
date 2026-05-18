# PromptVault



## Problem
Developers using LLMs lack a simple CLI tool to version, diff, and test their prompts. Prompts are often hardcoded in scripts or lost in notes, making it hard to track what works best.

## Solution  
A CLI tool that stores prompts in a SQLite database with versioning, provides diff capabilities between versions, and includes a demo mode that shows the workflow using hardcoded sample prompts. The tool uses OpenClaw for any LLM-assisted features (like suggesting improvements) to ensure local/cloud flexibility and offline demo capability.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-15
Score: 8/20
Phases: [1, 2, 3]
Built offline: False
