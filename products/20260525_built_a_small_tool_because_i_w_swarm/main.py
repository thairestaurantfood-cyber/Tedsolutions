#!/usr/bin/env python3
"""PromptVersion - CLI tool for managing version-controlled LLM prompts."""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

DB_PATH = Path("prompts.db")
SCHEMA_VERSION = 1

class PromptVersion:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self._init_db()
    
    def _init_db(self):
        with self.conn:
            self.conn.execute("CREATE TABLE IF NOT EXISTS prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, version INTEGER NOT NULL, content TEXT NOT NULL, model TEXT NOT NULL, temperature REAL NOT NULL, performance_score REAL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, metadata TEXT)")
            self.conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
            if not self.conn.execute("SELECT 1 FROM schema_version").fetchone():
                self.conn.execute("INSERT INTO schema_version (version) VALUES (1)")
    
    def add_prompt(self, name: str, version: int, content: str, model: str, temperature: float, performance_score: Optional[float] = None, metadata: Optional[Dict] = None) -> int:
        now = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO prompts (name, version, content, model, temperature, performance_score, created_at, updated_at, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, version, content, model, temperature, performance_score, now, now, metadata_json)
            )
            return cursor.lastrowid
    
    def get_prompt(self, name: str, version: int) -> Optional[Dict]:
        cursor = self.conn.execute("SELECT id, name, version, content, model, temperature, performance_score, created_at, updated_at, metadata FROM prompts WHERE name = ? AND version = ?", (name, version))
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "version": row[2], "content": row[3],
                "model": row[4], "temperature": row[5], "performance_score": row[6],
                "created_at": row[7], "updated_at": row[8], "metadata": json.loads(row[9]) if row[9] else {}
            }
        return None
    
    def list_prompts(self, name: Optional[str] = None) -> List[Dict]:
        query = "SELECT id, name, version, content, model, temperature, performance_score, created_at, updated_at, metadata FROM prompts"
        params = ()
        if name:
            query += " WHERE name = ?"
            params = (name,)
        query += " ORDER BY name, version"
        
        results = []
        for row in self.conn.execute(query, params):
            results.append({
                "id": row[0], "name": row[1], "version": row[2], "content": row[3],
                "model": row[4], "temperature": row[5], "performance_score": row[6],
                "created_at": row[7], "updated_at": row[8], "metadata": json.loads(row[9]) if row[9] else {}
            })
        return results
    
    def compare_versions(self, name: str, version1: int, version2: int) -> Dict:
        p1 = self.get_prompt(name, version1)
        p2 = self.get_prompt(name, version2)
        if not p1 or not p2:
            return {"error": "One or both versions not found"}
        return {
            "name": name, "version1": p1, "version2": p2,
            "differences": {
                "content": p1["content"] != p2["content"],
                "model": p1["model"] != p2["model"],
                "temperature": p1["temperature"] != p2["temperature"],
                "performance_score": p1.get("performance_score") != p2.get("performance_score")
            }
        }
    
    def demo(self):
        if DB_PATH.exists():
            DB_PATH.unlink()
        self.conn.close()
        self.__init__()
        
        samples = [
            {"name": "story_generator", "version": 1, "content": "Write a creative story about a dragon", "model": "gpt-4", "temperature": 0.7, "performance_score": 8.5, "metadata": {"author": "alice", "tags": ["creative", "fiction"]}},
            {"name": "story_generator", "version": 2, "content": "Write a creative story about a dragon in a fantasy world", "model": "gpt-4", "temperature": 0.8, "performance_score": 9.0, "metadata": {"author": "alice", "tags": ["creative", "fiction", "fantasy"]}},
            {"name": "code_assistant", "version": 1, "content": "Explain how this Python code works", "model": "gpt-3.5-turbo", "temperature": 0.3, "performance_score": 7.8, "metadata": {"author": "bob", "tags": ["technical", "coding"]}}
        ]
        
        for sample in samples:
            self.add_prompt(**sample)
        
        prompts = self.list_prompts()
        print("\n" + "="*120)
        print(f"{'ID':<5} {'Name':<20} {'Version':<10} {'Model':<15} {'Temp':<6} {'Score':<8} {'Created':<25} {'Content'}")
        print("="*120)
        
        for p in prompts:
            content_preview = p["content"][:50] + "..." if len(p["content"]) > 50 else p["content"]
            print(f"{p['id']:<5} {p['name']:<20} {p['version']:<10} {p['model']:<15} {p['temperature']:<6.1f} {p.get('performance_score', 0):<8.1f} {p['created_at'][:19].replace('T', ' '):<25} {content_preview}")
        
        print("="*120)
        print(f"\nTotal prompts: {len(prompts)}")
        return 0
    
    def close(self):
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description="PromptVersion - Manage version-controlled LLM prompts")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new prompt version")
    add_parser.add_argument("--name", required=True, help="Prompt name")
    add_parser.add_argument("--version", type=int, required=True, help="Version number")
    add_parser.add_argument("--content", required=True, help="Prompt content")
    add_parser.add_argument("--model", required=True, help="Model name")
    add_parser.add_argument("--temperature", type=float, required=True, help="Temperature")
    add_parser.add_argument("--score", type=float, help="Performance score")
    add_parser.add_argument("--metadata", help="JSON metadata")
    
    # Get command
    get_parser = subparsers.add_parser("get", help="Get a prompt version")
    get_parser.add_argument("--name", required=True, help="Prompt name")
    get_parser.add_argument("--version", type=int, required=True, help="Version number")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all prompts")
    list_parser.add_argument("--name", help="Filter by prompt name")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two versions")
    compare_parser.add_argument("--name", required=True, help="Prompt name")
    compare_parser.add_argument("--version1", type=int, required=True, help="First version")
    compare_parser.add_argument("--version2", type=int, required=True, help="Second version")
    
    # Check for --demo flag in original args
    if "--demo" in sys.argv:
        app = PromptVersion()
        try:
            return app.demo()
        finally:
            app.close()
    
    # Parse remaining args
    args = parser.parse_args()
    
    app = PromptVersion()
    try:
        if args.command == "add":
            metadata = json.loads(args.metadata) if args.metadata else {}
            app.add_prompt(args.name, args.version, args.content, args.model, args.temperature, args.score, metadata)
            print(f"Added {args.name} version {args.version}")
        elif args.command == "get":
            prompt = app.get_prompt(args.name, args.version)
            print(json.dumps(prompt, indent=2) if prompt else f"Prompt {args.name} version {args.version} not found")
        elif args.command == "list":
            for p in app.list_prompts(args.name):
                print(f"{p['name']} v{p['version']}: {p['content'][:50]}...")
        elif args.command == "compare":
            result = app.compare_versions(args.name, args.version1, args.version2)
            print(json.dumps(result, indent=2) if "error" not in result else result["error"])
        else:
            parser.print_help()
            return 1
    finally:
        app.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
