#!/usr/bin/env python3
"""Build 30 detailed, explicitly synthetic error cases as backwards-compatible
supplemental MathEdu-Cog 100 extension. Run AFTER scripts/build_db.py.
"""
import collections, json, sqlite3, html
from pathlib import Path
from error_case_content import CASES

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'mathedu_cog_100.sqlite'
PROV='PROV-GPT6-CURATED-20261117'
COLUMNS=['case_id','item_id','item_family_id','domain_code','domain','stage','difficulty','split',
         'title','error_tag','problem','reference_answer','simulated_student_response',
         'first_invalid_step','observed_error','candidate_cognitive_explanations',
         'diagnosis','correction','teaching_intervention','transfer_check','pseudo_understanding_check',
         'related_error_pattern_ids','provenance_id','provenance','evidence_level','approval']

def dump(obj):
 return json.dumps(obj,ensure_ascii=False,indent=2)

SCHEMA={
 '$schema':'https://json-schema.org/draft/2020-12/schema',
 'title':'MathEdu-Cog ErrorCase Supplement v1.1',
 'type':'object','additionalProperties':False,
 'required':COLUMNS,
 'properties':{
  'case_id':{'type':'string','pattern':'^EC-[0-9]{3}$'},
  'item_id':{'type':'string','pattern':'^[A-Z]{3}-[0-9]{3}$'},
  'item_family_id':{'type':'string'},
  'domain_code':{'type':'string','enum':['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG']},
  'domain':{'type':'string'},
  'stage':{'type':'string'},
  'difficulty':{'type':'integer','minimum':1,'maximum':5},
  'split':{'type':'string','enum':['train','validation','synthetic_test']},
  'title':{'type':'string','minLength':5},
  'error_tag':{'type':'string','minLength':3},
  'problem':{'type':'string','minLength':10},
  'reference_answer':{'type':'string','minLength':1},
  'simulated_student_response':{
    'type':'object','additionalProperties':False,
    'required':['source_type','steps','wrong_answer','first_invalid_step_index','scenario_intent'],
    'properties':{'source_type':{'const':'constructed_synthetic'},
     'steps':{'type':'array','minItems':2,'items':{'type':'string','minLength':5}},
     'wrong_answer':{'type':'string','minLength':1},
     'first_invalid_step_index':{'type':'integer','minimum':1},
     'scenario_intent':{'const':'illustrate_a_plausible_error_not_establish_its_real_frequency'}}},
  'first_invalid_step':{'type':'string','minLength':5},
  'observed_error':{'type':'string','minLength':10},
  'candidate_cognitive_explanations':{
    'type':'object','additionalProperties':False,
    'required':['leading_hypothesis','alternative_explanation','possible_counterevidence','inference_status'],
    'properties':{'leading_hypothesis':{'type':'string','minLength':10},
     'alternative_explanation':{'type':'string','minLength':10},
     'possible_counterevidence':{'type':'string','minLength':10},
     'inference_status':{'const':'hypothesis_not_diagnosis'}}},
  'diagnosis':{'type':'object','additionalProperties':False,
    'required':['probe','mathematically_correct_response','hypothesized_misconception_response','interpretation_caution'],
    'properties':{'probe':{'type':'string','minLength':10},
      'mathematically_correct_response':{'type':'string','minLength':5},
      'hypothesized_misconception_response':{'type':'string','minLength':5},
      'interpretation_caution':{'type':'string'}}},
  'correction':{'type':'object','additionalProperties':False,
    'required':['solution_steps','resolution'],
    'properties':{'solution_steps':{'type':'array','minItems':2,'items':{'type':'string','minLength':10}},
     'resolution':{'type':'string','minLength':1}}},
  'teaching_intervention':{'type':'object','additionalProperties':False,
    'required':['minimal_hint','feedback'],
    'properties':{'minimal_hint':{'type':'string','minLength':5},'feedback':{'type':'string','minLength':10}}},
  'transfer_check':{'type':'object','additionalProperties':False,
    'required':['problem','answer','rationale','assessed_status'],
    'properties':{'problem':{'type':'string','minLength':10},'answer':{'type':'string','minLength':1},
      'rationale':{'type':'string','minLength':5},'assessed_status':{'const':'not_administered'}}},
  'pseudo_understanding_check':{'type':'object','additionalProperties':False,
    'required':['risk','independent_evidence_needed','status'],
    'properties':{'risk':{'type':'string','minLength':10},
      'independent_evidence_needed':{'type':'string','minLength':10},
      'status':{'const':'untested_synthetic_risk'}}},
  'related_error_pattern_ids':{'type':'array','items':{'type':'string'}},
  'provenance_id':{'const':PROV},
  'provenance':{'type':'object','additionalProperties':False,
   'required':['generation','real_students','early_weak_models_executed','independent_human_review','math_check_scope'],
   'properties':{'generation':{'const':'GPT-6 authored illustrative cases with code validation'},
    'real_students':{'const':False},'early_weak_models_executed':{'const':False},
    'independent_human_review':{'const':False},'math_check_scope':{'const':'one_or_more_targeted_assertions_per_case'}}},
  'evidence_level':{'const':'synthetic_theoretical_candidate'},
  'approval':{'const':'pending_independent_review'}
 }}

