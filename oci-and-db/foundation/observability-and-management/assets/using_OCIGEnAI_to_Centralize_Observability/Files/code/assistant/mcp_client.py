"""MCP sessions live inside one investigation; they are never shared across users."""
import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.streamable_http import streamable_http_client
from .telemetry import traced

SERVER_NAMES={'db':'oracle.oci-db-observability-mcp-server','logan':'oci-logan-mcp',
    'identity':'db-assistant-identity','model_catalog':'db-assistant-model-catalog'}

def call_attributes(self,server,tool,args):
    result={'mcp.server.name':SERVER_NAMES.get(server,server),'mcp.server.alias':server,'mcp.tool.name':tool}
    result['mcp.connection.id']=self.config.get(server,{}).get('connection_id','builtin')
    if server=='db' and tool=='invoke_dbo_tool':result['db.operation.name']=str(args.get('tool_name',''))[:100]
    return result


class MCPToolError(RuntimeError):
    def __init__(self, raw):
        text = str(raw)
        status = re.search(r'''["']status["']\s*:\s*(\d{3})''', text)
        status = int(status.group(1)) if status else None
        self.category = 'mcp_failure'
        message = 'The MCP operation failed. An authorization denial has not been established.'
        if status == 400 and any(x in text.lower() for x in ('syntax', 'unexpected input', 'missing input', 'invalidparameter')):
            self.category = 'query_rejected'
            message = "OCI rejected the query syntax or arguments. Use Log Analytics pipelines, stats count (not count()), observed field names, and head rather than SQL LIMIT. For message matching use 'Original Log Content' like '%ORA-%', never where msg contains. Correct the query once; do not request wider permissions."
            if 'unexpected input for where' in text.lower():
                message = "The WHERE stage rejected the text-search operator. Put the text filter before the first pipe, without '*' or WHERE. Example: 'Original Log Content' like '%ORA-%' | stats count by 'Log Source'. For samples replace stats with fields Time, 'Log Source', 'Original Log Content' | sort -Time | head 10. Do not repeat WHERE with contains or like. This is a syntax error, not an IAM denial."
            if 'starttime' in text.lower():
                message='OCI rejected the Database Management time arguments. Use UTC milliseconds ending in Z, at least one hour of data, and a start within seven days of execution. The gateway normalizes supported time arguments; use its effective window. This is not an IAM denial.'
        elif status == 401:
            self.category = 'authentication_failed'
            message = 'OCI rejected authentication for this operation. Ask the operator to check the configured credentials.'
        elif status == 403:
            self.category = 'permission_denied'
            message = 'OCI explicitly denied this operation. Preserve the selected scope and report the missing permission.'
        elif status == 404:
            self.category = 'resource_unavailable'
            message = 'The resource was not found or not authorized. A permission denial alone is not established.'
        elif status is not None and status >= 500:
            self.category = 'service_unavailable'
            message = 'OCI returned a service-side server error for this operation. This is not an empty metric result or an established IAM denial. Preserve independent checks and report the failed branch.'
        super().__init__(message)


def unpack(result):
    raw = '\n'.join(c.text for c in result.content if hasattr(c, 'text'))
    if result.isError:
        raise MCPToolError(raw)
    if result.structuredContent is not None:
        if isinstance(result.structuredContent, dict) and result.structuredContent.get('error'):
            raise MCPToolError(result.structuredContent['error'])
        return result.structuredContent
    if raw.lower().startswith(('error', 'failed')):
        raise MCPToolError(raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and data.get('error'):
            raise MCPToolError(data['error'])
        return data
    except json.JSONDecodeError:
        return {'text':raw}


class MCPClients:
    def __init__(self, config, home):
        self.config, self.home = config, home
        self.stack = AsyncExitStack()
        self.sessions, self.schemas = {}, {}

    async def __aenter__(self):
        self.home.mkdir(parents=True, exist_ok=True)
        return self

    async def __aexit__(self, *exc):
        await self.stack.aclose()

    @traced('mcp.connect',lambda self,key:{'mcp.server.name':SERVER_NAMES.get(key,key),'mcp.connection.reused':key in self.sessions})
    async def connect(self, key):
        if key in self.sessions:
            return self.sessions[key]
        spec = self.config[key]
        if spec.get('transport', 'stdio') == 'stdio':
            env = dict(os.environ)
            if spec.get('isolate_oci_env'):
                env={k:v for k,v in env.items() if not k.startswith(('OCI_','GENAI_'))}
            env.update(spec.get('env', {}))
            # Parent-side instrumentation exports MCP timings; child servers do not need this credential.
            env.pop('APM_DATA_KEY',None)
            env.pop('APM_TRACES_ENDPOINT',None)
            for secret in ('SESSION_SECRET','OIDC_CLIENT_SECRET','CONNECTION_ENCRYPTION_KEY'):
                env.pop(secret,None)
            env['HOME'] = str(self.home)
            env['OCI_LOGAN_MCP_READ_ONLY'] = 'true'
            env['OCI_LOGAN_REPORT_ARTIFACT_DIR'] = str(self.home/'reports')
            env.pop('ORACLE_MCP_HOST', None)
            env.pop('ORACLE_MCP_PORT', None)
            io = await self.stack.enter_async_context(stdio_client(StdioServerParameters(
                command=spec['command'], args=spec.get('args', []), env=env)))
        else:
            url = spec['url']
            if not url.startswith('https://'):
                raise ValueError('Remote MCP endpoints must use HTTPS')
            headers = {}
            if spec.get('token_env'):
                headers['Authorization'] = 'Bearer '+os.environ[spec['token_env']]
            if spec.get('public_only'):
                from .remote_transport import validate_remote_url,public_client
                validate_remote_url(url)
                if spec.get('bearer_token'):headers['Authorization']='Bearer '+spec['bearer_token']
                client=await self.stack.enter_async_context(public_client(headers))
                io=await self.stack.enter_async_context(streamable_http_client(url,http_client=client))
            else:
                io = await self.stack.enter_async_context(streamablehttp_client(url, headers=headers))
        session = await self.stack.enter_async_context(ClientSession(io[0], io[1], read_timeout_seconds=timedelta(seconds=330)))
        await session.initialize()
        page, schemas = None, {}
        while True:
            result = await session.list_tools(cursor=page)
            schemas.update({t.name:t.inputSchema for t in result.tools})
            page = result.nextCursor
            if not page:
                break
        self.sessions[key], self.schemas[key] = session, schemas
        return session

    @traced(lambda self,server,tool,args:'mcp.'+server+'.'+tool,call_attributes)
    async def call(self, server, tool, args):
        session = await self.connect(server)
        if tool not in self.schemas[server]:
            raise ValueError('Required MCP capability is not exposed: '+tool)
        return unpack(await session.call_tool(tool, args))
