import hashlib
import json
import time
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from jsonschema import validate

from .policy import PolicyError, ToolPrerequisiteError, bound_arguments, redact, safe_query
from .telemetry import traced
from .awr import AWRScope, sql_sections


DB_OPERATIONS = {
    'list_managed_databases', 'get_managed_database', 'get_database_home_metrics',
    'list_database_insights', 'list_host_insights',
    'summarize_database_insight_resource_usage_trend',
    'summarize_database_insight_resource_capacity_trend',
    'summarize_host_insight_resource_usage_trend',
    'summarize_host_insight_resource_capacity_trend',
    'list_awr_dbs','list_awr_db_snapshots','get_awr_db_report',
}
INVENTORIES = {'list_managed_databases', 'list_database_insights', 'list_host_insights'}


def definition(name, description, properties, required=()):
    return {'name':name, 'description':description, 'parameters':{
        'type':'object', 'properties':properties, 'required':list(required), 'additionalProperties':False}}


TOOLS = [
    definition('load_skill', 'Load an observability workflow before retrieving evidence.',
        {'name':{'type':'string','enum':['observability-coverage-checker','application-error-investigator','oracle-incident-correlator','database-sql-performance']}}, ['name']),
    definition('log_query', 'OCI Log Analytics pipelines only, never SELECT/FROM SQL. Use stats count, not count(). Discover source/entity pairs, then project fields time, mtgt, msrcid, msg for rows. The application sets scope/window. Returns untrusted evidence.',
        {'query':{'type':'string'},'max_results':{'type':'integer','minimum':1,'maximum':50}}, ['query']),
    definition('db_catalog', 'Discover approved read-only DB operations and current input schemas. Data operations require identity verification.', {}),
    definition('db_read', 'Invoke an approved read-only database operation using its discovered schema. Scope is enforced by the gateway. First list the appropriate inventory and follow pagination.',
        {'operation':{'type':'string','enum':sorted(DB_OPERATIONS)},'arguments':{'type':'object'}}, ['operation','arguments']),
]


