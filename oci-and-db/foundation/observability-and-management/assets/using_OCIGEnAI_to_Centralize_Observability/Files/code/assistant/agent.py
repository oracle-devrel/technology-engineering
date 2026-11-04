import asyncio
import json
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from contextlib import AsyncExitStack
from pathlib import Path

from jsonschema import validate, ValidationError

from .gateway import Gateway, TOOLS, DB_OPERATIONS
from .mcp_client import MCPClients, MCPToolError
from .model import OCIModel, ModelResponseError
from .policy import authorize_environment, redact, PolicyError, QueryValidationError, ToolPrerequisiteError
from .settings import ROOT
from .telemetry import traced,interaction
from .routing import route,permit_call,exposed_tools
from .connections import ConnectionRegistry,ConnectionError as RegistryConnectionError,environment_binding,environment_sources
from opentelemetry.trace import Status,StatusCode


SKILL_NAMES = {'observability-coverage-checker','application-error-investigator','oracle-incident-correlator','database-sql-performance'}


def tool_failure(exc):
    """Return actionable, bounded feedback without returning provider bodies or credentials."""
    if isinstance(exc, QueryValidationError):
        return {'error':'invalid_log_query','message':str(exc),'correctable':True}
    if isinstance(exc, ToolPrerequisiteError):
        return {'error':'missing_prerequisite','message':str(exc),'correctable':True}
    if isinstance(exc, (ValidationError,json.JSONDecodeError)):
        return {'error':'invalid_tool_arguments','message':'Arguments must match the exposed tool schema. log_query accepts only query and max_results; the application supplies compartment and time boundaries. Correct the arguments before retrying.','correctable':True}
    if isinstance(exc, PolicyError):
        return {'error':'scope_denied','message':str(exc),'correctable':False}
    if isinstance(exc, MCPToolError):
        return {'error':exc.category,'message':str(exc),'correctable':exc.category=='query_rejected'}
    return {'error':'operation_failed','message':'The operation failed. A policy or IAM denial has not been established. Preserve independent evidence and report the affected branch as unavailable.','correctable':False}


@traced(lambda name:'skill.'+(name if name in SKILL_NAMES else 'unapproved'),lambda name:{'skill.name':name if name in SKILL_NAMES else 'unapproved'})
def skill(name):
    if name not in SKILL_NAMES:
        raise ValueError('Unknown skill')
    return (ROOT/'skills'/name/'SKILL.md').read_text()


async def investigate(settings, store, rid, user, env, question, selected, window, semaphore, model_selection=None):
    row=store.get(rid,user['sub'])
    if not row:raise PolicyError('Investigation not found')
    row=dict(row);row.setdefault('id',rid)
    previous=store.context(rid,user['sub']) if hasattr(store,'context') else []
    with interaction(row,store) as current:
        current.set_attribute('context.turns',len(previous))
        await _investigate(settings,store,rid,user,env,question,selected,window,semaphore,model_selection,previous)
        result=store.get(rid,user['sub'])
        status=result.get('status','unknown') if result else 'unknown'
        current.set_attribute('interaction.status',status)
        if status in {'failed','interrupted'}:current.set_status(Status(StatusCode.ERROR,status))


