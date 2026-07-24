// NL2SQL invocation wiring (§1.5: Responses API + MCP). With Text-to-SQL enabled
// the chat request must attach the DBTools MCP server as a tool — OCI discovers
// its toolset (schema_information / sql_run) — with the OAuth bearer and the
// routing prompt that tells the model it has database access.
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { sendChatMessage } from './helpers';

const STORE_ID = 'ocid1.semanticstore.test.store1';
// The dev server inlines NEXT_PUBLIC_NL2SQL_MCP_URL from .env.development; the
// Playwright process doesn't see it, so read it the same way for the assertion.
const NL2SQL_URL = process.env.NEXT_PUBLIC_NL2SQL_MCP_URL || (() => {
  try {
    const env = fs.readFileSync(path.join(process.cwd(), '.env.development'), 'utf-8');
    return env.match(/^NEXT_PUBLIC_NL2SQL_MCP_URL=(.+)$/m)?.[1]?.trim() || '';
  } catch { return ''; }
})();
test.skip(!NL2SQL_URL, 'NEXT_PUBLIC_NL2SQL_MCP_URL not configured');

async function captureResponsesPayload(page, seed) {
  await page.addInitScript((s) => {
    localStorage.setItem('nativeToolsEnabled', JSON.stringify({ native_text_to_sql: true }));
    localStorage.setItem('nl2sqlSemanticStoreIds', JSON.stringify(s.ids));
    if (s.meta) localStorage.setItem('nl2sqlSemanticStores', JSON.stringify(s.meta));
  }, seed);

  // Pretend the user already authorized — the tool attaches the bearer.
  await page.route('**/api/mcp/oauth/token**', (route) =>
    route.fulfill({ json: { hasToken: true, accessToken: 'tok-nl2sql-test' } }));
  await page.route('**/api/conversations', (route) =>
    route.fulfill({ json: { id: 'conv-nl2sql-test', metadata: {} } }));
  await page.route('**/api/generate-title', (route) =>
    route.fulfill({ json: { title: 'NL2SQL test' } }));

  let payload = null;
  await page.route('**/api/responses', (route) => {
    payload = route.request().postDataJSON();
    const lines = [
      { response_id: 'resp_nl2sql' },
      { text: 'Here is your data.' },
      { done: true },
    ];
    return route.fulfill({
      contentType: 'text/event-stream',
      body: lines.map(l => JSON.stringify(l)).join('\n') + '\n',
    });
  });

  await page.goto('/');
  await sendChatMessage(page, 'How many orders did we ship last month?');
  await expect(page.getByText('Here is your data.')).toBeVisible({ timeout: 30_000 });
  return payload;
}

test('attaches the Nl2Sql MCP tool with bearer and the generate_sql prompt', async ({ page }) => {
  const payload = await captureResponsesPayload(page, {
    ids: [STORE_ID],
    meta: [{ id: STORE_ID, displayName: 'Sales DB', schemas: 'ADMIN' }],
  });

  const tool = (payload?.tools || []).find(t => t.server_label === 'Nl2Sql');
  expect(tool, 'Nl2Sql MCP tool not attached').toBeTruthy();
  expect(tool.type).toBe('mcp');
  expect(tool.server_url).toBe(NL2SQL_URL);
  expect(tool.authorization).toBe('tok-nl2sql-test');
  expect(tool.require_approval).toBe('never');

  // Prompt directs the model to call generate_sql with the NL question + the
  // Semantic Store id (guide §1.5). The chain executor intercepts that call,
  // generates the SQL (data plane) and runs it through sql_run.
  expect(payload.systemPrompt).toContain('Text-to-SQL');
  expect(payload.systemPrompt).toContain('generate_sql');
  expect(payload.systemPrompt).toContain('semanticStoreId');
  expect(payload.systemPrompt).toContain(STORE_ID);
});

test('tool + prompt still emitted when only store ids exist (legacy migration)', async ({ page }) => {
  const payload = await captureResponsesPayload(page, { ids: [STORE_ID], meta: null });

  const tool = (payload?.tools || []).find(t => t.server_label === 'Nl2Sql');
  expect(tool, 'Nl2Sql MCP tool not attached').toBeTruthy();
  expect(payload.systemPrompt).toContain('generate_sql');
});
