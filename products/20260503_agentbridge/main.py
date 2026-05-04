#!/usr/bin/env python3
import os,sys,json,sqlite3,argparse,subprocess,re,shlex
from datetime import datetime
from pathlib import Path

DB=Path.home()/'jarvis'/'memory'/'agentbridge.db'
OUT=Path.home()/'jarvis'/'mcp_servers'
RESERVED={'and','or','not','in','is','if','else','elif','for','while','def','class',
          'return','import','from','as','with','try','except','finally','pass',
          'break','continue','lambda','yield','global','nonlocal','del','raise','assert'}

def get_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS bridges(id INTEGER PRIMARY KEY,name TEXT UNIQUE,cli_path TEXT,mcp_path TEXT,created_at TEXT,status TEXT)')
    db.commit();return db

def safe_param(name):
    name=re.sub(r'[^a-z0-9_]','_',name.lower()).lstrip('_') or 'arg'
    if name in RESERVED:name=name+'_arg'
    if name[0].isdigit():name='n_'+name
    return name

def expand_cmd(cli_path):
    """Expand ~ and return both string and list forms"""
    parts=shlex.split(os.path.expanduser(cli_path))
    return parts

def run_cmd(cmd,extra=[]):
    try:
        r=subprocess.run(cmd+extra,capture_output=True,text=True,timeout=10)
        return r.stdout+r.stderr
    except:return ''

def parse_cli(cli_path):
    base=expand_cmd(cli_path)
    help_text=run_cmd(base,['--help']) or run_cmd(base,['-h']) or run_cmd(base,['help'])
    if not help_text:
        return [{'name':'run','description':f'Run {Path(base[-1]).stem}','args':[],'subcommand':False,'flag':None}],''

    tools=[]

    # Pattern 1: git-style subcommands "  command    Description"
    for line in help_text.splitlines():
        m=re.match(r'^\s{1,6}([a-z][a-z0-9_-]{1,20})\s{2,}([A-Za-z].{3,60})',line)
        if m:
            name,desc=m.group(1),m.group(2).strip()
            if name in ('usage','options','commands','available','see','for','the','and','or','to','a'):continue
            tools.append({'name':name,'description':desc[:80],'args':[],'subcommand':True,'flag':None})

    # Pattern 2: argparse {sub1,sub2} in usage
    usage_match=re.search(r'\{([a-z,_-]+)\}',help_text)
    if usage_match and not tools:
        for cmd in usage_match.group(1).split(','):
            tools.append({'name':cmd,'description':f'Run {cmd}','args':[],'subcommand':True,'flag':None})

    # Pattern 3: --flag style tools (like pain_scout --scan --ideas)
    # Each meaningful flag becomes its own MCP tool
    flag_tools=[]
    for line in help_text.splitlines():
        m=re.match(r'^\s+(--[a-z][a-z0-9_-]+)(?:\s+([A-Z][A-Z0-9_]*))?(?:\s{2,}(.*))?',line)
        if m:
            flag=m.group(1)
            argtype=m.group(2) or ''
            desc=m.group(3) or flag.lstrip('-')
            if flag in ('--help','--demo'):continue
            if argtype:
                # --flag VALUE → parameter tool
                flag_tools.append({'name':safe_param(flag.lstrip('-')),'description':desc[:80],
                    'args':[{'flag':flag,'type':argtype,'desc':desc}],'subcommand':False,'flag':flag})
            else:
                # --flag (boolean) → standalone tool
                flag_tools.append({'name':safe_param(flag.lstrip('-')),'description':desc[:80] or flag.lstrip('-'),
                    'args':[],'subcommand':False,'flag':flag})

    if not tools and flag_tools:
        tools=flag_tools
    elif not tools:
        tools=[{'name':Path(base[-1]).stem.replace('-','_').replace('.','_'),
                'description':f'Run {Path(base[-1]).stem}','args':[],'subcommand':False,'flag':None}]

    # Drill subcommands for their args
    for t in tools[:10]:
        if t['subcommand']:
            sub_help=run_cmd(base,[t['name'],'--help'])
            if sub_help:
                for line in sub_help.splitlines():
                    m=re.match(r'^\s+(--[\w-]+)\s+([\w<>]*)\s*(.*)',line)
                    if m and m.group(1) not in ('--help','--demo','-h'):
                        t['args'].append({'flag':m.group(1),'type':m.group(2) or 'str','desc':m.group(3)[:60]})
    return tools,help_text

def generate_mcp_server(name,cli_path,tools):
    OUT.mkdir(parents=True,exist_ok=True)
    server_path=OUT/f'{name}_mcp.py'
    safe=re.sub(r'[^a-z0-9_]','_',name.lower())
    # Always use expanded absolute paths
    cmd_parts=expand_cmd(cli_path)
    cmd_json=json.dumps(cmd_parts)

    tool_funcs=[]
    for t in tools[:10]:
        tname=re.sub(r'[^a-z0-9_]','_',t['name'].lower())
        tdesc=t['description'][:80].replace('"',"'")
        params=[]
        arg_lines=[]
        seen=set()

        if t.get('flag') and not t['args']:
            # Boolean flag — no params, just append the flag
            arg_lines.append(f'    cmd += ["{t["flag"]}"]')
        elif t.get('flag') and t['args']:
            # Flag with value
            a=t['args'][0]
            pname=safe_param(a['flag'].lstrip('-'))
            params.append(f'{pname}: str = ""')
            arg_lines.append(f'    if {pname}: cmd += ["{a["flag"]}", {pname}]')
        else:
            for a in t['args'][:6]:
                if a['flag'] in ('--help','-h'):continue
                pname=safe_param(a['flag'].lstrip('-'))
                if pname in seen:pname=pname+'_2'
                seen.add(pname)
                params.append(f'{pname}: str = ""')
                arg_lines.append(f'    if {pname}: cmd += ["{a["flag"]}", {pname}]')

        params_str=', '.join(params)
        subcmd=f'["{t["name"]}"]' if t.get('subcommand') else '[]'
        arg_block='\n'.join(arg_lines) if arg_lines else '    pass'

        func=f'''
@mcp.tool
def {safe}_{tname}({params_str}) -> str:
    """{tdesc}"""
    import subprocess
    cmd = {cmd_json} + {subcmd}
{arg_block}
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return r.stdout or r.stderr or "Done"
    except Exception as e:
        return f"Error: {{e}}"
'''
        tool_funcs.append(func)

    code=f'''#!/usr/bin/env python3
# AgentBridge MCP Server — {name}
# Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} by JARVIS AgentBridge
# Works with: Claude Desktop, ChatGPT, Cursor, Windsurf, any MCP client
from fastmcp import FastMCP
mcp = FastMCP("{name}")
{"".join(tool_funcs)}
if __name__ == "__main__":
    mcp.run()
'''
    server_path.write_text(code)
    return server_path

