import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import json
import time

from assistant.catalog_mcp import pages
from assistant.offered_models import normalize_catalog, OfferedModels
from assistant.settings import Settings
from assistant.model import OCIModel
from assistant.gateway import TOOLS
import oci


REGION='eu-frankfurt-1'


def catalog_item(key,vendor='OpenAI',caps=None,modes=None,retired=None):
    label=vendor.lower()+'.'+key
    d={'modelId':label,'vendor':vendor,'capabilities':caps or ['CHAT'],'modelAccess':'HOSTED',
        'availability':[{'region':REGION,'servingModes':modes or ['ON_DEMAND'],'timeOnDemandRetired':retired}]}
    i={'id':'ocid1.generativeaimodel.'+key,'displayName':label,'vendor':vendor,
        'capabilities':caps or ['CHAT'],'type':'BASE','lifecycleState':'ACTIVE'}
    return d,i


class CatalogTests(unittest.TestCase):
    def test_multiple_vendors_and_unusable_offerings(self):
        entries=[catalog_item('large'),catalog_item('command-a','Cohere'),catalog_item('embed','Cohere',['TEXT_EMBEDDINGS']),
            catalog_item('dedicated','Meta',modes=['DEDICATED']),catalog_item('retired',retired='2020-01-01T00:00:00Z')]
        rows=normalize_catalog({'region':REGION,'discovery':[x[0] for x in entries],'inventory':[x[1] for x in entries]})
        enabled=[r for r in rows if r['enabled']]
        self.assertEqual(len(enabled),2)
        self.assertEqual({r['api_format'] for r in enabled},{'GENERIC','COHEREV2'})
        self.assertTrue(all(r['reason'] for r in rows if not r['enabled']))

    def test_no_unverified_on_demand_or_proxy_access(self):
        d,i=catalog_item('proxy');d['modelAccess']='PROXY'
        rows=normalize_catalog({'region':REGION,'discovery':[d],'inventory':[i]})
        self.assertFalse(rows[0]['enabled'])
        rows=normalize_catalog({'region':REGION,'discovery':[],'inventory':[i]})
        self.assertFalse(rows[0]['enabled'])

    def test_catalog_pagination_is_exhausted(self):
        seen=[]
        def read(compartment,page,limit,**filters):
            seen.append((compartment,page,filters))
            return SimpleNamespace(data={'items':[page or 'first']},headers={'opc-next-page':'next'} if page is None else {})
        result=pages(None,read,'compartment',region=[REGION])
        self.assertEqual(result,['first','next'])
        self.assertEqual(len(seen),2)
        self.assertEqual(seen[1][2]['region'],[REGION])


class AdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_admin_allowlist_blocks_cached_discovered_model(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            (p/'models.json').write_text(json.dumps({'default':'default','models':[{'id':'default','label':'Default','model_id':''}],'allowed_model_ids':[]}))
            s=Settings(mode='live',config_dir=p,data_dir=p)
            offered=OfferedModels(s)
            discovery,inventory=catalog_item('large')
            offered.rows=normalize_catalog({'region':REGION,'discovery':[discovery],'inventory':[inventory]})
            offered.updated=time.time()
            self.assertFalse(offered.public()['models'][0]['enabled'])
            with self.assertRaises(ValueError): await offered.resolve(offered.rows[0]['id'])

    async def test_cohere_v2_tool_calls_round_trip(self):
        m=oci.generative_ai_inference.models
        answer=m.CohereAssistantMessageV2(content=[],tool_plan='Read evidence',tool_calls=[m.CohereToolCallV2(id='c1',function={'name':'load_skill','arguments':{'name':'observability-coverage-checker'}})])
        requests=[]
        def chat(request):
            requests.append(request)
            return SimpleNamespace(data=SimpleNamespace(chat_response=m.CohereChatResponseV2(message=answer)))
        settings=SimpleNamespace(region=REGION,genai_compartment='compartment',model_id='unused')
        with patch('assistant.model.config_and_signer',return_value=({},None)),patch('assistant.model.oci.generative_ai_inference.GenerativeAiInferenceClient',return_value=SimpleNamespace(chat=chat)) as client_factory:
            model=OCIModel(settings,{'model_id':'model','region':REGION,'api_format':'COHEREV2'})
        self.assertEqual(client_factory.call_args.kwargs['timeout'],(10,180))
        history=[model.message('SYSTEM','Read'),model.message('USER','Health')]
        result=await model.chat(history,TOOLS)
        history.extend([result,model.message('TOOL','Evidence','c1')])
        await model.chat(history,TOOLS,require_tools=True)
        self.assertEqual(requests[0].chat_request.api_format,'COHEREV2')
        self.assertIsNone(requests[0].chat_request.tools_choice)
        self.assertEqual(requests[1].chat_request.tools_choice,'REQUIRED')
        self.assertTrue(all(t.type=='FUNCTION' for t in requests[0].chat_request.tools))
        self.assertEqual(requests[1].chat_request.messages[-2].tool_calls[0].type,'FUNCTION')
        self.assertEqual(requests[1].chat_request.messages[-1].tool_call_id,'c1')
        self.assertEqual(result.tool_calls[0].name,'load_skill')

    async def test_live_catalog_failure_does_not_become_a_demo_list(self):
        with tempfile.TemporaryDirectory() as d:
            s=Settings(mode='live',config_dir=Path(d),data_dir=Path(d),model_id='')
            offered=OfferedModels(s)
            result=await offered.refresh()
            self.assertEqual(result['source'],'oci')
            self.assertEqual(result['models'],[])
            self.assertTrue(result['error'])
            with self.assertRaises(ValueError): await offered.resolve('fake')
