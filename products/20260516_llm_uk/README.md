# LLM UK

Run sovereign LLM inference locally with Python stdlib only

## Problem
Developers need offline-capable LLM inference without cloud dependency or heavy dependencies, but existing solutions require Flask, requests, or large frameworks

## Solution  
A Python CLI tool that runs LLM inference locally using only stdlib, with offline demo mode, SQLite storage for prompts/responses, and simple reporting. Users can add custom prompts, list history, and generate reports without internet

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-16
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
