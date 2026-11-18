#!/usr/bin/env python3
"""MathEdu-Cog 100: reproducible builder for the authored synthetic seed dataset.
All conversations are illustrative simulations, not actual student observations.
Run: python scripts/build_db.py
"""
from __future__ import annotations
import collections
import hashlib
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'content' / 'blueprint.json'
SEED = ROOT / 'content' / 'seed_items.txt'
SCHEMA_ORIG = ROOT / 'schema' / 'record.schema.json'
VOCAB_ORIG = ROOT / 'schema' / 'vocabularies.json'
VERSION = '1.0.0'
DATE = '2026-11-15'
PROV_ID = 'PROV-GPT6-20261115'

DOMAINS = {
  'NUM':('arithmetic','数与运算'), 'ALG':('algebra','代数与方程'),
  'FUN':('functions','函数与图像'), 'GEO':('geometry','几何与解析几何'),
  'TRI':('functions','三角函数与向量'), 'PRO':('probability_statistics','概率与组合计数'),
  'STA':('probability_statistics','统计与数据分析'),
  'CAL':('calculus','微积分与数学分析'),
  'LIN':('linear_algebra','线性代数'), 'LOG':('discrete_math','逻辑与证明')
}
STAGES = {'初中':'middle_school','高中':'high_school','大学低年级':'undergraduate'}
CLUSTERS = {
 'NUM': [[1],[2],[3],[4,5],[6,7],[8],[9],[10]],
 'ALG': [[1],[2,3],[4,10],[5],[6],[7],[8],[9],[11],[12]],
 'FUN': [[1],[2],[3],[4,5],[6],[7,11],[8],[9,12],[10]],
 'GEO': [[1],[2],[3,4],[5],[6],[7,8],[9],[10]],
 'TRI': [[1,2],[3],[4],[5],[6],[7],[8]],
 'PRO': [[1],[2,3],[4],[5],[6],[7,8],[9],[10]],
 'STA': [[1,2],[3],[4],[5],[6],[7],[8]],
 'CAL': [[1,7],[2,4],[3,9],[5],[6],[8],[10],[11],[12]],
 'LIN': [[1,10],[2],[3,4],[5],[6],[7],[8],[9]],
 'LOG': [[1,5],[2],[3],[4,6],[7],[8]]
}
# Cross-concept paths are intentionally conservative: relatedness is not mistaken for prerequisite.
PREREQ_PAIRS = [
 ('NUM-002','NUM-006'),('NUM-006','NUM-007'),('NUM-001','NUM-005'),
 ('ALG-001','ALG-003'),('ALG-002','ALG-003'),('ALG-004','ALG-010'),('ALG-005','ALG-006'),
 ('FUN-001','FUN-002'),('FUN-001','FUN-008'),('FUN-003','FUN-010'),('FUN-009','FUN-012'),
 ('GEO-002','GEO-004'),('GEO-003','GEO-010'),('GEO-007','GEO-008'),
 ('TRI-001','TRI-003'),('TRI-002','TRI-004'),('TRI-003','TRI-008'),
 ('PRO-001','PRO-005'),('PRO-004','PRO-005'),('PRO-005','PRO-008'),('PRO-007','PRO-008'),
 ('STA-001','STA-005'),('STA-002','STA-008'),('STA-006','STA-007'),
 ('ALG-004','FUN-003'),('FUN-003','CAL-001'),('CAL-001','CAL-002'),('CAL-002','CAL-003'),
 ('CAL-002','CAL-005'),('CAL-003','CAL-009'),('CAL-001','CAL-012'),
 ('LIN-001','LIN-010'),('LIN-003','LIN-006'),('LIN-005','LIN-009'),('LIN-008','LIN-009'),
 ('LOG-001','LOG-005'),('LOG-004','LOG-007'),('LOG-007','LOG-008')
]
PROOF_IDS = set('ALG-012 FUN-012 GEO-003 GEO-005 GEO-010 PRO-006 CAL-003 CAL-006 CAL-010 CAL-011 CAL-012 LIN-005 LIN-007 LIN-009 LOG-001 LOG-002 LOG-004 LOG-005 LOG-006 LOG-007 LOG-008'.split())
MODELING_IDS = set('NUM-003 NUM-006 NUM-007 NUM-009 GEO-002 GEO-008 PRO-001 PRO-004 PRO-007 PRO-008 PRO-010 STA-004 STA-005 STA-006 STA-007 STA-008 CAL-004'.split())
# Separately checked by scripts/math_checks.py; never claim all records mathematically proven.
SYM_CHECK_IDS = set('NUM-001 NUM-002 NUM-003 NUM-004 NUM-005 NUM-006 NUM-008 NUM-009 NUM-010 ALG-001 ALG-002 ALG-003 ALG-004 ALG-005 ALG-006 ALG-007 ALG-008 ALG-009 ALG-010 ALG-011 FUN-004 FUN-005 FUN-007 FUN-008 GEO-002 GEO-004 GEO-005 GEO-007 GEO-008 GEO-009 TRI-001 TRI-002 TRI-003 TRI-004 TRI-005 TRI-006 TRI-007 TRI-008 PRO-001 PRO-002 PRO-003 PRO-004 PRO-005 PRO-006 PRO-007 PRO-008 PRO-009 PRO-010 STA-001 STA-002 STA-003 STA-004 STA-005 CAL-001 CAL-002 CAL-003 CAL-004 CAL-005 CAL-006 CAL-007 CAL-008 CAL-009 CAL-010 CAL-011 CAL-012 LIN-001 LIN-002 LIN-003 LIN-004 LIN-005 LIN-006 LIN-007 LIN-008 LIN-009 LIN-010 LOG-001 LOG-002 LOG-003 LOG-004 LOG-005 LOG-006 LOG-007 LOG-008'.split())
# SYM_CHECK_IDS is a candidate list: actual status set only after successful machine run;
# build initially says unverified until the math-check report is loaded and explicitly lists IDs.

