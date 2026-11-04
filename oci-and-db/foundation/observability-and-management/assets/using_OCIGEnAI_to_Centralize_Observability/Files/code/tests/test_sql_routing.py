import unittest
from assistant.routing import route,permit_call,exposed_tools,validate_preference
from assistant.gateway import DB_OPERATIONS,TOOLS
from assistant.policy import ToolPrerequisiteError
from assistant.awr import AWRScope,sql_sections

W=('2026-10-26T08:00:00+00:00','2026-10-27T08:00:00+00:00')

class RoutingTests(unittest.TestCase):
    def test_sql_requests_and_typo_cannot_use_logs_as_ranking(self):
        for q in ['show top sql statements','the top slq statement','use observability mcp and show me the top sql statement','Which SQL is degrading?']:
            r=route(q,operations=DB_OPERATIONS);self.assertTrue(r['sql']);self.assertEqual(r['mcp'],'db')
            self.assertNotIn('log_query',[t['name'] for t in exposed_tools(TOOLS,r)])
            with self.assertRaises(ToolPrerequisiteError):permit_call(r,'log_query',{'query':'* | stats count'})
            permit_call(r,'db_read',{'operation':'list_managed_databases'})

    def test_explicit_source_and_operation_are_validated_without_expanding_access(self):
        self.assertIn('database-sql-performance',TOOLS[0]['parameters']['properties']['name']['enum'])
        r=route('Check logs','logan','log_query',DB_OPERATIONS)
        self.assertEqual([t['name'] for t in exposed_tools(TOOLS,r)],['load_skill','log_query'])
        for source,op in [('other','auto'),('db','log_query'),('auto','execute_sql'),('auto','delete_database')]:
            with self.assertRaises(ValueError):validate_preference(source,op,DB_OPERATIONS)
        self.assertTrue(route('Top SQL','logan','auto',DB_OPERATIONS)['conflict'])
        self.assertFalse(route('Find SQL errors in the logs',operations=DB_OPERATIONS)['sql'])

class AWRSafetyTests(unittest.TestCase):
    def prepared(self):
        s=AWRScope(W);s.observe('list_awr_dbs',{'managed_database_id':'db1'},{'data':{'items':[{'awr_db_id':'123','db_name':'DB1','container_id':0}]}})
        rows=[{'awr_db_id':'123','snapshot_id':i,'instance_number':1,'time_db_startup':'2026-10-01T00:00:00Z','time_end':f'2026-10-27T0{i}:00:00Z','error_count':0} for i in (1,2,3)]
        rows.append({**rows[0],'snapshot_id':999,'time_end':'2026-10-25T00:00:00Z'})
        s.observe('list_awr_db_snapshots',{'managed_database_id':'db1','awr_db_id':'123'},{'data':{'items':rows}})
        return s

    def test_report_uses_only_same_database_snapshot_pair_inside_window(self):
        s=self.prepared();a={'managed_database_id':'db1','awr_db_id':'123'};s.prepare('get_awr_db_report',a)
        self.assertEqual((a['begin_sn_id_greater_than_or_equal_to'],a['end_sn_id_less_than_or_equal_to']),(1,3))
        self.assertEqual(a['report_format'],'TEXT');self.assertEqual(a['inst_nums'],['1'])
        for extra in [{'begin_sn_id_greater_than_or_equal_to':999},{'begin_sn_id_greater_than_or_equal_to':2},{'container_id':5},{'inst_nums':['2']},{'report_format':'HTML'},{'time_greater_than_or_equal_to':'2026-10-25T00:00:00Z'}]:
            with self.assertRaises(ToolPrerequisiteError):s.prepare('get_awr_db_report',{'managed_database_id':'db1','awr_db_id':'123',**extra})
        with self.assertRaises(ToolPrerequisiteError):s.prepare('get_awr_db_report',{'managed_database_id':'db2','awr_db_id':'123'})

    def test_no_pair_and_database_restart_do_not_silently_expand_report(self):
        s=AWRScope(W);s.databases[('db1','123')]=0
        s.observe('list_awr_db_snapshots',{'managed_database_id':'db1','awr_db_id':'123'},{'items':[
            {'awr_db_id':'123','snapshot_id':1,'instance_number':1,'time_db_startup':'2026-10-26T00:00:00Z','time_end':'2026-10-27T01:00:00Z'},
            {'awr_db_id':'123','snapshot_id':2,'instance_number':1,'time_db_startup':'2026-10-27T01:30:00Z','time_end':'2026-10-27T02:00:00Z'}]})
        with self.assertRaises(ToolPrerequisiteError):s.prepare('get_awr_db_report',{'managed_database_id':'db1','awr_db_id':'123'})

    def test_sql_tables_survive_large_report_preamble_without_losing_limits(self):
        content='preamble\n'*5000+'SQL ordered by Elapsed Time           DB/Inst: DB1/DB1 Snaps: 1-3\nSQL ID abc123 12 seconds\nSQL ordered by Elapsed Time           DB/Inst: DB1/DB1 Snaps: 1-3\nSQL ID def123 11 seconds\nSQL ordered by CPU Time               DB/Inst: DB1/DB1 Snaps: 1-3\nSQL ID xyz123 5 seconds\nInstance Activity Stats\nother data'
        result=sql_sections({'data':{'report':{'content':content}}},{'start':W[0],'end':W[1]})
        self.assertEqual(len(result['sql_sections']),2);self.assertIn('abc123',result['sql_sections'][0]['text']);self.assertFalse(result['partial'])
        missing=sql_sections({'content':'No SQL sections'},{});self.assertTrue(missing['partial']);self.assertEqual(missing['sql_sections'],[])
