# DoubleCheck CLI

Detect double bookings across CSV exports in seconds

## Problem
Freelancers and small agencies waste hours cross-checking multiple CSV exports for overlapping bookings, leading to overbookings and lost revenue.

## Solution  
A Python CLI that scans CSV exports from different booking platforms, detects overlapping time slots, and outputs a clear report of conflicts with timestamps and booking details.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-03
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
