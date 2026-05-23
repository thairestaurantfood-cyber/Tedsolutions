# PayLink



## Problem
Freelancers and indie hackers need a simple way to create payment links and track payments without setting up complex Stripe accounts or banking integrations, especially for quick one-off payments.

## Solution  
CLI tool that generates shareable payment links and tracks payment status locally using SQLite, with support for custom amounts, descriptions, and optional crypto addresses.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-20
Score: 13/20
Phases: [1, 2]
Built offline: False
