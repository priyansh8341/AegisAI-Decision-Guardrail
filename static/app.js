'use strict';
// Browser UI only. Assessment, policy and persistence live in the Python modules.
const $ = id => document.getElementById(id);
const state = {samples: [], records: [], total: 0, selected: null, compare: new Set(), tab: 'overview', cell: null, busy: false};
const names = {PENDING:'Awaiting review', APPROVED:'Approved', REVISION_REQUESTED:'Revision requested', BLOCKED:'Blocked', NOT_APPLICABLE:'Not reviewable'};
let toastTimer, elapsedTimer;

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}
function append(parent, ...children) { children.filter(Boolean).forEach(c => parent.append(c)); return parent; }
function button(text, cls, action) { const b = el('button', cls, text); b.type = 'button'; b.addEventListener('click', action); return b; }
function badge(text, cls) { return el('span', 'badge ' + (cls || String(text).toLowerCase()), text); }
function time(value, short = false) {
  return new Date(value).toLocaleString(undefined, short ? {month:'short',day:'numeric'} : {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
}
function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true, 4500); }
async function api(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.error?.message || data.detail || 'The request could not be completed.');
    error.record = data.id ? data : null;
    throw error;
  }
  return data;
}
function showDialog(title, content) {
  $('dialog-title').textContent = title; $('dialog-body').replaceChildren(content); $('info-dialog').showModal();
}
$('close-dialog').onclick = () => $('info-dialog').close();
$('info-dialog').addEventListener('click', e => { if(e.target === $('info-dialog')) {const r=e.target.getBoundingClientRect(); if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();} });
function methodology() {
  const c = el('div');
  append(c, el('p', '', 'AegisAI supports a human review. It does not certify a decision as safe, compliant or financially sound.'),
    el('h3', '', 'A transparent priority score'),
    el('p', '', 'Each risk receives a likelihood and impact rating from 1 to 5. Priority = likelihood × impact × 4. The overall score is the highest individual priority; scores are not averaged away.'),
    el('p', '', 'Low: below 32 · Medium: 32–59 · High: 60–79 · Critical: 80–100. These are ordinal priorities based on model judgments, not measured probabilities.'),
    el('h3', '', 'Appetite changes the review threshold'),
    el('p', '', 'Cautious: 32 · Balanced: 48 · Flexible: 64. At or above that threshold, the policy signals REVISE. At 80 or above it signals BLOCK. Below the threshold it signals REVIEW, never automatic approval.'),
    el('h3', '', 'Evidence and uncertainty'),
    el('p', '', 'An evidence match means only that a quotation appears in the submitted decision or constraints. It does not verify that the statement is true. Unmatched quotations are flagged. Inferred risks have no supporting quotation. Assumptions and open questions remain visible.'),
    el('h3', '', 'Samples, local storage and reviews'),
    el('p', '', 'Sample assessments are fixed examples; live mode calls your configured Ollama service. SQLite stores briefs, reports and review notes on this computer. Reviewer names are entered locally, not authenticated. Audit entries are appended by the application but are not tamper-proof.'),
    el('p', '', 'A review records a decision; it does not execute an external action. This workspace is a local single-user prototype. Scores and scenarios have not been calibrated against real outcomes.'));
  showDialog('How the assessment works', c);
}
$('method-button').onclick = methodology;
$('engine-button').onclick = async () => {
  const c=el('div');
  append(c,el('p','','Live assessments run through Ollama. Sample mode works without a model and is always labelled.'),el('h3','','Connect your local model'),
    el('p','','Install Ollama from its official website, then run these commands in your terminal:'),el('pre','','ollama pull llama3.2:3b\nollama serve'),
    el('p','','If Ollama is already running, you do not need another server. The configured model defaults to llama3.2:3b for a smaller local footprint. Set AEGIS_MODEL before starting AegisAI to use another installed model.'),
    el('p','','The default model service is http://127.0.0.1:11434. AEGIS_OLLAMA_URL can configure another trusted service; briefs will be sent to that configured service.'),
    button('Check connection again','button secondary',async()=>{await checkEngine();toast($('engine-label').textContent);}));
  showDialog('Local model connection',c);
};
async function checkEngine() {
  try {const s=await api('/api/status');$('engine-label').textContent = s.ready ? s.model + ' ready' : s.message; $('engine-button').classList.toggle('ready',s.ready);}
  catch { $('engine-label').textContent='Status unavailable'; }
}
function switchView(view) {
  $('workspace-view').hidden = view !== 'workspace'; $('library-view').hidden = view !== 'library';
  $('nav-workspace').classList.toggle('active',view==='workspace'); $('nav-library').classList.toggle('active',view==='library');
  $('breadcrumb-current').textContent = view === 'library' ? 'Library' : 'Workspace';
  $('nav-workspace').setAttribute('aria-current',view==='workspace'?'page':'false');
  $('nav-library').setAttribute('aria-current',view==='library'?'page':'false');
  if(view==='library') renderLibrary();
}
function navigate(view) {location.hash=view; switchView(view); window.scrollTo({top:0});}
$('nav-workspace').onclick=()=>navigate('workspace');
$('nav-library').onclick=()=>navigate('library');
$('view-history').onclick=()=>navigate('library');
$('recent-all').onclick=()=>navigate('library');
function newAssessment() {
  if(state.busy){toast('An assessment is still running. Wait for it to finish before starting another.');return;}
  document.querySelector('input[value="live"]').checked=true;
  updateMode();fillBrief({title:'',decision:'',constraints:'',owner:'',category:'Operations',appetite:'Balanced'});
  $('scenario').value='';state.selected=null;state.tab='overview';state.cell=null;
  $('report').hidden=true;$('empty-report').hidden=false;navigate('workspace');$('title').focus();
}
$('new-assessment').onclick=newAssessment;
function mode() {return document.querySelector('input[name="mode"]:checked').value;}
function fillBrief(brief) {for(const key of ['title','decision','constraints','owner','category','appetite']) $(key).value=brief[key]||''; updateCount();}
function updateCount() {$('decision-count').textContent=$('decision').value.length.toLocaleString()+' / 12,000';}
$('decision').addEventListener('input',updateCount);
function updateMode() {
  const sample=mode()==='sample';
  $('sample-notice').hidden=!sample;
  $('mode-note').textContent=sample?'Walk through a complete report using a fixed, illustrative scenario. No model is called.':'Uses your local Ollama model. Your brief stays in this local application and its configured model service.';
  $('run-label').textContent=sample?'Open sample assessment':'Assess this decision';
  for(const id of ['title','decision','constraints','owner']) $(id).readOnly=sample;
  for(const id of ['category','appetite']) $(id).disabled=sample;
  if(sample && !$('scenario').value) $('scenario').value=state.samples[0]?.id||'';
  if(sample) {const fixture=state.samples.find(x=>x.id===$('scenario').value);if(fixture)fillBrief(fixture.brief);}
  $('scenario').options[0].disabled=sample;
  $('form-error').hidden=true;
}
document.querySelectorAll('input[name="mode"]').forEach(r=>r.addEventListener('change',updateMode));
$('scenario').onchange=()=>{const sample=state.samples.find(x=>x.id===$('scenario').value);if(sample)fillBrief(sample.brief);};
$('try-sample').onclick=()=>{document.querySelector('input[value="sample"]').checked=true;updateMode();$('run-button').focus();$('brief-heading').scrollIntoView({block:'start',behavior:'smooth'});};
function loading(on) {
  state.busy=on;
  for(const n of $('brief-form').querySelectorAll('button,input,textarea,select')) n.disabled=on;
  if(!on) updateMode();
  $('loading-report').hidden=!on;
  $('empty-report').hidden=on || !!state.selected;
  $('report').hidden=on || !state.selected;
  clearInterval(elapsedTimer);
  if(on) {
    $('form-error').hidden=true;const start=Date.now();$('elapsed').textContent='Elapsed: 0 seconds';
    $('loading-title').textContent=mode()==='sample'?'Preparing your sample report':'Examining your decision';
    $('loading-description').textContent=mode()==='sample'?'Loading the fixed example, applying the scoring policy and saving the report.':'Generating a structured report for your review. The model can produce contradictions or unsupported claims.';
    elapsedTimer=setInterval(()=>$('elapsed').textContent='Elapsed: '+Math.floor((Date.now()-start)/1000)+' seconds',1000);
  }
}
$('brief-form').onsubmit=async e=>{
  e.preventDefault(); if(state.busy)return;
  const payload={mode:mode(),sample_id:$('scenario').value||null};
  for(const key of ['title','decision','constraints','owner','category','appetite']) payload[key]=$(key).value.trim();
  loading(true);
  let received=null, requestError=null;
  try {received=await api('/api/assess',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});}
  catch(error){received=error.record;requestError=error.message;}
  finally {loading(false);}
  if(received) {state.tab='overview';state.cell=null;showRecord(received);location.hash='record='+received.id;await refreshHistory();if(received.status==='completed')toast(payload.mode==='sample'?'Sample report saved to your library.':'Assessment saved. Ready for human review.');}
  else {$('form-error').textContent=requestError||'The assessment could not be saved.';$('form-error').hidden=false;}
};
function openRecord(record) {state.tab='overview';state.cell=null;showRecord(record);location.hash='record='+record.id;switchView('workspace');$('report').scrollIntoView({block:'start',behavior:'smooth'});}
async function loadRecord(id) {try{const r=await api('/api/assessments/'+encodeURIComponent(id));openRecord(r);}catch(e){toast(e.message);navigate('library');}}
function reportHeader(record) {
  const header=el('div','report-header'),left=el('div'),kicker=el('div','report-kicker');
  append(kicker,el('span','','ASSESSMENT REPORT'),badge(record.mode==='sample'?'FIXED SAMPLE':'LIVE MODEL',record.mode),badge(record.status==='failed'?'Not reviewable':names[record.review_status],record.status==='failed'?'failed':record.review_status.toLowerCase()));
  append(left,kicker,el('h2','',record.brief.title),el('div','report-meta',time(record.created_at)+' · '+(record.brief.owner||'Owner not assigned')+' · '+record.id));
  const tools=el('div','report-tools');
  for(const [type,label]of[['md','↓ Report'],['json','JSON']]) {const a=el('a','button secondary',label);a.href='/api/assessments/'+record.id+'/export/'+type;a.setAttribute('download','');a.title='Download '+(type==='md'?'Markdown report':'JSON data');tools.append(a);}
  append(header,left,tools);return header;
}
function showRecord(record) {
  state.selected=record;const root=$('report');root.replaceChildren(reportHeader(record));root.hidden=false;$('empty-report').hidden=true;$('loading-report').hidden=true;
  if(record.status==='failed') {
    const fail=el('div','card report-failure');
    append(fail,badge('ASSESSMENT FAILED','failed'),el('h2','','Assessment unavailable'),el('p','',record.error.message),
      el('p','','The failed attempt is saved in your library. It cannot be approved or treated as a completed assessment.'),
      button('Use this brief again','button secondary',()=>reuseBrief(record)),button('Check model setup','text-button',()=>$('engine-button').click()));
    root.append(fail);return;
  }
  const r=record.result,intro=el('div','report-intro');intro.append(el('div','tiny-label','DECISION PRIORITY'));
  const main=el('div','summary-main'),score=el('div','summary-score',r.score);score.append(el('small','',' / 100'));
  const signal=el('div','signal-area');append(signal,el('div','signal-label','POLICY SIGNAL'),el('div','signal-value',r.recommendation));
  append(main,score,signal);intro.append(main,el('p','',r.executive_summary));
  append(intro,append(el('div','summary-foot'),el('span','',r.level+' PRIORITY · '+record.brief.appetite+' appetite'),el('span','','Human decision required')));root.append(intro);
  const stats=el('div','report-stats');
  for(const [value,label,caption]of[[r.risks.length,'RISKS IDENTIFIED','Prioritised for review'],[r.evidence_matches+'/'+r.risks.length,'SOURCE MATCHES','Quotes matched to brief'],[r.open_questions.length,'OPEN QUESTIONS','Resolve before acting']]) {stats.append(append(el('div','mini-stat'),el('span','',label),el('strong','',value),el('small','',caption)));}root.append(stats);
  if(r.quality_review) {
    const q=r.quality_review,card=el('section','card');
    const labels={issues_found:'Potential problems need review',no_issues_detected:'No issues detected by the automated check',check_failed:'Automated check unavailable'};
    append(card,el('h3','',labels[q.status]||'Automated consistency review'),el('p','',q.limitation));
    if(q.message)card.append(el('p','notice error-notice',q.message));
    for(const finding of q.findings) {
      const detail=el('details');append(detail,el('summary','',finding.severity.toUpperCase()+' · '+finding.kind.replaceAll('_',' ')+' · '+finding.field),el('blockquote','',finding.quote),el('p','',finding.explanation));
      if(finding.source_quote)detail.append(el('p','','Brief: '+finding.source_quote));card.append(detail);
    }
    card.append(el('p','review-notice','Read the original brief and report before recording your judgment. This check does not establish correctness or approval.'));root.append(card);
  }
  const tabs=el('div','report-tabs');tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Report sections');
  for(const [id,label]of[['overview','Overview'],['risks','Risk register'],['review','Human review'],['audit','Audit trail']]) {
    const b=button(label,'report-tab',()=>{state.tab=id;state.cell=null;showRecord(record);$('tab-'+id).focus();});b.id='tab-'+id;b.setAttribute('role','tab');b.setAttribute('aria-selected',state.tab===id);b.setAttribute('aria-controls','report-panel');b.tabIndex=state.tab===id?0:-1;
    b.onkeydown=e=>{const ids=['overview','risks','review','audit'];let i=ids.indexOf(id);if(e.key==='ArrowRight')i=(i+1)%4;else if(e.key==='ArrowLeft')i=(i+3)%4;else if(e.key==='Home')i=0;else if(e.key==='End')i=3;else return;e.preventDefault();state.tab=ids[i];showRecord(record);$('tab-'+ids[i]).focus();};tabs.append(b);
  }root.append(tabs);
  const panel=el('div','report-panel');panel.id='report-panel';panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby','tab-'+state.tab);panel.tabIndex=0;
  if(state.tab==='overview')renderOverview(panel,record);
  if(state.tab==='risks')renderRisks(panel,record);
  if(state.tab==='review')renderReview(panel,record);
  if(state.tab==='audit')renderAudit(panel,record);
  root.append(panel);
}
function listCard(title,items) {const c=el('section','card');c.append(el('h3','',title));const ul=el('ul');items.forEach(s=>ul.append(el('li','',s)));c.append(ul);return c;}
function renderOverview(panel,record) {
  const r=record.result,c=el('section','card');c.append(el('h3','','Risk landscape'));
  const layout=el('div','matrix-layout'),left=el('div'),grid=el('div','matrix');grid.setAttribute('aria-label','Risk matrix: likelihood increases upward, impact increases to the right');
  for(let l=5;l>=1;l--)for(let i=1;i<=5;i++) {
    const matching=r.risks.filter(risk=>risk.likelihood===l&&risk.impact===i),score=l*i*4;
    const level=score>=80?'critical':score>=60?'high':score>=32?'medium':'low';
    const cell=button('','matrix-cell '+level,()=>{state.cell={l,i};state.tab='risks';showRecord(record);$('report-panel').focus();});
    cell.setAttribute('aria-label','Likelihood '+l+', impact '+i+': '+matching.length+' risks');cell.disabled=!matching.length;
    if(matching.length)cell.append(el('b','',matching.length));grid.append(cell);
  }
  append(left,grid,el('div','matrix-axis','LIKELIHOOD ↑  ·  IMPACT →'));
  const explanation=el('div');append(explanation,el('p','matrix-explainer','Each marker locates a risk by likelihood and impact. Select an occupied cell to inspect its risks.'),el('p','matrix-explainer',r.policy_explanation));
  const legend=el('div','legend');for(const name of ['Low','Medium','High','Critical'])legend.append(append(el('span'),el('i',name.toLowerCase()),document.createTextNode(name)));explanation.append(legend);append(layout,left,explanation);c.append(layout);panel.append(c);
  panel.append(listCard('Recommended next steps',r.next_steps),listCard('Questions to resolve',r.open_questions));
  const outlook=el('section','card');outlook.append(el('h3','','Scenario outlook'));
  for(const [key,title]of[['best_case','Best case'],['base_case','Base case'],['worst_case','Worst case']])append(outlook,el('h3','',title),el('p','',r.outlook[key]));panel.append(outlook);
  panel.append(listCard('Assumptions to challenge',r.assumptions));
  const source=el('section','card source-brief'),details=el('details');append(details,el('summary','','View the submitted brief'),el('pre','',record.brief.decision+'\n\nConstraints:\n'+(record.brief.constraints||'Not supplied')));append(source,el('h3','','Assessment provenance'),el('p','',record.engine+' · '+r.policy_version+' · '+(record.duration_ms/1000).toFixed(2)+' seconds'),details,button('Revise this brief','text-button',()=>reuseBrief(record)));panel.append(source);
}
function renderRisks(panel,record) {
  const r=record.result;
  if(state.cell) {const note=el('div','notice sample-notice');append(note,el('span','','Showing likelihood '+state.cell.l+' / impact '+state.cell.i+' risks. '),button('Show all risks','text-button',()=>{state.cell=null;showRecord(record);}));panel.append(note);}
  const list=el('div','risk-list');
  const risks=state.cell?r.risks.filter(x=>x.likelihood===state.cell.l&&x.impact===state.cell.i):r.risks;
  for(const [index,risk]of risks.entries()) {
    const item=el('details','risk-item');if(index===0)item.open=true;
    const summary=el('summary'),title=el('span','risk-title');append(title,el('strong','',risk.title),el('small','',risk.category+' · Priority '+risk.score+'/100'));append(summary,el('span','risk-id',risk.id),title,badge(risk.level));
    const body=el('div','risk-body');append(body,el('h4','','Why it matters'),el('p','',risk.rationale));
    const scores=el('div','risk-scores');append(scores,el('span','','Likelihood '+risk.likelihood+'/5'),el('span','','Impact '+risk.impact+'/5'));body.append(scores);
    append(body,el('h4','','Source evidence · '+risk.evidence_status),el('p','evidence-quote',risk.evidence||'Inferred risk. No source quotation supplied.'));
    if(risk.evidence_status==='unverified')body.append(el('p','','This quotation was not found in your brief. Verify or challenge it before acting.'));
    append(body,el('h4','','Recommended mitigation'),el('p','',risk.mitigation),el('h4','','What to monitor'),el('p','',risk.monitoring_signal));append(item,summary,body);list.append(item);
  }panel.append(list);
}
function reuseBrief(record) {
  document.querySelector('input[value="live"]').checked=true;updateMode();fillBrief(record.brief);$('scenario').value='';navigate('workspace');$('title').focus();$('brief-heading').scrollIntoView({block:'start',behavior:'smooth'});toast('Brief copied into live mode. Edit it before assessing.');
}
function renderReview(panel,record) {
  const c=el('section','card');append(c,el('h3','','Record your judgment'),el('p','','Review the risks and missing information, then record your own decision. The policy signal does not approve or execute this proposal.'));
  if(record.mode==='sample')c.append(el('div','notice sample-notice','This is a practice review of a fixed sample. It remains labelled as a sample in history and exports.'));
  const form=el('form','review-form');
  function field(label,id,node) {const wrap=el('div','field'),lab=el('label','',label);lab.htmlFor=id;node.id=id;append(wrap,lab,node);form.append(wrap);return node;}
  const reviewer=field('Reviewer name','reviewer',el('input'));reviewer.required=true;reviewer.minLength=2;reviewer.maxLength=80;reviewer.placeholder='Your name';reviewer.autocomplete='name';
  const action=field('Your decision','review-action',el('select'));
  for(const [value,label]of[['REVISION_REQUESTED','Request a revision'],['BLOCKED','Block this proposal'],['APPROVED','Approve after review']]) {const o=el('option','',label);o.value=value;action.append(o);}
  const note=field('Reasoning & conditions','review-note',el('textarea'));note.required=true;note.minLength=10;note.maxLength=2500;note.rows=4;note.placeholder='Explain your decision, conditions and any accepted risks…';
  const checks=[];
  if(record.mode==='live') {
    form.append(el('h4','','Before approving this assessment'));
    for(const [value,label]of[['source_facts','I checked key claims against the submitted brief and supporting evidence.'],['contradictions','I checked for conflicts between the brief, risks and assumptions.'],['actionability','I checked that mitigations and verification steps are practical.']]) {
      const wrap=el('label'),input=el('input');input.type='checkbox';input.value=value;input.style.width='auto';input.style.marginRight='8px';append(wrap,input,document.createTextNode(label));form.append(wrap);checks.push(input);
    }
    const source=el('details');append(source,el('summary','','Read the original brief'),el('pre','',record.brief.decision+'\n\nConstraints:\n'+(record.brief.constraints||'Not supplied')));form.append(source);
  }
  const error=el('div','notice error-notice');error.hidden=true;error.setAttribute('role','alert');form.append(error);
  const save=el('button','button primary','Save review to audit trail');save.type='submit';form.append(save);
  form.onsubmit=async e=>{e.preventDefault();save.disabled=true;error.hidden=true;try{const updated=await api('/api/assessments/'+record.id+'/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reviewer:reviewer.value.trim(),action:action.value,note:note.value.trim(),expected_version:record.version,checks_completed:checks.filter(x=>x.checked).map(x=>x.value)})});state.tab='audit';showRecord(updated);await refreshHistory();toast('Review saved with your note and timestamp.');}catch(e){error.textContent=e.message;error.hidden=false;}finally{save.disabled=false;}};
  append(c,form,el('p','review-notice','Reviewer names are self-entered in this local workspace. Reviews are stored, but they do not perform external actions.'));panel.append(c);
}
function renderAudit(panel,record) {
  const c=el('section','card');c.append(el('h3','','Review timeline'));
  for(const event of record.reviews) {const item=el('div','audit-item');append(item,append(el('div','audit-top'),el('strong','',event.reviewer),badge(names[event.action],event.action.toLowerCase())),el('small','',time(event.created_at)),el('p','',event.note));c.append(item);}
  const initial=el('div','audit-item');append(initial,el('strong','','Assessment created'),el('p','',(record.mode==='sample'?'Fixed sample loaded':'Model response validated')+' · '+time(record.created_at)));c.append(initial);
  if(!record.reviews.length)c.append(el('p','','No human review has been recorded yet.'));
  panel.append(c);panel.append(button('Record a review','button secondary',()=>{state.tab='review';showRecord(record);$('reviewer').focus();}));
}
async function refreshHistory() {
  try {const data=await api('/api/assessments');state.records=data.records;state.total=data.total;$('library-count').textContent=data.total;renderRecent();renderLibrary();}
  catch(e){$('recent-list').replaceChildren(el('p','muted','Could not load saved assessments.'));toast(e.message);}
}
function renderRecent() {
  const root=$('recent-list');root.replaceChildren();
  if(!state.records.length){root.append(el('p','muted small','Your saved assessments will appear here. Try a sample to explore the workflow.'));return;}
  for(const r of state.records.slice(0,3)) {
    const row=el('div','recent-row'),b=button('','recent-open',()=>openRecord(r));
    append(b,el('strong','',r.brief.title),el('small','',(r.mode==='sample'?'Sample':'Live')+' · '+time(r.created_at)));
    append(row,b,badge(r.result?.level||'FAILED'),el('span','recent-arrow','↗'));root.append(row);
  }
}
function filteredRecords(){const q=$('search').value.trim().toLocaleLowerCase();return state.records.filter(r=>{
  const level=r.result?.level||'FAILED';
  return (!q||[r.brief.title,r.brief.owner,r.brief.decision].join(' ').toLocaleLowerCase().includes(q))&&(!$('filter-level').value||level===$('filter-level').value)&&(!$('filter-review').value||r.review_status===$('filter-review').value)&&(!$('filter-mode').value||r.mode===$('filter-mode').value);
});}
function renderLibrary() {
  const stats=$('library-stats');stats.replaceChildren();const completed=state.records.filter(r=>r.result),live=completed.filter(r=>r.mode==='live');
  const statsData=[[state.total,'Saved assessments','Including failed attempts'],[completed.filter(r=>r.review_status==='PENDING').length,'Awaiting review','Completed reports only'],[live.filter(r=>r.result.score>=60).length,'High-priority live reports','Samples excluded'],[completed.filter(r=>r.mode==='sample').length,'Sample reports','Fixed illustrative examples']];
  for(const [value,label,caption]of statsData)stats.append(append(el('div','library-stat'),el('span','',label),el('strong','',value),el('small','',caption)));
  const records=filteredRecords(),root=$('library-list');root.replaceChildren();
  $('clear-search').hidden=!$('search').value;
  $('results-count').textContent=records.length+' shown · '+(state.total>500?'latest 500 of '+state.total:state.total)+' saved';
  $('compare-button').textContent='Compare selected ('+state.compare.size+'/2)';$('compare-button').disabled=state.compare.size!==2;
  if(!records.length) {const empty=el('div','library-empty');append(empty,el('h3','',state.records.length?'No matching assessments':'Your decision history starts here'),el('p','',state.records.length?'Try another search or clear the filters.':'Create an assessment or explore a sample to start your library.'),button(state.records.length?'Clear all filters':'Create an assessment','button secondary',()=>{if(state.records.length){$('search').value='';for(const id of ['filter-level','filter-review','filter-mode'])$(id).value='';renderLibrary();}else newAssessment();}));root.append(empty);return;}
  for(const r of records) {
    const row=el('div','library-row'),checkbox=el('input','compare-check');checkbox.type='checkbox';checkbox.setAttribute('aria-label','Compare '+r.brief.title);checkbox.checked=state.compare.has(r.id);checkbox.disabled=!r.result;
    checkbox.onchange=()=>{if(checkbox.checked){if(state.compare.size>=2){checkbox.checked=false;toast('Choose up to two completed reports.');return;}state.compare.add(r.id);}else state.compare.delete(r.id);renderLibrary();};
    const open=button('','library-open',()=>openRecord(r));append(open,el('strong','',r.brief.title),el('small','',(r.mode==='sample'?'SAMPLE':'LIVE')+' · '+r.brief.category+' · '+(r.brief.owner||'No owner')));
    const score=append(el('div','library-score'),el('strong','',r.result?r.result.score+' / 100':'—'),badge(r.result?.level||'FAILED'));
    append(row,checkbox,open,score,badge(r.status==='failed'?'Not reviewable':names[r.review_status],r.status==='failed'?'review-badge failed':'review-badge '+r.review_status.toLowerCase()),el('span','library-date',time(r.created_at,true)));root.append(row);
  }
}
for(const id of ['search','filter-level','filter-review','filter-mode'])$(id).addEventListener(id==='search'?'input':'change',renderLibrary);
$('clear-search').onclick=()=>{$('search').value='';renderLibrary();$('search').focus();};
$('compare-button').onclick=()=>{
  const records=[...state.compare].map(id=>state.records.find(r=>r.id===id)).filter(Boolean);if(records.length!==2)return;
  const content=el('div'),[a,b]=records,delta=b.result.score-a.result.score;
  content.append(el('div','compare-summary','Second report priority is '+(delta===0?'unchanged':Math.abs(delta)+' points '+(delta>0?'higher':'lower'))+'. Compare context and individual risks; this difference does not establish an improvement or a calibrated risk change.'));
  const grid=el('div','compare-grid');
  for(const record of records) {const col=el('section','compare-column');append(col,badge(record.mode.toUpperCase(),record.mode),el('h3','',record.brief.title),el('div','compare-score',record.result.score+' / 100'),el('p','',record.result.level+' · '+record.brief.appetite+' appetite'),el('p','','Policy: '+record.result.recommendation),el('p','','Human review: '+names[record.review_status]),el('p','',record.result.risks.length+' risks · '+record.result.evidence_matches+' source matches'),el('p','',record.result.executive_summary),button('Open this report','text-button',()=>{$('info-dialog').close();openRecord(record);}));grid.append(col);}content.append(grid);showDialog('Compare two assessments',content);
};
async function route() {
  const hash=location.hash.slice(1);
  if(hash.startsWith('record=')){const id=hash.slice(7);if(state.selected?.id!==id)await loadRecord(id);else switchView('workspace');}
  else switchView(hash==='library'?'library':'workspace');
}
window.addEventListener('hashchange',route);
async function init() {
  $('today').textContent=new Date().toLocaleDateString(undefined,{weekday:'short',day:'numeric',month:'short',year:'numeric'});
  checkEngine();
  try {state.samples=await api('/api/samples');for(const item of state.samples){const o=el('option','',item.name);o.value=item.id;$('scenario').append(o);}}
  catch(e){toast('Sample scenarios could not be loaded. '+e.message);}
  await refreshHistory();await route();
}
init();
