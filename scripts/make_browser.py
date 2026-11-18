#!/usr/bin/env python3
"""Build a static, self-contained question browser HTML from the SQLite DB.
MathJax (optional network) is used for formula typesetting; HTML data stays local.
"""
import sqlite3,json,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
con=sqlite3.connect(ROOT/'data'/'mathedu_cog_100.sqlite')
con.row_factory=sqlite3.Row
catalog=json.loads((ROOT/'data'/'question_catalog.json').read_text(encoding='utf-8'))
by_id={r['id']:r for r in catalog}
rows=[]
for q in con.execute('SELECT * FROM questions ORDER BY id'):
 x=by_id[q['id']].copy()
 def docs(table):return [json.loads(r[0]) for r in con.execute(f'SELECT doc FROM {table} WHERE item_id=? ORDER BY id',(q['id'],))]
 sols=docs('solutions');errs=docs('error_patterns');probes=docs('diagnostic_probes');hyps=docs('cognitive_hypotheses')
 interv=docs('teaching_interventions');responses=docs('student_observations')
 x['steps']=[s['explanation'] for m in sols[0]['methods'] for s in m['steps']]
 x['errors']=[{'type':e['surface_category'],'signature':e['observed_signature'],'wrong':e['wrong_answer_examples'][0]} for e in errs]
 x['pseudo']=[h['label'] for h in hyps if h['kind']=='pseudo_understanding'][0]
 x['probes']=[{'stem':p['stem'],'answer':p['correct_answer']} for p in probes]
 x['hint']=interv[0]['learner_facing_message']
 x['responses']=[{'answer':r['raw_response'],'correctness':r['correctness']} for r in responses]
 rows.append(x)
