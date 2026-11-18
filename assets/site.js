(()=>{
'use strict';
const D=JSON.parse(document.getElementById('site-data').textContent);
const $=(id)=>document.getElementById(id);
const state={mode:'items',q:'',domain:'',difficulty:'',limit:12};
const H=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const p=v=>H(v||'—');
const domains=Object.entries(D.domains);
for(const [code,name] of domains){const el=document.createElement('option');el.value=code;el.textContent=name;$('domain').appendChild(el)}
function normalize(s){return String(s||'').normalize('NFKC').toLowerCase()}
function filtered(){let a=state.mode==='items'?D.items:D.cases;const q=normalize(state.q).trim();return a.filter(x=>{
  const domain=x.domain_code||x.code;const d=x.difficulty;
  if(state.domain&&domain!==state.domain)return false;
  if(state.difficulty&&String(d)!==String(state.difficulty))return false;
  const search=[x.id,x.case_id,x.stem,x.problem,x.title,x.topic,x.domain,x.domain_name,x.answer,x.correct_answer,x.observed_error,x.error_tag].join(' ');
  return !q||normalize(search).includes(q);
})}
function card(x){
 const isCase=state.mode==='errors',id=isCase?x.case_id:x.id,title=isCase?x.title:x.stem,sub=isCase?x.problem:x.topic,
    domain=isCase?D.domains[x.domain_code]:D.domains[x.code];
 return `<button class="q-card" data-id="${H(id)}"><div class="q-upper"><span class="q-id">${H(id)}</span><div class="q-tags"><span>${H(domain)}</span><span class="dlevel">D${H(x.difficulty)}</span></div></div><h3>${H(title)}</h3><div class="q-foot"><span>${H((sub||'').length>47?(sub||'').slice(0,47)+'…':sub||'')}</span><span class="more">详情 ↗</span></div></button>`;
}
function render(){const arr=filtered();$('cards').innerHTML=arr.length?arr.slice(0,state.limit).map(card).join(''):'<div class="empty-state">未找到匹配内容，请尝试其他关键词或清除筛选。</div>';
$('result-counter').textContent=`${arr.length} ${state.mode==='items'?'道题目':'个案例'}`;
$('show-more').hidden=arr.length<=state.limit;
}
function section(title,html){return `<section class="detail-block"><h3>${title}</h3>${html}</section>`}
function ordered(rows){return `<ol>${(rows||[]).map(s=>`<li>${p(s)}</li>`).join('')}</ol>`}
function tagHeader(x,isCase){return `<div class="detail-kicker"><span>${H(D.domains[isCase?x.domain_code:x.code])}</span><span>D${H(x.difficulty)}</span><span>${H(isCase?'模拟错误案例':x.stage)}</span></div>`}
function itemDetail(x){
 const errors=(x.errors||[]).map(e=>`<div class="detail-box rose"><strong>${p(e.observed_signature)}</strong><br/>${p((e.wrong_answer_examples||[]).join('；'))}</div>`).join('');
 const probes=(x.probes||[]).map((x,i)=>`<div class="detail-box gray"><b>追问 ${i+1}：</b>${p(x.stem)}<br/><small>预期正确回答：${p(x.correct_answer)}</small></div>`).join('');
 const hypo=(x.hypotheses||[]).map(h=>`<p>• ${p(h.label)} <small>（候选认知假设）</small></p>`).join('');
 return `${tagHeader(x,false)}<h2>${p(x.stem)}</h2>${section('参考答案',`<div class="detail-box"><b>${p(x.correct_answer)}</b></div>`)}${section('标准解法',ordered(x.solution_steps))}${section('典型错误表现',errors)}${section('认知假设与伪理解线索',hypo||'<p>尚未提供详细标签。</p>')}${section('诊断性追问',probes)}${section('教学引导',`<div class="detail-box">${p(x.intervention||'提供最小提示并鼓励学生独立推理。')}</div>`)}<div class="source-note">本条内容为 AI 合成的研究候选标注，尚未通过独立教师审核或真实学生认知测量。</div>`;
}
function caseDetail(x){
 let steps=x.simulated_student_response?.steps||[];
 const first=Number(x.simulated_student_response?.first_invalid_step_index||0);
 const numbered=`<ol>${steps.map((s,i)=>`<li class="${i+1===first?'step-invalid':''}">${p(s)}${i+1===first?' <small>← 第一处关键错误</small>':''}</li>`).join('')}</ol>`;
 let hyp=x.candidate_cognitive_explanations||{};
 let dia=x.diagnosis||{},corr=x.correction||{},inter=x.teaching_intervention||{},trans=x.transfer_check||{};
 return `${tagHeader(x,true)}<h2>${p(x.title)}</h2><p class="mathline"><b>母题：</b>${p(x.problem)} <small>（关联 ${p(x.item_id)}）</small></p>${section('模拟学生的错误推导',numbered+`<div class="detail-box rose"><b>错误答案：</b>${p(x.simulated_student_response?.wrong_answer)}</div>`)}${section('第一处失误',`<div class="detail-box rose">${p(x.observed_error)}</div>`)}${section('候选认知解释',`<p><b>主要假设：</b>${p(hyp.leading_hypothesis)}</p><p><b>其他可能：</b>${p(hyp.alternative_explanation)}</p>`)}${section('诊断性追问',`<div class="detail-box gray">${p(dia.probe)}</div><p><b>正确回答：</b>${p(dia.mathematically_correct_response)}</p>`)}${section('正确解法',ordered(corr.solution_steps)+`<div class="detail-box"><b>正确结论：</b>${p(corr.resolution)}</div>`)}${section('教学引导',`<p><b>最小提示：</b>${p(inter.minimal_hint)}</p><p>${p(inter.feedback)}</p>`)}${section('独立迁移验证',`<div class="detail-box gray">${p(trans.problem)}</div><p><b>参考答案：</b>${p(trans.answer)}</p>`)}<div class="source-note">AI 构造的模拟学生错误案例，不能据此判断真实学生的理解状态或教学效果。</div>`;
}
function openDetail(id){const x=(state.mode==='items'?D.items:D.cases).find(v=>(v.id||v.case_id)===id);if(!x)return;$('detail-id').textContent=`${state.mode==='items'?'题目':'错误案例'} · ${id}`;$('detail-content').innerHTML=state.mode==='items'?itemDetail(x):caseDetail(x);$('overlay').hidden=false;document.body.style.overflow='hidden';$('detail-close').focus();if(window.MathJax?.typesetPromise)window.MathJax.typesetPromise([$('detail-content')]).catch(()=>{});
}
function closeDetail(){$('overlay').hidden=true;document.body.style.overflow=''}
$('cards').addEventListener('click',e=>{const card=e.target.closest('[data-id]');if(card)openDetail(card.dataset.id)});
document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{state.mode=b.dataset.mode;state.limit=12;document.querySelectorAll('[data-mode]').forEach(t=>{t.classList.toggle('active',t===b);t.setAttribute('aria-selected',String(t===b))});render()}));
$('search').addEventListener('input',e=>{state.q=e.target.value;state.limit=12;render()});
$('domain').addEventListener('change',e=>{state.domain=e.target.value;state.limit=12;render()});
$('difficulty').addEventListener('change',e=>{state.difficulty=e.target.value;state.limit=12;render()});
$('reset').addEventListener('click',()=>{state.q='';state.domain='';state.difficulty='';state.limit=12;$('search').value='';$('domain').value='';$('difficulty').value='';render()});
$('show-more').addEventListener('click',()=>{state.limit+=12;render()});
$('detail-close').addEventListener('click',closeDetail);
$('overlay').addEventListener('click',e=>{if(e.target.dataset.close)closeDetail()});
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeDetail();if(e.key==='/'&&!/input|textarea/i.test(document.activeElement.tagName)){e.preventDefault();$('search').focus()}});
render();
})();
