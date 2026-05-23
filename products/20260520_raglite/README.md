# RagLite

Instant local RAG: turn any PDF or CSV into a queryable knowledge base in 30 seconds

## Problem
Small businesses and indie hackers waste hours manually searching through PDFs and spreadsheets for key information, with no easy offline-first solution.

## Solution  
Drag-and-drop any PDF or CSV into RagLite, which automatically extracts text, chunks it, and stores it in a local SQLite database. Query it instantly with natural language—no internet, no cloud, no complex setup.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-20
Score: 11/20
Phases: [1, 2, 3]
Built offline: False
