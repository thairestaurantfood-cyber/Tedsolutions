# AgentBridge



## Problem
Developers waste hours wrapping CLI tools (e.g., ffmpeg, pandoc, sqlite3) as MCP servers for AI agents. Existing solutions require complex boilerplate and deep MCP knowledge.

## Solution  
A Python CLI that auto-generates an MCP server from any command-line tool in under 5 lines of code. Just point it at a binary, and it handles stdio communication, tool discovery, and session management automatically.

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
