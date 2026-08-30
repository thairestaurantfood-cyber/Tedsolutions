# ConfigValidator



## Problem
Misconfigured apps cause deployment failures. Need a CLI tool that validates JSON/YAML/TOML configs and shows formatted error reports.

## Solution  
A CLI tool that validates configuration files against schemas with error reporting, showing formatted table of validation errors and warnings, with --demo mode showing sample validation data

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
