// Integration test for the client-side MCP execution loop (gpt-oss path):
// the model emits an OpenAI-style function_call for an MCP tool, the client
// must run the tool through /api/mcp and chain a follow-up request with
// function_call_output so the model can produce the final answer.
//
// Runs fully offline: /api/responses, /api/conversations and
// /api/generate-title are mocked at the browser level, while /api/mcp is the
// REAL proxy route hitting a throwaway MCP server this test spins up on
// localhost — so the JSON-RPC leg (auth handling included) is exercised for real.
import { test, expect } from '@playwright/test';
import http from 'node:http';
import { sendChatMessage } from './helpers';

// Serial: both tests drive full chat flows against the dev server and share the
// throwaway MCP server lifecycle — running them in parallel workers makes the
// second one flaky (timeouts on the chained response under concurrent load).
test.describe.configure({ mode: 'serial' });

const TOOL_OUTPUT = 'chain-ok-42: the warehouse holds 17 crates';

let mcpServer;
let mcpPort;
let mcpCalls = [];

test.beforeAll(async () => {
  mcpServer = http.createServer((req, res) => {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      let rpc = {};
      try { rpc = JSON.parse(body); } catch { /* keep {} */ }
      mcpCalls.push(rpc);
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        jsonrpc: '2.0',
        id: rpc.id ?? null,
        result: { content: [{ type: 'text', text: TOOL_OUTPUT }] },
      }));
    });
  });
  await new Promise((resolve) => mcpServer.listen(0, '127.0.0.1', resolve));
  mcpPort = mcpServer.address().port;
});

test.afterAll(async () => {
  await new Promise((resolve) => mcpServer.close(resolve));
});

test('function_call delegation runs the tool and chains the final answer', async ({ page }) => {
  mcpCalls = [];

  // The chain loop resolves servers from localStorage('mcpServers');
  // sanitizeLabel("echo srv") → "echo_srv" must match the fn_name below.
  await page.addInitScript(({ port }) => {
    localStorage.setItem('mcpServers', JSON.stringify([{
      id: 'srv-test',
      name: 'echo srv',
      endpoint: `http://127.0.0.1:${port}/mcp`,
      enabled: true,
      authType: 'none',
    }]));
  }, { port: mcpPort });

  await page.route('**/api/conversations', (route) =>
    route.fulfill({ json: { id: 'conv-chain-test', metadata: {} } }));
  await page.route('**/api/generate-title', (route) =>
    route.fulfill({ json: { title: 'Chain test' } }));

  let responsesCalls = 0;
  let chainedBody = null;
  await page.route('**/api/responses', async (route) => {
    responsesCalls += 1;
    if (responsesCalls === 1) {
      // Pass 1: the model "wants" the MCP tool but OCI didn't run it.
      const lines = [
        { thinking: true },
        { response_id: 'resp_test_1' },
        {
          mcp_function_call: {
            item_id: 'fc_test_1',
            call_id: 'call_test_1',
            fn_name: 'mcp__echo_srv__lookup_inventory',
            server_label: 'echo_srv',
            tool_name: 'lookup_inventory',
            arguments: '{"warehouse":"north"}',
          },
        },
        { done: true },
      ];
      return route.fulfill({
        contentType: 'text/event-stream',
        body: lines.map(l => JSON.stringify(l)).join('\n') + '\n',
      });
    }
    // Pass 2: the chained request must carry the tool result back.
    chainedBody = route.request().postDataJSON();
    const lines = [
      { response_id: 'resp_test_2' },
      { text: 'The north warehouse holds 17 crates.' },
      { done: true },
    ];
    return route.fulfill({
      contentType: 'text/event-stream',
      body: lines.map(l => JSON.stringify(l)).join('\n') + '\n',
    });
  });

  await page.goto('/');
  await sendChatMessage(page, 'How many crates in the north warehouse?');

  // Final answer rendered → the chain completed.
  await expect(page.getByText('The north warehouse holds 17 crates.'))
    .toBeVisible({ timeout: 30_000 });

  // The chip for the tool exists and is NOT stuck "calling".
  await expect(page.getByText(/Using Lookup inventory/i)).toHaveCount(0);
  await expect(page.getByText(/Lookup inventory/i).first()).toBeVisible();

  // The real /api/mcp leg hit our throwaway server: MCP handshake first,
  // then the actual call.
  expect(mcpCalls.map(c => c.method)).toEqual(['initialize', 'tools/call']);
  const toolCall = mcpCalls[1];
  expect(toolCall.params?.name).toBe('lookup_inventory');
  expect(toolCall.params?.arguments).toEqual({ warehouse: 'north' });

  // The chained request carried function_call + function_call_output.
  expect(responsesCalls).toBe(2);
  const inputItems = chainedBody?.input || [];
  const fnCall = inputItems.find(i => i.type === 'function_call');
  const fnOut = inputItems.find(i => i.type === 'function_call_output');
  expect(fnCall?.call_id).toBe('call_test_1');
  expect(fnOut?.call_id).toBe('call_test_1');
  expect(fnOut?.output).toContain(TOOL_OUTPUT);
});