con.close()
DATA=json.dumps(rows,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
PAGE=r'''<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MathEdu-Cog 100 · 数学认知题库</title>
<style>
:root{--bg:#f5f7fb;--surface:#fff;--ink:#14263d;--muted:#697a8b;--line:#e2e8ef;--brand:#226f91;--tag:#e9f3f8;--warn:#fff7e7}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft Yahei",sans-serif;color:var(--ink);background:var(--bg);line-height:1.65}header{background:linear-gradient(110deg,#132944,#1e5571);padding:24px max(20px,calc((100vw - 1350px)/2));color:white}header h1{font-size:27px;font-weight:750;margin:0 0 3px}header p{margin:0;opacity:.82;font-size:14px}.app{max-width:1370px;margin:auto;display:grid;grid-template-columns:minmax(260px,355px) minmax(0,1fr);gap:22px;padding:22px}.sidebar,.main{background:var(--surface);border:1px solid var(--line);border-radius:16px;box-shadow:0 5px 18px #14304b08}.sidebar{height:calc(100vh - 155px);min-height:490px;position:sticky;top:16px;display:flex;flex-direction:column;overflow:hidden}.filters{padding:17px;border-bottom:1px solid var(--line)}input,select{width:100%;padding:11px 12px;border:1px solid #cbd5df;border-radius:9px;background:white;color:var(--ink);font:inherit;font-size:14px}input:focus,select:focus{outline:2px solid #9ac7dc;border-color:#78b5d0}.selector-row{display:grid;grid-template-columns:1.2fr .8fr;gap:8px;margin-top:10px}.count{font-size:12px;color:var(--muted);margin-top:11px}.qlist{overflow:auto;min-height:0;padding:8px}.qitem{display:block;text-align:left;width:100%;border:1px solid transparent;background:transparent;border-radius:10px;padding:12px;cursor:pointer;transition:background .12s;font:inherit;color:inherit}.qitem:hover{background:#f1f6fa}.qitem.active{background:#e8f3f8;border-color:#b9d8e6}.qhead{font-weight:700;font-size:13px}.qtopic{font-size:12px;color:var(--muted);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.qmeta{display:flex;gap:6px;margin-top:6px;color:#4f7590;font-size:11px}.main{min-height:650px;padding:clamp(20px,3vw,38px)}.topline{display:flex;gap:10px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--muted)}.pill{border-radius:50px;background:var(--tag);color:#225f7b;padding:2px 10px;font-size:12px;font-weight:600}.main h2{font-size:27px;margin:11px 0 14px;letter-spacing:-.02em}.stem{background:#f2f6f9;padding:20px;border:1px solid #dde7ed;border-radius:12px;font-size:17px;line-height:1.85;overflow-wrap:anywhere}.section{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}.section h3{font-size:17px;margin:0 0 10px}.desc{font-size:14px;color:var(--muted)}.step{border-left:3px solid #a7c8d9;padding:5px 0 6px 14px;margin-bottom:9px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:13px}.smallcard{padding:14px;background:#fafcfd;border:1px solid var(--line);border-radius:11px;overflow-wrap:anywhere}.smallcard b{font-size:13px}.smallcard p{font-size:14px;margin:7px 0 3px}.wrong{color:#9a503f}.notice{background:var(--warn);color:#795b2c;padding:12px 15px;font-size:13px;border-radius:9px;margin-top:25px}.answer{font-size:16px;font-weight:650;color:#17675c;margin:7px 0 16px}details{border:1px solid var(--line);border-radius:11px;margin-top:10px;padding:11px 14px}summary{cursor:pointer;font-size:15px;font-weight:650}summary:hover{color:var(--brand)}details[open] summary{margin-bottom:10px}footer{text-align:center;color:#789;padding:0 20px 20px;font-size:12px}.muted{color:var(--muted)}.empty{padding:30px;color:var(--muted)}@media(max-width:900px){.app{display:block;padding:13px}.sidebar{position:static;height:350px;min-height:350px;margin-bottom:13px}.main{padding:18px;min-height:500px}.pair{grid-template-columns:1fr}.main h2{font-size:22px}} 
</style>
<script>window.MathJax={tex:{inlineMath:[['\\(','\\)']]},options:{skipHtmlTags:['script','noscript','style','textarea','pre']}};</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
<header><h1>MathEdu-Cog 100</h1><p>数学教育 AI 认知题库 · 100 道题 · 10 大领域 · 5 级难度 · 全部为合成种子数据</p></header>
<div class="app">
<aside class="sidebar"><div class="filters"><input id="q" placeholder="搜索题号、主题、题目、误区……" aria-label="搜索"><div class="selector-row"><select id="domain" aria-label="领域"></select><select id="difficulty" aria-label="难度"><option value="">全部难度</option><option value="D1">D1</option><option value="D2">D2</option><option value="D3">D3</option><option value="D4">D4</option><option value="D5">D5</option></select></div><div class="count" id="count"></div></div><div class="qlist" id="qlist"></div></aside>
<main class="main" id="detail"><div class="empty">选择左侧题目即可查看解答、错误模式、诊断与教学策略。</div></main>
</div>
<footer>离线可阅读全部内容；数学公式的自动排版需要加载 MathJax。数据未经真人实验与独立专家审核。</footer>
<script id="dataset" type="application/json">__DATA__</script>
<script>
(function(){
const data=JSON.parse(document.getElementById('dataset').textContent);
const titles={NUM:'数与运算',ALG:'代数与方程',FUN:'函数与图像',GEO:'几何与解析几何',TRI:'三角函数与向量',PRO:'概率与组合计数',STA:'统计与数据分析',CAL:'微积分与数学分析',LIN:'线性代数',LOG:'逻辑、离散数学与证明'};
const $=id=>document.getElementById(id);
const esc=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const text=v=>esc(v).replace(/\n/g,'<div></div>');
const short=v=>v.length>62?v.substring(0,62)+'…':v;
let selected='CAL-003';
$('domain').innerHTML='<option value="">全部领域</option>'+Object.entries(titles).map(([k,v])=>`<option value="${k}">${esc(v)}</option>`).join('');
function filtered(){const term=$('q').value.trim().toLowerCase(),dom=$('domain').value,diff=$('difficulty').value;return data.filter(x=>(!dom||x.id.startsWith(dom+'-'))&&(!diff||x.difficulty===diff)&&(!term||[x.id,x.topic,x.stem,x.correct_answer,x.pseudo,...x.errors.map(e=>e.signature)].join(' ').toLowerCase().includes(term)));}
function renderList(){const arr=filtered();$('count').textContent=`显示 ${arr.length} / 100 道题 · 点击查看详细标注`;
$('qlist').innerHTML=arr.map(x=>`<button class="qitem ${x.id===selected?'active':''}" data-id="${x.id}"><div class="qhead">${esc(x.id)} · ${esc(x.difficulty)} <span class="muted">${esc(titles[x.id.slice(0,3)])}</span></div><div class="qtopic">${esc(x.topic)}</div><div class="qmeta"><span>${esc(x.education_stage)}</span> · <span>${esc(x.split)}</span></div></button>`).join('')||'<div class="empty">没有匹配题目。</div>';
$('qlist').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{selected=b.dataset.id;renderList();renderDetail();if(window.innerWidth<900)window.scrollTo({top:400,behavior:'smooth'});}));}
function renderDetail(){const x=data.find(z=>z.id===selected);if(!x)return;
const error=x.errors.map((e,i)=>`<div class="smallcard"><b>错误 ${i+1}｜${esc(e.type)}</b><p>${text(e.signature)}</p><p class="wrong">示例：${text(e.wrong)}</p></div>`).join('');
const probes=x.probes.map((p,i)=>`<div class="smallcard"><b>诊断 ${i+1}</b><p>${text(p.stem)}</p><details><summary>查看参考答案</summary><p>${text(p.answer)}</p></details></div>`).join('');
$('detail').innerHTML=`<div class="topline"><span class="pill">${esc(x.id)}</span><span class="pill">${esc(x.difficulty)}</span><span>${esc(titles[x.id.slice(0,3)])}</span><span>·</span><span>${esc(x.education_stage)}</span></div><h2>${esc(x.topic)}</h2><div class="stem">${text(x.stem)}</div>
<section class="section"><h3>标准答案与推理</h3><details><summary>展开标准答案与关键步骤</summary><p class="answer">${text(x.correct_answer)}</p>${x.steps.map((st,i)=>`<div class="step"><b>步骤 ${i+1}</b><div>${text(st)}</div></div>`).join('')}</details></section>
<section class="section"><h3>错误与认知假设</h3><p class="desc">以下均为理论候选错误，不代表真实学生中的发生频率。</p><div class="pair">${error}</div><div class="smallcard" style="margin-top:12px"><b>伪理解风险</b><p>${text(x.pseudo)}</p><p class="desc">答对且未解释充分 ≠ 已被证实为伪理解；还需诊断证据。</p></div></section>
<section class="section"><h3>诊断性追问</h3><div class="pair">${probes}</div></section>
<section class="section"><h3>建议的最小教学提示</h3><div class="smallcard">${text(x.hint)}</div></section>
<section class="section"><h3>模拟学生回答</h3><details><summary>查看 4 条 AI 合成回答</summary>${x.responses.map((r,i)=>`<div class="step"><b>${i+1}. ${esc(r.correctness)}</b><div>${text(r.answer)}</div></div>`).join('')}</details></section>
<div class="notice"><b>研究使用提醒：</b>题目内容与认知标签由 AI 生成；所有模拟回答和教学数据均非真人观察。数据库的自动验证不能代替独立专家和真实学生评估。</div>`;
if(window.MathJax&&MathJax.typesetPromise)MathJax.typesetPromise([$('detail')]).catch(()=>{});
}
['q','domain','difficulty'].forEach(id=>$(id).addEventListener(id==='q'?'input':'change',renderList));
renderList();renderDetail();
})();
</script>
</body></html>'''
html_text=PAGE.replace('__DATA__',DATA)
(ROOT/'题库浏览器.html').write_text(html_text,encoding='utf-8')
print('Created browser HTML',len(html_text),'characters,',len(rows),'questions')
