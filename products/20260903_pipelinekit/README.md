# PipelineKit

Chain CLI tools with one JSON config

## Problem
JARVIS builders waste time writing glue code to chain CLI tools together. No simple way to define a pipeline of tools with data passing between them.

## Solution  
A CLI tool that reads a JSON pipeline definition, runs each tool in sequence, passing data via stdin/stdout or files, with built-in retry, logging, and error handling.

## Usage
```bash
python3 main.py --help
python3 main.py --demo
```

## Tech Stack
os, sys, json, csv, sqlite3, argparse, datetime, pathlib, subprocess, urllib.request, re, time

## Built by JARVIS
Date: 2026-09-03
Score: 13/20
Phases: [1, 2, 3]
Built offline: False
