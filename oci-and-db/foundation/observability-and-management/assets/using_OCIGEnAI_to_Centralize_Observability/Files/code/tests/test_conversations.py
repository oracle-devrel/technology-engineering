import asyncio
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import oci
from httpx import ASGITransport,AsyncClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from assistant.agent import investigate
from assistant.settings import Settings
from assistant.store import Store,ConversationScopeError
from assistant.web import create_app
from assistant import telemetry

CID='ocid1.compartment.test'
ENV={'label':'Test','compartment_id':CID,'compartment_name':'Transport test','groups':['dbas'],'subjects':[]}
USER={'sub':'alice','name':'Alice','groups':['dbas']}
WINDOW=('2026-10-20T14:37:55+00:00','2026-10-22T14:37:55+00:00')
MODEL={'id':'model','label':'Test model','model_id':'ocid1.generativeaimodel.test','region':'eu-frankfurt-1'}

class ConversationTests(unittest.TestCase):
    def test_migration_preserves_old_reports_and_context_is_private_bounded_and_ordered(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'old.sqlite3'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE runs (id TEXT PRIMARY KEY, owner TEXT, environment TEXT, question TEXT, status TEXT, answer TEXT, events TEXT, created REAL)')
                c.execute("INSERT INTO runs VALUES ('legacy','alice','lab','old question','complete','old answer','[]',1)")
            store=Store(path)
            self.assertEqual(store.get('legacy','alice')['answer'],'old answer')
            self.assertIsNone(store.get('legacy','alice')['conversation_id'])
            first=store.create_run('alice','lab','first question',30,compartment_id=CID,window=WINDOW)
            cid=store.get(first,'alice')['conversation_id'];store.update(first,status='complete',answer='Historical evidence')
            for number in range(7):
                rid=store.create_run('alice','lab',f'follow-up {number}',30,conversation_id=cid,compartment_id=CID,window=WINDOW)
                store.update(rid,status='complete',answer=f'answer {number}')
            last=store.create_run('alice','lab','current',30,conversation_id=cid,compartment_id=CID,window=WINDOW)
            turns=store.context(last,'alice')
            self.assertEqual(len(turns),6);self.assertEqual(turns[-1]['answer'],'answer 6')
            self.assertTrue(all(t['utc_start']==WINDOW[0] for t in turns))
            self.assertIsNone(store.conversation(cid,'bob'))
            self.assertEqual(store.context(last,'bob'),[])
            store.update(last,status='complete')
            with self.assertRaises(LookupError):store.create_run('bob','lab','steal context',30,conversation_id=cid,compartment_id=CID)
            with self.assertRaises(ConversationScopeError):store.create_run('alice','lab','change scope',30,conversation_id=cid,compartment_id='ocid1.compartment.other')
            resumed=Store(path)
            self.assertEqual(resumed.conversation(cid,'alice')['trace_id'],store.conversation(cid,'alice')['trace_id'])

class ConversationWebTests(unittest.IsolatedAsyncioTestCase):
    async def test_preferred_source_and_operation_are_persisted_and_server_validated(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/'access.json').write_text(json.dumps({'environments':{'lab':ENV}}));(p/'mcp.json').write_text('{}')
            s=Settings(mode='demo',base_url='http://localhost:8000',data_dir=p/'data',config_dir=p,session_secret='x'*40)
            app=create_app(s);store=app.state.store
            async with AsyncClient(transport=ASGITransport(app=app),base_url=s.base_url) as client:
                client.cookies.set('db_session',store.session(USER));me=(await client.get('/api/me')).json()
                self.assertIn('get_awr_db_report',[t['id'] for t in me['routing_options']['tools']])
                headers={'origin':s.base_url,'x-csrf-token':me['csrf']}
                body={'question':'Show top SQL','environment':'lab','preferred_mcp':'db','preferred_tool':'get_awr_db_report'}
                response=await client.post('/api/runs',json=body,headers=headers);self.assertEqual(response.status_code,202)
                await asyncio.sleep(.03);r=store.get(response.json()['id'],'alice');self.assertEqual(r['routing']['tool'],'get_awr_db_report')
                for extra in [{'preferred_tool':'execute_sql'},{'preferred_mcp':'logan','preferred_tool':'auto'},{'preferred_mcp':'unknown'}]:
                    denied=await client.post('/api/runs',json={**body,**extra},headers=headers);self.assertEqual(denied.status_code,400)
                self.assertEqual(len(store.history('alice')),1)

    async def test_followup_api_ownership_revocation_and_environment_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);policy={'environments':{'lab':ENV}}
            (p/'access.json').write_text(json.dumps(policy));(p/'mcp.json').write_text('{}')
            s=Settings(mode='demo',base_url='http://localhost:8000',data_dir=p/'data',config_dir=p,session_secret='x'*40)
            app=create_app(s);store=app.state.store
            async with AsyncClient(transport=ASGITransport(app=app),base_url=s.base_url) as client:
                client.cookies.set('db_session',store.session(USER));me=(await client.get('/api/me')).json()
                headers={'origin':s.base_url,'x-csrf-token':me['csrf']}
                response=await client.post('/api/runs',json={'question':'Count alert logs','environment':'lab'},headers=headers)
                self.assertEqual(response.status_code,202);cid=response.json()['conversation_id'];trace_id=response.json()['trace_id']
                await asyncio.sleep(.03)
                response=await client.post('/api/runs',json={'question':'What about those logs?','environment':'lab','conversation_id':cid},headers=headers)
                self.assertEqual(response.status_code,202);await asyncio.sleep(.03)
                conversation=(await client.get('/api/conversations/'+cid)).json()
                self.assertEqual(len(conversation['turns']),2);self.assertEqual(conversation['trace_id'],trace_id)
                self.assertIn('Previous interactions in context: 1',conversation['turns'][-1]['answer'])
                client.cookies.set('db_session',store.session({'sub':'bob','name':'Bob','groups':['dbas']}))
                self.assertEqual((await client.get('/api/conversations/'+cid)).status_code,404)
                bob=(await client.get('/api/me')).json()
                response=await client.post('/api/runs',json={'question':'Read their context','environment':'lab','conversation_id':cid},headers={'origin':s.base_url,'x-csrf-token':bob['csrf']})
                self.assertEqual(response.status_code,404)
                client.cookies.set('db_session',store.session(USER))
                policy['environments']['lab']['compartment_id']='ocid1.compartment.changed';(p/'access.json').write_text(json.dumps(policy))
                self.assertEqual((await client.get('/api/conversations/'+cid)).status_code,403)
                self.assertEqual((await client.get('/api/runs/'+conversation['turns'][0]['id'])).status_code,403)
                self.assertEqual((await client.get('/api/conversations')).json(),[])

