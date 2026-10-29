const $=id=>document.getElementById(id);
let csrf='', pollToken=0, catalog=null, environmentCount=0, busy=false, conversationId='';
let routingOptions={mcps:[],tools:[]};
let environmentOptions=[], environmentNodes=new Map(), collapsedEnvironments=new Set();
function closeEnvironmentPicker(focus=false){
  $('environment-panel').hidden=true;$('environment-toggle').setAttribute('aria-expanded','false');
  if(focus)$('environment-toggle').focus();
}
function syncEnvironmentPicker(){
  const selected=environmentNodes.get($('environment').value);
  const sources=selected?.available_mcps||['db','logan'];
  for(const option of $('preferred-mcp').options)option.disabled=option.value!=='auto'&&!sources.includes(option.value);
  if($('preferred-mcp').selectedOptions[0]?.disabled){$('preferred-mcp').value='auto';renderOperationOptions();}
  $('environment-caption').textContent=selected?.path||'Choose compartment';
  $('environment-toggle').title=selected?.path||'Choose compartment';
  $('environment-toggle').disabled=busy||$('environment').disabled||!environmentCount;
  $('environment-lock').hidden=!conversationId;
  document.querySelectorAll('.environment-choice').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.environment===$('environment').value)));
  if($('environment-toggle').disabled)closeEnvironmentPicker();
}
function renderEnvironmentTree(){
  const query=$('environment-search').value.trim().toLocaleLowerCase();
  const matchCache=new Map();
  function matches(node){
    if(!matchCache.has(node.id))matchCache.set(node.id,!query||node.path.toLocaleLowerCase().includes(query)||node.children.some(matches));
    return matchCache.get(node.id);
  }
  let visible=0;
  function list(nodes){
    const ul=document.createElement('ul');
    for(const node of nodes){
      if(!matches(node))continue;visible++;
      const li=document.createElement('li'),row=document.createElement('div');row.className='environment-row';
      if(node.children.length){
        const expand=document.createElement('button');expand.type='button';expand.className='environment-expand';
        const open=!!query||!collapsedEnvironments.has(node.id);expand.textContent=open?'▾':'▸';expand.setAttribute('aria-expanded',String(open));expand.setAttribute('aria-label',(open?'Collapse ':'Expand ')+node.label);
        expand.onclick=()=>{const child=li.querySelector('ul');const opening=child.hidden;child.hidden=!opening;expand.textContent=opening?'▾':'▸';expand.setAttribute('aria-expanded',String(opening));expand.setAttribute('aria-label',(opening?'Collapse ':'Expand ')+node.label);if(opening)collapsedEnvironments.delete(node.id);else collapsedEnvironments.add(node.id);};row.append(expand);
      }else{const spacer=document.createElement('span');spacer.className='environment-expand-spacer';row.append(spacer);}
      const choose=document.createElement('button');choose.type='button';choose.className='environment-choice';choose.dataset.environment=node.id;choose.textContent=node.label;choose.title=node.path;choose.setAttribute('aria-pressed',String(node.id===$('environment').value));
      choose.onclick=()=>{if($('environment').disabled||busy)return;$('environment').value=node.id;syncEnvironmentPicker();closeEnvironmentPicker(true);updateSubmit();};row.append(choose);li.append(row);
      if(node.children.length){const children=list(node.children);children.hidden=!query&&collapsedEnvironments.has(node.id);li.append(children);}ul.append(li);
    }
    return ul;
  }
  const tree=list(environmentOptions.filter(n=>!n.parent_id));$('environment-tree').replaceChildren(tree);
  if(!visible){const empty=document.createElement('p');empty.className='note';empty.textContent='No matching compartments.';$('environment-tree').append(empty);}
  $('environment-count').textContent=query?visible+' compartments shown':environmentCount+' authorized compartment'+(environmentCount===1?'':'s');
}
function loadEnvironmentOptions(rows){
  environmentNodes=new Map(rows.map(r=>[r.id,{...r,children:[],path:''}]));
  for(const node of environmentNodes.values())if(environmentNodes.has(node.parent_id))environmentNodes.get(node.parent_id).children.push(node);else node.parent_id=null;
  function path(node){return node.path||(node.path=(node.parent_id?path(environmentNodes.get(node.parent_id))+' / ':'')+node.label);}
  for(const node of environmentNodes.values()){path(node);node.children.sort((a,b)=>a.label.localeCompare(b.label));}
  environmentOptions=[...environmentNodes.values()].sort((a,b)=>a.label.localeCompare(b.label));
  $('environment').replaceChildren();for(const row of rows){const option=document.createElement('option');option.value=row.id;option.textContent=environmentNodes.get(row.id).path;$('environment').append(option);}
  renderEnvironmentTree();syncEnvironmentPicker();
}
$('environment-toggle').onclick=()=>{
  if(!$('environment-panel').hidden){closeEnvironmentPicker();return;}
  $('environment-search').value='';renderEnvironmentTree();$('environment-panel').hidden=false;$('environment-toggle').setAttribute('aria-expanded','true');$('environment-search').focus();
};
$('environment-search').oninput=renderEnvironmentTree;
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('environment-panel').hidden){e.preventDefault();closeEnvironmentPicker(true);}});
document.addEventListener('click',e=>{if(!e.target.closest('.environment-picker'))closeEnvironmentPicker();});

