# AgentBridge

Turn any CLI tool into an MCP server in 5 minutes

## Problem
Developers have powerful CLI tools but cannot connect them to Claude, ChatGPT or any AI agent without writing complex MCP server boilerplate.

## Solution  
A Python CLI that wraps any existing command-line tool and auto-generates a working MCP server with proper tool definitions, input schemas, and error handling.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-03
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
