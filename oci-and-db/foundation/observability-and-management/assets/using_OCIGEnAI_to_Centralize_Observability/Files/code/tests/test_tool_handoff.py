"""A tool-free plan must not silently terminate an operational workflow."""
import asyncio,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import oci
from assistant.agent import investigate
from assistant.settings import Settings
from assistant.store import Store
from assistant.policy import PolicyError,ToolPrerequisiteError
from test_conversations import ENV,USER,WINDOW,MODEL

m=oci.generative_ai_inference.models

def answer(text='',name=None,args=None):
    return m.AssistantMessage(content=[m.TextContent(text=text)] if text else [],tool_calls=[m.FunctionCall(id='call',name=name,arguments=json.dumps(args or {}))] if name else [])

class Clients:
    def __init__(self,*a):pass
    async def __aenter__(self):return self
    async def __aexit__(self,*a):pass

class HandoffTests(unittest.IsolatedAsyncioTestCase):
    async def test_top_sql_cannot_complete_with_logs_or_catalog_only(self):
        row,requests,executed=await self.run_agent([answer(name='log_query',args={'query':'* | stats count'}),answer(name='db_catalog')]+[answer('Top SQL is unavailable in the catalog.')]*5,question='Show the top SQL statement')
        self.assertEqual(row['status'],'partial')
        self.assertFalse(any(name=='log_query' for name,args in executed))
        self.assertIn('top-SQL ranking was not established',row['answer'])
        self.assertTrue(any(e.get('mcp')=='db' for e in row['events']))

    async def test_empty_reply_preserves_timeline_and_reports_model_failure(self):
        row,requests,executed=await self.run_agent([answer(name='log_query',args={'query':'* | stats count'}),answer()],selected='application-error-investigator',question='Check recent logs')
        self.assertEqual(row['status'],'partial')
        self.assertIn('selected model returned no answer',row['answer'])
        self.assertNotIn('authentication',row['answer'])
        self.assertEqual(len(executed),1)
        self.assertEqual(row['events'][-1]['error_code'],'empty_model_response')

    async def run_agent(self,responses,selected='observability-coverage-checker',denied=False,question='Check monitoring coverage'):
        requests=[];executed=[]
        class Model:
            def __init__(self,*a,**kw):pass
            def message(self,role,text,tool_call_id=None):
                cls={'SYSTEM':m.SystemMessage,'USER':m.UserMessage,'ASSISTANT':m.AssistantMessage,'TOOL':m.ToolMessage}[role]
                return cls(content=[m.TextContent(text=text)],**({'tool_call_id':tool_call_id} if tool_call_id else {}))
            async def chat(self,messages,definitions,require_tools=False):
                requests.append(require_tools)
                return responses.pop(0) if responses else answer('I will now begin.')
        class Gateway:
            def __init__(self,clients,env,window,audit,**kw):self.audit=audit;self.empty_cpu_trend=False
            async def execute(self,name,args):
                executed.append((name,args))
                if args.get('operation')=='summarize_database_insight_resource_usage_trend':self.empty_cpu_trend=True
                if denied:raise PolicyError('Access denied')
                if name!='db_catalog':self.audit({'server':'logan' if name=='log_query' else 'db','tool':'run_query' if name=='log_query' else 'invoke_dbo_tool','outcome':'ok'})
                return json.dumps({'observed':True})
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'access.json').write_text(json.dumps({'environments':{'lab':ENV}}));(p/'mcp.json').write_text(json.dumps({'logan':{}}))
            settings=Settings(mode='live',config_dir=p,data_dir=p/'data');store=Store(p/'data/a.sqlite3')
            rid=store.create_run('alice','lab',question,30,MODEL,compartment_id=ENV['compartment_id'],window=WINDOW)
            with patch('assistant.agent.OCIModel',Model),patch('assistant.agent.MCPClients',Clients),patch('assistant.agent.Gateway',Gateway):
                await investigate(settings,store,rid,USER,ENV,question,selected,WINDOW,asyncio.Semaphore(1),MODEL)
            return store.get(rid,'alice'),requests,executed

    async def test_plan_then_partial_coverage_continues_until_all_branches(self):
        responses=[answer('I will check the logs. Plan: I will now begin.'),answer(name='log_query',args={'query':'* | stats count'}),answer('Logs observed.'),answer(name='db_catalog')]
        for op in ['list_managed_databases','list_database_insights','list_host_insights']:
            responses.append(answer(name='db_read',args={'operation':op,'arguments':{}}))
        responses.append(answer('Database and log coverage observed.'))
        row,requests,executed=await self.run_agent(responses)
        self.assertEqual(row['status'],'complete');self.assertEqual(len(executed),5)
        self.assertEqual(sum(requests),2)

    async def test_auto_plan_after_skill_is_continued(self):
        row,requests,_=await self.run_agent([answer(name='load_skill',args={'name':'application-error-investigator'}),answer('I will now begin.'),answer(name='log_query',args={'query':'* | stats count'}),answer('Observed 24 records.')],selected='auto',question='Count alert log records')
        self.assertEqual(row['status'],'complete');self.assertIn(True,requests)

    async def test_repeated_plans_are_bounded_and_never_marked_complete(self):
        row,requests,_=await self.run_agent([])
        self.assertEqual(len(requests),4);self.assertEqual(row['status'],'partial')
        self.assertIn('Coverage checks not completed',row['answer'])

    async def test_explicit_denial_does_not_force_retry(self):
        row,requests,executed=await self.run_agent([answer(name='log_query',args={'query':'* | stats count'}),answer('Access is denied.')],denied=True)
        self.assertEqual(len(executed),1);self.assertFalse(any(requests));self.assertEqual(row['status'],'partial')

    async def test_explanation_without_plan_does_not_force_tools(self):
        row,requests,executed=await self.run_agent([answer('Monitoring coverage describes which resources send telemetry.')],selected='auto',question='Explain telemetry')
        self.assertEqual(len(requests),1);self.assertEqual(executed,[])

    async def test_cpu_followup_does_not_inherit_broad_coverage_requirements(self):
        row,requests,executed=await self.run_agent([answer(name='db_read',args={'operation':'list_managed_databases','arguments':{}}),answer(name='db_read',args={'operation':'get_database_home_metrics','arguments':{'managed_database_id':'ocid1.database.test'}}),answer('Reported CPU utilization: 1 percent for the measured database.')],question='which is the most utilized DB?')
        self.assertEqual(row['status'],'complete');self.assertFalse(any(requests))
        self.assertNotIn('log_query',row['answer']);self.assertNotIn('list_host_insights',row['answer'])

    async def test_cpu_claim_without_any_metric_read_is_not_accepted(self):
        row,requests,executed=await self.run_agent([answer('CPU data is unavailable. No data returned.')]*4,question='Show CPU utilization')
        self.assertEqual(row['status'],'partial');self.assertIn('CPU measurements were not retrieved',row['answer'])
        self.assertEqual(sum(requests),3)

    def test_discovery_prerequisites_are_correctable_not_permission_denials(self):
        from assistant.agent import tool_failure
        f=tool_failure(ToolPrerequisiteError('Load the catalog'))
        self.assertEqual(f['error'],'missing_prerequisite');self.assertTrue(f['correctable'])

    async def test_empty_opsi_trend_requires_database_management_path(self):
        row,requests,executed=await self.run_agent([
            answer(name='db_read',args={'operation':'list_managed_databases','arguments':{}}),
            answer(name='db_read',args={'operation':'summarize_database_insight_resource_usage_trend','arguments':{'resource_metric':'CPU'}}),
            answer('All databases have no CPU data.'),
            answer(name='db_read',args={'operation':'get_database_home_metrics','arguments':{'managed_database_id':'ocid1.database.test'}}),
            answer('Database Management returned CPU samples.')],question='Which DB is most utilized?')
        self.assertEqual(row['status'],'complete');self.assertIn(True,requests)
        self.assertEqual(executed[-1][1]['operation'],'get_database_home_metrics')
