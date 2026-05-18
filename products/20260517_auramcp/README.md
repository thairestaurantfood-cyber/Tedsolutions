# AuraMCP

Git operations via natural language in Claude Desktop

## Problem
Developers waste context-switching when they need to leave Claude Desktop to run Git commands in terminal. They want to ask Claude to 'show recent commits', 'create branch feature/x', or 'check status' and get instant results.

## Solution  
An MCP server that exposes Git operations as tools: git status, git log, git diff, git branch, git checkout, git add, git commit, git push, git pull. Works with any local Git repository and integrates directly with Claude Desktop via MCP protocol.

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
