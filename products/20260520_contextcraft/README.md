# ContextCraft



## Problem
AI agents fail on large codebases because they lack contextual understanding. Current solutions require expensive embeddings or fail to provide relevant code snippets.

## Solution  
CLI tool that creates a local SQLite AST index of codebases, enabling fast semantic search without embeddings. Supports querying for functions, classes, and usage patterns.

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