def create():
 assert len(CASES)==30 and len({c['item_id'] for c in CASES})==30
 conn=sqlite3.connect(DB)
 conn.execute('PRAGMA foreign_keys=ON')
 conn.row_factory=sqlite3.Row
 q={r['id']:dict(r) for r in conn.execute('select * from questions')}
 assert len(q)==100
 conn.execute('''CREATE TABLE IF NOT EXISTS error_cases (
  case_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL UNIQUE REFERENCES questions(id),
  domain_code TEXT NOT NULL,
  stage TEXT NOT NULL,
  difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5),
  split TEXT NOT NULL CHECK(split IN ('train','validation','synthetic_test')),
  title TEXT NOT NULL,
  error_tag TEXT NOT NULL,
  first_invalid_step INTEGER NOT NULL,
  provenance_id TEXT NOT NULL REFERENCES provenance(id),
  doc TEXT NOT NULL CHECK(json_valid(doc))
 )''')
 conn.execute('CREATE INDEX IF NOT EXISTS idx_error_cases_domain ON error_cases(domain_code,difficulty)')
 conn.execute('CREATE INDEX IF NOT EXISTS idx_error_cases_tag ON error_cases(error_tag)')
 conn.execute('CREATE INDEX IF NOT EXISTS idx_error_cases_split ON error_cases(split)')
 conn.execute('DELETE FROM error_cases')
 pdoc={'record_type':'provenance','id':PROV,'origin_type':'llm_synthetic',
       'generator_model':'GPT-6','validation_level':'targeted_math_checks_not_empirical',
       'timestamp':'2026-11-17','notes':'30 curated illustrative error cases, not real student observations.'}
 conn.execute('INSERT OR REPLACE INTO provenance(id,origin_type,generator_model,validation_level,doc) VALUES(?,?,?,?,?)',
              (PROV,'llm_synthetic','GPT-6','targeted_math_checks_not_empirical',dump(pdoc)))
 cases=[]
 for n,raw in enumerate(CASES,1):
  item=raw['item_id']; assert item in q,item
  assert 1<=raw['first_invalid_step']<=len(raw['wrong_steps'])
  original=q[item]; related=[]
  if raw['related_pattern_suffix'] in ('1','2'):
   rid=f'E-{item}-{raw["related_pattern_suffix"]}'
   exists=conn.execute('select 1 from error_patterns where id=? and item_id=?',(rid,item)).fetchone()
   assert exists,rid
   related.append(rid)
  case={
   'case_id':f'EC-{n:03d}','item_id':item,'item_family_id':original['family_id'],
   'domain_code':original['domain_code'],'domain':original['domain'],'stage':original['stage'],
   'difficulty':original['difficulty'],'split':original['split'],
   'title':raw['title'],'error_tag':raw['error_tag'],
   'problem':original['stem'],'reference_answer':original['correct_answer'],
   'simulated_student_response':{
    'source_type':'constructed_synthetic','steps':raw['wrong_steps'],
    'wrong_answer':raw['wrong_answer'],'first_invalid_step_index':raw['first_invalid_step'],
    'scenario_intent':'illustrate_a_plausible_error_not_establish_its_real_frequency'},
   'first_invalid_step':raw['wrong_steps'][raw['first_invalid_step']-1],
   'observed_error':raw['mechanism'],
   'candidate_cognitive_explanations':{
    'leading_hypothesis':raw['candidate_hypothesis'],
    'alternative_explanation':raw['alternative_explanation'],
    'possible_counterevidence':raw['disconfirming_evidence'],
    'inference_status':'hypothesis_not_diagnosis'},
   'diagnosis':{
    'probe':raw['diagnostic_question'],
    'mathematically_correct_response':raw['diagnostic_answer'],
    'hypothesized_misconception_response':raw['suspected_response'],
    'interpretation_caution':'预期回答只是针对某误区的理论预测，不能据单题反应确诊学生状态。'},
   'correction':{'solution_steps':raw['correct_steps'],'resolution':original['correct_answer']},
   'teaching_intervention':{'minimal_hint':raw['minimal_hint'],'feedback':raw['feedback']},
   'transfer_check':{'problem':raw['transfer_problem'],'answer':raw['transfer_answer'],
                     'rationale':raw['transfer_explanation'],'assessed_status':'not_administered'},
   'pseudo_understanding_check':{
    'risk':f'学生即使在讲解后能够复述本题结论“{original["correct_answer"]}”，仍可能只是记住了答案或纠错步骤。',
    'independent_evidence_needed':f'在不展示原解法的条件下，独立解决并解释迁移题：{raw["transfer_problem"]}',
    'status':'untested_synthetic_risk'},
   'related_error_pattern_ids':related,'provenance_id':PROV,
   'provenance':{'generation':'GPT-6 authored illustrative cases with code validation',
      'real_students':False,'early_weak_models_executed':False,'independent_human_review':False,
      'math_check_scope':'one_or_more_targeted_assertions_per_case'},
   'evidence_level':'synthetic_theoretical_candidate','approval':'pending_independent_review'}
  conn.execute('''INSERT INTO error_cases(case_id,item_id,domain_code,stage,difficulty,split,title,error_tag,first_invalid_step,provenance_id,doc)
                  VALUES(?,?,?,?,?,?,?,?,?,?,?)''',
   (case['case_id'],item,case['domain_code'],case['stage'],case['difficulty'],case['split'],
    case['title'],case['error_tag'],case['simulated_student_response']['first_invalid_step_index'],
    PROV,json.dumps(case,ensure_ascii=False)))
  cases.append(case)
 conn.commit()
 assert conn.execute('pragma integrity_check').fetchone()[0]=='ok'
 assert not conn.execute('pragma foreign_key_check').fetchall()
 conn.close()
 (ROOT/'schema'/'error_case.schema.json').write_text(dump(SCHEMA)+'\n',encoding='utf-8')
 p=ROOT/'data'/'error_cases_30.jsonl'
 p.write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in cases),encoding='utf-8')
 return cases

