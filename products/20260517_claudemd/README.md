# CLAUDEmd



## Problem
Claude Code users lack an optimized CLAUDE.md file that guides the AI to understand their codebase, leading to less effective code generation and debugging.

## Solution  
A CLI tool that scans the local directory, detects language/framework/structure, uses openclaw_helper.py to call Gemini for generating a tailored CLAUDE.md, then provides a demo and polished output.

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