def dump(obj):return json.dumps(obj,ensure_ascii=False,separators=(',',':'))

def load_inputs():
 bp=json.loads(PLAN.read_text(encoding='utf-8'))['items']
 rows=[]
 for lineno,line in enumerate(SEED.read_text(encoding='utf-8').splitlines(),1):
  if not line.strip():continue
  parts=line.split('§')
  if len(parts)!=15:raise RuntimeError(f'line {lineno}: {len(parts)} fields, expected 15')
  rows.append(dict(zip(['id','stem','answer','step1','step2','error1','wrong1','error2','wrong2','probe1','probe1answer','probe2','probe2answer','hint','pseudo'],parts)))
 assert len(bp)==len(rows)==100
 for spec,item in zip(bp,rows):
  assert spec['slot_id']==item['id'],(spec['slot_id'],item['id'])
  item.update({k:spec[k] for k in ['domain_code','domain','education_stage','relative_difficulty','topic','assessment_target','item_family_id']})
 return rows

def concept_map(items):
 by_id={x['id']:x for x in items}
 mapping={};groups=[]
 for prefix,clusters in CLUSTERS.items():
  for j,idxs in enumerate(clusters,1):
   ci=f'C-{prefix}-{j:03d}'
   members=[f'{prefix}-{i:03d}' for i in idxs]
   for mid in members:
    assert mid in by_id
    if mid in mapping:raise AssertionError(mid)
    mapping[mid]=ci
   groups.append((ci,members))
 assert len(mapping)==100 and len(groups)==80,(len(mapping),len(groups))
 return mapping,groups

def error_type(s):
 if any(w in s for w in ('符号','负号','正负','不等号方向','负数')): return 'sign_error'
 if any(w in s for w in ('证明','归纳','量词','反例','必要','充分')): return 'proof_gap'
 if any(w in s for w in ('分母','定义域','条件','边界','未定式','除以可能为零')):return 'condition_ignored'
 if any(w in s for w in ('图像','坐标','位置','单位','可视','视觉')):return 'representation_translation'
 if any(w in s for w in ('推广','任何','任意','全局','所有','必须')):return 'incorrect_generalization'
 if any(w in s for w in ('同类项','约分','移项','展开号码','乘法','方程')):return 'algebraic_manipulation'
 return 'rule_misapplication'

def pseudo_subtype(s, q):
 # These are theory-driven risk classifications, not observed learner diagnoses.
 overrides={
  'surface_pattern':set('NUM-002 NUM-008 FUN-001 FUN-005 FUN-006 GEO-002 TRI-003 TRI-005 STA-001 STA-004 CAL-004 CAL-008 LIN-001 LOG-003'.split()),
  'false_generalization':set('NUM-003 NUM-007 ALG-006 ALG-012 FUN-002 FUN-009 GEO-005 GEO-010 PRO-001 PRO-004 PRO-006 PRO-009 STA-003 STA-006 STA-007 CAL-006 CAL-011 CAL-012 LIN-003 LIN-004 LIN-005 LIN-009 LOG-001 LOG-004 LOG-008'.split()),
  'fragile_transfer':set('ALG-004 ALG-008 ALG-010 ALG-011 FUN-003 FUN-008 FUN-011 TRI-006 TRI-008 PRO-007 CAL-001 CAL-009 LIN-010'.split()),
  'unjustified_fluency':set('ALG-012 GEO-010 STA-006 CAL-007 LIN-007 LOG-006 LOG-007'.split()),
  'hindsight_illusion':set('CAL-002 FUN-008 PRO-008 STA-008 CAL-010 LIN-009'.split()),
  'template_matching':set('NUM-004 NUM-006 NUM-010 ALG-001 ALG-003 ALG-009 FUN-007 FUN-010 GEO-003 GEO-004 GEO-007 GEO-008 GEO-009 TRI-004 TRI-007 PRO-002 PRO-003 PRO-005 PRO-010 STA-005 CAL-005 LIN-006 LOG-002 LOG-005'.split())
 }
 for code,ids in reversed(list(overrides.items())):
  if q in ids:return code
 if any(k in s for k in ('背','记住','记忆','牢记','背诵','记得','记口诀')):return 'rote_recall'
 if any(k in s for k in ('套','公式','机械','步骤','套路')):return 'template_matching'
 if any(k in s for k in ('推广','过度','任何','所有','普遍')):return 'false_generalization'
 if any(k in s for k in ('图像','外表','数字','视觉','符号')):return 'surface_pattern'
 if any(k in s for k in ('迁移','换题','遇到','变式')):return 'fragile_transfer'
 if any(k in s for k in ('看着','解析','讲解后','讲过')):return 'hindsight_illusion'
 if any(k in s for k in ('表达','解释得很','术语')):return 'unjustified_fluency'
 return 'answer_only'

def item_format(x):
 if x['id'] in PROOF_IDS:return 'proof'
 if x['id'] in MODELING_IDS and any(z in x['stem'] for z in ['商品','食堂','骰','硬币','概率','抽','学校','距离','元','米','秒','样本','班级','绳']):return 'modeling'
 if any(z in x['stem'] for z in ['判断','是否','能否','解释','说明','比较','评判','为什么']):return 'explanation'
 return 'free_response'

def cognitive_processes(x):
 p=['conceptual','reasoning']
 if x['id'] in PROOF_IDS:p.append('proof')
 if x['id'] in MODELING_IDS:p.append('formulate')
 if x['id'].startswith(('ALG','NUM','CAL','LIN','TRI')):p.append('procedural')
 if '图' in x['stem'] or '坐标' in x['stem']:p.append('representation')
 return list(dict.fromkeys(p))

