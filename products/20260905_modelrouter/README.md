# ModelRouter

Route your LLM requests to the fastest, cheapest, or highest quality provider automatically.

## Problem
Developers using multiple LLM providers (local Ollama, cloud APIs like Groq, Gemini) manually switch between them, wasting time and money on suboptimal choices.

## Solution  
A CLI tool that intelligently routes LLM requests based on user-defined priorities (speed, cost, quality) and real-time provider performance metrics.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-09-05
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
