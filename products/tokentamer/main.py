#!/usr/bin/env python3
import os,sys,sqlite3,argparse,random,urllib.request,json
from datetime import datetime,timedelta
from pathlib import Path
DB=Path.home()/'jarvis'/'memory'/'tokentamer.db'
PRICES={'mistral-small-latest':{'in':0.10,'out':0.30},'mistral-large-latest':{'in':2.00,'out':6.00},'default':{'in':0.10,'out':0.30}}

def send_tg_alert(msg):
    token=os.getenv('TG_TOKEN','')
    chat=os.getenv('TG_CHAT','')
    if not token or not chat:return
    try:
        data=json.dumps({"chat_id":chat,"text":msg}).encode()
        req=urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage",data=data,headers={"Content-Type":"application/json"})
        urllib.request.urlopen(req,timeout=8)
    except Exception as e:
        print(f"[TG] failed: {e}",file=sys.stderr)

def get_db():
    DB.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB)
    db.execute('CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY,ts TEXT,script TEXT,model TEXT,prompt_tokens INTEGER,completion_tokens INTEGER,cost_usd REAL,task TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS budgets(script TEXT PRIMARY KEY,daily_limit_usd REAL,alert_pct INTEGER DEFAULT 80)')
    db.execute('CREATE TABLE IF NOT EXISTS alerts_sent(script TEXT,date TEXT,pct INTEGER,PRIMARY KEY(script,date,pct))')
    db.commit();return db

def calc_cost(model,tin,tout):
    p=PRICES.get(model,PRICES['default'])
    return(tin*p['in']+tout*p['out'])/1_000_000

def check_and_alert(db,script,spent,limit,alert_pct):
    """Fire TG alert once per threshold per day — 80% and 100%"""
    today=datetime.now().strftime('%Y-%m-%d')
    for threshold in [alert_pct,100]:
        if spent>=(limit*threshold/100):
            existing=db.execute('SELECT 1 FROM alerts_sent WHERE script=? AND date=? AND pct=?',(script,today,threshold)).fetchone()
            if not existing:
                emoji='🚨' if threshold>=100 else '⚠️'
                label='OVER BUDGET' if threshold>=100 else f'{threshold}% WARNING'
                msg=f"{emoji} TOKENTAMER {label}\n\nScript: {script}\nSpent: ${spent:.4f} / ${limit:.2f}\nThreshold: {threshold}%\n\n{'STOP THIS SCRIPT NOW' if threshold>=100 else 'Budget running low'}"
                send_tg_alert(msg)
                db.execute('INSERT OR IGNORE INTO alerts_sent VALUES(?,?,?)',(script,today,threshold))
                db.commit()
                print(f"[TG] Alert sent: {script} at {threshold}%")

