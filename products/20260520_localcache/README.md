# LocalCache



## Problem
Users frequently re-run the same commands and want instant retrieval of previous output without re-executing, especially for long-running or expensive operations.

## Solution  
CLI tool that caches stdout/stderr of commands with a user-defined key, allowing retrieval, deletion, and listing of cached results using a local SQLite database.

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
