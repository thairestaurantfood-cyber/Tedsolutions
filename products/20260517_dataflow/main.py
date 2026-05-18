import os
import json
import csv
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/.jarvis/dataflow/demo.db')

def print_table(title, columns, rows):
    print(f"\n{title}")
    text_rows = [[("" if value is None else str(value)) for value in row] for row in rows]
    widths = [len(column) for column in columns]
    for row in text_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], min(len(value), 40))
    line = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    print(line)
    print("| " + " | ".join(column.ljust(widths[index]) for index, column in enumerate(columns)) + " |")
    print(line)
    for row in text_rows:
        clipped = [value if len(value) <= 40 else value[:37] + "..." for value in row]
        print("| " + " | ".join(value.ljust(widths[index]) for index, value in enumerate(clipped)) + " |")
    print(line)

def clean_text(text):
    return text.strip()

def clean_missing(text, default=""):
    return text if text.strip() else default

def clean_number(text):
    try:
        return str(float(text))
    except:
        return text

def transform_data(raw_text, detected_format, inferred_columns, sample_data, quality_issues):
    cleaned = {
        'raw_text': clean_text(raw_text),
        'detected_format': detected_format,
        'inferred_columns': inferred_columns,
        'sample_data': clean_text(sample_data),
        'quality_issues': clean_text(quality_issues),
        'timestamp': datetime.now().isoformat()
    }

    if detected_format == 'CSV':
        rows = []
        for line in cleaned['sample_data'].split('\n')[1:]:
            if line.strip():
                parts = line.split(',')
                if len(parts) >= 3:
                    cleaned_row = {
                        'id': clean_number(clean_missing(parts[0])),
                        'name': clean_text(parts[1]),
                        'age': clean_number(clean_missing(parts[2]))
                    }
                    rows.append(cleaned_row)
        return rows
    elif detected_format == 'JSON':
        try:
            data = json.loads(cleaned['sample_data'])
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except:
            pass
    return []

def demo():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS exports (id INTEGER PRIMARY KEY, format TEXT, filename TEXT, content TEXT, timestamp TEXT)")

    sample_data = [
        {'id': '1', 'name': 'Invoice #1001', 'amount': '1500.50', 'date': '2024-01-15'},
        {'id': '2', 'name': 'Receipt #2002', 'amount': '75.25', 'date': '2024-01-16'},
        {'id': '3', 'name': 'Payment #3003', 'amount': '2200.00', 'date': '2024-01-17'}
    ]

    for item in sample_data:
        conn.execute("INSERT INTO exports (format, filename, content, timestamp) VALUES (?, ?, ?, ?)",
                    ('json', f"{item['name']}.json", json.dumps(item), datetime.now().isoformat()))

    conn.commit()

    rows = conn.execute("SELECT id, format, filename, content, timestamp FROM exports ORDER BY id").fetchall()
    print_table("Export Records", ["ID", "Format", "Filename", "Content Preview", "Timestamp"], rows)

    conn.close()
    print("\nDemo complete.")

def export_to_csv(rows, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        if rows:
            writer.writerow(rows[0].keys())
            for row in rows:
                writer.writerow(row.values())
    return filename

def export_to_json(rows, filename):
    with open(filename, 'w') as f:
        json.dump(rows, f, indent=2)
    return filename

def export_to_sql(rows, filename):
    with open(filename, 'w') as f:
        for row in rows:
            columns = ', '.join(row.keys())
            values = ', '.join(f"'{v}'" for v in row.values())
            f.write(f"INSERT INTO data VALUES ({values});\n")
    return filename

def export_to_xml(rows, filename):
    with open(filename, 'w') as f:
        f.write('<?xml version="1.0"?>\n<data>\n')
        for row in rows:
            f.write('  <record>\n')
            for k, v in row.items():
                f.write(f'    <{k}>{v}</{k}>\n')
            f.write('  </record>\n')
        f.write('</data>\n')
    return filename

def export_data(rows, format_type, output_path):
    if not rows:
        print("No data to export")
        return None

    filename = f"{output_path}.{format_type.lower()}"
    if format_type == 'CSV':
        return export_to_csv(rows, filename)
    elif format_type == 'JSON':
        return export_to_json(rows, filename)
    elif format_type == 'SQL':
        return export_to_sql(rows, filename)
    elif format_type == 'XML':
        return export_to_xml(rows, filename)
    return None

def main():
    parser = argparse.ArgumentParser(description="DataFlow Universal Exporter")
    parser.add_argument('--demo', action='store_true', help='Run demo')
    pre, _ = parser.parse_known_args()
    if pre.demo:
        demo()
        return

    subparsers = parser.add_subparsers(dest='command')
    export_parser = subparsers.add_parser('export', help='Export data to specified format')
    export_parser.add_argument('--format', choices=['CSV', 'JSON', 'SQL', 'XML'], required=True, help='Output format')
    export_parser.add_argument('--input', help='Input file path')
    export_parser.add_argument('--output', default='output', help='Output file path without extension')
    export_parser.add_argument('--batch', type=int, help='Batch size for processing')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == 'export':
        if not args.input:
            print("Input file required for export")
            return

        with open(args.input, 'r') as f:
            content = f.read()

        detected_format = 'CSV' if ',' in content else 'JSON' if '{' in content else 'TEXT'
        rows = transform_data(content, detected_format, [], content, "")

        output_file = export_data(rows, args.format, args.output)
        if output_file:
            print(f"\nExported to: {output_file}")
            with open(output_file, 'r') as f:
                preview = f.read()[:200] + "..." if len(f.read()) > 200 else f.read()
            print("\nPreview:")
            print(preview)

if __name__ == '__main__':
    main()