def cmd_status():
    db=get_db();today=datetime.now().strftime('%Y-%m-%d')
    rows=db.execute('SELECT script,model,SUM(prompt_tokens),SUM(completion_tokens),SUM(cost_usd),COUNT(*) FROM usage WHERE ts LIKE ? GROUP BY script,model ORDER BY SUM(cost_usd) DESC',(today+'%',)).fetchall()
    total=sum(r[4] for r in rows)
    print(f"\n{'='*58}")
    print(f"  TOKENTAMER - {today}   Total: ${total:.4f}")
    print(f"{'='*58}")
    if not rows:print('  No usage today.')
    else:
        print(f"  {'Script':<20}{'Model':<18}{'In':>7}{'Out':>7}{'Cost':>9}")
        for sc,mo,tin,tout,cost,calls in rows:
            m=mo.replace('mistral-','').replace('-latest','')
            print(f"  {sc:<20}{m:<18}{tin:>7,}{tout:>7,}${cost:>8.4f}")
    budgets=db.execute('SELECT script,daily_limit_usd,alert_pct FROM budgets').fetchall()
    if budgets:
        print('\n  Budgets:')
        for sc,limit,pct in budgets:
            spent=sum(r[4] for r in rows if r[0]==sc)
            bar_pct=min(100,int(spent/limit*100))if limit else 0
            bar='█'*(bar_pct//10)+'░'*(10-bar_pct//10)
            status='OVER' if spent>=limit else('WARN' if bar_pct>=pct else'OK')
            print(f"  {sc:<18}[{bar}]{bar_pct:>3}% ${spent:.4f}/${limit:.2f} {status}")
            check_and_alert(db,sc,spent,limit,pct)
    print(f"{'='*58}\n");db.close()

def cmd_log(script,model,tin,tout,task=None):
    db=get_db();cost=calc_cost(model,tin,tout)
    db.execute('INSERT INTO usage(ts,script,model,prompt_tokens,completion_tokens,cost_usd,task)VALUES(?,?,?,?,?,?,?)',(datetime.now().isoformat(),script,model,tin,tout,cost,task))
    db.commit()
    # Check budget immediately after every log — catch threshold crossings in real time
    budgets=db.execute('SELECT daily_limit_usd,alert_pct FROM budgets WHERE script=?',(script,)).fetchone()
    if budgets:
        today=datetime.now().strftime('%Y-%m-%d')
        spent=db.execute('SELECT SUM(cost_usd) FROM usage WHERE script=? AND ts LIKE?',(script,today+'%')).fetchone()[0] or 0
        check_and_alert(db,script,spent,budgets[0],budgets[1])
    db.close()
    print(f'Logged:{script}|{tin}in/{tout}out|${cost:.5f}')

def cmd_budget(script,limit,alert=80):
    db=get_db()
    db.execute('INSERT OR REPLACE INTO budgets VALUES(?,?,?)',(script,limit,alert))
    db.commit();db.close()
    print(f'Budget:{script}=${limit:.2f}/day alert {alert}%')

def demo():
    DB.unlink(missing_ok=True);db=get_db()
    scripts=['evolve','daily_plan','jarvis_quality','jarvis_reflect','pain_scout']
    models=['mistral-small-latest','mistral-small-latest','mistral-large-latest']
    now=datetime.now()
    for i in range(40):
        sc=scripts[i%len(scripts)];mo=models[i%len(models)]
        ts=(now-timedelta(hours=i*0.4)).isoformat()
        tin=random.randint(200,1200);tout=random.randint(100,600)
        db.execute('INSERT INTO usage(ts,script,model,prompt_tokens,completion_tokens,cost_usd,task)VALUES(?,?,?,?,?,?,?)',(ts,sc,mo,tin,tout,calc_cost(mo,tin,tout),'demo'))
    db.execute("INSERT OR REPLACE INTO budgets VALUES('evolve',0.05,80)")
    db.execute("INSERT OR REPLACE INTO budgets VALUES('daily_plan',0.02,80)")
    db.commit();db.close()
    print('Demo data loaded');cmd_status()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--demo',action='store_true')
    pre,_=parser.parse_known_args()
    if pre.demo:demo();return
    sub=parser.add_subparsers(dest='command')
    sub.add_parser('status')
    pl=sub.add_parser('log')
    pl.add_argument('--script',required=True)
    pl.add_argument('--model',default='mistral-small-latest')
    pl.add_argument('--in',dest='tin',type=int,required=True)
    pl.add_argument('--out',dest='tout',type=int,required=True)
    pl.add_argument('--task',default=None)
    pb=sub.add_parser('budget')
    pb.add_argument('--script',required=True)
    pb.add_argument('--limit',type=float,required=True)
    pb.add_argument('--alert',type=int,default=80)
    args=parser.parse_args()
    if not args.command:parser.print_help();return
    if args.command=='status':cmd_status()
    elif args.command=='log':cmd_log(args.script,args.model,args.tin,args.tout,args.task)
    elif args.command=='budget':cmd_budget(args.script,args.limit,args.alert)
if __name__=='__main__':main()
