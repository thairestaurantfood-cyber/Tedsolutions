import os
import sys
import json
import sqlite3
import argparse
from pathlib import Path

def demo():
    DB_PATH = os.path.expanduser('~/.jarvis/claudemd_scan.db')
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_files INTEGER,
            extensions_json TEXT,
            primary_language TEXT,
            key_files_json TEXT,
            frameworks_json TEXT,
            structure_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    demo_data = {
        "total_files": 12,
        "extensions": {
            ".py": 8,
            ".js": 3,
            ".md": 1
        },
        "primary_language": "Python",
        "key_files": ["main.py", "setup.py", "README.md"],
        "frameworks": ["None detected"],
        "structure": {
            "src": 5,
            "tests": 2,
            "docs": 1
        }
    }

    cursor.execute('''
        INSERT INTO scan_results
        (total_files, extensions_json, primary_language, key_files_json, frameworks_json, structure_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        demo_data["total_files"],
        json.dumps(demo_data["extensions"]),
        demo_data["primary_language"],
        json.dumps(demo_data["key_files"]),
        json.dumps(demo_data["frameworks"]),
        json.dumps(demo_data["structure"])
    ))
    conn.commit()

    cursor.execute('SELECT * FROM scan_results ORDER BY timestamp DESC LIMIT 1')
    row = cursor.fetchone()

    print("\n=== Directory Scan Results ===")
    print(f"Total Files: {row[1]}")
    print(f"Primary Language: {row[3]}")
    print("\nExtensions:")
    extensions = json.loads(row[2])
    for ext, count in extensions.items():
        print(f"  {ext}: {count}")

    print("\nKey Files:")
    key_files = json.loads(row[4])
    for f in key_files:
        print(f"  - {f}")

    print("\nStructure:")
    structure = json.loads(row[6])
    for dir_name, count in structure.items():
        print(f"  {dir_name}: {count} items")

    conn.close()
    sys.exit(0)

def scan_directory(path="."):
    path = Path(path).expanduser()
    extensions = {}
    key_files = []
    frameworks = []
    structure = {}

    framework_indicators = {
        "React": [".js", ".jsx", "package.json"],
        "Vue": [".vue", "package.json"],
        "Django": ["manage.py", "requirements.txt"],
        "Flask": ["app.py", "requirements.txt"],
        "FastAPI": ["main.py", "requirements.txt"]
    }

    for item in path.rglob("*"):
        if item.is_file():
            ext = item.suffix
            extensions[ext] = extensions.get(ext, 0) + 1

            if ext in [".py", ".js"]:
                key_files.append(str(item.relative_to(path)))

            for lang, indicators in framework_indicators.items():
                if any(ind in str(item) for ind in indicators):
                    if lang not in frameworks:
                        frameworks.append(lang)

            parent = str(item.parent.relative_to(path))
            structure[parent] = structure.get(parent, 0) + 1

    primary_language = max(extensions.items(), key=lambda x: x[1])[0] if extensions else "Unknown"

    results = {
        "total_files": sum(extensions.values()),
        "extensions": extensions,
        "primary_language": primary_language,
        "key_files": key_files[:5],
        "frameworks": frameworks if frameworks else ["None detected"],
        "structure": structure
    }

    DB_PATH = os.path.expanduser('~/.jarvis/claudemd_scan.db')
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            total_files INTEGER,
            extensions_json TEXT,
            primary_language TEXT,
            key_files_json TEXT,
            frameworks_json TEXT,
            structure_json TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        INSERT INTO scan_results
        (total_files, extensions_json, primary_language, key_files_json, frameworks_json, structure_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        results["total_files"],
        json.dumps(results["extensions"]),
        results["primary_language"],
        json.dumps(results["key_files"]),
        json.dumps(results["frameworks"]),
        json.dumps(results["structure"])
    ))
    conn.commit()
    conn.close()

    print("\n=== Directory Scan Results ===")
    print(f"Total Files: {results['total_files']}")
    print(f"Primary Language: {results['primary_language']}")
    print("\nExtensions:")
    for ext, count in results["extensions"].items():
        print(f"  {ext}: {count}")

    print("\nKey Files:")
    for f in results["key_files"]:
        print(f"  - {f}")

    print("\nStructure:")
    for dir_name, count in results["structure"].items():
        print(f"  {dir_name}: {count} items")

def generate_claudemd():
    DB_PATH = os.path.expanduser('~/.jarvis/claudemd_scan.db')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM scan_results ORDER BY timestamp DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()

    if not row:
        print("No scan results found. Run a scan first.")
        return

    data = {
        "total_files": row[1],
        "extensions": json.loads(row[2]),
        "primary_language": row[3],
        "key_files": json.loads(row[4]),
        "frameworks": json.loads(row[5]),
        "structure": json.loads(row[6])
    }

    claudemd_content = f"""# CLAUDE.md

## Project Overview
- **Total Files**: {data['total_files']}
- **Primary Language**: {data['primary_language']}
- **Frameworks**: {', '.join(data['frameworks'])}

## File Extensions
"""
    for ext, count in data['extensions'].items():
        claudemd_content += f"- `{ext}`: {count} files\n"

    claudemd_content += "\n## Key Files\n"
    for f in data['key_files']:
        claudemd_content += f"- `{f}`\n"

    claudemd_content += "\n## Directory Structure\n"
    for dir_name, count in data['structure'].items():
        claudemd_content += f"- `{dir_name}`: {count} items\n"

    claudemd_path = Path("CLAUDE.md")
    with open(claudemd_path, 'w') as f:
        f.write(claudemd_content)

    print(f"\nCLAUDE.md generated at {claudemd_path.absolute()}")
    print("\nPreview:")
    print(claudemd_content[:500] + "..." if len(claudemd_content) > 500 else claudemd_content)

def main():
    parser = argparse.ArgumentParser(description="CLAUDEmd - AI-Powered Project Documentation Generator")
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    scan_parser = subparsers.add_parser('scan', help='Scan directory and store results')
    scan_parser.add_argument('path', nargs='?', default='.', help='Directory path to scan')

    subparsers.add_parser('generate', help='Generate CLAUDE.md from latest scan')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'scan':
        scan_directory(args.path)
    elif args.command == 'generate':
        generate_claudemd()

if __name__ == "__main__":
    main()
def generate_claudemd_with_openclaw(data):
    """Use OpenClaw/Gemini to generate intelligent CLAUDE.md content."""
    prompt = f"""You are an expert at writing CLAUDE.md files for Claude Code users.
Generate a comprehensive CLAUDE.md for a project with these characteristics:
- Primary Language: {data['primary_language']}
- Total Files: {data['total_files']}
- Frameworks: {', '.join(data['frameworks'])}
- Key Files: {', '.join(data['key_files'])}
- Structure: {json.dumps(data['structure'])}

Write a CLAUDE.md that helps Claude Code understand this codebase.
Include: project overview, architecture notes, coding conventions, key commands, and what to avoid.
Be specific and practical. Output only the CLAUDE.md content."""

    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "infer", "model", "run", "--prompt", prompt, "--model", "google/gemini-2.5-flash"],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.strip().splitlines()
        content = "\n".join(l for l in lines if not l.startswith(("model.", "provider:", "outputs:")))
        return content if len(content) > 100 else None
    except Exception as e:
        print(f"  [OpenClaw unavailable: {e}]")
        return None
