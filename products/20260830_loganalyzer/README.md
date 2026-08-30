# LogAnalyzer



## Problem
DevOps and developers waste time grepping logs. Need a tool that can extract patterns, count occurrences, and show formatted output.

## Solution  
A CLI tool that parses and analyzes application logs with pattern matching, showing matching lines with counts in formatted table output, with --demo mode showing sample log data

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-08-30
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