test('Nl2Sql delegation runs the DBTools MCP tool via /api/mcp', async ({ page }) => {
  // Nl2Sql is the native MCP pseudo-server (label "Nl2Sql"), resolved from env
  // rather than mcpServers. When OCI delegates its tool call (a built-in like
  // schema_information), the chain executor must run it through the REAL /api/mcp
  // proxy against a throwaway MCP server. Before the synthesized config existed,
  // this died with "Server 'Nl2Sql' not configured".
  const mcpRequests = [];
  await page.route('**/api/mcp', (route) => {
    const body = route.request().postDataJSON();
    mcpRequests.push(body);
    if (body.method === 'initialize') {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 1, result: { serverInfo: { name: 'nl2sql' } }, _sessionId: 'sess-nl2sql-1' } });
    }
    return route.fulfill({ json: { jsonrpc: '2.0', id: 2, result: { content: [{ type: 'text', text: 'ORDERS, ORDER_ITEMS, PRODUCTS' }] } } });
  });
  await page.route('**/api/conversations', (route) =>
    route.fulfill({ json: { id: 'conv-nl2sql-chain', metadata: {} } }));
  await page.route('**/api/generate-title', (route) =>
    route.fulfill({ json: { title: 'NL2SQL chain' } }));

  let responsesCalls = 0;
  let chainedBody = null;
  await page.route('**/api/responses', async (route) => {
    responsesCalls += 1;
    if (responsesCalls === 1) {
      const lines = [
        { response_id: 'resp_nl2sql_1' },
        {
          mcp_function_call: {
            item_id: 'fc_nl2sql_1',
            call_id: 'call_nl2sql_1',
            fn_name: 'mcp__Nl2Sql__schema_information',
            server_label: 'Nl2Sql',
            tool_name: 'schema_information',
            arguments: '{"schema":"ADMIN","level":"DETAILED"}',
          },
        },
        { done: true },
      ];
      return route.fulfill({
        contentType: 'text/event-stream',
        body: lines.map(l => JSON.stringify(l)).join('\n') + '\n',
      });
    }
    chainedBody = route.request().postDataJSON();
    const lines = [
      { response_id: 'resp_nl2sql_2' },
      { text: 'The ADMIN schema has ORDERS, ORDER_ITEMS and PRODUCTS.' },
      { done: true },
    ];
    return route.fulfill({
      contentType: 'text/event-stream',
      body: lines.map(l => JSON.stringify(l)).join('\n') + '\n',
    });
  });

  await page.goto('/');
  await sendChatMessage(page, 'What tables are in ADMIN?');

  await expect(page.getByText('The ADMIN schema has ORDERS, ORDER_ITEMS and PRODUCTS.')).toBeVisible({ timeout: 30_000 });

  // The DBTools MCP server endpoint + oauth2.1 were synthesized; handshake then call.
  expect(mcpRequests.map(r => r.method)).toEqual(['initialize', 'tools/call']);
  expect(mcpRequests[1].endpoint).toContain('dbtools');
  expect(mcpRequests[1].authType).toBe('oauth2.1');
  expect(mcpRequests[1].params?.name).toBe('schema_information');

  // The model gets the tool result back, not a "not configured" error.
  const fnOut = (chainedBody?.input || []).find(i => i.type === 'function_call_output');
  expect(fnOut?.output).toContain('ORDERS');
  expect(fnOut?.output).not.toContain('not configured');
});