def split_map(items):
 # Deterministic question-family split, not a real external generalization benchmark.
 ordered=sorted(items,key=lambda x:hashlib.sha256(('mathedu100-seed-v1:'+x['item_family_id']).encode()).hexdigest())
 return {x['id']:('train' if i<70 else 'validation' if i<85 else 'synthetic_test') for i,x in enumerate(ordered)}

def make_records(items):
 cid_map,groups=concept_map(items)
 byid={i['id']:i for i in items}
 split=split_map(items)
 out=[]
 def add(t,**x):
  obj={'record_type':t,'schema_version':VERSION,'id':x.pop('id')}
  if t!='provenance':obj['provenance_id']=PROV_ID
  obj.update(x)
  out.append(obj)
  return obj
 add('provenance',id=PROV_ID, origin_type='llm_synthetic',
     source_description='GPT-6 / ChatGPT 在本次会话中创作的原创数学题、候选误区、示例学生回答与脚本化教学对话；未调用早期小模型，未使用真实学生数据。',
     source_locator='content/seed_items.txt; scripts/build_db.py',
     creator_role='llm', generator_model='GPT-6 (ChatGPT; authored + deterministic templates)',
     generator_prompt_version='mathedu-cog100-authoring-v1',
     license='No license grant asserted; user-generated project material; check applicable terms before redistribution.',
     consent_status='not_applicable',privacy_review='not_applicable',
     validation_level='theoretical_candidate',review_status='draft',created_date=DATE,
     permitted_uses=['training','evaluation','research'],
     version_note='全部学生数据为演示性的 AI 角色模拟；没有外部真人或教师认可。')
 
 # Concept graph: nodes are reusable clusters; define relations only with explicit curated prerequisites.
 prereq=collections.defaultdict(set)
 for pre,nxt in PREREQ_PAIRS:
  a,b=cid_map[pre],cid_map[nxt]
  if a!=b:prereq[b].add(a)
 for c,members in groups:
  sample=[byid[m] for m in members]
  topic='；'.join(dict.fromkeys(z['topic'] for z in sample))
  domain=DOMAINS[sample[0]['domain_code']][0]
  # Stage = earliest stage within cluster; cross_level for mixed stages.
  stages={STAGES[z['education_stage']] for z in sample}
  stage=next(iter(stages)) if len(stages)==1 else 'cross_level'
  add('concept',id=c,label=topic,
      definition=f'知识单元「{topic}」。核心理解要求：{sample[0]["assessment_target"]}。一个可操作的判断依据是：{sample[0]["step1"]}',
      domain=domain,education_stage=stage,prerequisite_ids=sorted(prereq[c]),
      relations=[{'concept_id':v,'relation':'prerequisite_of'} for v in sorted(set(k for k,v in prereq.items() if c in v))],
      representations=['symbolic','verbal'],examples=[sample[0]['stem']],
      nonexamples=[sample[0]['wrong1']], boundary_conditions=[sample[0]['error1']],
      assessment_targets=['conceptual','reasoning'])
 
 for n,x in enumerate(items,1):
  q=x['id']; domain=DOMAINS[x['domain_code']][0]; st=STAGES[x['education_stage']]
  cid=cid_map[q]; ids=dict(sol='S-'+q,err1='E-'+q+'-1',err2='E-'+q+'-2',
       hyp1='H-'+q+'-1',hyp2='H-'+q+'-2',pu='H-'+q+'-PU',unknown='H-'+q+'-UNK',
       probe1='P-'+q+'-1',probe2='P-'+q+'-2',inter='T-'+q,
       obs_correct='O-'+q+'-C',obs_err1='O-'+q+'-E1',obs_err2='O-'+q+'-E2',obs_pu='O-'+q+'-PU',
       inference='I-'+q+'-E',inference_pu='I-'+q+'-PU',session='SE-'+q,outcome='LO-'+q,pref='PR-'+q)
  add('item',id=q,stem=x['stem'],domain=domain,education_stage=st,
      item_format=item_format(x),correct_answer=x['answer'],language='zh-CN',
      solution_ids=[ids['sol']],
      rubric=[{'criterion':'识别概念和适用条件','weight':0.30},{'criterion':'关键步骤正确','weight':0.40},{'criterion':'结论及解释完整','weight':0.30}],
      knowledge_requirements=[{'concept_id':cid,'role':'essential','evidence':x['assessment_target']}],
      cognitive_processes=cognitive_processes(x),item_family_id=x['item_family_id'],
      difficulty={'value':int(x['relative_difficulty'][1]),'basis':'model_estimate','sample_size':0,
                  'notes':'按学段内的相对难度分级；未经过真实作答 IRT 校准'},
      estimated_duration_sec=90+int(x['relative_difficulty'][1])*75,
      representation_modes=['text','latex'],
      licensing_notes='原创 AI 合成题；重分发前请核查适用条款',
      exposure_policy='ordinary_training' if split[q]=='train' else 'reserved_test')
  add('solution',id=ids['sol'],item_id=q,
      methods=[{'method_id':'method-1','name':'标准两段推导',
          'steps':[{'step_id':'st-1','explanation':x['step1'],'justification':'运用题目对应的定义、定理或条件并保持合法推理。',
                    'concept_ids':[cid],'scoring_key':'识别条件及核心变形'},
                   {'step_id':'st-2','explanation':x['step2'],'justification':'由上一步结果推出结论，并检查关键限制。',
                    'concept_ids':[cid],'scoring_key':'完成推理与解释'}],
          'final_answer':x['answer']}],
      rubric_criteria=[{'criterion_id':'definition','description':'正确识别条件','points':3},
                       {'criterion_id':'reasoning','description':'推理和计算有依据','points':4},
                       {'criterion_id':'answer','description':'最终结论及解释完整','points':3}],
      mathematical_validity_check='unverified',
      common_invalid_steps=[x['error1'],x['error2']])
  for j in (1,2):
   e=ids[f'err{j}'];h=ids[f'hyp{j}']; sig=x[f'error{j}']; wrong=x[f'wrong{j}']
   add('error_pattern',id=e,item_ids=[q],concept_ids=[cid],
       observed_signature=sig,surface_category=error_type(sig),
       wrong_answer_examples=[wrong],first_error_location=sig,
       candidate_hypothesis_ids=[h,ids['unknown']],
       notes_on_ambiguity='此处为人为设计的错误表现；不能仅凭此行为认定真实学生具有某个内在认知机制。',
       evidence_level='theoretical_candidate')
   add('cognitive_hypothesis',id=h,label=sig,kind='concept_misconception',
       concept_ids=[cid],description=f'候选机制：{sig}。其可能在本题中导致：{wrong}',
       positive_evidence=[f'重复出现的错误推理：{wrong}'],
       counter_evidence=[f'能独立说明：{x["step1"]}'],
       alternative_explanations=['抄写、符号输入或计算上的偶发失误','对题干有不同理解','缺少更早的前置知识'],
       associated_error_ids=[e],diagnostic_probe_ids=[ids['probe1'] if j==1 else ids['probe2']],
       evidence_level='theoretical_candidate',
       do_not_diagnose_from=['单一错误答案','模型预设的学生角色标签'])
  add('cognitive_hypothesis',id=ids['pu'],label=x['pseudo'],
      kind='pseudo_understanding',pseudo_understanding_subtype=pseudo_subtype(x['pseudo'],q),concept_ids=[cid],
      description=f'答对或复述结论仍不能保证理解：{x["pseudo"]}',
      positive_evidence=['结果正确，但无法说明关键定义或适用条件的独立回答'],
      counter_evidence=['无需提示就能处理具有关键差异的近迁移题并说明原理'],
      alternative_explanations=['学生只是回答简短，并不意味着缺乏理解','表达能力、时间限制可能影响解释完整性'],
      diagnostic_probe_ids=[ids['probe1'],ids['probe2']],
      do_not_diagnose_from=['只给正确结论一次','没有明确自评时推测学生自信程度'],
      evidence_level='theoretical_candidate')
  add('cognitive_hypothesis',id=ids['unknown'],label='仅凭当前回答证据不足',
      kind='insufficient_evidence',concept_ids=[cid],
      description='单次作答无法排除正确理解、偶发失误和概念误区等竞争性解释。',
      positive_evidence=['仅有一次答案或缺少推理'],counter_evidence=['经独立多题核查呈现稳定模式'],
      alternative_explanations=['稳定误区','暂时失误','回答不充分'],
      diagnostic_probe_ids=[ids['probe1'],ids['probe2']],
      evidence_level='theoretical_candidate',do_not_diagnose_from=['初次作答'])
  for j in (1,2):
   add('diagnostic_probe',id=ids[f'probe{j}'],stem=x[f'probe{j}'],probe_type='near_transfer' if j==1 else 'explain_reason',
       base_item_id=q,concept_ids=[cid],
       hypotheses_to_distinguish=[ids[f'hyp{j}'],ids['pu'],ids['unknown']],
       predicted_responses=[
         {'hypothesis_id':ids[f'hyp{j}'],'expected_response_pattern':f'仍运用错误规则：{x[f"error{j}"]}',
          'evidence_direction':'supports','qualitative_strength':'moderate'},
         {'hypothesis_id':ids['pu'],'expected_response_pattern':'能够复述结论，但对变式或解释仍缺少独立理由。',
          'evidence_direction':'ambiguous','qualitative_strength':'weak'},
         {'hypothesis_id':ids['unknown'],'expected_response_pattern':f'能给出并解释：{x[f"probe{j}answer"]}',
          'evidence_direction':'weakens','qualitative_strength':'moderate'}],
       correct_answer=x[f'probe{j}answer'],
       scoring_criteria=['回答数学结论正确','解释使用的定义或关键条件','能指出与原题的关系或差别'],
       answer_leakage_risk='low',information_value='medium',information_value_basis='model_estimate',
       next_step_if_success='换用未出现过的变式继续验证，不直接判定已完全掌握。',
       next_step_if_failure='追问具体推理依据，必要时提供最小提示。',
       notes_on_non_identifiability='一次变式仍不足以区分全部认知状态；预测回答未经过真实学生实测。',
       evidence_level='theoretical_candidate')
  add('teaching_intervention',id=ids['inter'],target_hypothesis_ids=[ids['hyp1'],ids['hyp2']],
      action='minimal_hint',objective='remediate',learner_facing_message=x['hint'],
      teacher_rationale=f'当前存在「{x["error1"]}」等解释，不应立即泄露最终答案；通过过程提示引导学生恢复关键推理。',
      scaffolding_level='minimal',reveals_solution=False,
      risks=['提示可能被误解为答案线索','模拟器的纠错反应不代表真实教学效果'],
      expected_observable_signal=f'学生能独立提到核心依据：{x["assessment_target"]}',
      followup_probe_id=ids['probe2'],validation_level='theoretical_candidate')

  # Standalone synthetic responses. All are purposely scripted, not empirical model samples.
  obs_forms={
    'correct':(ids['obs_correct'],f'我先看关键条件：{x["step1"]} 接着，{x["step2"]} 因而 {x["answer"]}',
                'correct',[],'独立、完整的示范型回答'),
    'err1':(ids['obs_err1'],f'我觉得：{x["wrong1"]}',
            'incorrect',[ids['err1']],'按照第一种预设错误规则的角色模拟'),
    'err2':(ids['obs_err2'],f'我认为：{x["wrong2"]}',
            'incorrect',[ids['err2']],'按照第二种预设错误规则的角色模拟'),
    'pseudo':(ids['obs_pu'],f'我记得结论是：{x["answer"]}。但为什么这样，我暂时解释不清。',
             'partial',[],'结论正确但缺乏解释的角色模拟；并不证明真有伪理解')
  }
  for name,(oid,resp,correctness,errids,notes) in obs_forms.items():
   add('student_observation',id=oid,
      student_pseudonym=f'SIM-{q}-{name.upper()}',
      **({'session_id':ids['session']} if name=='err1' else {}),
      target_id=q,raw_response=resp,correctness=correctness,
      observed_error_ids=errids,observed_features=[notes],
      evidence_quotes=[resp],assistance='none',source_type='llm_synthetic',modality='text',
      confidence_collection_method='not_collected',
      evidence_notes='离线脚本化角色模拟，非真实学生，未实际调用弱模型。')
  add('cognitive_inference',id=ids['inference'],student_pseudonym=f'SIM-{q}-ERR1',
      observation_ids=[ids['obs_err1']],
      hypotheses=[{'hypothesis_id':ids['hyp1'],'support':'plausible',
                   'supporting_observation_ids':[ids['obs_err1']],
                   'contradicting_observation_ids':[],
                   'confidence_score':0.6,'confidence_semantics':'uncalibrated_model_score',
                   'rationale':f'该模拟回答符合预设错误特征「{x["error1"]}」，但不能据此推断真人心理。'},
                  {'hypothesis_id':ids['unknown'],'support':'plausible',
                   'supporting_observation_ids':[ids['obs_err1']],
                   'contradicting_observation_ids':[],
                   'confidence_score':0.4,'confidence_semantics':'uncalibrated_model_score',
                   'rationale':'单次回答无法排除偶然失误或题意误解。'}],
      concept_state_estimates=[{'concept_id':cid,'axis':'conceptual','state':'unknown',
                                'evidence_observation_ids':[ids['obs_err1']]}],
      overall_certainty='low',uncertainty_reason='没有独立变式与长期记录。',
      recommended_probe_id=ids['probe1'],decision_policy='先诊断再提示，不直接判定认知障碍。',
      known_limits=['预设认知角色不等于真实认知状态','未经过真实学生分布校准'],annotator_role='model_candidate')
  add('cognitive_inference',id=ids['inference_pu'],student_pseudonym=f'SIM-{q}-PSEUDO',
      observation_ids=[ids['obs_pu']],
      hypotheses=[{'hypothesis_id':ids['pu'],'support':'plausible',
                   'supporting_observation_ids':[ids['obs_pu']],
                   'contradicting_observation_ids':[],
                   'confidence_score':0.45,'confidence_semantics':'uncalibrated_model_score',
                   'rationale':'答案正确且解释不足只能触发进一步验证。'},
                  {'hypothesis_id':ids['unknown'],'support':'plausible',
                   'supporting_observation_ids':[ids['obs_pu']],
                   'contradicting_observation_ids':[],
                   'confidence_score':0.55,'confidence_semantics':'uncalibrated_model_score',
                   'rationale':'简短回答可能只是表达方式，而非理解不足。'}],
      overall_certainty='insufficient',uncertainty_reason='缺乏独立推理与迁移证据，不能贴伪理解确诊标签。',
      recommended_probe_id=ids['probe2'],decision_policy='要求解释机制或给出关键变式。',
      known_limits=['没有真实信心自评','该输入为合成角色模拟'],annotator_role='model_candidate')
  # 8-turn dialogue with variation in simulated outcome, without asserting mastery.
  branch=n%4
  if branch==0:
   last=f'我尝试独立回答变式：{x["probe2answer"]}。但我还想再做一题确认。'
  elif branch==1:
   last='我大致知道方向了，但现在还不能完全独立说明为什么。'
  elif branch==2:
   last=f'我还是有点混乱，可能会继续犯错：{x["error2"]}。'
  else:
   last='我不确定。刚才是看着提示推的，换题时还需要重新思考。'
  turns=[
   ('ai_tutor',x['stem'],None,None,None),
   ('student',obs_forms['err1'][1],None,ids['obs_err1'],None),
   ('ai_tutor',x['probe1'],ids['probe1'],None,None),
   ('student',f'我原先是这样理解的：{x["wrong1"]}。但这道变式题我拿不准。',None,None,None),
   ('ai_tutor',x['hint'],None,None,ids['inter']),
   ('student',f'我试着重新推：{x["step1"]}。接下来是不是需要检查适用条件？',None,None,None),
   ('ai_tutor',x['probe2'],ids['probe2'],None,None),
   ('student',last,None,None,None),
  ]
  add('teaching_session',id=ids['session'],student_pseudonym=f'SIM-{q}-ERR1',source_type='llm_synthetic',
      item_ids=[q],learning_goals=[x['assessment_target']],
      session_constraints=['全部对话为剧本式合成；对后续学生反应不得做因果归因'],
      turns=[dict({'turn_id':f'turn-{i+1}','speaker':speaker,'message':msg,'item_id':q,'visible_to_student':True},
                **({'probe_id':p} if p else {}),
                **({'observation_id':o} if o else {}),
                **({'intervention_id':it} if it else {}))
             for i,(speaker,msg,p,o,it) in enumerate(turns)],
      observation_ids=[ids['obs_err1']],inference_ids=[ids['inference']],
      intervention_ids=[ids['inter']],outcome_ids=[ids['outcome']],
      completion_reason='session_end',
      discussion_notes='最后一轮仅为模拟的言语反应；没有独立真实后测，不能认定教学有效。')
  add('learning_outcome',id=ids['outcome'],student_pseudonym=f'SIM-{q}-ERR1',
      session_id=ids['session'],target_item_id=q,concept_ids=[cid],
      assessment_timing='during_lesson',independent_assessment=False,
      score={'correctness':'unscorable','explanation_quality':'not_assessed','transfer_level':'not_assessed'},
      support_received_during_assessment='unknown',
      observed_evidence=['只有脚本化会话中的学生言语，没有独立作答测量。'],
      causal_attribution='not_assessed',
      limitations=['全合成，不存在真人学习效果','后测未进行','不能用于训练因果教学成功的标签'])
  # Clear normative teaching preference (NOT experimentally measured effectiveness).
  if n%3==0:
   good=('minimal_hint',x['hint'],'以最少线索引导独立推理，保留学生主体性。')
  elif n%3==1:
   good=('diagnostic_question',x['probe1'],'用变式检验潜在规则，避免从一次错答直接确诊。')
  else:
   good=('diagnostic_question',x['probe2'],'让学生阐明条件或举反例，获取区分性信息。')
  if n%2:
   bad=('explicit_answer',f'答案是：{x["answer"]}。你直接记住这个结论就好了。','过早给出最终答案，缺少诊断与独立思考。')
  else:
   bad=('concept_explanation',f'你肯定就是「{x["error1"]}」，这点不用再问，直接背答案。','单次作答过度确诊，忽略替代解释。')
  a=good if n%2 else bad
  b=bad if n%2 else good
  choice='a' if n%2 else 'b'
  a_score=4 if choice=='a' else 1
  b_score=4 if choice=='b' else 1
  add('teaching_preference',id=ids['pref'],context_observation_ids=[ids['obs_err1']],
      context_inference_id=ids['inference'],
      candidate_a={'candidate_id':'a','action':a[0],'message':a[1],'teaching_rationale':a[2]},
      candidate_b={'candidate_id':'b','action':b[0],'message':b[1],'teaching_rationale':b[2]},
      choice=choice,
      rating_rubric=[{'dimension':dim,'candidate_scores':{'a':a_score,'b':b_score},
                      'justification':f'比较基于规范性教学原则：{good[2]}对照{bad[2]}'}
                     for dim in ['diagnostic_information','uncertainty_calibration','student_agency','non_leakage']],
      decision_explanation='在证据不足时，优先采用不给出最终答案的具体诊断/最小提示，而不是直接泄题或武断贴认知标签。此为规范性候选偏好而非实测教学效果。',
      assessor_role='model_candidate',evidence_level='theoretical_candidate')
 return out,split,cid_map

