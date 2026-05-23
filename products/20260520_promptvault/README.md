# PromptVault



## Problem
Developers using LLMs frequently need to version, compare, and track changes to their prompts, but there's no good CLI solution for prompt version control like git for code.

## Solution  
CLI tool that stores LLM prompts in a local SQLite database with versioning, allowing save, diff, list, and restore operations, with optional git-like interface for prompt management.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-20
Score: 13/20
Phases: [1, 2]
Built offline: False