test('generate_sql delegation generates SQL then executes it via sql_run', async ({ page }) => {
  // Two-step NL2SQL (guide §1.5 + execution): the model calls generate_sql, and
  // the chain executor must INTERCEPT it — generate the SQL via /api/nl2sql (data
  // plane) then RUN it through the DBTools sql_run tool, returning the rows. The
  // model never calls sql_run itself; it only sees the data.
  await page.addInitScript(() => {
    localStorage.setItem('nativeToolsEnabled', JSON.stringify({ native_text_to_sql: true }));
    localStorage.setItem('nl2sqlSemanticStoreIds', JSON.stringify(['ocid1.semanticstore.test.s1']));
  });

  let nl2sqlBody = null;
  await page.route('**/api/nl2sql', (route) => {
    nl2sqlBody = route.request().postDataJSON();
    return route.fulfill({ json: { sql: 'SELECT COUNT(*) FROM ADMIN.ORDERS', status: 'SUCCEEDED' } });
  });

  const mcpRequests = [];
  await page.route('**/api/mcp', (route) => {
    const body = route.request().postDataJSON();
    mcpRequests.push(body);
    if (body.method === 'initialize') {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 1, result: { serverInfo: { name: 'nl2sql' } }, _sessionId: 'sess-gsql-1' } });
    }
    return route.fulfill({ json: { jsonrpc: '2.0', id: 2, result: { content: [{ type: 'text', text: 'TOTAL_ORDERS\n42' }] } } });
  });
  // native_text_to_sql is on, so the send path does a token pre-flight; pretend
  // the user already authorized so the message actually reaches /api/responses.
  await page.route('**/api/mcp/oauth/token**', (route) =>
    route.fulfill({ json: { hasToken: true, accessToken: 'tok-gsql-test' } }));
  await page.route('**/api/conversations', (route) =>
    route.fulfill({ json: { id: 'conv-gsql', metadata: {} } }));
  await page.route('**/api/generate-title', (route) =>
    route.fulfill({ json: { title: 'gen sql' } }));

  let responsesCalls = 0;
  let chainedBody = null;
  await page.route('**/api/responses', async (route) => {
    responsesCalls += 1;
    if (responsesCalls === 1) {
      const lines = [
        { response_id: 'resp_gsql_1' },
        {
          mcp_function_call: {
            item_id: 'fc_gsql_1',
            call_id: 'call_gsql_1',
            fn_name: 'mcp__Nl2Sql__generate_sql',
            server_label: 'Nl2Sql',
            tool_name: 'generate_sql',
            arguments: JSON.stringify({ inputNaturalLanguageQuery: 'How many orders?', metadata: { semanticStoreId: 'ocid1.semanticstore.test.s1' } }),
          },
        },
        { done: true },
      ];
      return route.fulfill({ contentType: 'text/event-stream', body: lines.map(l => JSON.stringify(l)).join('\n') + '\n' });
    }
    chainedBody = route.request().postDataJSON();
    const lines = [
      { response_id: 'resp_gsql_2' },
      { text: 'There are 42 orders.' },
      { done: true },
    ];
    return route.fulfill({ contentType: 'text/event-stream', body: lines.map(l => JSON.stringify(l)).join('\n') + '\n' });
  });

  await page.goto('/');
  await sendChatMessage(page, 'How many orders are there?');

  await expect(page.getByText('There are 42 orders.')).toBeVisible({ timeout: 30_000 });

  // Generation got the NL question + the store id.
  expect(nl2sqlBody?.question).toContain('orders');
  expect(nl2sqlBody?.semanticStoreId).toBe('ocid1.semanticstore.test.s1');

  // Execution ran the GENERATED SQL (not the model's text) through sql_run.
  expect(mcpRequests.map(r => r.method)).toEqual(['initialize', 'tools/call']);
  expect(mcpRequests[1].params?.name).toBe('sql_run');
  expect(mcpRequests[1].params?.arguments?.source).toBe('SELECT COUNT(*) FROM ADMIN.ORDERS');

  // The model got the rows back (with the SQL), not a "tool not found" error.
  const fnOut = (chainedBody?.input || []).find(i => i.type === 'function_call_output');
  expect(fnOut?.output).toContain('42');
  expect(fnOut?.output).toContain('SELECT COUNT(*)');
});