DDL='''
PRAGMA foreign_keys=ON;
CREATE TABLE provenance(id TEXT PRIMARY KEY, origin_type TEXT NOT NULL, generator_model TEXT, validation_level TEXT NOT NULL, doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE concepts(id TEXT PRIMARY KEY, label TEXT NOT NULL, domain TEXT NOT NULL, doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE concept_edges(from_concept TEXT NOT NULL REFERENCES concepts(id),to_concept TEXT NOT NULL REFERENCES concepts(id),relation TEXT NOT NULL, PRIMARY KEY(from_concept,to_concept,relation));
CREATE TABLE questions(id TEXT PRIMARY KEY, family_id TEXT NOT NULL UNIQUE, domain_code TEXT NOT NULL, domain TEXT NOT NULL, stage TEXT NOT NULL, difficulty INTEGER NOT NULL CHECK(difficulty BETWEEN 1 AND 5), split TEXT NOT NULL CHECK(split IN ('train','validation','synthetic_test')), stem TEXT NOT NULL, correct_answer TEXT NOT NULL, provenance_id TEXT NOT NULL REFERENCES provenance(id), doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE INDEX idx_questions_domain ON questions(domain_code,difficulty);
CREATE INDEX idx_questions_split ON questions(split);
CREATE TABLE item_concepts(item_id TEXT NOT NULL REFERENCES questions(id),concept_id TEXT NOT NULL REFERENCES concepts(id),role TEXT NOT NULL,PRIMARY KEY(item_id,concept_id));
CREATE TABLE solutions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),status TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE error_patterns(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),category TEXT NOT NULL,signature TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE cognitive_hypotheses(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),kind TEXT NOT NULL,label TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE diagnostic_probes(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),stem TEXT NOT NULL,correct_answer TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE student_observations(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),session_id TEXT, correctness TEXT NOT NULL,source_type TEXT NOT NULL,raw_response TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE cognitive_inferences(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),student_pseudonym TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_interventions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),action TEXT NOT NULL,message TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_sessions(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),source_type TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE learning_outcomes(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),independent_assessment INTEGER NOT NULL,causal_attribution TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE teaching_preferences(id TEXT PRIMARY KEY,item_id TEXT NOT NULL REFERENCES questions(id),choice TEXT NOT NULL,doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE TABLE all_records(id TEXT PRIMARY KEY,record_type TEXT NOT NULL,provenance_id TEXT REFERENCES provenance(id),doc TEXT NOT NULL CHECK(json_valid(doc)));
CREATE INDEX idx_allrecords_type ON all_records(record_type);
CREATE VIEW question_summary AS SELECT q.id,q.domain_code,q.stage,q.difficulty,q.split,q.stem,q.correct_answer,
 (SELECT COUNT(*) FROM error_patterns e WHERE e.item_id=q.id) AS n_errors,
 (SELECT COUNT(*) FROM diagnostic_probes p WHERE p.item_id=q.id) AS n_probes,
 (SELECT COUNT(*) FROM student_observations o WHERE o.item_id=q.id) AS n_observations,
 (SELECT COUNT(*) FROM teaching_sessions s WHERE s.item_id=q.id) AS n_sessions
 FROM questions q;
'''

