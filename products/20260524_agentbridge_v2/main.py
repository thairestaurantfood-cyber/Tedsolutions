#!/usr/bin/env python3
import argparse, ast, json, os, sqlite3, sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


def extract_argparse_schema(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source)
        schema = {'commands': [], 'arguments': []}

        def sv(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return node.value
            return None

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            attr = getattr(getattr(node, 'func', None), 'attr', None)

            if attr == 'add_parser' and node.args:
                name = sv(node.args[0])
                desc = next((sv(kw.value) for kw in node.keywords if kw.arg == 'help'), None)
                if name:
                    schema['commands'].append({'name': name, 'description': desc})

            if attr == 'add_argument' and node.args:
                name = sv(node.args[0])
                if name:
                    name = name.lstrip('-')
                    help_text = next((sv(kw.value) for kw in node.keywords if kw.arg == 'help'), None)
                    arg_type = next((kw.value.id for kw in node.keywords if kw.arg == 'type' and isinstance(kw.value, ast.Name)), None)
                    required = next((kw.value.value for kw in node.keywords if kw.arg == 'required' and isinstance(kw.value, ast.Constant)), False)
                    schema['arguments'].append({'name': name, 'help': help_text, 'type': arg_type, 'required': required})

        return schema
    except Exception as e:
        print(f"Error extracting schema: {e}", file=sys.stderr)
        return None


def generate_mcp_server(schema, output_dir='output'):
    try:
        os.makedirs(output_dir, exist_ok=True)
        server_path = f"{output_dir}/mcp_server.py"
        schema_str = json.dumps(schema).replace('false', 'False').replace('null', 'None')
        with open(server_path, 'w') as f:
            f.write(f"""#!/usr/bin/env python3
# MCP Server stub for AgentBridge
# Schema endpoint would be available at: http://localhost:8080/schema
# Execute endpoint would be available at: http://localhost:8080/execute
print("MCP Server stub - endpoints would be:")
print("- GET /schema - Returns the extracted schema")
print("- POST /execute - Execute commands with args")
print("Schema:", {schema_str})
""")
        return server_path
    except Exception as e:
        print(f"Error generating MCP server: {e}", file=sys.stderr)
        return None
        
        with open(os.path.join(output_dir, 'mcp_server.py'), 'w') as f:
            f.write(server_code)
        
        return os.path.join(output_dir, 'mcp_server.py')
    
    except Exception as e:
        print(f"Error generating MCP server: {e}", file=sys.stderr)
        return None


def demo_mode():
    try:
        if os.path.exists('demo.db'):
            os.remove('demo.db')
        
        conn = sqlite3.connect('demo.db')
        conn.execute('CREATE TABLE demo_data (id INTEGER PRIMARY KEY, name TEXT NOT NULL, value INTEGER NOT NULL, description TEXT)')
        conn.executemany('INSERT INTO demo_data VALUES (?, ?, ?, ?)', [
            (1, 'Command A', 100, 'First demo command'),
            (2, 'Command B', 200, 'Second demo command'),
            (3, 'Command C', 300, 'Third demo command'),
            (4, 'Command D', 400, 'Fourth demo command')
        ])
        conn.commit()
        
        print("\n" + "="*60)
        print("DEMO MODE - AgentBridge Schema Extraction")
        print("="*60)
        print(f"{'ID':<5} {'Name':<15} {'Value':<10} {'Description':<25}")
        print("-" * 60)
        
        for row in conn.execute('SELECT * FROM demo_data'):
            print(f"{row[0]:<5} {row[1]:<15} {row[2]:<10} {row[3]:<25}")
        
        print("="*60)
        print("Demo completed successfully!")
        print("="*60 + "\n")
        conn.close()
        return 0
    except Exception as e:
        print(f"Error in demo mode: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description='AgentBridge: Extract argparse schema and generate MCP server')
    args, remaining = parser.parse_known_args()
    
    if '--demo' in remaining:
        sys.exit(demo_mode())
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    extract_parser = subparsers.add_parser('extract', help='Extract schema from Python script')
    extract_parser.add_argument('file', help='Python script file to analyze')
    extract_parser.add_argument('--output', help='Output directory', default='output')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        
        schema = extract_argparse_schema(args.file)
        if schema:
            print("Extracted Schema:")
            print(json.dumps(schema, indent=2))
            server_path = generate_mcp_server(schema, args.output)
            if server_path:
                print(f"\nMCP Server generated at: {server_path}")
                print("Run with: python3", server_path)
        else:
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()