test('generate_sql execution retries once on a transient sql_run error', async ({ page }) => {
  // sql_run can hit a transient JSON-RPC error (OAuth-token blip / -32603). The
  // SELECT is read-only, so the intercept retries ONCE and the model still gets
  // the rows — the user never sees the blip.
  await page.addInitScript(() => {
    localStorage.setItem('nativeToolsEnabled', JSON.stringify({ native_text_to_sql: true }));
    localStorage.setItem('nl2sqlSemanticStoreIds', JSON.stringify(['ocid1.semanticstore.test.s1']));
  });
  await page.route('**/api/mcp/oauth/token**', (route) =>
    route.fulfill({ json: { hasToken: true, accessToken: 'tok' } }));
  await page.route('**/api/nl2sql', (route) =>
    route.fulfill({ json: { sql: 'SELECT 1 FROM dual', status: 'SUCCEEDED' } }));

  let sqlRunCalls = 0;
  await page.route('**/api/mcp', (route) => {
    const body = route.request().postDataJSON();
    if (body.method === 'initialize') {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 1, result: {}, _sessionId: 's1' } });
    }
    sqlRunCalls += 1;
    if (sqlRunCalls === 1) {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 2, error: { code: -32603, message: 'Authorization failed or requested resource not found.' } } });
    }
    return route.fulfill({ json: { jsonrpc: '2.0', id: 3, result: { content: [{ type: 'text', text: 'OK 7' }] } } });
  });
  await page.route('**/api/conversations', (route) => route.fulfill({ json: { id: 'c', metadata: {} } }));
  await page.route('**/api/generate-title', (route) => route.fulfill({ json: { title: 't' } }));

  let responsesCalls = 0;
  let chainedBody = null;
  await page.route('**/api/responses', async (route) => {
    responsesCalls += 1;
    if (responsesCalls === 1) {
      const lines = [
        { response_id: 'r1' },
        { mcp_function_call: { item_id: 'fc1', call_id: 'call1', fn_name: 'mcp__Nl2Sql__generate_sql', server_label: 'Nl2Sql', tool_name: 'generate_sql', arguments: JSON.stringify({ inputNaturalLanguageQuery: 'count?', metadata: { semanticStoreId: 'ocid1.semanticstore.test.s1' } }) } },
        { done: true },
      ];
      return route.fulfill({ contentType: 'text/event-stream', body: lines.map(l => JSON.stringify(l)).join('\n') + '\n' });
    }
    chainedBody = route.request().postDataJSON();
    const lines = [{ response_id: 'r2' }, { text: 'Done: 7.' }, { done: true }];
    return route.fulfill({ contentType: 'text/event-stream', body: lines.map(l => JSON.stringify(l)).join('\n') + '\n' });
  });

  await page.goto('/');
  await sendChatMessage(page, 'count?');
  await expect(page.getByText('Done: 7.')).toBeVisible({ timeout: 30_000 });

  // sql_run ran twice: first transient error → one retry → success.
  expect(sqlRunCalls).toBe(2);
  const fnOut = (chainedBody?.input || []).find(i => i.type === 'function_call_output');
  expect(fnOut?.output).toContain('OK 7');
  expect(fnOut?.output).not.toContain('Authorization failed');
});

test('generate_sql surfaces the Authorize banner when sql_run rejects a stale token', async ({ page }) => {
  // A stale OAuth token is rejected by the MCP server as a JSON-RPC error (HTTP
  // 200), not a 401 — so the user must get the Authorize banner to re-login,
  // NOT a dead error chip. (Also exercises the empty-metadata storeId fallback.)
  await page.addInitScript(() => {
    localStorage.setItem('nativeToolsEnabled', JSON.stringify({ native_text_to_sql: true }));
    localStorage.setItem('nl2sqlSemanticStoreIds', JSON.stringify(['ocid1.semanticstore.test.s1']));
  });
  await page.route('**/api/mcp/oauth/token**', (route) =>
    route.fulfill({ json: { hasToken: true, accessToken: 'tok' } }));
  await page.route('**/api/nl2sql', (route) =>
    route.fulfill({ json: { sql: 'SELECT 1 FROM dual', status: 'SUCCEEDED' } }));
  await page.route('**/api/mcp', (route) => {
    const body = route.request().postDataJSON();
    if (body.method === 'initialize') {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 1, result: {}, _sessionId: 's1' } });
    }
    return route.fulfill({ json: { jsonrpc: '2.0', id: 2, error: { code: -32603, message: 'Authorization failed or requested resource not found.' } } });
  });
  await page.route('**/api/conversations', (route) => route.fulfill({ json: { id: 'c', metadata: {} } }));
  await page.route('**/api/generate-title', (route) => route.fulfill({ json: { title: 't' } }));

  let responsesCalls = 0;
  await page.route('**/api/responses', async (route) => {
    responsesCalls += 1;
    const lines = responsesCalls === 1
      ? [
          { response_id: 'r1' },
          { mcp_function_call: { item_id: 'fc1', call_id: 'call1', fn_name: 'mcp__Nl2Sql__generate_sql', server_label: 'Nl2Sql', tool_name: 'generate_sql', arguments: JSON.stringify({ inputNaturalLanguageQuery: 'count?', metadata: {} }) } },
          { done: true },
        ]
      : [{ response_id: 'r2' }, { text: 'should not happen' }, { done: true }];
    return route.fulfill({ contentType: 'text/event-stream', body: lines.map(l => JSON.stringify(l)).join('\n') + '\n' });
  });

  await page.goto('/');
  await sendChatMessage(page, 'count?');

  // Stale token → Authorize banner (not a dead error), and the chain stops
  // before the follow-up answer.
  await expect(page.getByText(/Authorization needed/i)).toBeVisible({ timeout: 30_000 });
  expect(responsesCalls).toBe(1);
});
