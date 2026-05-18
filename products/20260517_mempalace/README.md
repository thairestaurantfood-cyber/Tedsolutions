# MemPalace



## Problem
AI agents and LLMs lack persistent, structured memory systems for long-term context retention. Developers need a way to give their AI agents reliable memory that survives across sessions and conversations.

## Solution  
A CLI tool that provides persistent memory for AI agents using SQLite with vector embeddings (via local Ollama models). Features include memory storage, retrieval, forgetting mechanisms, and memory consolidation. Integrates via stdin/stdout for agent frameworks.

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