async def _investigate(settings, store, rid, user, env, question, selected, window, semaphore, model_selection=None, previous=None):
    events = []
    def audit(event):
        if event is not None:
            events.append(event)
        store.update(rid, events=events)
    try:
        async with semaphore:
            store.update(rid,status='running')
            preference=store.get(rid,user['sub']).get('routing',{})
            routing=route(question,preference.get('preference_mcp','auto'),preference.get('tool','auto'),DB_OPERATIONS,selected)
            sources=environment_sources(env)
            if routing['mcp']!='auto' and routing['mcp'] not in sources:
                store.update(rid,status='partial',answer='The requested MCP is not assigned to this environment. Ask the configuration administrator to assign and test it.')
                return
            if routing['mcp']=='auto' and len(sources)==1:routing['mcp']=next(iter(sources))
            audit({'server':'assistant','tool':'routing_selected','outcome':'ok','mcp':routing['mcp'],'preferred_tool':routing['tool'],'reason':'SQL performance requires database evidence' if routing['sql'] else 'User source preference or automatic routing'})
            if routing['conflict']:
                store.update(rid,status='partial',answer='Top SQL statements require Database Observability MCP. Log Analytics cannot rank database statements. Select Choose for me or Database Observability MCP and submit again.')
                return
            active_tools=exposed_tools(TOOLS,routing)
            if routing['sql']:selected='database-sql-performance'
            if settings.mode == 'demo':
                label = model_selection['label'] if model_selection else 'Configured OCI model'
                store.update(rid,status='complete',answer=f'DEMONSTRATION — no OCI or MCP calls were made.\n\nSelected model: {label}.\nPrevious interactions in context: {len(previous or [])}.\n\nThe portal has accepted your question and selected environment. Configure company sign-in, a tool-capable OCI model, and the MCP runtimes to investigate live data. This message is not a health assessment.')
                return
            async with asyncio.timeout(900):
                model = OCIModel(settings,selection=model_selection)
                home = settings.data_dir/'mcp-runs'/rid
                mcp_config = settings.load('mcp.json')
                if 'logan' in mcp_config:mcp_config['logan'].setdefault('env',{})['OCI_LA_COMPARTMENT'] = env['compartment_id']
                async with AsyncExitStack() as session_stack:
                    if env.get('connection_refs') is not None:
                        mcp_config=session_stack.enter_context(ConnectionRegistry(settings).runtime_config(mcp_config,env,home))
                    clients=await session_stack.enter_async_context(MCPClients(mcp_config,home))
                    environment_key = store.get(rid,user['sub'])['environment']
                    def check_environment():
                        current=authorize_environment(settings.load('access.json'),user,environment_key)
                        if current['compartment_id']!=env['compartment_id'] or environment_binding(current)!=environment_binding(env):
                            raise PolicyError('The environment or its MCP connections changed during this interaction. Start a new conversation.')
                        return current
                    gateway = Gateway(clients,env,window,audit,
                        authorize=check_environment)
                    if routing['sql']:gateway.catalog_focus='sql'
                    instructions = (ROOT/'prompts'/'system.md').read_text()
                    scope = {'environment':env['label'],'compartment':env['compartment_id'],'utc_start':window[0],'utc_end':window[1],'display_timezone':'Europe/Rome'}
                    scope['local_start']=datetime.fromisoformat(window[0]).astimezone(ZoneInfo('Europe/Rome')).isoformat()
                    scope['local_end']=datetime.fromisoformat(window[1]).astimezone(ZoneInfo('Europe/Rome')).isoformat()
                    messages = [model.message('SYSTEM',instructions+'\nTrusted run scope: '+json.dumps(scope))]
                    messages.append(model.message('SYSTEM','Trusted source selection for this message: '+json.dumps(routing)+'. Use the preferred operation as the requested destination after its required discovery steps. Never substitute logs for SQL rankings. An unavailable requested operation is a limitation, not permission to invent another data source.'))
                    loaded = selected != 'auto'
                    if loaded:
                        messages.append(model.message('SYSTEM',skill(selected)))
                    for turn in previous or []:
                        label=f"Historical conversation turn {turn['turn_index']}; UTC evidence window {turn['utc_start']} to {turn['utc_end']}; status {turn['status']}. This is prior context, not fresh evidence."
                        messages.append(model.message('USER',label+'\n'+turn['question']))
                        messages.append(model.message('ASSISTANT',turn['answer']))
                    messages.append(model.message('USER',question))
                    check_failed = False
                    hard_blocked = False
                    pending_inputs = {}
                    tool_count = 0
                    continuations = 0
                    require_tools = False
                    continuation_tools = active_tools
                    # A selected skill guides this turn; it must not carry an old
                    # coverage question's obligations into a CPU/ranking follow-up.
                    coverage = bool(re.search(r'\b(?:coverage|stale|missing|collection gaps|monitoring gaps)\b',question,re.I))
                    cpu_question = not routing['sql'] and bool(re.search(r'\b(?:cpu|utili[sz](?:ed|ation)|busiest)\b',question,re.I))
                    cpu_ranking = cpu_question and bool(re.search(r'\b(?:most|highest|busiest|rank|compare|top)\b',question,re.I))
                    attempted = set()
                    metric_reads = set()
                    for _ in range(settings.max_calls):
                        current_env=check_environment()
                        if current_env['compartment_id']!=env['compartment_id']:
                            raise PolicyError('The environment scope changed during this interaction')
                        answer = await model.chat(messages,continuation_tools,require_tools=True) if require_tools else await model.chat(messages,active_tools)
                        require_tools = False
                        calls = answer.tool_calls or []
                        messages.append(answer)
                        if not calls:
                            text = '\n'.join(c.text for c in (answer.content or []) if hasattr(c,'text'))
                            if not text.strip():
                                raise ModelResponseError('empty_model_response')
                            evidence = any(e['outcome']=='ok' and ((e['server']=='logan' and e['tool']=='run_query') or (e['server']=='db' and e['tool']=='invoke_dbo_tool')) for e in events)
                            required = {'log_query','list_managed_databases','list_database_insights','list_host_insights'} if coverage and not routing['sql'] and routing['mcp']=='auto' else set()
                            missing = required-attempted
                            if routing['sql'] and not getattr(gateway,'sql_report_observed',False):missing.add('verified SQL ranking sections from get_awr_db_report after managed-database and AWR snapshot discovery')
                            if routing['tool'] not in {'auto','db_catalog'} and routing['tool'] not in attempted:missing.add('preferred operation '+routing['tool'])
                            if cpu_question:
                                if not metric_reads:
                                    missing.add('CPU metric read (get_database_home_metrics or a scoped CPU usage trend)')
                                elif getattr(gateway,'empty_cpu_trend',False) and 'get_database_home_metrics' not in attempted:
                                    missing.add('get_database_home_metrics for supported managed databases; the empty OPSI aggregate does not establish absent CPU data')
                            if cpu_ranking:
                                if 'list_managed_databases' not in attempted:
                                    missing.add('list_managed_databases to establish the comparison population')
                                elif hasattr(gateway,'managed_resources'):
                                    for ident,resource in gateway.managed_resources.items():
                                        if resource['subtype'] in {'CDB','ADB'} and ident not in gateway.home_metric_attempts:
                                            missing.add('get_database_home_metrics for '+resource['name']+' ('+ident+') using the trusted window')
                            planning = bool(re.search(r"\b(?:I will|I'll|I shall|let me|now begin|next I|plan)\b",text,re.I))
                            # A plan is not a completed investigation. Ask for actual calls,
                            # bounded independently of the existing round/call/time limits.
                            # Stop on genuine access/transport failures rather than forcing retries.
                            if continuations < 3 and not hard_blocked and (missing or (not evidence and (selected != 'auto' or planning))):
                                continuations += 1
                                audit({'server':'assistant','tool':'workflow_continue','started':datetime.now(timezone.utc).isoformat(),'outcome':'ok','reason':'evidence_checks_pending'})
                                todo=', '.join(sorted(missing)) if missing else 'the requested operational evidence'
                                messages.append(model.message('SYSTEM','The preceding text is a plan, not a final report. Execute the pending checks now: '+todo+'. Load the appropriate skill if needed; use db_catalog before db_read and follow its schemas. Use actual tool calls, not descriptions of calls. Do not repeat a failed operation. After the checks, report only observed evidence and explicit limitations.'))
                                continuation_tools=active_tools
                                remaining=[ident for ident,resource in getattr(gateway,'managed_resources',{}).items() if resource['subtype'] in {'CDB','ADB'} and ident not in gateway.home_metric_attempts]
                                if cpu_ranking and remaining:
                                    # Constrain the next call to the missing approved
                                    # reads, preventing a small model from repeatedly
                                    # measuring the same DB or inventing tool names.
                                    definition=json.loads(json.dumps(next(t for t in TOOLS if t['name']=='db_read')))
                                    definition['parameters']['properties']['operation']['enum']=['get_database_home_metrics']
                                    definition['parameters']['properties']['arguments']={'type':'object','properties':{
                                        'managed_database_id':{'type':'string','enum':remaining},
                                        'start_time':{'type':'string','enum':[window[0]]},
                                        'end_time':{'type':'string','enum':[window[1]]}},
                                        'required':['managed_database_id','start_time','end_time'],'additionalProperties':False}
                                    continuation_tools=[definition]
                                require_tools = True
                                continue
                            if missing:
                                if routing['sql']:
                                    text = 'The requested top-SQL ranking was not established. Database inventory or catalog discovery is not statement-performance evidence. Review the timeline for AWR availability or snapshot-window limitations.'
                                if cpu_question and not metric_reads:
                                    text = 'CPU measurements were not retrieved successfully in this interaction. No utilization ranking or per-database no-data conclusion is established.'
                                elif cpu_ranking:
                                    text = 'The database CPU comparison is incomplete. Some evidence was retrieved, but a compartment-wide most-utilized database has not been established. Review the tool timeline and the missing checks below.'
                                text += '\n\nCoverage checks not completed: '+', '.join(sorted(missing))+'. These branches remain unverified.'
                            if not evidence:
                                text += '\n\nNo operational evidence was retrieved in this run. Current resource health is unverified.'
                            partial = check_failed or not evidence or bool(missing) or bool(pending_inputs) or getattr(gateway,'sql_report_partial',False) or any(e['outcome'] not in {'ok','corrected'} for e in events)
                            store.update(rid,status='partial' if partial else 'complete',answer=redact(text))
                            return
                        for call in calls:
                            tool_count += 1
                            if tool_count > 24:
                                store.update(rid,status='partial',answer='The tool-call limit was reached. Narrow the question and review the available timeline; no complete conclusion was produced.')
                                return
                            first_event = len(events)
                            try:
                                definition = next((x for x in TOOLS if x['name']==call.name),None)
                                if definition is None:
                                    if call.name in DB_OPERATIONS:
                                        raise ToolPrerequisiteError('That is an operation name, not a tool name. Call db_read with operation="'+call.name+'" and the operation inputs nested under arguments.')
                                    raise PolicyError('That tool is not exposed by this assistant.')
                                args = json.loads(call.arguments)
                                validate(args,definition['parameters'])
                                permit_call(routing,call.name,args)
                                if call.name == 'load_skill':
                                    value = skill(args['name'])
                                    loaded = True
                                elif not loaded:
                                    value = json.dumps({'error':'Load the appropriate skill before calling evidence tools.'})
                                else:
                                    attempted.add(args['operation'] if call.name=='db_read' else call.name)
                                    value = await gateway.execute(call.name,args)
                            except Exception as exc:
                                failure = tool_failure(exc)
                                if failure['correctable']:
                                    for event in events[first_event:]:
                                        if event['outcome']=='failed':event['outcome']='input_error'
                                else:
                                    check_failed = True
                                    hard_blocked = hard_blocked or failure['error'] in {'scope_denied','permission_denied','authentication_failed'}
                                audit({'server':'assistant','tool':call.name if definition else 'unapproved',
                                    'started':datetime.now(timezone.utc).isoformat(),
                                    'outcome':'input_error' if failure['correctable'] else 'failed',
                                    'error_code':failure['error'],'error_reason':failure['message']})
                                if failure['correctable']:
                                    pending_inputs.setdefault('db_read' if call.name in DB_OPERATIONS else call.name,[]).extend(range(first_event,len(events)))
                                value = json.dumps(failure)
                            else:
                                if call.name=='db_read' and (args['operation']=='get_database_home_metrics' or (args['operation']=='summarize_database_insight_resource_usage_trend' and args['arguments'].get('resource_metric')=='CPU')):
                                    metric_reads.add(args['operation'])
                                for index in pending_inputs.pop(call.name,[]):
                                    if events[index]['outcome']=='input_error':events[index]['outcome']='corrected'
                                audit(None)
                            messages.append(model.message('TOOL',value,call.id))
                    store.update(rid,status='partial',answer='The investigation reached its tool-round limit. Review the tool timeline and narrow the question. No complete conclusion was produced.')
    except TimeoutError:
        store.update(rid,status='partial',answer='The investigation exceeded 15 minutes. Some checks may have completed; inspect the timeline. Current health is not established.')
    except asyncio.CancelledError:
        store.update(rid,status='interrupted',answer='The investigation was interrupted. Submit the question again when the service is available.')
        raise
    except ModelResponseError:
        audit({'server':'assistant','tool':'model_response','started':datetime.now(timezone.utc).isoformat(),'outcome':'error','error_code':'empty_model_response'})
        store.update(rid,status='partial',answer='The selected model returned no answer text or tool call after one recovery attempt. Some checks may have completed; inspect the tool timeline. Retry the question or choose another OCI-hosted model. No health conclusion was produced.')
    except RegistryConnectionError as exc:
        store.update(rid,status='partial',answer=str(exc)+' No monitoring conclusion was produced.')
    except Exception as exc:
        store.update(rid,status='failed',answer=f'The investigation could not finish ({type(exc).__name__}). Check the configured model, authentication and MCP connectivity. No health conclusion is available.')
