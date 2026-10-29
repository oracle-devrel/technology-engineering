import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import oci

from assistant.gateway import TOOLS
from assistant.mcp_client import MCPClients
from assistant.model import OCIModel, ModelResponseError


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_dynamic_child_receives_only_its_selected_oci_profile(self):
        with tempfile.TemporaryDirectory() as d:
            config={'identity':{'command':sys.executable,'args':[str(Path(__file__).parent/'fake_mcp.py')],
                'env':{'OCI_CONFIG_PROFILE':'TENANT_B'},'isolate_oci_env':True}}
            with patch.dict('os.environ',{'OCI_CONFIG_PROFILE':'TENANT_A','OCI_RESOURCE_PRINCIPAL_RPST':'parent-secret',
                    'SESSION_SECRET':'cookie-secret','CONNECTION_ENCRYPTION_KEY':'encryption-secret','OIDC_CLIENT_SECRET':'oidc-secret'}):
                async with MCPClients(config,Path(d)) as client:
                    result=await client.call('identity','get_compartment',{'compartment_id':'ocid1.compartment.test'})
                    self.assertEqual(result['oci_profile'],'TENANT_B');self.assertFalse(result['parent_token_present']);self.assertFalse(result['app_secret_present'])

    async def test_reasoning_only_reply_retries_same_model_without_publishing_reasoning(self):
        m=oci.generative_ai_inference.models
        requests=[]
        responses=[m.AssistantMessage(content=[m.TextContent(text='')],reasoning_content='private internal reasoning'),
            m.AssistantMessage(content=[m.TextContent(text='Observed evidence summary.')])]
        def chat(request):
            requests.append(request)
            return SimpleNamespace(data=SimpleNamespace(chat_response=SimpleNamespace(choices=[SimpleNamespace(message=responses.pop(0),finish_reason='length')])) )
        settings=SimpleNamespace(region='eu-frankfurt-1',genai_compartment='compartment',model_id='openai.gpt-oss-20b')
        with patch('assistant.model.config_and_signer',return_value=({},None)),patch('assistant.model.oci.generative_ai_inference.GenerativeAiInferenceClient',return_value=SimpleNamespace(chat=chat)):
            model=OCIModel(settings,selection={'model_id':'ocid1.generativeaimodel.selected','label':'openai.gpt-oss-20b','region':settings.region})
        messages=[model.message('USER','Find log errors')]
        result=await model.chat(messages,TOOLS,require_tools=True)
        self.assertEqual(result.content[0].text,'Observed evidence summary.')
        self.assertEqual([r.chat_request.max_tokens for r in requests],[4096,8192])
        self.assertTrue(all(r.serving_mode.model_id=='ocid1.generativeaimodel.selected' for r in requests))
        self.assertTrue(all(r.chat_request.reasoning_effort=='LOW' for r in requests))
        self.assertTrue(all(r.chat_request.tool_choice.type=='REQUIRED' for r in requests))
        self.assertEqual(len(messages),1)

    async def test_repeated_empty_reply_stops_after_one_recovery(self):
        calls=[]
        def chat(request):
            calls.append(request)
            return SimpleNamespace(data=SimpleNamespace(chat_response=SimpleNamespace(choices=[])))
        settings=SimpleNamespace(region='eu-frankfurt-1',genai_compartment='compartment',model_id='meta.llama-3.3-70b-instruct')
        with patch('assistant.model.config_and_signer',return_value=({},None)),patch('assistant.model.oci.generative_ai_inference.GenerativeAiInferenceClient',return_value=SimpleNamespace(chat=chat)):
            model=OCIModel(settings)
        with self.assertRaises(ModelResponseError):await model.chat([model.message('USER','Check logs')],TOOLS)
        self.assertEqual(len(calls),2)
        self.assertIsNone(calls[0].chat_request.reasoning_effort)

    async def test_real_stdio_transport_discovers_and_reads_identity(self):
        with tempfile.TemporaryDirectory() as d:
            config={'identity':{'command':sys.executable,'args':[str(Path(__file__).parent/'fake_mcp.py')]}}
            with patch.dict('os.environ',{'APM_DATA_KEY':'must-not-reach-mcp'}):
                async with MCPClients(config,Path(d)) as client:
                    result=await client.call('identity','get_compartment',{'compartment_id':'ocid1.compartment.test'})
                    self.assertEqual(result['id'],'ocid1.compartment.test')
                    self.assertFalse(result['apm_key_present'])
                    self.assertIn('compartment_id',client.schemas['identity']['get_compartment']['properties'])

    async def test_oci_sdk_request_and_tool_message_round_trip(self):
        m=oci.generative_ai_inference.models
        answer=m.AssistantMessage(content=[],tool_calls=[m.FunctionCall(id='call-1',name='load_skill',arguments=json.dumps({'name':'observability-coverage-checker'}))])
        received=[]
        def chat(request):
            received.append(request)
            return SimpleNamespace(data=SimpleNamespace(chat_response=SimpleNamespace(choices=[SimpleNamespace(message=answer)])))
        fake=SimpleNamespace(chat=chat)
        settings=SimpleNamespace(region='eu-frankfurt-1',genai_compartment='ocid1.compartment.test',model_id='ocid1.generativeaimodel.test')
        with patch('assistant.model.config_and_signer',return_value=({},None)),patch('assistant.model.oci.generative_ai_inference.GenerativeAiInferenceClient',return_value=fake):
            model=OCIModel(settings,selection={'model_id':'ocid1.generativeaimodel.selected','region':'uk-london-1'})
        result=await model.chat([model.message('SYSTEM','Use the tool'),model.message('USER','Check coverage')],TOOLS)
        self.assertEqual(result.tool_calls[0].name,'load_skill')
        self.assertEqual(received[0].chat_request.tools[0].type,'FUNCTION')
        self.assertEqual(received[0].chat_request.api_format,'GENERIC')
        self.assertEqual(received[0].serving_mode.model_id,'ocid1.generativeaimodel.selected')
        message=model.message('TOOL','Evidence',result.tool_calls[0].id)
        self.assertEqual(message.role,'TOOL')
        self.assertEqual(message.tool_call_id,'call-1')
