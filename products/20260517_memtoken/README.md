# MemToken



## Problem
AI agents lack persistent memory and real-time token visibility. Each interaction starts from scratch, wasting tokens on context reconstruction, while developers have no insight into token costs until bills arrive.

## Solution  
A local-first AI agent memory system that combines persistent context storage with real-time token monitoring. Uses SQLite with semantic search for memory and provides live token analytics to minimize costs while maximizing agent effectiveness.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-17
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