def table_for(t):
 return {'solution':'solutions','error_pattern':'error_patterns','cognitive_hypothesis':'cognitive_hypotheses',
 'diagnostic_probe':'diagnostic_probes','student_observation':'student_observations',
 'cognitive_inference':'cognitive_inferences','teaching_intervention':'teaching_interventions',
 'teaching_session':'teaching_sessions','learning_outcome':'learning_outcomes','teaching_preference':'teaching_preferences'}[t]

def write_db(records,items,splits,cids):
 db=ROOT/'data'/'mathedu_cog_100.sqlite'
 if db.exists():db.unlink()
 con=sqlite3.connect(db)
 con.executescript(DDL)
 order=['provenance','concept','item','solution','error_pattern','cognitive_hypothesis','diagnostic_probe','student_observation',
        'cognitive_inference','teaching_intervention','teaching_session','learning_outcome','teaching_preference']
 byid={x['id']:x for x in records}
 with con:
  for t in order:
   for r in (z for z in records if z['record_type']==t):
    id=r['id'];doc=dump(r)
    if t=='provenance':con.execute('INSERT INTO provenance VALUES(?,?,?,?,?)',(id,r['origin_type'],r.get('generator_model'),r['validation_level'],doc))
    elif t=='concept':con.execute('INSERT INTO concepts VALUES(?,?,?,?)',(id,r['label'],r['domain'],doc))
    elif t=='item':
     ix=id
     con.execute('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?,?,?,?)',
         (id,r['item_family_id'],id.split('-')[0],r['domain'],r['education_stage'],int(r['difficulty']['value']),splits[id],r['stem'],r['correct_answer'],r['provenance_id'],doc))
     con.execute('INSERT INTO item_concepts VALUES(?,?,?)',(id,cids[id],'essential'))
    else:
     ix = (r.get('item_id') or r.get('base_item_id') or r.get('target_item_id')
           or r.get('target_id') or r.get('item_ids',[None])[0] or id.split('-',maxsplit=1)[1])
     # ID suffix for I-/SE-/LO-/PR-/T-/H-/E-/O- includes extra segments
     if t not in ('solution','diagnostic_probe','student_observation','error_pattern','learning_outcome'):
      for prefix in ('I-','SE-','T-','PR-','H-'):
       if id.startswith(prefix):
        tokens=id[len(prefix):].split('-')
        ix='-'.join(tokens[:2])
        break
     table=table_for(t)
     if t=='solution':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',(id,ix,r['mathematical_validity_check'],doc))
     elif t=='error_pattern':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(id,ix,r['surface_category'],r['observed_signature'],doc))
     elif t=='cognitive_hypothesis':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(id,ix,r['kind'],r['label'],doc))
     elif t=='diagnostic_probe':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(id,ix,r['stem'],r['correct_answer'],doc))
     elif t=='student_observation':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?,?,?)',(id,ix,r.get('session_id'),r['correctness'],r['source_type'],r['raw_response'],doc))
     elif t=='cognitive_inference':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',(id,ix,r['student_pseudonym'],doc))
     elif t=='teaching_intervention':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(id,ix,r['action'],r['learner_facing_message'],doc))
     elif t=='teaching_session':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',(id,ix,r['source_type'],doc))
     elif t=='learning_outcome':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?,?)',(id,ix,int(r['independent_assessment']),r['causal_attribution'],doc))
     elif t=='teaching_preference':con.execute(f'INSERT INTO {table} VALUES(?,?,?,?)',(id,ix,r['choice'],doc))
    con.execute('INSERT INTO all_records VALUES(?,?,?,?)',(id,t,r.get('provenance_id'),doc))
  for r in (z for z in records if z['record_type']=='concept'):
   for pred in r.get('prerequisite_ids',[]):
    con.execute('INSERT OR IGNORE INTO concept_edges VALUES(?,?,?)',(pred,r['id'],'prerequisite_of'))
  bad=con.execute('PRAGMA foreign_key_check').fetchall()
  if bad:raise RuntimeError(f'Foreign-key failures: {bad[:15]}')
 con.close()
 (ROOT/'schema'/'schema.sql').write_text(DDL,encoding='utf-8')
 return db

