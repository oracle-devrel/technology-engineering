const $=id=>document.getElementById(id);
let csrf='',state=null,stopped=false,connectionBusy=false,environmentBusy=false,notice='';
async function api(path,options={}){
 const response=await fetch(path,{credentials:'same-origin',...options});const body=await response.json().catch(()=>({}));
 if(!response.ok)throw new Error(typeof body.detail==='string'?body.detail:'The configuration request failed.');return body;
}
function fail(error){$('configuration-error').textContent=error.message;$('configuration-error').hidden=false;}
function write(path,body,method='POST'){return api(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)});}
function showFields(){
 const key=$('connection-auth').value==='api_key',remote=$('connection-transport').value==='https',logan=$('connection-kind').value==='logan';
 $('api-key-fields').hidden=!key;$('https-fields').hidden=!remote;$('profile-fields').hidden=key;$('namespace-fields').hidden=!logan;
 $('save-connection').textContent=remote?'Save & test connection':'Save, start & test';
 for(const field of ['tenancy_id','user_id','private_key'])$('connection-form').elements[field].required=key;
 $('connection-form').elements.url.required=remote;$('connection-form').elements.namespace.required=logan;
}
function optionList(select,kind,selected){
 select.replaceChildren();const none=document.createElement('option');none.value='';none.textContent='Not assigned';select.append(none);
 for(const c of state.connections.filter(c=>c.kind===kind&&c.enabled&&c.status==='ready')){const option=document.createElement('option');option.value=c.id;option.textContent=c.label+' · '+c.region;select.append(option);}
 select.value=[...select.options].some(o=>o.value===selected)?selected:'';
}
function button(label,action){const b=document.createElement('button');b.type='button';b.className='quiet';b.textContent=label;b.onclick=()=>Promise.resolve(action()).catch(fail);return b;}
function render(){
 $('configuration-state').textContent=notice||(state.demo?'Demo mode: connections cannot be started.':state.credentials_ready?'Configuration available · managed MCPs start on demand.':'Secure credential storage is not configured. An operator must supply CONNECTION_ENCRYPTION_KEY.');
 $('save-connection').disabled=connectionBusy||state.demo||!state.credentials_ready;$('save-environment').disabled=environmentBusy||state.demo||!state.credentials_ready;
 const profiles=$('connection-profile'),selected=profiles.value;profiles.replaceChildren();for(const name of state.profiles){const o=document.createElement('option');o.value=name;o.textContent=name;profiles.append(o);}if(state.profiles.includes(selected))profiles.value=selected;
 $('connections').replaceChildren();if(!state.connections.length)$('connections').textContent='No additional connections yet. The existing deployment connections continue to serve their current environments.';
 for(const c of state.connections){
  const item=document.createElement('div');item.className='configuration-item';const title=document.createElement('strong');title.textContent=c.label+' · '+(c.kind==='db'?'Database Observability':'LogAn');
  const status=document.createElement('p');status.className='status-'+c.status;status.textContent=(c.enabled?c.status:'disabled')+' · '+(c.transport==='managed'?'Bundled MCP · starts on demand':'HTTPS MCP')+' · '+c.region;
  const scope=document.createElement('p');scope.textContent='Tenancy: '+c.tenancy_id+' · Test compartment: '+c.test_compartment_id;
  item.append(title,status,scope);if(c.last_error){const error=document.createElement('p');error.textContent=c.last_error;item.append(error);}
  const actions=document.createElement('div');actions.className='configuration-actions';const test=button('Test connection',async()=>{await write('/api/admin/connections/'+c.id+'/test',{});await refresh();});test.disabled=!c.enabled||state.demo;
  actions.append(test,button(c.enabled?'Disable':'Enable',async()=>{await write('/api/admin/connections/'+c.id+'/enabled',{enabled:!c.enabled});await refresh();}));item.append(actions);$('connections').append(item);
 }
 optionList($('environment-db'),'db',$('environment-db').value);optionList($('environment-logan'),'logan',$('environment-logan').value);
 $('configured-environments').replaceChildren();if(!state.environments.length)$('configured-environments').textContent='Assign a tested connection to create a selectable environment.';
 for(const e of state.environments){const item=document.createElement('div');item.className='configuration-item';const title=document.createElement('strong');title.textContent=e.label+(e.enabled?'':' · disabled');const text=document.createElement('p');text.textContent=e.compartment_name+' · '+e.region+' · '+e.compartment_id;item.append(title,text,button('Edit assignment',()=>editEnvironment(e)));if(e.enabled)item.append(button('Disable environment',async()=>{await write('/api/admin/environments/'+e.id+'/disable',{});await refresh();}));$('configured-environments').append(item);}
}
async function refresh(){state=await api('/api/admin/configuration');render();}
function editEnvironment(e){const form=$('environment-form');form.elements.id.value=e.id;form.elements.label.value=e.label;form.elements.compartment_id.value=e.compartment_id;form.elements.subjects.value=e.subjects.join('\n');form.elements.groups.value=e.groups.join('\n');optionList($('environment-db'),'db',e.connection_refs.db||'');optionList($('environment-logan'),'logan',e.connection_refs.logan||'');form.scrollIntoView({behavior:'smooth',block:'start'});}
for(const id of ['connection-kind','connection-transport','connection-auth'])$(id).onchange=showFields;
$('connection-form').onsubmit=async event=>{
 event.preventDefault();connectionBusy=true;render();$('configuration-error').hidden=true;
 const form=event.currentTarget,body=Object.fromEntries(new FormData(form));
 if(body.auth_mode==='existing_profile')for(const k of ['tenancy_id','user_id','fingerprint','private_key','key_passphrase'])delete body[k];
 if(body.transport==='managed'){delete body.url;delete body.bearer_token;}if(body.kind!=='logan')delete body.namespace;
 try{await write('/api/admin/connections',body);for(const k of ['private_key','key_passphrase','bearer_token'])form.elements[k].value='';form.elements.label.value='';await refresh();}
 catch(error){fail(error);}finally{connectionBusy=false;render();}
};
$('environment-form').onsubmit=async event=>{
 event.preventDefault();environmentBusy=true;render();$('configuration-error').hidden=true;
 const form=event.currentTarget,body=Object.fromEntries(new FormData(form)),identifier=body.id;delete body.id;
 body.subjects=body.subjects.split('\n').map(x=>x.trim()).filter(Boolean);body.groups=body.groups.split('\n').map(x=>x.trim()).filter(Boolean);
 try{await write('/api/admin/environments'+(identifier?'/'+identifier:''),body,identifier?'PUT':'POST');notice='Environment verified and saved. Return to conversations and start a new conversation to select it.';await refresh();}
 catch(error){fail(error);}finally{environmentBusy=false;render();}
};
$('new-environment').onclick=()=>{$('environment-form').reset();$('configured-environment-id').value='';$('environment-subjects').value=state.subject;};
(async()=>{try{const me=await api('/api/me');if(!me.is_admin)throw new Error('Configuration administrator access is required.');csrf=me.csrf;await refresh();$('environment-subjects').value=state.subject;$('configuration-workspace').hidden=false;showFields();}
 catch(error){fail(error);$('configuration-state').textContent='Configuration is unavailable for this sign-in.';stopped=true;}})();
setInterval(()=>{if(!stopped&&state&&!document.hidden&&!connectionBusy&&!environmentBusy&&state.connections.some(c=>c.status==='pending'))refresh().catch(fail);},4000);