def make_case_docs(cases):
 out=['# 数学教育 AI：30 道典型错误案例（详细标注版）','','**数据属性**：以下“学生解答”均由 AI 设定场景编写，非真实学生记录；认知机制为待验证假设。',
  '**关联方式**：每例对应原 MathEdu-Cog 100 题库中的一道题，可通过题号查询数据库。',
  '**教学使用**：建议先展示题干与模拟错误解法，让学习者独立找错；之后再展示诊断与纠正。','']
 domains={'NUM':'数与运算','ALG':'代数与方程','FUN':'函数与图像','GEO':'几何与解析几何',
          'TRI':'三角函数与向量','PRO':'概率与组合计数','STA':'统计与数据分析',
          'CAL':'微积分与数学分析','LIN':'线性代数','LOG':'数学逻辑与证明'}
 prior=None
 for x in cases:
  d=x['domain_code'];
  if d!=prior:out.extend([f'## {domains[d]}','']);prior=d
  s=x['simulated_student_response']; co=x['correction']; dg=x['diagnosis']; tg=x['transfer_check'];h=x['candidate_cognitive_explanations']
  out.extend([f'### {x["case_id"]}｜{x["title"]}（{x["item_id"]}，D{x["difficulty"]}）','',
   '**原题**', '', f'> {x["problem"]}', '', '**模拟学生的错误解答**', ''])
  out.extend([f'{j}. {v}' for j,v in enumerate(s['steps'],1)])
  out.extend(['',f'**错误结论**：{s["wrong_answer"]}',
   f'**第一处失误**：第 {s["first_invalid_step_index"]} 步——{x["first_invalid_step"]}',
   f'**错误机制**：{x["observed_error"]}', '', '**正确解法**',''])
  out.extend([f'{j}. {v}' for j,v in enumerate(co['solution_steps'],1)])
  out.extend(['',f'**正确结论**：{co["resolution"]}', '', '**认知分析（仅为假设）**','',
   f'- 候选误区：{h["leading_hypothesis"]}',
   f'- 其他解释：{h["alternative_explanation"]}',
   f'- 可能推翻该假设的证据：{h["possible_counterevidence"]}',
   '', '**诊断性追问**', '', f'> {dg["probe"]}', '',
   f'**合理回答**：{dg["mathematically_correct_response"]}',
   f'**若仍受该误区影响，可能的回答**：{dg["hypothesized_misconception_response"]}',
   '', '**分层教学干预**', '',
   f'- 最小提示：{x["teaching_intervention"]["minimal_hint"]}',
   f'- 进一步引导：{x["teaching_intervention"]["feedback"]}',
   '', '**伪理解风险（仍需验证）**', '', x['pseudo_understanding_check']['risk'], '', x['pseudo_understanding_check']['independent_evidence_needed'],
   '', '**独立迁移检验（尚未施测）**', '', f'> {tg["problem"]}', '',
   f'**参考答案**：{tg["answer"]}',f'**推导依据**：{tg["rationale"]}',
   '', f'*来源：AI 构造案例；非真实学生数据；独立教师审核：未完成；题目划分：{x["split"]}。*',
   '', '---',''])
 (ROOT/'docs'/'30道错误案例详解.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
 idx=['# 30 道错误案例索引','',
  '| 案例 | 关联题目 | 难度 | 错误机制 | 第一处失误 |',
  '|---|---|---:|---|---|']
 for x in cases:
  invalid=x['first_invalid_step'].replace('|','\\|').replace('\n',' ')
  if len(invalid)>50:invalid=invalid[:48]+'…'
  idx.append(f"| {x['case_id']} {x['title']} | {x['item_id']} | D{x['difficulty']} | `{x['error_tag']}` | 第{x['simulated_student_response']['first_invalid_step_index']}步：{invalid} |")
 (ROOT/'docs'/'30道错误案例索引.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')

def make_full_question_book():
 conn=sqlite3.connect(DB);conn.row_factory=sqlite3.Row
 out=['# MathEdu-Cog 100：完整题目与认知标注','',
  '这是 100 道题的可阅读汇编，包含标准答案、解法步骤、两种理论错误模式、诊断追问与教学提示。',
  '全部模拟学生记录与误区均属合成/理论候选，不应视为真人观察。','']
 for q in conn.execute('select * from questions order by domain_code,id'):
  q=dict(q)
  sol=json.loads(conn.execute('select doc from solutions where item_id=?',(q['id'],)).fetchone()[0])
  errs=[json.loads(r[0]) for r in conn.execute('select doc from error_patterns where item_id=? order by id',(q['id'],))]
  probes=[json.loads(r[0]) for r in conn.execute('select doc from diagnostic_probes where item_id=? order by id',(q['id'],))]
  t=conn.execute('select message from teaching_interventions where item_id=?',(q['id'],)).fetchone()
  out.extend([f"## {q['id']}｜{q['domain_code']} · D{q['difficulty']} · {q['stage']}",'',
   f"**题目**：{q['stem']}",'',f"**参考答案**：{q['correct_answer']}",'',
   '**标准解法**',''])
  for m in sol['methods']:
   for j,step in enumerate(m['steps'],1):out.append(f"{j}. {step['explanation']}")
  out.extend(['','**典型错误与候选误区**',''])
  for j,e in enumerate(errs,1):
   out.append(f"{j}. {e['observed_signature']}。模拟错误：{'; '.join(e['wrong_answer_examples'])}")
  out.extend(['','**诊断追问**',''])
  for j,p in enumerate(probes,1):out.append(f"{j}. {p['stem']}（参考：{p['correct_answer']}）")
  if t:out.extend(['',f'**教学最小提示**：{t[0]}'])
  out.extend(['','---',''])
 conn.close()
 (ROOT/'docs'/'100道题完整标注版.md').write_text('\n'.join(out)+'\n',encoding='utf-8')

def make_training_views(cases):
 for part in ('train','validation','synthetic_test'):(ROOT/'exports'/part).mkdir(parents=True,exist_ok=True)
 for name in ('error_case_analysis_sft','error_case_tutor_sft'):
  rows=[]
  for c in cases:
   s=c['simulated_student_response'];h=c['candidate_cognitive_explanations'];dg=c['diagnosis'];co=c['correction']
   profile=f"题目：{c['problem']}\n\n模拟学生作答：\n"+'\n'.join(f'{i}. {v}' for i,v in enumerate(s['steps'],1))
   if name=='error_case_analysis_sft':
    system='你是数学教育认知诊断助理。先指出可观察的数学错误，再给出候选认知原因和替代解释；不得将单次作答视为确诊。'
    user=profile+'\n\n请指出首个失误、正确关键步骤，并设计一个有区分力的追问。'
    answer=(f"首个失误：第{s['first_invalid_step_index']}步。\n观察到的错误：{c['observed_error']}\n"
      f"可能原因：{h['leading_hypothesis']}\n其他解释：{h['alternative_explanation']}\n"
      f"纠正要点：{' '.join(co['solution_steps'])}\n诊断追问：{dg['probe']}\n"
      f"期待的数学解释：{dg['mathematically_correct_response']}\n限制：这些只是候选解释，尚无真实学生验证。")
   else:
    system='你是数学教师。面对学生的具体错误，先给最小且有针对性的提示，再设计追问，不要直接确诊其认知状态。'
    user=profile+'\n\n现在请给一条帮助学生自行发现错误的提示和一道诊断追问。'
    answer=(f"最小提示：{c['teaching_intervention']['minimal_hint']}\n"
            f"诊断追问：{dg['probe']}\n"
            f"若学生仍无法解释，再进一步引导：{c['teaching_intervention']['feedback']}\n"
            f"注意：不要仅据一次回答断言学生的内在状态。")
   rows.append({'id':f'{c["case_id"]}-{name}', 'item_id':c['item_id'],
                'case_id':c['case_id'],'family_id':c['item_family_id'],
                'split':c['split'],'synthetic':True,
                'messages':[{'role':'system','content':system},{'role':'user','content':user},
                            {'role':'assistant','content':answer}]})
  (ROOT/'exports'/f'{name}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
  for part in ('train','validation','synthetic_test'):
   selected=[r for r in rows if r['split']==part]
   (ROOT/'exports'/part/f'{name}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')

def make_browser(cases):
 # All data embedded: no API/server/network required to browse records.
 mini=[{k:v for k,v in c.items() if k not in ('provenance','provenance_id','item_family_id')} for c in cases]
 source=json.dumps(mini,ensure_ascii=False).replace('</','<\\/')
 html_content=r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MathEdu-Cog 100 · 30 道错误案例</title>
<style>
:root{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans SC","Microsoft Yahei",sans-serif;color:#17212e;background:#f5f7fa}
*{box-sizing:border-box}body{margin:0}.shell{max-width:1440px;margin:auto;padding:24px 28px 56px}
header{display:flex;gap:18px;align-items:flex-end;justify-content:space-between;margin-bottom:16px}
h1{font-size:30px;letter-spacing:-.8px;margin:5px 0 8px}h2{font-size:21px;margin:24px 0 13px}h3{font-size:15px;margin:0 0 9px}
.muted{color:#657486}.eyebrow{font-weight:700;letter-spacing:2px;color:#3b6873;text-transform:uppercase;font-size:12px}
.warning{background:#fff9e8;border:1px solid #efdb9f;color:#69551e;padding:13px 17px;border-radius:12px;margin-bottom:20px;font-size:13px}
.crumb a{color:#205c85;text-decoration:none}button,select,input{font:inherit}button{cursor:pointer}
.toolbar{display:flex;gap:12px;margin:16px 0 20px}.toolbar input,.toolbar select{background:white;border:1px solid #dbe2ea;border-radius:11px;padding:12px;color:#1d2c3c}
.toolbar input{min-width:170px;flex:1}.toolbar select{min-width:150px}.layout{display:grid;grid-template-columns:340px minmax(0,1fr);gap:20px;align-items:start}
.side,.detail{background:white;border:1px solid #e1e7ee;border-radius:16px;box-shadow:0 4px 16px rgba(25,45,65,.04)}
.side{max-height:calc(100vh - 70px);overflow:auto;position:sticky;top:18px;padding:10px}
.item{display:block;width:100%;text-align:left;background:transparent;border:0;border-radius:11px;padding:13px 12px;color:#243648}
.item:hover{background:#f3f7f9}.item.active{background:#eaf4f5}.item .small{display:block;margin:5px 0 0;color:#78899a;font-size:12px}
.item b{font-size:14px}.item .id{font-size:12px;font-weight:700;color:#40818a;margin-right:7px}
.detail{padding:27px 32px;min-height:650px}.chips{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0 18px}.chip{font-size:12px;padding:5px 10px;background:#eef2f7;border-radius:999px;color:#466075}
.section{border-top:1px solid #e6ebf0;padding-top:20px;margin-top:20px}.math{white-space:pre-wrap;line-height:1.85;overflow-wrap:anywhere}
.box{background:#f6f9fb;border:1px solid #e8edf2;border-radius:12px;padding:16px 18px;line-height:1.85}
.wrong{border-left:3px solid #c66a4f;background:#fff7f5}.right{border-left:3px solid #29896e;background:#f3faf7}
.steps{padding-left:22px}.steps li{padding:4px 0;line-height:1.88}.steps li.bad{background:#fff1eb;border-radius:6px;padding:6px 8px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:14px}.note{font-size:13px;color:#607587;line-height:1.7}
.inline-link{color:#1e607f;text-decoration:none;border-bottom:1px solid #bed0dc}.stats{display:flex;gap:20px;font-size:13px;color:#647587}.empty{text-align:center;padding:50px 20px;color:#778899}
@media(max-width:960px){.layout{grid-template-columns:1fr}.side{position:static;max-height:260px}.columns{grid-template-columns:1fr}.detail{padding:20px}.toolbar{flex-wrap:wrap}.shell{padding:18px}}
@media print{.side,.toolbar,.crumb{display:none}.layout{display:block}.detail{border:0;box-shadow:none;padding:0}.shell{padding:0}}
</style>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)'],['$','$']],displayMath:[['\\[','\\]']]},svg:{fontCache:'global'}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head><body><main class="shell"><header><div><div class="eyebrow">MATHEDU-COG · CASE LIBRARY</div><h1>30 道典型数学错误案例</h1><div class="muted">从错误推理出发，练习认知诊断与针对性教学</div></div><div class="crumb"><a href="题库浏览器.html">查看原版 100 题</a></div></header>
<div class="warning">⚠️ 所有“学生作答”都是 AI 构造的教学示例，并非真实学生数据。误区与预测回答仅为假设，尚未完成独立专家审核与学生实测。</div>
<div class="stats"><span id="summary"></span><span>10 个数学领域</span><span>与 100 题核心数据库关联</span></div>
<div class="toolbar"><input id="search" placeholder="搜索题号、主题、错误、题干…" aria-label="搜索案例"><select id="domain" aria-label="数学领域"><option value="">全部领域</option></select><select id="difficulty" aria-label="难度"><option value="">全部难度</option><option value="1">D1</option><option value="2">D2</option><option value="3">D3</option><option value="4">D4</option><option value="5">D5</option></select></div>
<div class="layout"><nav class="side" id="list" aria-label="案例列表"></nav><article class="detail" id="detail"></article></div>
</main><script>const CASES=__CASES__;
const NAMES={NUM:'数与运算',ALG:'代数与方程',FUN:'函数与图像',GEO:'几何与解析几何',TRI:'三角函数与向量',PRO:'概率与组合计数',STA:'统计与数据分析',CAL:'微积分与数学分析',LIN:'线性代数',LOG:'逻辑与证明'};
const $=id=>document.getElementById(id);let selected=CASES[0].case_id;
function node(tag,txt,className=''){const z=document.createElement(tag);if(txt!==undefined)z.textContent=txt;if(className)z.className=className;return z}
function append(el,...children){for(const ch of children)el.appendChild(ch);return el}
function section(root,title,txt,cls=''){const sec=node('section',undefined,'section');sec.appendChild(node('h3',title));sec.appendChild(node('div',txt,'box math '+cls));root.appendChild(sec);return sec}
function steps(root,title,arr,bad=0,cls=''){const s=node('section',undefined,'section');s.appendChild(node('h3',title));const ol=node('ol',undefined,'steps '+cls);arr.forEach((v,i)=>{const li=node('li',v,'math'+(i+1===bad?' bad':''));ol.appendChild(li)});s.appendChild(ol);root.appendChild(s)}
function txtp(parent,key,value){parent.appendChild(node('p',key+'：'+value,'math'))}
function show(c){selected=c.case_id;const area=$('detail');area.replaceChildren();area.appendChild(node('div',c.case_id+' / '+c.item_id,'eyebrow'));area.appendChild(node('h2',c.title));const chips=node('div',undefined,'chips');[NAMES[c.domain_code],`D${c.difficulty}`,c.stage,`来源：模拟案例`,c.error_tag].forEach(t=>chips.appendChild(node('span',t,'chip')));area.appendChild(chips);
section(area,'原题',c.problem);steps(area,'模拟学生错误推理',c.simulated_student_response.steps,c.simulated_student_response.first_invalid_step_index,'wrong');
section(area,'错误结论',c.simulated_student_response.wrong_answer,'wrong');section(area,'第一处失误',c.first_invalid_step,'wrong');section(area,'为什么错',c.observed_error);
steps(area,'正确解法',c.correction.solution_steps,0,'right');section(area,'正确结论',c.correction.resolution,'right');
const hy=node('section',undefined,'section');hy.appendChild(node('h3','认知分析（仅为假设）'));const hb=node('div',undefined,'box');txtp(hb,'候选误区',c.candidate_cognitive_explanations.leading_hypothesis);txtp(hb,'其他解释',c.candidate_cognitive_explanations.alternative_explanation);txtp(hb,'反向证据',c.candidate_cognitive_explanations.possible_counterevidence);hy.appendChild(hb);area.appendChild(hy);
section(area,'诊断追问',c.diagnosis.probe);section(area,'可能的优质回答',c.diagnosis.mathematically_correct_response,'right');section(area,'误区仍存在时可能的回答',c.diagnosis.hypothesized_misconception_response);
section(area,'最小提示',c.teaching_intervention.minimal_hint);section(area,'进一步教学引导',c.teaching_intervention.feedback);
section(area,'伪理解风险（待验证）',c.pseudo_understanding_check.risk+'\n'+c.pseudo_understanding_check.independent_evidence_needed);
section(area,'独立迁移检验（未施测）',c.transfer_check.problem);section(area,'迁移题参考答案',c.transfer_check.answer+'\n'+c.transfer_check.rationale,'right');
area.appendChild(node('p','说明：所有作答为合成案例；尚未经真人实验或独立数学教师审核；数据划分：'+c.split,'note'));renderList();if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([area]).catch(()=>{})}
function match(c){const q=$('search').value.trim().toLowerCase(),d=$('domain').value,lv=$('difficulty').value;
return (!d||c.domain_code===d)&&(!lv||String(c.difficulty)===lv)&&(!q||[c.case_id,c.item_id,NAMES[c.domain_code],c.title,c.problem,c.observed_error,c.error_tag,c.diagnosis.probe,c.candidate_cognitive_explanations.leading_hypothesis].join(' ').toLowerCase().includes(q))}
function renderList(){const subset=CASES.filter(match);$('summary').textContent=`当前 ${subset.length} / 30 个案例`;
const target=$('list');target.replaceChildren();if(!subset.length){target.appendChild(node('div','没有匹配案例','empty'));return}
for(const c of subset){const b=node('button',undefined,'item'+(c.case_id===selected?' active':''));b.type='button';b.appendChild(node('span',c.case_id,'id'));b.appendChild(node('b',c.title));b.appendChild(node('span',`${c.item_id} · ${NAMES[c.domain_code]} · D${c.difficulty}`,'small'));b.onclick=()=>show(c);target.appendChild(b)}}
for(const [d,t] of Object.entries(NAMES)){const op=node('option',t);op.value=d;$('domain').appendChild(op)}
for(const id of ['search','domain','difficulty'])$(id).addEventListener(id==='search'?'input':'change',()=>{renderList();const subset=CASES.filter(match);if(subset.length&&!subset.some(c=>c.case_id===selected))show(subset[0])});
show(CASES[0]);</script></body></html>'''
 (ROOT/'30道错误案例浏览器.html').write_text(html_content.replace('__CASES__',source),encoding='utf-8')

if __name__=='__main__':
 cases=create()
 make_case_docs(cases)
 make_full_question_book()
 make_training_views(cases)
 make_browser(cases)
 print('Built',len(cases),'linked cases; splits:',dict(collections.Counter(c['split'] for c in cases)))