def export_training(records,splits):
 byid={z['id']:z for z in records}
 train=[];diag=[];labels=[];preferences=[];smoke=[]
 def msg(role,content):return {'role':role,'content':content}
 for q in [z for z in records if z['record_type']=='item']:
  qid=q['id'];split=splits[qid];family=q['item_family_id']
  err=[byid[f'E-{qid}-{j}'] for j in (1,2)]
  hp=[byid[f'H-{qid}-{j}'] for j in (1,2)]
  probes=[byid[f'P-{qid}-{j}'] for j in (1,2)]
  s=byid[f'SE-{qid}'];pref=byid[f'PR-{qid}']
  # Cognitive analysis: one sample for each synthetic error, and one uncertain answer-only case.
  for j in (1,2,3):
   oid=f'O-{qid}-{("E"+str(j)) if j<3 else "PU"}'
   obs=byid[oid];seen=obs['raw_response']
   if j<3:
    target={'observations':[seen],'hypotheses':[{'candidate':hp[j-1]['description'],'support':'plausible'},
      {'candidate':'偶发失误或题意误解','support':'possible'}],
      'certainty':'low','next_probe':probes[j-1]['stem'],
      'reason':'只有一次错误表现，无法确诊潜在认知原因。'}
   else:
    target={'observations':[seen],'hypotheses':[{'candidate':'可能存在答案记忆或解释证据不足','support':'plausible'},
      {'candidate':'理解正确但回答过于简短','support':'possible'}],
      'certainty':'insufficient','next_probe':probes[1]['stem'],
      'reason':'答对结论不等于已经证明真正理解；不能推定未经询问的自信程度。'}
   diag.append({'id':f'DIAG-{qid}-{j}','item_id':qid,'family_id':family,'split':split,
     'synthetic':True,'messages':[
      msg('system','你是谨慎的数学认知诊断 AI。只根据当前可见回答提出候选假设，不做心理确诊；给出下一道诊断问题。'),
      msg('user',f'题目：{q["stem"]}\n学生当前回答：{seen}'),
      msg('assistant',dump(target))]})
  # Label generation has math answer in input intentionally; no student future in input.
  labels.append({'id':f'LABEL-{qid}','item_id':qid,'family_id':family,'split':split,'synthetic':True,
    'messages':[msg('system','为数学题生成候选认知标注；务必区分可观察错误与潜在假设，不虚构真实学生频率。'),
       msg('user',f'题目：{q["stem"]}\n正确答案：{q["correct_answer"]}'),
       msg('assistant',dump({'candidate_errors':[{'signature':e['observed_signature'],'wrong_example':e['wrong_answer_examples'][0]} for e in err],
                  'pseudo_understanding_risk':byid[f'H-{qid}-PU']['description'],
                  'diagnostic_probes':[{'question':p['stem'],'answer':p['correct_answer']} for p in probes],
                  'evidence_level':'theoretical_candidate'}))]})
  # Strict teacher prefix: tutor target is always next assistant turn, and no future turn appears in prompt.
  turns=s['turns']
  for idx,turn in enumerate(turns):
   if turn['speaker']!='ai_tutor' or idx==0:continue
   history=[msg('assistant' if t['speaker']=='ai_tutor' else 'user',t['message']) for t in turns[:idx]]
   assert history[-1]['role']=='user'
   # No hidden answer, probe key, annotation or future student reply in the teacher context.
   train.append({'id':f'TUTOR-{qid}-{idx}','item_id':qid,'family_id':family,'split':split,'synthetic':True,
    'turn_index':idx,'messages':[msg('system','你是以学生思考为中心的数学教师。根据已发生的对话选择下一步，不武断诊断，不提前泄露完整答案。'),
            *history,msg('assistant',turn['message'])]})
  chosen=pref['candidate_a'] if pref['choice']=='a' else pref['candidate_b']
  rejected=pref['candidate_b'] if pref['choice']=='a' else pref['candidate_a']
  preferences.append({'id':f'PREF-{qid}','item_id':qid,'family_id':family,'split':split,'synthetic':True,
    'prompt':[msg('system','比较同一数学教学情境下的下一步教学行动。'),
              msg('user',f'题目：{q["stem"]}\n学生回答：{byid[f"O-{qid}-E1"]["raw_response"]}')],
    'chosen':msg('assistant',chosen['message']),'rejected':msg('assistant',rejected['message']),
    'rationale':pref['decision_explanation'],'evidence_level':'theoretical_candidate'})
 for name,rows in [('tutoring_sft',train),('cognitive_diagnosis_sft',diag),('label_generation_sft',labels),('teaching_preferences',preferences)]:
  (ROOT/'exports'/f'{name}.jsonl').write_text(''.join(dump(row)+'\n' for row in rows),encoding='utf-8')
  # Model-training files must use the train subdirectory only; reserve other groups.
  for partition in ('train','validation','synthetic_test'):
   folder=ROOT/'exports'/partition
   folder.mkdir(exist_ok=True)
   (folder/f'{name}.jsonl').write_text(''.join(dump(row)+'\n' for row in rows if row['split']==partition),encoding='utf-8')
 smoke=[x for x in diag+train+labels if x['split']=='synthetic_test']
 (ROOT/'exports'/'synthetic_smoke_test.jsonl').write_text(''.join(dump(row)+'\n' for row in smoke),encoding='utf-8')
 return dict(tutoring_sft=len(train),cognitive_diagnosis_sft=len(diag),label_generation_sft=len(labels),teaching_preferences=len(preferences),synthetic_smoke_test=len(smoke))