class TraceTests(unittest.IsolatedAsyncioTestCase):
    async def test_two_real_mcp_round_trips_share_trace_and_history_survives_restart(self):
        exporter=InMemorySpanExporter();received=[];m=oci.generative_ai_inference.models
        class Client:
            def __init__(self):self.calls=0
            def chat(self,request):
                received.append(request);self.calls+=1
                if self.calls==1:answer=m.AssistantMessage(content=[],tool_calls=[m.FunctionCall(id='skill',name='load_skill',arguments=json.dumps({'name':'application-error-investigator'}))])
                elif self.calls==2:answer=m.AssistantMessage(content=[],tool_calls=[m.FunctionCall(id='logs',name='log_query',arguments=json.dumps({'query':'* | stats count as Records','max_results':1}))])
                else:answer=m.AssistantMessage(content=[m.TextContent(text='24 alert records in the verified window.')],tool_calls=[])
                return SimpleNamespace(data=SimpleNamespace(chat_response=SimpleNamespace(choices=[SimpleNamespace(message=answer)])))
        try:
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder);(p/'access.json').write_text(json.dumps({'environments':{'lab':ENV}}))
                fixture={'command':sys.executable,'args':[str(Path(__file__).parent/'fake_mcp.py')]}
                (p/'mcp.json').write_text(json.dumps({'identity':fixture,'logan':fixture}))
                settings=Settings(mode='live',config_dir=p,data_dir=p/'data');telemetry.configure(settings,exporter)
                store=Store(p/'data/assistant.sqlite3');first=store.create_run('alice','lab','Count alert logs',30,MODEL,compartment_id=CID,window=WINDOW)
                cid=store.get(first,'alice')['conversation_id']
                with patch('assistant.model.config_and_signer',return_value=({},None)),patch('assistant.model.oci.generative_ai_inference.GenerativeAiInferenceClient',side_effect=lambda *a,**kw:Client()):
                    await investigate(settings,store,first,USER,ENV,'Count alert logs','auto',WINDOW,asyncio.Semaphore(1),MODEL)
                    self.assertEqual(store.get(first,'alice')['status'],'complete')
                    telemetry.flush();first_spans=exporter.get_finished_spans();telemetry.shutdown()
                    exporter=InMemorySpanExporter();telemetry.configure(settings,exporter)
                    store=Store(p/'data/assistant.sqlite3')
                    second=store.create_run('alice','lab','How many of those?',30,MODEL,conversation_id=cid,compartment_id=CID,window=WINDOW)
                    await investigate(settings,store,second,USER,ENV,'How many of those?','auto',WINDOW,asyncio.Semaphore(1),MODEL)
                telemetry.flush();spans=tuple(first_spans)+exporter.get_finished_spans()
                roots=[s for s in spans if s.name=='dbassistant.conversation'];interactions=[s for s in spans if s.name=='dbassistant.interaction']
                self.assertEqual(len(roots),1);self.assertEqual(len(interactions),2)
                self.assertEqual(len({s.context.trace_id for s in spans}),1)
                self.assertTrue(all(s.parent.span_id==roots[0].context.span_id for s in interactions))
                self.assertEqual(sum(s.name=='genai.chat' for s in spans),6)
                self.assertEqual(sum(s.name.startswith('skill.') for s in spans),2)
                self.assertEqual(sum('mcp.tool.name' in s.attributes for s in spans),6)
                allowed_parents={s.context.span_id for s in spans}
                self.assertTrue(all(s.parent is None or s.parent.span_id in allowed_parents for s in spans))
                texts=[' '.join(c.text for c in msg.content or [] if hasattr(c,'text')) for msg in received[3].chat_request.messages]
                self.assertTrue(any('24 alert records' in t for t in texts));self.assertTrue(any('Historical conversation turn 1' in t for t in texts))
                exported=' '.join(s.to_json() for s in spans)
                self.assertNotIn('Count alert logs',exported);self.assertNotIn('24 alert records',exported);self.assertNotIn('stats count',exported)
                with self.assertRaises(ValueError):
                    with telemetry.span('failure'):raise ValueError('password=DO_NOT_EXPORT raw SQL')
                telemetry.flush();failure=exporter.get_finished_spans()[-1]
                self.assertNotIn('DO_NOT_EXPORT',failure.to_json());self.assertEqual(failure.status.description,'ValueError')
        finally:telemetry.shutdown()
