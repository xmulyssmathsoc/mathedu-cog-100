#!/usr/bin/env python3
"""Query the self-contained SQLite database. No external services required.
Examples:
 python scripts/query.py --id CAL-003
 python scripts/query.py --domain PRO --difficulty 3 --limit 6
 python scripts/query.py --id LIN-009 --json
"""
import argparse, json, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description='MathEdu-Cog 100: search questions and cognitive annotations')
 p.add_argument('--id',help='exact ID, e.g. CAL-003')
 p.add_argument('--domain',choices=['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG'])
 p.add_argument('--difficulty',type=int,choices=list(range(1,6)),help='maximum difficulty')
 p.add_argument('--limit',type=int,default=20)
 p.add_argument('--json',action='store_true')
 args=p.parse_args()
 con=sqlite3.connect(ROOT/'data'/'mathedu_cog_100.sqlite')
 con.row_factory=sqlite3.Row
 stmt='SELECT id,domain_code,difficulty,stage,split,stem,correct_answer FROM questions WHERE 1=1'
 vals=[]
 if args.id:stmt+=' AND id=?';vals.append(args.id)
 if args.domain:stmt+=' AND domain_code=?';vals.append(args.domain)
 if args.difficulty:stmt+=' AND difficulty<=?';vals.append(args.difficulty)
 stmt+=' ORDER BY domain_code,id LIMIT ?';vals.append(args.limit)
 questions=[dict(q) for q in con.execute(stmt,vals).fetchall()]
 for q in questions:
  id=q['id']
  q['steps']=[e['explanation'] for row in con.execute('SELECT doc FROM solutions WHERE item_id=?',(id,)) for m in json.loads(row[0])['methods'] for e in m['steps']]
  q['errors']=[{'category':r['category'],'signature':r['signature'],'example':json.loads(r['doc'])['wrong_answer_examples'][0]} for r in con.execute('SELECT category,signature,doc FROM error_patterns WHERE item_id=? ORDER BY id',(id,))]
  q['probes']=[{'question':r['stem'],'answer':r['correct_answer']} for r in con.execute('SELECT stem,correct_answer FROM diagnostic_probes WHERE item_id=? ORDER BY id',(id,))]
  q['teaching_hint']=con.execute('SELECT message FROM teaching_interventions WHERE item_id=?',(id,)).fetchone()[0]
 con.close()
 if args.json:print(json.dumps(questions,ensure_ascii=False,indent=2));return
 if not questions:print('未找到匹配题目。');return
 for q in questions:
  print('\n'+'='*72)
  print(q['id'],f'D{q["difficulty"]}',q['stage'],f'({q["split"]})')
  print('题目:',q['stem'],'\n标准答案:',q['correct_answer'])
  for k,step in enumerate(q['steps'],1):print(f'步骤{k}:',step)
  print('候选错误:', '； '.join(z['signature'] for z in q['errors']))
  for k,p in enumerate(q['probes'],1):print(f'诊断{k}:',p['question'],'\n    答案:',p['answer'])
  print('最小提示:',q['teaching_hint'])

if __name__=='__main__':main()
