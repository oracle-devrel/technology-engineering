"""Trusted, bounded routing choices. Preferences never expand the gateway catalog."""
import re
import copy
from .policy import ToolPrerequisiteError

SQL_OPERATIONS={'list_awr_dbs','list_awr_db_snapshots','get_awr_db_report'}

def is_sql_ranking(question):
    sql=bool(re.search(r'\b(?:sql|slq|statements?)\b',question,re.I))
    return sql and bool(re.search(r'\b(?:top|slow\w*|expensive|rank\w*|degrad\w*|regress\w*|performance|highest|most)\b',question,re.I))

def routing_options(operations):
    return {'mcps':[{'id':'auto','label':'Choose for me'},{'id':'db','label':'Database Observability MCP'},{'id':'logan','label':'Log Analytics MCP (LogAn)'}],
        'tools':[{'id':'auto','mcp':'auto','label':'Choose for me'}, {'id':'log_query','mcp':'logan','label':'Search logs'}]+
        [{'id':op,'mcp':'db','label':{'get_awr_db_report':'Top SQL — AWR report','list_awr_dbs':'Discover AWR databases','list_awr_db_snapshots':'Discover AWR snapshots','get_database_home_metrics':'Database CPU and activity'}.get(op,op.replace('_',' '))} for op in sorted(operations)]}

def validate_preference(mcp,tool,operations):
    if mcp not in {'auto','db','logan'}:raise ValueError('Unknown preferred MCP')
    if tool not in {'auto','log_query'}|operations:raise ValueError('Unknown or unapproved preferred operation')
    source='logan' if tool=='log_query' else 'db' if tool!='auto' else mcp
    if mcp!='auto' and source!=mcp:raise ValueError('The preferred operation belongs to a different MCP')
    return source

def route(question,mcp='auto',tool='auto',operations=frozenset(),workflow='auto'):
    source=validate_preference(mcp,tool,operations)
    sql=is_sql_ranking(question) or tool=='get_awr_db_report' or workflow=='database-sql-performance'
    conflict=sql and source=='logan'
    if sql and source=='auto':source='db'
    return {'mcp':source,'tool':tool,'sql':sql,'conflict':conflict,'preference_mcp':mcp}

def permit_call(routing,name,args):
    if name=='load_skill':return
    if routing['sql'] and name=='log_query':
        raise ToolPrerequisiteError('Top SQL needs Database Observability evidence. Log Analytics cannot substitute for statement ranking. Use db_catalog, list_managed_databases, list_awr_dbs, list_awr_db_snapshots and get_awr_db_report.')
    if routing['mcp']=='db' and name=='log_query':raise ToolPrerequisiteError('The selected source is Database Observability MCP. Use the approved DB catalog.')
    if routing['mcp']=='logan' and name in {'db_read','db_catalog'}:raise ToolPrerequisiteError('The selected source is Log Analytics MCP. Use log_query or change the source for your next message.')

def exposed_tools(tools,routing):
    result=copy.deepcopy([t for t in tools if not (routing['mcp']=='db' and t['name']=='log_query') and not (routing['mcp']=='logan' and t['name'] in {'db_read','db_catalog'})])
    if routing['sql']:
        for tool in result:
            if tool['name']=='db_read':tool['parameters']['properties']['operation']['enum']=sorted(SQL_OPERATIONS|{'list_managed_databases'})
    return result
