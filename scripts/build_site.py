#!/usr/bin/env python3
"""Generate the offline-friendly GitHub Pages explorer from canonical dataset files.
No network requests, no additional Python packages required.
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAINS = {
    'NUM': '数与运算', 'ALG': '代数与方程', 'FUN': '函数与图像',
    'GEO': '几何与解析几何', 'TRI': '三角函数与向量',
    'PRO': '概率与组合计数', 'STA': '统计与数据分析',
    'CAL': '微积分与数学分析', 'LIN': '线性代数',
    'LOG': '逻辑、离散数学与证明',
}

records = [json.loads(line) for line in (ROOT / 'data/canonical_records.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
by_type = defaultdict(list)
for r in records: by_type[r['record_type']].append(r)
solutions = {r['item_id']: r for r in by_type['solution']}
errors = defaultdict(list)
for r in by_type['error_pattern']:
    for key in r.get('item_ids',[]): errors[key].append(r)
probes = defaultdict(list)
for r in by_type['diagnostic_probe']: probes[r['base_item_id']].append(r)
hypotheses = defaultdict(list)
for r in by_type['cognitive_hypothesis']:
    for cid in r.get('associated_error_ids',[]):
        for item in by_type['error_pattern']:
            if item['id']==cid:
                for qid in item.get('item_ids',[]):
                    if len(hypotheses[qid])<4 and r not in hypotheses[qid]: hypotheses[qid].append(r)
interventions = {r['id'].replace('T-',''):r for r in by_type['teaching_intervention']}
items=[]
for r in by_type['item']:
    key=r['id']
    item={
        'id':key,'code':key.split('-')[0],'stem':r['stem'],
        'difficulty':r['difficulty']['value'],'stage':r['education_stage'],
        'correct_answer':r['correct_answer'],
        'topic':r.get('knowledge_requirements',[{}])[0].get('evidence',''),
        'solution_steps':[
            step.get('explanation','')
            for method in solutions.get(key,{}).get('methods',[])
            for step in method.get('steps',[])
        ],
        'errors':[{k:v for k,v in err.items() if k in ('observed_signature','wrong_answer_examples','first_error_location')} for err in errors[key]],
        'probes':[{k:v for k,v in probe.items() if k in ('stem','correct_answer','probe_type')} for probe in probes[key]],
        'hypotheses':[{k:v for k,v in hyp.items() if k in ('label','kind')} for hyp in hypotheses[key]][:3],
        'intervention':interventions.get(key,{}).get('learner_facing_message',''),
    }
    items.append(item)
cases=[json.loads(line) for line in (ROOT/'data/error_cases_30.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
site={'domains':DOMAINS,'items':items,'cases':cases}
assert len(items)==100 and len(cases)==30
assert all(item['solution_steps'] and len(item['errors'])==2 and len(item['probes'])==2 for item in items)
serialized=json.dumps(site,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
html=(ROOT/'site/template.html').read_text(encoding='utf-8').replace('__INLINE_JSON__',serialized)
(ROOT/'index.html').write_text(html,encoding='utf-8')
print('Generated offline/site explorer:',len(items),'questions,',len(cases),'cases,',len(html.encode('utf-8')),'bytes')
