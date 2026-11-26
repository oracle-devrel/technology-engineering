import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from jsonschema import ValidationError

from assistant.gateway import Gateway
from assistant.policy import PolicyError, authorize_environment, bound_arguments, redact, safe_query
from assistant.settings import Settings
from assistant.web import create_app
from assistant.models import ModelCatalog


CID='ocid1.compartment.oc1..lab'
OTHER='ocid1.compartment.oc1..other'
ENV={'label':'Lab','compartment_name':'Lab','compartment_id':CID,'groups':['dbas'],'subjects':[]}
POLICY={'environments':{'lab':ENV}}


class PolicyTests(unittest.TestCase):
    def test_user_cannot_select_unassigned_environment(self):
        with self.assertRaises(PolicyError):
            authorize_environment(POLICY,{'sub':'alice','groups':['finance']},'lab')

    def test_hierarchy_only_exposes_authorized_parents_and_breaks_cycles(self):
        from assistant.policy import environment_options
        def env(label,cid,parent=None,groups=['dbas']):return {**ENV,'label':label,'compartment_id':cid,'parent_compartment_id':parent,'groups':groups}
        policy={'environments':{'root':env('Visible root','ocid1.compartment.root'),
            'lab':env('Lab',CID,'ocid1.compartment.root'),
            'secret':env('Secret parent','ocid1.compartment.secret',groups=['finance']),
            'orphan':env('Allowed child','ocid1.compartment.child','ocid1.compartment.secret')}}
        rows=environment_options(policy,{'sub':'alice','groups':['dbas']})
        by_id={r['id']:r for r in rows}
        self.assertEqual(by_id['lab']['parent_id'],'root');self.assertIsNone(by_id['orphan']['parent_id'])
        self.assertNotIn('Secret parent',json.dumps(rows));self.assertNotIn('ocid1.compartment.secret',json.dumps(rows))
        policy['environments']['root']['parent_compartment_id']=CID
        cyclic=environment_options(policy,{'sub':'alice','groups':['dbas']})
        self.assertTrue(any(r['parent_id'] is None for r in cyclic if r['id'] in {'lab','root'}))

    def test_nested_scope_and_subtree_cannot_bypass_policy(self):
        for args in [{'filter':{'compartment_id':OTHER}},{'compartment_id_in_subtree':True},{'scope':'tenancy'}]:
            with self.assertRaises(PolicyError):
                bound_arguments(args,CID,{'compartment_id':{}})
        self.assertEqual(bound_arguments({},CID,{'compartment_id':{}})['compartment_id'],CID)

    def test_write_query_stage_and_oauth_token_redaction(self):
        with self.assertRaises(PolicyError):
            safe_query("* | export data")
        self.assertNotIn('secret',redact('GET /callback?code=secret&state=secret'))

    def test_live_cannot_use_example_credentials(self):
        s=Settings(mode='live',base_url='https://assistant.example.com',issuer='https://id.example.com',client_id='REPLACE_ME',client_secret='secret',model_id='model',genai_compartment=CID,session_secret='x'*40)
        with self.assertRaises(ValueError): s.validate()