def register_claude(name,server_path):
    config_paths=[
        Path.home()/'.config'/'Claude'/'claude_desktop_config.json',
        Path('/mnt/c/Users')/os.getenv('WINUSER','tedsa')/'AppData'/'Roaming'/'Claude'/'claude_desktop_config.json'
    ]
    for cp in config_paths:
        if cp.parent.exists():
            try:
                cfg=json.loads(cp.read_text()) if cp.exists() else {}
                cfg.setdefault('mcpServers',{})
                cfg['mcpServers'][name]={'command':'python3','args':[str(server_path)]}
                cp.write_text(json.dumps(cfg,indent=2))
                return str(cp)
            except:continue
    return None

def cmd_bridge(cli_path,name=None):
    base=expand_cmd(cli_path)
    name=name or re.sub(r'[^a-z0-9_-]','_',Path(base[-1]).stem.lower())
    print(f"🔍 Parsing {cli_path}...")
    tools,_=parse_cli(cli_path)
    print(f"✅ Found {len(tools)} tools: {[t['name'] for t in tools]}")
    print(f"⚙️  Generating MCP server...")
    server_path=generate_mcp_server(name,cli_path,tools)
    r=subprocess.run([sys.executable,'-m','py_compile',str(server_path)],capture_output=True,text=True)
    if r.returncode!=0:
        print(f"⚠️  Syntax issue: {r.stderr.strip()}")
    else:
        print(f"✅ Server verified (no syntax errors): {server_path}")
    cfg=register_claude(name,server_path)
    if cfg:print(f"✅ Claude Desktop config updated: {cfg}")
    else:print(f"ℹ️  Add manually — command: python3  args: [{server_path}]")
    db=get_db()
    db.execute('INSERT OR REPLACE INTO bridges VALUES(NULL,?,?,?,?,?)',
        (name,cli_path,str(server_path),datetime.now().isoformat(),'active'))
    db.commit();db.close()
    print(f"\n🚀 Start server:  python3 {server_path}\n")

def cmd_list():
    db=get_db()
    rows=db.execute('SELECT name,cli_path,mcp_path,status FROM bridges').fetchall()
    if not rows:print('No bridges yet.');return
    print(f"\n{'='*62}")
    print(f"  {'Name':<16}{'CLI':<28}{'Status'}")
    print(f"{'='*62}")
    for name,cli,mcp,status in rows:
        print(f"  {name:<16}{cli[:27]:<28}{status}")
        print(f"    → {mcp}")
    print(f"{'='*62}\n")

def cmd_run(name):
    db=get_db()
    row=db.execute('SELECT mcp_path FROM bridges WHERE name=?',(name,)).fetchone()
    if not row:print(f"❌ No bridge: {name}");return
    print(f"🚀 Starting {name} MCP server — Ctrl+C to stop")
    os.execv(sys.executable,[sys.executable,row[0]])

def demo():
    DB.unlink(missing_ok=True)
    print("="*62)
    print("  AGENTBRIDGE — Turn any CLI into an MCP server")
    print("="*62)
    print("\n📦 Test 1: git (real-world subcommand-style CLI)\n")
    cmd_bridge('git','git')
    print("📦 Test 2: pain_scout (flag-style JARVIS CLI)\n")
    cmd_bridge(f"python3 {Path.home()/'jarvis'/'jarvis_pain_scout.py'}",'pain_scout')
    cmd_list()
    print("📄 pain_scout MCP server preview:")
    server=OUT/'pain_scout_mcp.py'
    if server.exists():
        for l in server.read_text().splitlines()[:40]:print(f"  {l}")
        print("  ...")
    print("\n✅ AgentBridge handles any CLI style — subcommands or flags.")
    print("   Claude/ChatGPT/Cursor can now run your JARVIS tools directly.\n")

def main():
    parser=argparse.ArgumentParser(description='AgentBridge — Turn any CLI into an MCP server')
    parser.add_argument('--demo',action='store_true')
    pre,_=parser.parse_known_args()
    if pre.demo:demo();return
    sub=parser.add_subparsers(dest='command')
    pb=sub.add_parser('bridge',help='Bridge a CLI')
    pb.add_argument('cli',help='CLI path or command')
    pb.add_argument('--name',default=None)
    sub.add_parser('list',help='List bridges')
    pr=sub.add_parser('run',help='Start MCP server')
    pr.add_argument('name',help='Bridge name')
    args=parser.parse_args()
    if not args.command:parser.print_help();return
    if args.command=='bridge':cmd_bridge(args.cli,args.name)
    elif args.command=='list':cmd_list()
    elif args.command=='run':cmd_run(args.name)
if __name__=='__main__':main()
