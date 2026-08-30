# EndpointChecker



## Problem
Developers need to know if their APIs are healthy. No simple CLI tool exists that checks multiple endpoints and shows formatted response times.

## Solution  
A CLI tool that monitors and tests API endpoint health with response time tracking, showing results in formatted table output, with --demo mode showing sample endpoint data

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
