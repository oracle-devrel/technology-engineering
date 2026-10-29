import unittest
from types import SimpleNamespace
from assistant.policy import safe_query,PolicyError,QueryValidationError
from assistant.mcp_client import unpack,MCPToolError
from assistant.agent import tool_failure

class LogFeedbackTests(unittest.TestCase):
    def test_valid_multiline_and_literal_pipe_queries_preserve_guard(self):
        for q in ['* | stats\ncount as Records', '"ORA-00600|ORA-00060" | fields Time, Entity | head 10', '"count()" | head 1']:
            self.assertEqual(safe_query(q),q)
        for q in ['* | export bucket', '* | stats count | execute command', '* |', '* | where Entity = "unterminated']:
            with self.assertRaises(QueryValidationError):safe_query(q)

    def test_sql_and_empty_count_receive_correctable_syntax_feedback(self):
        for q in ['SELECT COUNT(*) FROM logs','* | stats count() as Records']:
            with self.assertRaises(QueryValidationError) as caught:safe_query(q)
            feedback=tool_failure(caught.exception)
            self.assertEqual(feedback['error'],'invalid_log_query')
            self.assertTrue(feedback['correctable'])
        self.assertEqual(tool_failure(PolicyError('Cross-compartment access is blocked'))['error'],'scope_denied')

    def test_upstream_query_errors_are_not_reported_as_iam_denials(self):
        result=SimpleNamespace(isError=False,structuredContent=None,content=[SimpleNamespace(text="Error: {'status': 400, 'code': 'InvalidParameter', 'message': 'Missing input for STATS function COUNT. Syntax: STATS COUNT'}")])
        with self.assertRaises(MCPToolError) as caught:unpack(result)
        feedback=tool_failure(caught.exception)
        self.assertEqual(feedback['error'],'query_rejected')
        self.assertTrue(feedback['correctable'])
        self.assertNotIn('opc-request-id',feedback['message'])
        self.assertEqual(tool_failure(RuntimeError('Connection closed'))['error'],'operation_failed')
        self.assertFalse(tool_failure(RuntimeError('Connection closed'))['correctable'])

    def test_explicit_authorization_and_missing_resource_remain_distinct(self):
        for status,category in [(401,'authentication_failed'),(403,'permission_denied'),(404,'resource_unavailable'),(500,'service_unavailable')]:
            self.assertEqual(MCPToolError("{'status': "+str(status)+"}").category,category)

    def test_where_text_search_rejection_returns_usable_leading_filter(self):
        error=MCPToolError("{'status':400,'message':'Unexpected input for WHERE: like','private':'do-not-return'}")
        self.assertEqual(error.category,'query_rejected')
        self.assertIn('before the first pipe',str(error))
        self.assertIn("'Original Log Content' like '%ORA-%' | stats count",str(error))
        self.assertNotIn('do-not-return',str(error))
