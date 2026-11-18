#!/usr/bin/env python3
"""Fast, offline-only integrity smoke checks; no third-party dependencies."""
import json, sqlite3, re
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cn=sqlite3.connect(ROOT/'data/mathedu_cog_100.sqlite')
assert cn.execute('pragma integrity_check').fetchone()[0]=='ok'
assert not cn.execute('pragma foreign_key_check').fetchall()
assert cn.execute('select count(*) from questions').fetchone()[0]==100
assert cn.execute('select count(*) from error_cases').fetchone()[0]==30
assert cn.execute('select count(*) from all_records').fetchone()[0]==2081
cases=[json.loads(s) for s in (ROOT/'data/error_cases_30.jsonl').read_text(encoding='utf8').splitlines() if s.strip()]
assert len(cases)==30 and len({c['case_id'] for c in cases})==30
assert all(c['simulated_student_response']['source_type']=='constructed_synthetic' for c in cases)
assert Counter(c['domain_code'] for c in cases)==dict.fromkeys(['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG'],3)
ids={x[0]:x[1] for x in cn.execute('select id, split from questions')}
assert all(c['item_id'] in ids and c['split']==ids[c['item_id']] for c in cases)
site=(ROOT/'index.html').read_text(encoding='utf8')
assert '__INLINE_JSON__' not in site
m=re.search(r'<script id="site-data" type="application/json">(.*?)</script>',site,re.S)
assert m
obj=json.loads(m.group(1))
assert len(obj['items'])==100 and len(obj['cases'])==30
assert all(len(r['solution_steps'])>=1 and len(r['probes'])==2 for r in obj['items'])
for folder in ['train','validation','synthetic_test']:
    assert (ROOT/'exports'/folder/'tutoring_sft.jsonl').is_file()
assert (ROOT/'assets/banner.svg').is_file()
print('PASS: 100 core items, 30 synthetic cases, 2,081 canonical records, linked splits, static explorer and assets')
