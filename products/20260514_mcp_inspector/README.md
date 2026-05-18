# MCP Inspector



## Problem
Developers building MCP servers have no way to see what tool calls are being made, what parameters are passed, or why calls fail

## Solution  
A CLI tool that logs and displays MCP tool calls in real time using SQLite, with formatted table output and --demo mode showing simulated intercepts

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-14
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
