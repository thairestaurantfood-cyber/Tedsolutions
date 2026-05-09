# ArbBot CLI

Find and exploit price gaps across prediction markets in real-time

## Problem
Indie devs and small businesses waste hours checking Kalshi, Polymarket, and SX.bet manually for arbitrage opportunities, missing quick profits due to slow data sync and lack of automation.

## Solution  
CLI tool that scrapes all three markets, calculates arbitrage spreads, and alerts you to profitable trades—all in under 5 seconds. Runs locally (no API keys needed) with optional automation for repeatable profits.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-05-08
Score: 10/20
Phases: [1, 2, 3]
Built offline: False