def main():
 import shutil
 from jsonschema import Draft202012Validator
 items=load_inputs()
 records,splits,cids=make_records(items)
 schema=json.loads(SCHEMA_ORIG.read_text(encoding='utf-8'))
 validator=Draft202012Validator(schema)
 for r in records:
  errors=list(validator.iter_errors(r))
  if errors:
   raise ValueError(f'{r["id"]} invalid: '+str(errors[0])[:1500])
 (ROOT/'data'/'canonical_records.jsonl').write_text(''.join(dump(x)+'\n' for x in records),encoding='utf-8')
 catalog=[{'id':x['id'],'domain':x['domain'],'education_stage':x['education_stage'],
          'difficulty':x['relative_difficulty'],'topic':x['topic'],'concept_id':cids[x['id']],
          'stem':x['stem'],'correct_answer':x['answer'],'split':splits[x['id']]}
          for x in items]
 (ROOT/'data'/'question_catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
 db=write_db(records,items,splits,cids)
 exports=export_training(records,splits)
 counts=dict(collections.Counter(r['record_type'] for r in records))
 domain_counts=dict(collections.Counter(x['domain_code'] for x in items))
 diff_counts=dict(sorted(collections.Counter(x['relative_difficulty'] for x in items).items()))
 summary={'dataset':'MathEdu-Cog 100','version':VERSION,'date':DATE,'status':'synthetic_seed_for_research',
          'core_items':100,'domain_counts':domain_counts,'difficulty_counts':diff_counts,
          'record_counts':counts,'total_records':len(records),'training_exports':exports,
          'question_split_counts':dict(collections.Counter(splits.values())),
          'item_formats':dict(collections.Counter(item_format(x) for x in items)),
          'provenance':{'actual_weak_model_calls':0,'real_student_observations':0,'expert_approved':0,
                        'generator_model':'GPT-6','simulated_dialogues_are_scripted':True},
          'source_verification':'jsonschema validated; refer to report for actual math spot checks',
          'known_limitations':['所有学生行为与学习效果都未经过真人数据校准',
                               '模型设计的诊断价值不等于实测区分度',
                               '偏好是规范性构造，不是教学干预的因果证据',
                               '同一模型生成/自校验不是独立专家审核']}
 (ROOT/'reports'/'coverage_report.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
 print('DB:',db,'\nCOUNTS:',json.dumps(counts,ensure_ascii=False),'\nEXPORTS:',exports)

if __name__=='__main__':main()