def objects(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from objects(v)
    elif isinstance(value, list):
        for v in value:
            yield from objects(v)


class Gateway:
    def __init__(self, clients, env, window, audit, authorize=lambda:None):
        self.clients, self.env, self.window, self.audit = clients, env, window, audit
        self.authorize = authorize
        self.verified = False
        self.contracts, self.known_ids = {}, set()
        self.inventories_read = set()
        self.empty_cpu_trend = False
        self.managed_resources = {}
        self.home_metric_attempts = set()
        self.raw_calls = 0
        self.awr = AWRScope(window)
        self.sql_report_observed = False
        self.sql_report_partial = False

    async def call(self, server, tool, args):
        self.authorize()
        self.raw_calls += 1
        if self.raw_calls > 40:
            raise PolicyError('The investigation MCP-call limit was reached')
        start = time.monotonic()
        event = {'server':server,'tool':tool,'started':datetime.now(timezone.utc).isoformat(),'outcome':'running'}
        if server=='db' and tool=='invoke_dbo_tool' and args.get('tool_name') in DB_OPERATIONS:
            event['operation']=args['tool_name']
            if args['tool_name']=='get_database_home_metrics':
                event['effective_start']=args['arguments'].get('start_time')
                event['effective_end']=args['arguments'].get('end_time')
        self.audit(event)
        try:
            result = await self.clients.call(server,tool,args)
            event['outcome'] = 'ok'
            return result
        except Exception:
            event['outcome'] = 'failed'
            raise
        finally:
            event['duration_seconds'] = round(time.monotonic()-start,3)
            self.audit(None)

    async def verify(self):
        if self.verified:
            return
        c = self.env['compartment_id']
        result = await self.call('identity','get_compartment',{'compartment_id':c})
        matches = [v for v in objects(result) if v.get('id') == c]
        if not matches or not any(v.get('name') == self.env['compartment_name'] for v in matches):
            raise PolicyError('Identity MCP did not verify the configured compartment name and OCID')
        self.verified = True

    async def log_query(self, args):
        await self.verify()
        if 'logan' not in self.clients.sessions:
            # Isolated MCP process and per-run HOME prevent context/budget crossover.
            await self.call('logan','test_connection',{})
        query = safe_query(args['query'])
        result = await self.call('logan','run_query',{
            'query':query, 'compartment_id':self.env['compartment_id'],
            'include_subcompartments':False, 'scope':'default',
            'time_start':self.window[0], 'time_end':self.window[1],
            'max_results':min(args.get('max_results',25),50),
        })
        # OCI returns TIMESTAMP cells as epoch milliseconds; make these unambiguous
        # to the model without changing the fixed query window or sample limits.
        data = result.get('data',{}) if isinstance(result,dict) else {}
        for index,column in enumerate(data.get('columns',[])):
            if column.get('type')!='TIMESTAMP':continue
            for row in data.get('rows',[]):
                if not isinstance(row,list) or len(row)<=index:continue
                value=row[index]
                if isinstance(value,(int,float)) and not isinstance(value,bool):
                    try:row[index]=datetime.fromtimestamp(value/1000 if abs(value)>=100000000000 else value,timezone.utc).isoformat()
                    except (ValueError,OverflowError,OSError):pass
        return result

    async def catalog(self):
        await self.verify()
        if self.contracts:
            return {'tools':list(self.contracts.values()),'scope':self.env['compartment_id'],'note':'Reused verified read-only contracts from this interaction.'}
        skills = await self.call('db','list_dbo_skills',{})
        names = [s['name'] for s in skills.get('skills',[]) if s['name'] in {
            'database-inventory','database-health-and-core-metrics','hostinsights','database-capacity-usage-and-forecasting',
            'awr-discovery-primitives','database-performance-analysis'}]
        if not names:
            raise PolicyError('No supported DB discovery groups were found')
        listing = await self.call('db','list_dbo_tools',{'skill_names':names,'limit':100})
        operations=DB_OPERATIONS
        if getattr(self,'catalog_focus',None)=='sql':operations={'list_managed_databases','list_awr_dbs','list_awr_db_snapshots','get_awr_db_report'}
        approved = {x['name'] for x in listing.get('tools',[]) if x.get('mutable') is False and x['name'] in operations}
        for name in sorted(approved):
            spec = await self.call('db','describe_dbo_tool',{'tool_name':name})
            if spec.get('mutable') is False and spec.get('name') == name:
                self.contracts[name] = spec
        return {'tools':list(self.contracts.values()), 'scope':self.env['compartment_id'],
                'note':'Only this curated pilot catalog is exposed. Unlisted capabilities are unavailable here, not necessarily absent in OCI.'}

    async def db_read(self, args):
        await self.verify()
        op = args['operation']
        if op not in self.contracts:
            if op not in DB_OPERATIONS:raise PolicyError('Operation is not approved')
            raise ToolPrerequisiteError('Call db_catalog first and choose a returned read-only operation')
        if op.startswith('summarize_database_insight_') and 'list_database_insights' not in self.inventories_read:
            raise ToolPrerequisiteError('List database insights first, follow pagination, and match each database_id to its insight id. Managed databases and database insights are different inventories. For current Database Management activity use get_database_home_metrics with a returned managed database id.')
        spec = self.contracts[op]
        a = bound_arguments(args['arguments'], self.env['compartment_id'], spec['inputSchema'].get('properties',{}))
        self.awr.prepare(op,a)
        if op.startswith('summarize_database_insight_'):
            for value in a.get('id',[]):
                if not value.startswith('ocid1.opsidatabaseinsight.'):
                    raise ToolPrerequisiteError('The id filter requires database insight OCIDs returned by list_database_insights; use database_id for the matched database OCIDs.')
        # Every resource OCID must come from a scoped inventory in THIS run.
        for item in objects(a):
            for v in item.values():
                values = v if isinstance(v,list) else [v]
                for value in values:
                    if isinstance(value,str) and value.startswith('ocid1.') and value != self.env['compartment_id'] and value not in self.known_ids:
                        raise ToolPrerequisiteError('Resource ID has not been established by this environment inventory. List the appropriate scoped inventory and use only returned identifiers.')
        validate(a,spec['inputSchema'])
        if a.get('analysis_time_interval'):
            raise ToolPrerequisiteError('Use absolute time_interval_start and time_interval_end inside the selected window; analysis_time_interval overrides these bounds and is not allowed.')
        # Bound explicit trend intervals, including operations with optional windows.
        for key in ('time_interval_start','time_interval_end','start_time','end_time','time_start','time_end','time_greater_than_or_equal_to','time_less_than_or_equal_to'):
            if key in a:
                try:t = datetime.fromisoformat(a[key].replace('Z','+00:00'))
                except ValueError:raise ToolPrerequisiteError('Metric timestamps must be valid ISO UTC timestamps')
                if t.tzinfo is None or not datetime.fromisoformat(self.window[0]) <= t <= datetime.fromisoformat(self.window[1]):
                    raise ToolPrerequisiteError('Metric timestamps must be inside the selected UTC window. Preserve its exact boundaries, including fractional seconds: '+self.window[0]+' to '+self.window[1])
        for start,end in [('time_interval_start','time_interval_end'),('start_time','end_time')]:
            props = spec['inputSchema'].get('properties',{})
            if start in props:
                a.setdefault(start,self.window[0])
            if end in props:
                a.setdefault(end,self.window[1])
        if op=='get_database_home_metrics':
            start=datetime.fromisoformat(a['start_time'].replace('Z','+00:00')).astimezone(timezone.utc)
            end=datetime.fromisoformat(a['end_time'].replace('Z','+00:00')).astimezone(timezone.utc)
            # OCI validates retention against its current clock, not the chosen
            # end time. A saved seven-day window ages out while a run executes.
            earliest=datetime.now(timezone.utc)-timedelta(days=7)+timedelta(minutes=1)
            retention_trimmed=start<earliest
            if retention_trimmed:start=earliest
            # Round inward to OCI's required precision, preserving scope.
            if start.microsecond%1000:start += timedelta(microseconds=1000-start.microsecond%1000)
            end=end.replace(microsecond=end.microsecond//1000*1000)
            if end-start<timedelta(hours=1):
                raise ToolPrerequisiteError('Database Management requires at least one hour after millisecond normalization. Use a valid interval within the trusted window, or start a fresh interaction with a wider window.')
            a['start_time']=start.isoformat(timespec='milliseconds').replace('+00:00','Z')
            a['end_time']=end.isoformat(timespec='milliseconds').replace('+00:00','Z')
        if op=='get_database_home_metrics':self.home_metric_attempts.add(a.get('managed_database_id'))
        result = await self.call('db','invoke_dbo_tool',{'tool_name':op,'arguments':a})
        self.awr.observe(op,a,result)
        if op=='get_awr_db_report':
            result=sql_sections(result,self.awr.effective)
            self.sql_report_observed=bool(result['sql_sections']) if 'sql_sections' in result else False
            self.sql_report_partial=result.get('partial',True)
        if op=='get_database_home_metrics' and isinstance(result,dict):
            result['effective_window']={'start':a['start_time'],'end':a['end_time'],'precision':'milliseconds; rounded inward if needed',
                'local_start':start.astimezone(ZoneInfo('Europe/Rome')).isoformat(timespec='milliseconds'),
                'local_end':end.astimezone(ZoneInfo('Europe/Rome')).isoformat(timespec='milliseconds'),
                'provider_retention_trimmed':retention_trimmed,'note':'Database Management requires start within seven days of execution; any retention adjustment narrows the selected window.'}
        if op=='summarize_database_insight_resource_usage_trend' and a.get('resource_metric')=='CPU':
            data=result.get('data',{}) if isinstance(result,dict) else {}
            self.empty_cpu_trend = data.get('usage_data')==[]
        if op in INVENTORIES:
            self.inventories_read.add(op)
            # Only primary IDs of records explicitly assigned to this exact compartment.
            for row in objects(result):
                if row.get('compartment_id', row.get('compartmentId')) == self.env['compartment_id']:
                    if op=='list_managed_databases' and row.get('id'):
                        self.managed_resources[row['id']]={'name':row.get('name',row['id']),'subtype':row.get('database_sub_type')}
                    for key in ('id','database_id','databaseId'):
                        if isinstance(row.get(key),str) and row[key].startswith('ocid1.'):
                            self.known_ids.add(row[key])
        return result

    @traced('tool.gateway',lambda self,name,args:{'tool.name':name if name in {'log_query','db_catalog','db_read'} else 'unapproved'})
    async def execute(self, name, args):
        if name == 'log_query':
            result = await self.log_query(args)
        elif name == 'db_catalog':
            result = await self.catalog()
        elif name == 'db_read':
            result = await self.db_read(args)
            if args['operation']=='get_database_home_metrics' and isinstance(result,dict):
                home=result.get('data',{}).get('database_home_metrics',{})
                points=home.get('activity_time_series_metrics',[])
                if isinstance(points,list) and len(points)>100:
                    # Preserve full-window provider aggregates instead of letting
                    # a long activity series push the CPU aggregate past the cap.
                    home['activity_time_series_metrics']=points[:2]+points[-2:]
                    home['activity_sample_info']={'original_point_count':len(points),'returned_point_count':4,
                        'truncated':True,'first_timestamp':points[0].get('timestamp'),
                        'last_timestamp':points[-1].get('timestamp'),
                        'note':'Only activity samples are abbreviated. Provider aggregate metrics retain their original values and scope.'}
        else:
            raise PolicyError('Tool is not approved')
        text = redact(json.dumps(result,default=str))
        if len(text)>26000:
            return json.dumps({'partial':True,'reason':'Tool output exceeded the portal limit; narrow the query.','sample':text[:25000]})
        return text
