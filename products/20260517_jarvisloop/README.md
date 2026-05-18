# JARVISLoop



## Problem
JARVIS builds great products but doesn't use them in its own build process, missing opportunities to demonstrate product efficacy and create a self-improving loop.

## Solution  
A meta-tool that wires JARVIS's own products together: TokenTamer logs evolve.py API calls, MCP Inspector monitors builds, and AgentBridge exposes CLI tools as MCP servers - proving our products work by using them ourselves.

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
