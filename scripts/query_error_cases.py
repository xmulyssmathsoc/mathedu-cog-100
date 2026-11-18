#!/usr/bin/env python3
"""Query added 30 detailed error cases in MathEdu-Cog SQLite database."""
import argparse,json,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description='查询 MathEdu-Cog 30 例数学错误案例')
p.add_argument('--id',help='案例编号，例如 EC-022')
p.add_argument('--item',help='原始题目编号，例如 CAL-003')
p.add_argument('--domain',choices=['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG'])
p.add_argument('--limit',type=int,default=30)
p.add_argument('--json',action='store_true')
a=p.parse_args()
conn=sqlite3.connect(ROOT/'data'/'mathedu_cog_100.sqlite')
cond=[];vals=[]
for col,value in [('case_id',a.id),('item_id',a.item),('domain_code',a.domain)]:
 if value:cond.append(f'{col}=?');vals.append(value)
where='WHERE '+' AND '.join(cond) if cond else ''
rows=[json.loads(r[0]) for r in conn.execute(f'SELECT doc FROM error_cases {where} ORDER BY case_id LIMIT ?',vals+[max(0,a.limit)])]
if a.json:print(json.dumps(rows if len(rows)!=1 else rows[0],ensure_ascii=False,indent=2))
else:
 for r in rows:
  print(f"{r['case_id']} | {r['item_id']} | D{r['difficulty']} | {r['title']}")
  print('题干:',r['problem'])
  print('错误答案:',r['simulated_student_response']['wrong_answer'])
  print('第一处失误:',r['first_invalid_step'])
  print('追问:',r['diagnosis']['probe'])
  print('参考答案:',r['reference_answer'])
  print('---')
