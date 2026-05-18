import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.expanduser('~/.jarvis/memory/tokentight.db')

def demo():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            token_count INTEGER NOT NULL,
            compressed_text TEXT NOT NULL,
            compression_ratio REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS common_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            verbose_phrase TEXT UNIQUE NOT NULL,
            concise_replacement TEXT NOT NULL,
            token_savings INTEGER NOT NULL,
            category TEXT NOT NULL
        )
    ''')

    # Insert sample patterns with realistic token savings
    patterns = [
        ("in order to", "to", 2, "conjunction"),
        ("due to the fact that", "because", 4, "conjunction"),
        ("at this point in time", "now", 4, "time"),
        ("for the purpose of", "for", 3, "preposition"),
        ("in the event that", "if", 3, "condition"),
        ("until such time as", "until", 3, "time"),
        ("in the near future", "soon", 3, "time"),
        ("in the process of", "while", 3, "time"),
        ("in the majority of cases", "usually", 4, "frequency"),
        ("in the absence of", "without", 3, "negation")
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO common_patterns
        (verbose_phrase, concise_replacement, token_savings, category)
        VALUES (?, ?, ?, ?)
    ''', patterns)

    # Insert demo token data showing compression
    demo_data = [
        ("The quick brown fox jumps over the lazy dog.", 9, "The quick brown fox jumps over the lazy dog.", 1.0),
        ("Pack my box with five dozen liquor jugs.", 8, "Pack my box with five dozen liquor jugs.", 1.0),
        ("How vexingly quick daft zebras jump!", 6, "How vexingly quick daft zebras jump!", 1.0),
        ("TokenTight compresses text efficiently while preserving meaning.", 7, "TokenTight compresses text efficiently while preserving meaning.", 1.0),
        ("Demonstrating token efficiency with realistic sample data for the demo.", 10, "Demonstrating token efficiency with realistic sample data for the demo.", 1.0)
    ]

    cursor.executemany('''
        INSERT INTO token_data (original_text, token_count, compressed_text, compression_ratio, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', [(text, tokens, compressed, ratio, datetime.now().isoformat()) for text, tokens, compressed, ratio in demo_data])

    conn.commit()

    # Retrieve and display all data
    cursor.execute('SELECT id, original_text, token_count, compressed_text, compression_ratio, timestamp FROM token_data ORDER BY id')
    token_rows = cursor.fetchall()

    cursor.execute('SELECT id, verbose_phrase, concise_replacement, token_savings, category FROM common_patterns ORDER BY id')
    pattern_rows = cursor.fetchall()

    conn.close()

    # Print formatted tables
    print("\nTokenTight Demo - Token Efficiency Examples:")
    print("=" * 120)
    print(f"{'ID':<3} {'Original Text':<50} {'Tokens':<6} {'Compressed Text':<50} {'Ratio':<6} {'Timestamp'}")
    print("=" * 120)
    for row in token_rows:
        print(f"{row[0]:<3} {row[1][:47]:<50} {row[2]:<6} {row[3][:47]:<50} {row[4]:<6.2f} {row[5]}")
    print("=" * 120)
    print(f"Total token examples: {len(token_rows)}\n")

    print("\nTokenTight Demo - Common Pattern Replacements:")
    print("=" * 100)
    print(f"{'ID':<3} {'Verbose Phrase':<25} {'Replacement':<15} {'Savings':<8} {'Category'}")
    print("=" * 100)
    for row in pattern_rows:
        print(f"{row[0]:<3} {row[1][:23]:<25} {row[2][:13]:<15} {row[3]:<8} {row[4]}")
    print("=" * 100)
    print(f"Total patterns loaded: {len(pattern_rows)}")
    print("\nDemo complete.\n")

def main():
    parser = argparse.ArgumentParser(description='TokenTight - Reduce LLM token usage through intelligent compression')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample data')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')

    # Count tokens command
    count_parser = subparsers.add_parser('count', help='Count tokens in text')
    count_parser.add_argument('text', type=str, help='Text to count tokens in')

    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress text using pattern replacements')
    compress_parser.add_argument('text', type=str, help='Text to compress')

    # List patterns command
    subparsers.add_parser('patterns', help='List all common pattern replacements')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if args.command == 'count':
        text = args.text
        words = text.split()
        token_count = len(words)
        print(f"\nToken count for input text: {token_count}\n")

    elif args.command == 'compress':
        text = args.text
        cursor.execute('SELECT verbose_phrase, concise_replacement FROM common_patterns')
        replacements = cursor.fetchall()

        compressed = text
        total_savings = 0

        for verbose, concise in replacements:
            if verbose in compressed:
                count = compressed.count(verbose)
                compressed = compressed.replace(verbose, concise)
                total_savings += count * (len(verbose.split()) - len(concise.split()))

        words = compressed.split()
        token_count = len(words)

        print("\nCompression Results:")
        print("=" * 80)
        print(f"Original text: {text}")
        print(f"Compressed text: {compressed}")
        print(f"Original token count: {len(text.split())}")
        print(f"Compressed token count: {token_count}")
        print(f"Token savings: {len(text.split()) - token_count}")
        print(f"Compression ratio: {token_count/len(text.split()):.2f}")
        print("=" * 80)

        # Store the compressed version
        cursor.execute('''
            INSERT INTO token_data (original_text, token_count, compressed_text, compression_ratio, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (text, len(text.split()), compressed, token_count/len(text.split()), datetime.now().isoformat()))
        conn.commit()

    elif args.command == 'patterns':
        cursor.execute('SELECT verbose_phrase, concise_replacement, token_savings, category FROM common_patterns ORDER BY id')
        rows = cursor.fetchall()

        print("\nCommon Pattern Replacements:")
        print("=" * 80)
        print(f"{'Verbose Phrase':<25} {'Replacement':<15} {'Savings':<8} {'Category'}")
        print("=" * 80)
        for row in rows:
            print(f"{row[0][:23]:<25} {row[1][:13]:<15} {row[2]:<8} {row[3]}")
        print("=" * 80)
        print(f"Total patterns: {len(rows)}\n")

    conn.close()

if __name__ == '__main__':
    main()