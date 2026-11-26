"""Bounded MCP startup/capability/scope tests, without sending credentials to GenAI."""
import asyncio
import tempfile
from datetime import datetime,timedelta,timezone
from pathlib import Path
from jsonschema import validate
from .connections import ConnectionError
from .mcp_client import MCPClients,MCPToolError
from .telemetry import traced


async def check_data_path(clients,kind,compartment):
    if kind=='db':
        required={'list_dbo_skills','list_dbo_tools','describe_dbo_tool','invoke_dbo_tool'}
        await clients.connect('db')
        if not required<=set(clients.schemas['db']):raise ConnectionError('The endpoint is not a compatible Database Observability MCP')
        contract=await clients.call('db','describe_dbo_tool',{'tool_name':'list_managed_databases'})
        schema=contract.get('inputSchema',{})
        if contract.get('name')!='list_managed_databases' or contract.get('mutable') is not False or 'compartment_id' not in schema.get('properties',{}):
            raise ConnectionError('The DB MCP must expose scoped, read-only managed-database inventory')
        args={'compartment_id':compartment,'limit':1}
        for key in ('compartment_id_in_subtree','include_subcompartments'):
            if key in schema.get('properties',{}):args[key]=False
        validate(args,schema)
        await clients.call('db','invoke_dbo_tool',{'tool_name':'list_managed_databases','arguments':args})
    else:
        await clients.connect('logan')
        schema=clients.schemas['logan'].get('run_query',{})
        required={'compartment_id','include_subcompartments','time_start','time_end','query','max_results'}
        if not required<=set(schema.get('properties',{})):raise ConnectionError('The LogAn MCP must support explicit compartment, subtree exclusion and absolute query time bounds')
        end=datetime.now(timezone.utc)-timedelta(seconds=5)
        args={'compartment_id':compartment,'include_subcompartments':False,'time_start':(end-timedelta(minutes=15)).isoformat(),
              'time_end':end.isoformat(),'query':'* | stats count','max_results':1}
        if 'scope' in schema.get('properties',{}):args['scope']='default'
        validate(args,schema)
        await clients.call('logan','run_query',args)


@traced('mcp.connection.test',lambda registry,identifier,compartment=None:{'mcp.connection.id':identifier})
async def verify_connection(registry,identifier,compartment=None):
    settings=registry.settings;public=registry.get(identifier)
    if not public['enabled']:raise ConnectionError('Enable this connection before testing it')
    compartment=compartment or public['test_compartment_id']
    env={'compartment_id':compartment,'tenancy_id':public['tenancy_id'],'region':public['region']}
    home=settings.data_dir/'connection-tests';home.mkdir(exist_ok=True,parents=True)
    async with asyncio.timeout(120):
        with tempfile.TemporaryDirectory(prefix='test-',dir=home) as folder:
            home=Path(folder)
            with registry.runtime_config(settings.load('mcp.json'),env,home,{public['kind']:identifier},require_ready=False) as config:
                async with MCPClients(config,home/'session') as clients:
                    identity=await clients.call('identity','get_compartment',{'compartment_id':compartment})
                    if identity.get('id')!=compartment or identity.get('lifecycle_state')!='ACTIVE':raise ConnectionError('OCI could not verify an active target compartment')
                    if identity.get('tenancy_id')!=public['tenancy_id']:raise ConnectionError('The identity connection returned a different tenancy')
                    await check_data_path(clients,public['kind'],compartment)
                    return {'compartment_id':compartment,'compartment_name':identity['name'],'tenancy_id':public['tenancy_id'],'region':public['region']}


def safe_connection_error(exc):
    if isinstance(exc,ConnectionError):return str(exc)
    if isinstance(exc,MCPToolError):return str(exc)
    if isinstance(exc,TimeoutError):return 'The MCP connection test exceeded two minutes. Check connectivity and the configured identity.'
    return 'Connection test failed ('+type(exc).__name__+'). Check the profile/API key, endpoint reachability and read permissions.'
