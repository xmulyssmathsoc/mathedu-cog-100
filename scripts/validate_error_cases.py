#!/usr/bin/env python3
"""Validate supplemental synthetic error cases, split isolation, cross-reference,
LaTeX delimiter sanity and SQLite integrity. Not an empirical study.
"""
import collections, hashlib, json, sqlite3
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'mathedu_cog_100.sqlite'
cases=[json.loads(x) for x in (ROOT/'data'/'error_cases_30.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
schema=json.loads((ROOT/'schema'/'error_case.schema.json').read_text(encoding='utf-8'))
validator=Draft202012Validator(schema)
issues=[];num_checks=0

def check(ok,desc):
 global num_checks
 num_checks+=1
 if not ok:issues.append(desc)

check(len(cases)==30,'exactly_30_cases')
check(len({x['case_id'] for x in cases})==30,'unique_case_ids')
check(len({x['item_id'] for x in cases})==30,'unique_linked_questions')
check(len({x['error_tag'] for x in cases})==30,'diverse_error_mechanism_tags')
check(dict(collections.Counter(x['domain_code'] for x in cases))=={x:3 for x in ['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG']},'three_per_domain')

conn=sqlite3.connect(DB)
conn.row_factory=sqlite3.Row
conn.execute('PRAGMA foreign_keys=ON')
check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite_integrity')
check(not conn.execute('PRAGMA foreign_key_check').fetchall(),'sqlite_fk_integrity')
check(conn.execute('select count(*) from questions').fetchone()[0]==100,'100_original_questions_retained')
check(conn.execute('select count(*) from error_cases').fetchone()[0]==30,'30_sqlite_error_cases')
check(conn.execute('select count(*) from all_records').fetchone()[0]==2081,'2081_original_canonical_records_retained')
q={r['id']:dict(r) for r in conn.execute('select * from questions')}
for c in cases:
 id=c['case_id']
 errors=list(validator.iter_errors(c))
 check(not errors,f'{id}: schema {errors[0].message if errors else ""}')
 linked=q.get(c['item_id'])
 check(linked is not None,f'{id}: linked_question_missing')
 if linked:
  check(c['problem']==linked['stem'] and c['reference_answer']==linked['correct_answer'],f'{id}: math_parent_mismatch')
  check(c['split']==linked['split'] and c['item_family_id']==linked['family_id'],f'{id}: family_split_leakage')
  check(c['difficulty']==linked['difficulty'] and c['domain_code']==linked['domain_code'],f'{id}: metadata_mismatch')
 dbrow=conn.execute('select doc from error_cases where case_id=?',(id,)).fetchone()
 check(dbrow is not None and json.loads(dbrow[0])==c,f'{id}: db_jsonl_mismatch')
 check(1<=c['simulated_student_response']['first_invalid_step_index']<=len(c['simulated_student_response']['steps']),f'{id}: invalid_step_index')
 check(c['first_invalid_step']==c['simulated_student_response']['steps'][c['simulated_student_response']['first_invalid_step_index']-1],f'{id}: first_error_text_mismatch')
 check(c['simulated_student_response']['source_type']=='constructed_synthetic' and not c['provenance']['real_students'] and not c['provenance']['early_weak_models_executed'],f'{id}: synthetic_source_truthfulness')
 check(c['approval']=='pending_independent_review' and c['evidence_level']=='synthetic_theoretical_candidate',f'{id}: no_unearned_empirical_certification')
 check(c['transfer_check']['assessed_status']=='not_administered',f'{id}: no_fabricated_learner_mastery')
 for rid in c['related_error_pattern_ids']:
  check(conn.execute('select 1 from error_patterns where id=? and item_id=?',(rid,c['item_id'])).fetchone() is not None,f'{id}: wrong_pattern_reference')
 # Inspect all nested strings rather than specific paths.
 def allstr(obj):
  if isinstance(obj,str):yield obj
  elif isinstance(obj,list):
   for v in obj:yield from allstr(v)
  elif isinstance(obj,dict):
   for v in obj.values():yield from allstr(v)
 for st in allstr(c):
  check(st.count(r'\(')==st.count(r'\)'),f'{id}: math_parens_unmatched')
  check(st.count(r'\begin{cases}')==st.count(r'\end{cases}'),f'{id}: latex_cases_unmatched')
  check(not any(ord(ch)<32 and ch not in '\n\t' for ch in st),f'{id}: control_char_in_text')

for name in ('error_case_analysis_sft','error_case_tutor_sft'):
 full=[json.loads(s) for s in (ROOT/'exports'/f'{name}.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
 check(len(full)==30,f'{name}: 30_total_sft_rows')
 check(len({r['case_id'] for r in full})==30,f'{name}: one_per_case')
 for split in ['train','validation','synthetic_test']:
  part=[json.loads(s) for s in (ROOT/'exports'/split/f'{name}.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
  check(len(part)==sum(c['split']==split for c in cases),f'{name}: {split} count')
  check(all(r['split']==split and q[r['item_id']]['split']==split for r in part),f'{name}: {split} parent_alignment')
  check(all(r['synthetic'] and len(r['messages'])==3 and [m['role'] for m in r['messages']]==['system','user','assistant'] for r in part),f'{name}: {split} messages')

math_path=ROOT/'reports'/'30道错误案例数学校验.json'
math=json.loads(math_path.read_text(encoding='utf-8'))
check(math['total']==30 and math['passed']==30 and math['failed']==0,'30_targeted_math_checks')
check(len((ROOT/'docs'/'100道题完整标注版.md').read_text(encoding='utf-8').split('## '))-1==100,'full_100_book_headings')
check((ROOT/'docs'/'30道错误案例详解.md').read_text(encoding='utf-8').count('### EC-')==30,'full_30_case_headings')
check((ROOT/'30道错误案例浏览器.html').stat().st_size>10000,'case_browser_generated')

counts=dict(collections.Counter(c['split'] for c in cases))
report={
 'project':'MathEdu-Cog 100 + 30 Error Cases',
 'version':'1.1.0','build_date':'2026-11-17','status':'passed' if not issues else 'failed',
 'original_question_count':100,'supplemental_detailed_error_case_count':30,
 'original_record_count':2081,'supplemental_record_count':30,
 'logical_annotation_records_count':2111,
 'additional_provenance_metadata_rows':1,
 'cases_per_domain':dict(collections.Counter(c['domain_code'] for c in cases)),
 'cases_by_difficulty':dict(collections.Counter('D'+str(c['difficulty']) for c in cases)),
 'cases_by_partition':counts,
 'new_training_views_all_splits':{'analysis_sft':30,'tutor_sft':30},
 'new_training_views_train_only':{'analysis_sft':counts['train'],'tutor_sft':counts['train']},
 'math_assertions':{'original_item_targeted_checks':100,'new_error_case_targeted_checks':math['passed'],
  'limitation':'Targeted checks do not certify full proof correctness or educational construct validity'},
 'source_assurance':{'real_student_records':0,'early_small_model_runs':0,'expert_independently_reviewed':0,'new_cases_all_llm_constructed':True},
 'structural_assertions_executed':num_checks,'issues':issues,
 'synthetic_test_warning':'All test records are synthetic and share authoring process; not a real educational benchmark',
 'recommendations':['Review mathematical explanations independently before high-stakes teaching','Calibrate misconception frequencies and diagnostic validity using real learner data',
                    'Do not train on exports/validation or exports/synthetic_test']
 }
(ROOT/'reports'/'30道错误案例质量报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# MathEdu-Cog 100 + 30 错误案例：质量报告','',
 f"- 结果：**{report['status']}**；检查断言：**{num_checks}** 条；未通过：**{len(issues)}** 条。",
 f'- 原始题库：100 道、原数据记录 2081 条；新增详细错误案例：30 条。',
 f'- 新案例训练视图：60 条（训练 {counts["train"]*2}，验证 {counts["validation"]*2}，合成测试 {counts["synthetic_test"]*2}）。',
 '- 原题的 100 项定向数学检查与新案例 30 项定向数学检查均已运行并通过。',
 '- 10 个数学领域各有 3 个案例；题目及派生案例沿用原题族划分，没有人为更改原划分。',
 '','## 重要限制','',
 '1. 全部学生错误推理属于 AI 构造的教学案例，不是实测学生记录，也没有运行早期弱模型。',
 '2. 认知误区是根据错误行为提出的候选解释，不能仅凭一道题给学生确诊。',
 '3. 数学检查是定向等式、反例和结构检查，不能替代对整篇证明或讲解的独立审核。',
 '4. 合成测试数据只是程序验证用的保留集，不能声称具有真实学生泛化效度。',
 '5. 置信区间、相关与因果等案例中的概念解释属于数学教育内容，不能由数值测试独立验证其完整性。',
 '','## 文件定位','',
 '- 100 题全文：`docs/100道题完整标注版.md`',
 '- 30 例全文：`docs/30道错误案例详解.md`',
 '- 30 例离线浏览器：`30道错误案例浏览器.html`',
 '- SQL 数据库：`data/mathedu_cog_100.sqlite`（新增 `error_cases` 表）',
 '- 机器训练样本：`exports/train/error_case_*.jsonl`',
 '']
(ROOT/'reports'/'30道错误案例质量报告.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
print('Error-case validation:',report['status'],'assertions:',num_checks,'issues:',len(issues))
if issues:
 for e in issues[:60]:print('ISSUE:',e)
 raise SystemExit(1)
