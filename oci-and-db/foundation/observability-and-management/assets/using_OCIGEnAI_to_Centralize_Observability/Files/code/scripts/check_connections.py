"""Operator-run live check. Performs one small, billable model request and MCP discovery.

Run inside the deployed container. It does not query observability data or expose secrets.
"""
import asyncio
import json
import secrets
import argparse

from assistant.gateway import Gateway, TOOLS
from assistant.mcp_client import MCPClients
from assistant.model import OCIModel
from assistant.offered_models import OfferedModels
from assistant.policy import timestamps
from assistant.settings import Settings


async def main():
    s=Settings(); s.validate()
    if s.mode!='live':
        raise ValueError('Use the browser preview for demo mode')
    parser=argparse.ArgumentParser()
    parser.add_argument('--list-models',action='store_true')
    parser.add_argument('--model',default='')
    args=parser.parse_args()
    offered=OfferedModels(s)
    if args.list_models:
        print(json.dumps(await offered.refresh(),indent=2))
        return
    selection=await offered.resolve(args.model)
    model=OCIModel(s,selection=selection)
    result=await model.chat([model.message('SYSTEM','Call load_skill once with name observability-coverage-checker. Do not answer with plain text.'),model.message('USER','Check tool calling.')],TOOLS)
    calls=result.tool_calls or []
    assert any(c.name=='load_skill' and json.loads(c.arguments).get('name')=='observability-coverage-checker' for c in calls), 'Selected model did not return a compatible function call'
    print('OCI Generic Chat + tool call: OK ('+selection['label']+')')
    for key,env in s.load('access.json')['environments'].items():
        config=s.load('mcp.json')
        config['logan'].setdefault('env',{})['OCI_LA_COMPARTMENT']=env['compartment_id']
        async with MCPClients(config,s.data_dir/'checks'/secrets.token_hex(8)) as clients:
            gateway=Gateway(clients,env,timestamps(1),lambda event:None)
            await gateway.verify()
            print(key+': identity verification OK')
            for server,names in {'logan':{'run_query'},'db':{'list_dbo_skills','list_dbo_tools','describe_dbo_tool','invoke_dbo_tool'}}.items():
                await clients.connect(server)
                assert names.issubset(clients.schemas[server]), 'Missing MCP tools'
                print(key+': '+server+' discovery OK')
    print('Discovery checks passed. A real scoped inventory/log query and browser sign-in are still required.')


if __name__=='__main__':
    asyncio.run(main())
