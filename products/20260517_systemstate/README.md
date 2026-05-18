# SystemState



## Problem
The JARVIS system lacks a canonical state tracker. Agents need to read the system state first to know what happened (plan written, build started, build passed, build failed, Codex fixed, published) and coordinate.

## Solution  
A CLI tool that writes to ~/jarvis/memory/system_state.json after every major event. Under 200 lines, stdlib only.

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
