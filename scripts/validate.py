#!/usr/bin/env python3
"""Full structural, referential and split-leakage integrity validation.
Does not establish construct validity, student realism, or expert mathematical approval.
"""
import collections, json, sqlite3, hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
ROOT=Path(__file__).resolve().parents[1]
records=[json.loads(s) for s in (ROOT/'data'/'canonical_records.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()]
by_id={r['id']:r for r in records}
issues=[]
passed_checks=[]

def check(cond,description):
 if cond:passed_checks.append(description)
 else:issues.append(description)

def ref(r,ref_id,expected_type=None):
 check(ref_id in by_id,f'{r["id"]}: missing reference {ref_id}')
 if ref_id in by_id and expected_type:
  check(by_id[ref_id]['record_type']==expected_type,f'{r["id"]}: {ref_id} not {expected_type}')

check(len(by_id)==len(records),'unique_record_ids')
schema=json.loads((ROOT/'schema'/'record.schema.json').read_text(encoding='utf-8'))
validator=Draft202012Validator(schema)
for r in records:
 err=list(validator.iter_errors(r))
 if err:issues.append(f'JSON schema invalid {r["id"]}: {err[0].message[:180]}')
 if r['record_type']!='provenance':ref(r,r['provenance_id'],'provenance')
 if r['record_type']=='concept':
  for c in r.get('prerequisite_ids',[]):ref(r,c,'concept')
  for rel in r.get('relations',[]):ref(r,rel['concept_id'],'concept')
 if r['record_type']=='item':
  for s in r.get('solution_ids',[]):ref(r,s,'solution')
  for x in r['knowledge_requirements']:ref(r,x['concept_id'],'concept')
 if r['record_type']=='solution':ref(r,r['item_id'],'item')
 if r['record_type']=='error_pattern':
  for i in r.get('item_ids',[]):ref(r,i,'item')
  for c in r.get('concept_ids',[]):ref(r,c,'concept')
  for h in r.get('candidate_hypothesis_ids',[]):ref(r,h,'cognitive_hypothesis')
 if r['record_type']=='cognitive_hypothesis':
  for c in r['concept_ids']:ref(r,c,'concept')
  for e in r.get('associated_error_ids',[]):ref(r,e,'error_pattern')
  for p in r.get('diagnostic_probe_ids',[]):ref(r,p,'diagnostic_probe')
 if r['record_type']=='diagnostic_probe':
  ref(r,r['base_item_id'],'item')
  for c in r['concept_ids']:ref(r,c,'concept')
  for h in r['hypotheses_to_distinguish']:ref(r,h,'cognitive_hypothesis')
  for z in r.get('predicted_responses',[]):ref(r,z['hypothesis_id'],'cognitive_hypothesis')
 if r['record_type']=='student_observation':
  ref(r,r['target_id'],'item')
  if r.get('session_id'):ref(r,r['session_id'],'teaching_session')
  for e in r.get('observed_error_ids',[]):ref(r,e,'error_pattern')
 if r['record_type']=='cognitive_inference':
  for o in r['observation_ids']:ref(r,o,'student_observation')
  for h in r['hypotheses']:ref(r,h['hypothesis_id'],'cognitive_hypothesis')
  if r.get('recommended_probe_id'):ref(r,r['recommended_probe_id'],'diagnostic_probe')
 if r['record_type']=='teaching_intervention':
  for h in r.get('target_hypothesis_ids',[]):ref(r,h,'cognitive_hypothesis')
  if r.get('followup_probe_id'):ref(r,r['followup_probe_id'],'diagnostic_probe')
 if r['record_type']=='teaching_session':
  for i in r.get('item_ids',[]):ref(r,i,'item')
  for field,expected in [('observation_ids','student_observation'),('inference_ids','cognitive_inference'),
                         ('intervention_ids','teaching_intervention'),('outcome_ids','learning_outcome')]:
   for v in r.get(field,[]):ref(r,v,expected)
  for t in r['turns']:
   for f,expected in [('item_id','item'),('probe_id','diagnostic_probe'),
                      ('observation_id','student_observation'),('inference_id','cognitive_inference'),
                      ('intervention_id','teaching_intervention')]:
    if t.get(f):ref(r,t[f],expected)
 if r['record_type']=='learning_outcome':
  ref(r,r['target_item_id'],'item')
  ref(r,r['session_id'],'teaching_session')
  for c in r['concept_ids']:ref(r,c,'concept')
 if r['record_type']=='teaching_preference':
  for o in r['context_observation_ids']:ref(r,o,'student_observation')
  if r.get('context_inference_id'):ref(r,r['context_inference_id'],'cognitive_inference')

counts=dict(collections.Counter(r['record_type'] for r in records))
expected={'provenance':1,'concept':80,'item':100,'solution':100,'error_pattern':200,'cognitive_hypothesis':400,
'diagnostic_probe':200,'teaching_intervention':100,'student_observation':400,'cognitive_inference':200,
 'teaching_session':100,'learning_outcome':100,'teaching_preference':100}
check(counts==expected,'all_13_entity_counts_match')
items=[r for r in records if r['record_type']=='item']
diff_counts=collections.Counter(int(i['difficulty']['value']) for i in items)
check([diff_counts[j] for j in range(1,6)]==[15,25,25,20,15],'planned_difficulty_distribution')
domain_counts=collections.Counter(q['id'].split('-')[0] for q in items)
check([domain_counts[k] for k in ['NUM','ALG','FUN','GEO','TRI','PRO','STA','CAL','LIN','LOG']]==[10,12,12,10,8,10,8,12,10,8],'planned_domain_distribution')
check(len(set(i['stem'] for i in items))==100,'unique_question_stems')
check(all(r['provenance_id']=='PROV-GPT6-20261115' for r in records if r['record_type']!='provenance'),'all_records_have_source')
check(all(r['source_type']=='llm_synthetic' for r in records if r['record_type'] in ('student_observation','teaching_session')),'all_students_marked_synthetic')
check(all(r['evidence_level']=='theoretical_candidate' for r in records if 'evidence_level' in r),'no_false_empirical_certifications')
check(all(r['score']['correctness']=='unscorable' and not r['independent_assessment'] and r['causal_attribution']=='not_assessed' for r in records if r['record_type']=='learning_outcome'),'no_fabricated_outcome_assessments')
check(all('self_report_confidence' not in r and r['confidence_collection_method']=='not_collected' for r in records if r['record_type']=='student_observation'),'no_fabricated_confidence_scores')
check(all(len(r['turns'])==8 and r['completion_reason']=='session_end' for r in records if r['record_type']=='teaching_session'),'eight_turn_sessions_not_mastery_claims')
check(all(len(r['stem'].strip())>8 and len(r['correct_answer'].strip())>0 for r in items),'nonempty_problem_and_answers')
check(all(q['difficulty']['basis']=='model_estimate' and q['difficulty']['sample_size']==0 for q in items),'difficulty_not_claimed_as_empirical')

for i in items:
 id=i['id']
 check(by_id[f'E-{id}-1']['observed_signature']!=by_id[f'E-{id}-2']['observed_signature'],f'{id}: different_error_mechanisms')
 check(by_id[f'E-{id}-1']['wrong_answer_examples'][0]!=by_id[f'E-{id}-2']['wrong_answer_examples'][0],f'{id}: different_wrong_examples')
 check(by_id[f'P-{id}-1']['stem']!=by_id[f'P-{id}-2']['stem'],f'{id}: different_probes')
 check(by_id[f'P-{id}-1']['stem']!=i['stem'] and by_id[f'P-{id}-2']['stem']!=i['stem'],f'{id}: probes_not_identical_to_original')
 check(by_id[f'H-{id}-PU']['kind']=='pseudo_understanding',f'{id}: has_pseudo_understanding_risk')
 check(by_id[f'SE-{id}']['turns'][0]['message']==i['stem'],f'{id}: conversation_opens_with_problem')
 # Do not equate 'scripted student said correct' with mastery
 check(by_id[f'LO-{id}']['score']['correctness']=='unscorable',f'{id}: outcome_unscorable')

tex_strings=[]
for r in records:
 if r['record_type']=='item':tex_strings.append((r['id'],r['stem']))
 if r['record_type']=='solution':
  tex_strings.extend((r['id'],s['explanation']) for m in r['methods'] for s in m['steps'])
for id,text in tex_strings:
 check(text.count('\\(')==text.count('\\)'),f'{id}: paired_inline_latex_delimiters')
 check(text.count('\\begin{cases}')==text.count('\\end{cases}'),f'{id}: paired_piecewise_environment')

# SQLite checks and queryable integrity.
db=sqlite3.connect(ROOT/'data'/'mathedu_cog_100.sqlite')
db.execute('PRAGMA foreign_keys=ON')
check(not db.execute('PRAGMA foreign_key_check').fetchall(),'sqlite_foreign_key_checks')
check(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite_integrity_check')
for tab,number in [('questions',100),('concepts',80),('error_patterns',200),('diagnostic_probes',200),
                   ('student_observations',400),('teaching_sessions',100),('all_records',2081)]:
 check(db.execute('SELECT COUNT(*) FROM '+tab).fetchone()[0]==number,f'sqlite_{tab}_count')
check(db.execute('SELECT COUNT(*) FROM question_summary WHERE n_errors=2 AND n_probes=2 AND n_observations=4 AND n_sessions=1').fetchone()[0]==100,'per_item_record_minimums')
item_split=dict(db.execute('select id,split from questions').fetchall())

# Teacher training must contain only the conversation prefix, never later student turns.
export_counts={}
for name in ['tutoring_sft','cognitive_diagnosis_sft','label_generation_sft','teaching_preferences']:
 path=ROOT/'exports'/f'{name}.jsonl'
 rows=[json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]
 export_counts[name]=len(rows)
 check(len(rows)==(300 if name in ('tutoring_sft','cognitive_diagnosis_sft') else 100),f'{name}: expected_rows')
 check(all(r['split']==item_split[r['item_id']] for r in rows),f'{name}: split_matches_item')
 check(all(r.get('synthetic') is True for r in rows),f'{name}: synthetic_flag')
 for partition in ('train','validation','synthetic_test'):
  file=ROOT/'exports'/partition/f'{name}.jsonl'
  part=[json.loads(s) for s in file.read_text(encoding='utf-8').splitlines() if s.strip()]
  check(all(z['split']==partition for z in part),f'{name}: only_{partition}')
  check(sum(r['split']==partition for r in rows)==len(part),f'{name}: {partition}_count')
 if name=='tutoring_sft':
  for r in rows:
   source=by_id[f'SE-{r["item_id"]}']['turns'];idx=r['turn_index']
   context=r['messages'][1:-1];target=r['messages'][-1]
   check(len(context)==idx,f'{r["id"]}: prompt_prefix_length')
   check(all(m['content']==turn['message'] for m,turn in zip(context,source[:idx])),f'{r["id"]}: prompt_only_past_turns')
   check(target['content']==source[idx]['message'],f'{r["id"]}: next_tutor_only')

# Disjoint families across partitions: all derived records inherit the parent split.
sets={s:set() for s in ('train','validation','synthetic_test')}
for q in items:sets[item_split[q['id']]].add(q['item_family_id'])
check(not (sets['train']&sets['validation'] or sets['train']&sets['synthetic_test'] or sets['validation']&sets['synthetic_test']),'family_disjoint_partitions')
check({p:len(v) for p,v in sets.items()}=={'train':70,'validation':15,'synthetic_test':15},'exact_partition_sizes')

math=json.loads((ROOT/'reports'/'math_checks.json').read_text(encoding='utf-8'))
check(math['executed']==100 and math['failed']==0 and math['passed']==100,'targeted_math_checks_all_pass')

report={'dataset':'MathEdu-Cog 100','validation_date':'2026-11-15',
 'result':'passed' if not issues else 'failed',
 'validated_entity_count':len(records),'record_counts':counts,
 'num_structural_assertions_passed':len(passed_checks),'issues_count':len(issues),'issues':issues[:100],
 'training_exports':export_counts,'difficulty_counts':dict(diff_counts),
 'unique_stems':len(set(x['stem'] for x in items)),
 'source_assurance':{'real_student_records':0,'real_small_model_runs':0,'human_expert_reviewed':0,'llm_synthetic':True},
 'automated_math_checks':{'passed':math['passed'],'total':math['executed'],
    'scope':'One targeted check per question; not full proof or expert validation'},
 'checks_are_not': ['Expert audit','Real-student behavioral validity','Causal teaching-effect evidence','Independent evaluation of model generalization'],
 'cautions': ['Dialogue responses are semi-templated: use as training pipeline smoke-test/seed, not as naturalistic empirical conversation data.',
             'Preference pairs are intentionally obvious good-vs-bad contrasts, requiring harder negatives for production preference training.',
             'The synthetic_test split is generated by the same authoring process; it is not a real holdout benchmark.',
             'Only exports/train/*.jsonl should be used for model fitting.']}
(ROOT/'reports'/'quality_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('Quality:',report['result'], 'assertions passed:',report['num_structural_assertions_passed'],'issues:',len(issues))
for i in issues[:25]:print('ISSUE',i)
if issues:raise SystemExit(1)
