# LocalLens

Privacy-first CLI web scraper with local LLM analysis

## Problem
Developers and small businesses need to extract and analyze web data without sending sensitive info to third-party APIs or cloud services.

## Solution  
Scrapes websites locally, stores data in SQLite, and analyzes it with a local LLM (no internet required). Runs entirely offline with optional cloud sync for backups.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-29
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