function renderRoutingOptions(data){
  routingOptions=data||{mcps:[],tools:[]};
  $('preferred-mcp').replaceChildren();
  for(const item of routingOptions.mcps){const o=document.createElement('option');o.value=item.id;o.textContent=item.label;$('preferred-mcp').append(o);}
  renderOperationOptions();
}
function renderOperationOptions(){
  const previous=$('preferred-tool').value,source=$('preferred-mcp').value;
  $('preferred-tool').replaceChildren();
  for(const item of routingOptions.tools){
    if(source!=='auto'&&item.mcp!=='auto'&&item.mcp!==source)continue;
    const o=document.createElement('option');o.value=item.id;o.textContent=item.label;$('preferred-tool').append(o);
  }
  if([...$('preferred-tool').options].some(o=>o.value===previous))$('preferred-tool').value=previous;
  $('routing-help').textContent='Applies to your next message. Top SQL uses Database Observability and verified AWR snapshots. Required discovery and access checks still run.';
}
$('preferred-mcp').onchange=renderOperationOptions;

async function api(path,options={}) {
  const r=await fetch(path,{credentials:'same-origin',...options});
  if(!r.ok){const b=await r.json().catch(()=>({}));throw new Error(typeof b.detail==='string'?b.detail:'The request could not be completed');}
  return r.json();
}
function updateSubmit(){
  syncEnvironmentPicker();
  $('submit').disabled=busy||environmentCount===0||!catalog||!!catalog.error||!catalog.models.some(m=>m.id===$('model').value&&m.enabled);
  $('new-conversation').disabled=busy;
}
function renderModels(data){
  catalog=data;
  let remembered='';try{remembered=localStorage.getItem('db-assistant-model')||'';}catch{}
  const preferred=$('model').value||remembered;
  $('model').replaceChildren();
  const groups=new Map();
  for(const m of data.models){
    const vendor=m.vendor||'Configured models';
    if(!groups.has(vendor)){const group=document.createElement('optgroup');group.label=vendor;groups.set(vendor,group);$('model').append(group);}
    const o=document.createElement('option');o.value=m.id;o.disabled=!m.enabled;
    o.textContent=m.label+(m.enabled?'':' — '+(m.reason||'not configured'));
    o.title=m.reason||m.tool_support||'Applies to the next investigation';groups.get(vendor).append(o);
  }
  if(!data.models.length){const o=document.createElement('option');o.textContent='No models available';o.value='';$('model').append(o);}
  $('model').value=data.models.some(m=>m.id===preferred&&m.enabled)?preferred:data.default_model;
  const stamp=data.updated_at?' · Updated '+new Date(data.updated_at).toLocaleTimeString():'';
  $('catalog-status').textContent=data.error||(data.source==='demo'?'Sample model catalog · Demo, not connected to OCI':'OCI GenAI catalog · '+data.region)+stamp;
  updateSubmit();
}
async function loadModels(force=false){
  $('refresh-models').disabled=true;$('catalog-status').textContent='Loading models offered by OCI Generative AI…';
  try{const data=await api(force?'/api/models/refresh':'/api/models',force?{method:'POST',headers:{'X-CSRF-Token':csrf}}:{});renderModels(data);}
  catch(e){catalog=null;$('catalog-status').textContent=e.message;updateSubmit();}
  finally{$('refresh-models').disabled=false;}
}
async function loadHistory(){
  const [rows,runs]=await Promise.all([api('/api/conversations'),api('/api/runs')]);$('history').replaceChildren();
  if(!rows.length)$('history').textContent='Your saved conversations will appear here.';
  for(const r of rows){const b=document.createElement('button'),small=document.createElement('small');b.textContent=r.title;small.textContent=new Date((r.updated||r.created)*1000).toLocaleString()+' · '+r.turn_count+(r.turn_count===1?' message':' messages');b.append(small);b.onclick=()=>openConversation(r.id);$('history').append(b);}
  const legacy=runs.filter(r=>!r.conversation_id);$('legacy-reports').hidden=!legacy.length;$('legacy-history').replaceChildren();
  for(const r of legacy){const b=document.createElement('button');b.textContent=r.question.slice(0,90);b.onclick=()=>{newConversation();show(r.id);};$('legacy-history').append(b);}
}
function rememberConversation(id){
  const url=new URL(location.href);if(id)url.searchParams.set('conversation',id);else url.searchParams.delete('conversation');window.history.replaceState({},'',url);
}
function newConversation(){
  ++pollToken;conversationId='';rememberConversation('');busy=false;$('environment').disabled=false;$('transcript').replaceChildren();$('transcript').hidden=true;$('result').hidden=true;$('error').hidden=true;$('conversation-title').textContent='New conversation';$('conversation-meta').textContent='Ask a question, then continue with follow-ups in the same environment.';$('question').value='';$('question').placeholder='What would you like to investigate?';updateSubmit();
}
function renderConversation(c){
  $('conversation-title').textContent=c.title;$('conversation-meta').textContent='Saved conversation · '+c.environment+(c.tracing_enabled?' · APM trace: '+c.trace_id:' · APM tracing is off')+(c.has_earlier_turns?' · Showing the latest 100 interactions':'');
  $('environment').value=c.environment;$('environment').disabled=true;$('transcript').hidden=false;$('transcript').replaceChildren();$('result').hidden=true;
  for(const r of c.turns){
    const turn=document.createElement('article');turn.className='turn';const q=document.createElement('p');q.className='user-message';q.textContent=r.question;
    const meta=document.createElement('div');meta.className='turn-meta';meta.textContent='Message '+r.turn_index+' · '+r.status+(r.model?.label?' · '+r.model.label:'')+(r.utc_start?' · Evidence: '+r.utc_start+' → '+r.utc_end:'')+(c.tracing_enabled&&r.interaction_span_id?' · Span: '+r.interaction_span_id:'');
    if(r.routing?.mcp&&r.routing.mcp!=='auto')meta.textContent+=' · Source: '+(r.routing.mcp==='db'?'Database Observability MCP':'Log Analytics MCP')+(r.routing.tool!=='auto'?' · '+r.routing.tool:'');
    const answer=document.createElement('pre');answer.textContent=r.answer||'Collecting evidence…';turn.append(q,meta,answer);
    if(!['queued','running'].includes(r.status)){const a=document.createElement('a');a.href='/api/runs/'+r.id+'/report';a.textContent='Download this interaction and evidence timeline';turn.append(a);}
    if(r.events.length){const details=document.createElement('details'),summary=document.createElement('summary'),list=document.createElement('ol');summary.textContent='Evidence collection';for(const e of r.events){const li=document.createElement('li');li.textContent=e.server+' · '+(e.operation||e.tool)+' — '+e.outcome;list.append(li);}details.append(summary,list);turn.append(details);}
    $('transcript').append(turn);
  }
  $('question').placeholder='Ask a follow-up about this conversation…';
}
async function openConversation(id){
  const marker=++pollToken;conversationId=id;rememberConversation(id);$('error').hidden=true;
  while(marker===pollToken){
    try{
      const c=await api('/api/conversations/'+encodeURIComponent(id));if(marker!==pollToken)return;renderConversation(c);
      busy=c.turns.some(r=>['queued','running'].includes(r.status));updateSubmit();$('new-conversation').disabled=busy;
      if(!busy){await loadHistory();return;}await new Promise(resolve=>setTimeout(resolve,2500));
    }catch(e){$('error').textContent=e.message;$('error').hidden=false;busy=false;updateSubmit();return;}
  }
}
async function show(id){
  const marker=++pollToken;$('result').hidden=false;$('error').hidden=true;
  while(marker===pollToken){
    try{
      const r=await api('/api/runs/'+id);if(marker!==pollToken)return;
      $('status').textContent=r.status;$('run-question').textContent=r.question;
      $('run-model').textContent=r.model?.label?'Model: '+r.model.label+' · '+r.model.region:'Model not recorded for this older investigation.';
      $('answer').textContent=r.answer||'Collecting evidence. You can leave this page and return to the investigation later.';
      $('events').replaceChildren();for(const e of r.events){const li=document.createElement('li');li.textContent=`${e.server} · ${e.operation||e.tool} — ${e.outcome}${e.duration_seconds!==undefined?' · '+e.duration_seconds+' s':''}`;$('events').append(li);}
      const pending=['queued','running'].includes(r.status);busy=pending;updateSubmit();$('download').hidden=pending;$('download').href='/api/runs/'+id+'/report';
      if(!pending){await loadHistory();return;}
      await new Promise(resolve=>setTimeout(resolve,2500));
    }catch(e){$('error').textContent=e.message;$('error').hidden=false;busy=false;updateSubmit();return;}
  }
}
$('ask').onsubmit=async e=>{e.preventDefault();busy=true;updateSubmit();$('error').hidden=true;try{const r=await api('/api/runs',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({question:$('question').value,environment:$('environment').value,model:$('model').value,skill:$('skill').value,hours:Number($('hours').value),conversation_id:conversationId,preferred_mcp:$('preferred-mcp').value,preferred_tool:$('preferred-tool').value})});conversationId=r.conversation_id;$('question').value='';await loadHistory();await openConversation(conversationId);}catch(err){$('error').textContent=err.message;$('error').hidden=false;busy=false;updateSubmit();}};
$('new-conversation').onclick=()=>{newConversation();$('question').focus();};
$('model').onchange=()=>{try{localStorage.setItem('db-assistant-model',$('model').value);}catch{}updateSubmit();};
$('refresh-models').onclick=()=>loadModels(true);
document.querySelectorAll('[data-question]').forEach(b=>b.onclick=()=>{$('question').value=b.dataset.question;$('question').focus();});
$('logout').onclick=async()=>{await api('/auth/logout',{method:'POST',headers:{'X-CSRF-Token':csrf}});location.href='/';};
(async()=>{try{const me=await api('/api/me');csrf=me.csrf;$('configuration-link').hidden=!me.is_admin;$('identity').textContent=me.name;$('logout').hidden=false;$('welcome').hidden=true;$('workspace').hidden=false;$('demo').hidden=me.mode!=='demo';renderRoutingOptions(me.routing_options);environmentCount=me.environments.length;loadEnvironmentOptions(me.environments);$('denied').hidden=environmentCount>0;updateSubmit();await loadHistory();const resume=new URL(location.href).searchParams.get('conversation');if(resume)openConversation(resume);if(environmentCount)await loadModels();else $('catalog-status').textContent='Model access requires an assigned environment.';}catch(e){$('welcome').hidden=false;}})();