class FakeMCP:
    def __init__(self):
        self.sessions={'logan':True}
        self.calls=[]
    async def call(self,server,tool,args):
        self.calls.append((server,tool,args))
        if server=='identity': return {'id':CID,'name':'Lab'}
        return {'data':{'rows':[]}}


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def test_revoked_grant_blocks_the_next_mcp_call(self):
        m=FakeMCP()
        def revoked(): raise PolicyError('Revoked')
        g=Gateway(m,ENV,('a','b'),lambda e:None,authorize=revoked)
        with self.assertRaises(PolicyError): await g.log_query({'query':'* | head 1'})
        self.assertEqual(m.calls,[])

    async def test_log_scope_is_forced_by_gateway(self):
        m=FakeMCP(); g=Gateway(m,ENV,('2026-10-01T00:00:00+00:00','2026-10-01T01:00:00+00:00'),lambda e:None)
        await g.execute('log_query',{'query':"namespace = 'test' | stats count",'max_results':10})
        call=m.calls[-1]
        self.assertEqual(call[2]['compartment_id'],CID)
        self.assertIs(call[2]['include_subcompartments'],False)
        self.assertEqual(call[2]['scope'],'default')
        self.assertEqual(m.calls[0][0],'identity')

    async def test_unknown_database_and_mutating_tools_are_blocked(self):
        m=FakeMCP();g=Gateway(m,ENV,('2026-10-01T00:00:00+00:00','2026-10-01T01:00:00+00:00'),lambda e:None)
        with self.assertRaises(PolicyError): await g.execute('restart_database',{})
        with self.assertRaises(PolicyError): await g.db_read({'operation':'get_managed_database','arguments':{'managed_database_id':'ocid1.database.foreign'}})
        g.contracts['get_managed_database']={'inputSchema':{'type':'object','properties':{'managed_database_id':{'type':'string'}},'required':['managed_database_id'],'additionalProperties':False}}
        with self.assertRaises(PolicyError): await g.db_read({'operation':'get_managed_database','arguments':{'managed_database_id':'ocid1.database.foreign'}})
        self.assertFalse(any(tool=='invoke_dbo_tool' for _,tool,_ in m.calls))

    async def test_opsi_trends_require_insight_discovery_and_absolute_window(self):
        from assistant.policy import ToolPrerequisiteError
        g=Gateway(FakeMCP(),ENV,('2026-10-01T00:00:00+00:00','2026-10-01T01:00:00+00:00'),lambda e:None)
        op='summarize_database_insight_resource_usage_trend'
        g.contracts[op]={'inputSchema':{'type':'object','properties':{'resource_metric':{'type':'string'},'analysis_time_interval':{'type':'string'}}}}
        with self.assertRaises(ToolPrerequisiteError):await g.db_read({'operation':op,'arguments':{'resource_metric':'CPU'}})
        g.inventories_read.add('list_database_insights')
        with self.assertRaises(ToolPrerequisiteError):await g.db_read({'operation':op,'arguments':{'resource_metric':'CPU','analysis_time_interval':'P30D'}})

    async def test_home_metrics_use_utc_milliseconds_rounded_inside_scope(self):
        from datetime import datetime,timedelta,timezone
        from assistant.policy import timestamps
        m=FakeMCP();g=Gateway(m,ENV,('2026-10-01T00:00:00+00:00','2026-10-01T03:00:00+00:00'),lambda e:None)
        ident='ocid1.database.test';g.known_ids.add(ident)
        g.contracts['get_database_home_metrics']={'inputSchema':{'type':'object','properties':{'managed_database_id':{'type':'string'},'start_time':{'type':'string'},'end_time':{'type':'string'}}}}
        with patch('assistant.gateway.datetime') as clock:
            clock.now.return_value=datetime(2026,10,1,3,tzinfo=timezone.utc)
            clock.fromisoformat.side_effect=datetime.fromisoformat
            r=await g.db_read({'operation':'get_database_home_metrics','arguments':{'managed_database_id':ident,'start_time':'2026-10-01T00:00:00.123456+00:00','end_time':'2026-10-01T02:00:00.123456+00:00'}})
        args=m.calls[-1][2]['arguments']
        self.assertEqual(args['start_time'],'2026-10-01T00:00:00.124Z')
        self.assertEqual(args['end_time'],'2026-10-01T02:00:00.123Z')
        self.assertEqual(r['effective_window']['start'],args['start_time'])
        start,end=timestamps(1)
        self.assertEqual(datetime.fromisoformat(end)-datetime.fromisoformat(start),timedelta(hours=1))
        self.assertRegex(start,r'\.\d{3}\+00:00$')

    async def test_large_home_series_keeps_cpu_aggregate_and_labels_sampling(self):
        g=Gateway(FakeMCP(),ENV,('a','b'),lambda e:None)
        points=[{'timestamp':str(i),'cpu_time':{'value':i}} for i in range(150)]
        async def read(args):return {'data':{'database_home_metrics':{'activity_time_series_metrics':points,'cpu_utilization_aggregate_metrics':{'cpu_utilization':{'value':7.5,'unit':'PERCENT'}}}}}
        g.db_read=read
        result=json.loads(await g.execute('db_read',{'operation':'get_database_home_metrics','arguments':{}}))['data']['database_home_metrics']
        self.assertEqual(result['cpu_utilization_aggregate_metrics']['cpu_utilization']['value'],7.5)
        self.assertEqual(len(result['activity_time_series_metrics']),4)
        self.assertEqual(result['activity_sample_info']['original_point_count'],150)
        self.assertTrue(result['activity_sample_info']['truncated'])

    async def test_backend_report_truncation_is_explicit(self):
        m=FakeMCP()
        async def response(*args): return {'id':CID,'name':'Lab','message':'x'*30000}
        m.call=response
        g=Gateway(m,ENV,('a','b'),lambda e:None)
        result=json.loads(await g.execute('log_query',{'query':'* | head 1'}))
        self.assertTrue(result['partial'])


class WebTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp=tempfile.TemporaryDirectory();p=Path(self.temp.name)
        (p/'access.json').write_text(json.dumps(POLICY));(p/'mcp.json').write_text('{}')
        self.s=Settings(mode='demo',base_url='http://localhost:8000',data_dir=p/'data',config_dir=p,session_secret='x'*48)
        self.app=create_app(self.s)
        self.client=AsyncClient(transport=ASGITransport(app=self.app),base_url='http://localhost:8000')
        self.user={'sub':'alice','name':'Alice','groups':['dbas']}
        token=self.app.state.store.session(self.user)
        self.client.cookies.set('db_session',token)
        self.me=(await self.client.get('/api/me')).json()

    async def asyncTearDown(self):
        await self.client.aclose();self.temp.cleanup()

    async def test_me_exposes_hierarchy_after_per_user_access_filtering(self):
        policy=json.loads((self.s.config_dir/'access.json').read_text())
        root={**ENV,'label':'Authorized root','compartment_id':'ocid1.compartment.root'}
        policy['environments']['root']=root
        policy['environments']['lab']['parent_compartment_id']=root['compartment_id']
        policy['environments']['hidden']={**ENV,'label':'Hidden finance compartment','compartment_id':'ocid1.compartment.finance','groups':['finance']}
        (self.s.config_dir/'access.json').write_text(json.dumps(policy))
        response=await self.client.get('/api/me');self.assertEqual(response.status_code,200)
        rows={r['id']:r for r in response.json()['environments']}
        self.assertEqual(rows['lab']['parent_id'],'root');self.assertNotIn('hidden',rows)
        self.assertNotIn('Hidden finance compartment',response.text)

    async def test_other_user_cannot_read_or_download_report(self):
        store=self.app.state.store
        rid=store.create_run('bob','lab','Private question',30)
        self.assertEqual((await self.client.get('/api/runs/'+rid)).status_code,404)
        self.assertEqual((await self.client.get('/api/runs/'+rid+'/report')).status_code,404)

    async def test_csrf_and_scope_denied_before_agent_runs(self):
        payload={'question':'Check health','environment':'lab'}
        self.assertEqual((await self.client.post('/api/runs',json=payload)).status_code,403)
        payload['environment']='other'
        r=await self.client.post('/api/runs',json=payload,headers={'origin':self.s.base_url,'x-csrf-token':self.me['csrf']})
        self.assertEqual(r.status_code,403)

    async def test_demo_answers_never_call_oci(self):
        with patch('assistant.agent.OCIModel',side_effect=AssertionError('OCI was called')):
            r=await self.client.post('/api/runs',json={'question':'Check health','environment':'lab'},headers={'origin':self.s.base_url,'x-csrf-token':self.me['csrf']})
            self.assertEqual(r.status_code,202)
            await asyncio.sleep(.03)
            result=(await self.client.get('/api/runs/'+r.json()['id'])).json()
            self.assertIn('DEMONSTRATION',result['answer'])

    async def test_revoke_environment_blocks_existing_report(self):
        rid=self.app.state.store.create_run('alice','lab','Existing question',30)
        (self.s.config_dir/'access.json').write_text(json.dumps({'environments':{}}))
        self.assertEqual((await self.client.get('/api/runs/'+rid)).status_code,403)

    def configure_models(self):
        config={'default':'large','models':[
            {'id':'large','label':'Large model','model_id':'ocid1.generativeaimodel.large'},
            {'id':'small','label':'Small model','model_id':'ocid1.generativeaimodel.small'},
            {'id':'disabled','label':'Disabled model','enabled':False}]}
        (self.s.config_dir/'models.json').write_text(json.dumps(config))

    async def test_model_choice_is_used_and_recorded_in_report(self):
        self.configure_models()
        me=(await self.client.get('/api/models')).json()
        self.assertEqual(me['default_model'],'large')
        self.assertNotIn('model_id',me['models'][0])
        r=await self.client.post('/api/runs',json={'question':'Check health','environment':'lab','model':'small'},headers={'origin':self.s.base_url,'x-csrf-token':self.me['csrf']})
        self.assertEqual(r.status_code,202)
        await asyncio.sleep(.03)
        run=(await self.client.get('/api/runs/'+r.json()['id'])).json()
        self.assertEqual(run['model']['id'],'small')
        self.assertIn('Selected model: Small model',run['answer'])
        report=await self.client.get('/api/runs/'+r.json()['id']+'/report')
        self.assertIn('Model: Small model',report.text)

    async def test_unknown_and_disabled_models_are_rejected(self):
        self.configure_models()
        for model in ['https://unapproved.example/model','disabled']:
            r=await self.client.post('/api/runs',json={'question':'Check health','environment':'lab','model':model},headers={'origin':self.s.base_url,'x-csrf-token':self.me['csrf']})
            self.assertEqual(r.status_code,400)
        self.assertEqual(self.app.state.store.history('alice'),[])

    async def test_unconfigured_models_are_disabled_in_live_catalog(self):
        self.configure_models()
        config=json.loads((self.s.config_dir/'models.json').read_text())
        config['models'].append({'id':'missing','label':'Not configured','model_id':''})
        (self.s.config_dir/'models.json').write_text(json.dumps(config))
        self.s.mode='live'
        with self.assertRaises(ValueError): ModelCatalog(self.s).resolve('missing')


if __name__=='__main__':
    unittest.main()
