// Live tests against the REAL OCI Generative AI API. These cost tokens and need
// valid OCI credentials on the dev server, so they only run when explicitly
// requested:  LIVE_API=1 npx playwright test tests/live.spec.js
// `npm test` skips them entirely.
import { test, expect } from '@playwright/test';

const LIVE = process.env.LIVE_API === '1';
test.skip(!LIVE, 'live OCI tests only run with LIVE_API=1');

// Real model calls are slow — give every test plenty of room.
test.describe.configure({ timeout: 180_000 });

/** POST /api/responses and collect the NDJSON stream into an event list. */
async function streamResponses(request, payload) {
  const res = await request.post('/api/responses', { data: payload, timeout: 170_000 });
  expect(res.status(), await res.text().catch(() => '')).toBe(200);
  const body = await res.text();
  const events = body.split('\n').filter(Boolean).map(l => {
    try { return JSON.parse(l); } catch { return { _unparsed: l }; }
  });
  return events;
}

const textOf = (events) => events.filter(e => e.text).map(e => e.text).join('');
const hasDone = (events) => events.some(e => e.done === true);
const errorsOf = (events) => events.filter(e => e.error).map(e => e.error);

test.describe('live: /api/responses streaming', () => {
  for (const model of ['openai.gpt-oss-120b', 'google.gemini-2.5-flash']) {
    test(`plain chat completes on ${model}`, async ({ request }) => {
      const events = await streamResponses(request, {
        model,
        input: 'Reply with exactly the word: pong',
        systemPrompt: 'You are a terse echo bot.',
      });
      expect(errorsOf(events), `stream errors: ${errorsOf(events)}`).toEqual([]);
      expect(hasDone(events)).toBe(true);
      expect(textOf(events).toLowerCase()).toContain('pong');
      // response_id must be surfaced for chaining
      expect(events.some(e => e.response_id)).toBe(true);
    });
  }

  test('code_interpreter tool runs and streams chip events (gemini)', async ({ request }) => {
    // A hash is uncomputable mentally, so the model can't skip the sandbox the
    // way it does for trivial arithmetic. sha256("oci-live-test")[:8] = 76eb5f0a.
    const events = await streamResponses(request, {
      model: 'google.gemini-2.5-flash',
      input: 'Run Python to compute the SHA-256 hex digest of the exact string "oci-live-test" and reply with its first 8 hex characters.',
      tools: [{ type: 'code_interpreter', container: { type: 'auto', memory_limit: '4g' } }],
    });
    expect(errorsOf(events)).toEqual([]);
    expect(hasDone(events)).toBe(true);
    // The chip pipeline must see the tool: either live code deltas/status or the
    // final code_execution result (path depends on how OCI streams it).
    const sawTool = events.some(e => e.code_execution || e.code_delta || e.code_status
      || (e.mcp && e.mcp.tool === 'code_interpreter'));
    expect(sawTool, 'no code interpreter events in stream').toBe(true);
    expect(textOf(events)).toContain('76eb5f0a');
  });

  test('conversation roundtrip: create → chat → items persisted', async ({ request }) => {
    const conv = await request.post('/api/conversations', {
      data: { metadata: { topic: 'live-test' }, items: [] },
    });
    expect(conv.status()).toBe(200);
    const { id: conversationId } = await conv.json();
    expect(conversationId).toBeTruthy();

    const events = await streamResponses(request, {
      model: 'openai.gpt-oss-120b',
      input: 'Remember this codeword: ZANZIBAR. Confirm you got it.',
      conversationId,
    });
    expect(errorsOf(events)).toEqual([]);
    expect(hasDone(events)).toBe(true);

    // Second turn in the same conversation must see the first turn's context.
    const events2 = await streamResponses(request, {
      model: 'openai.gpt-oss-120b',
      input: 'What was the codeword? Reply with just the codeword.',
      conversationId,
    });
    expect(errorsOf(events2)).toEqual([]);
    expect(textOf(events2).toUpperCase()).toContain('ZANZIBAR');

    // Items API returns the stored turns.
    const items = await request.get(`/api/conversations?id=${conversationId}&getItems=true`);
    expect(items.status()).toBe(200);
    const itemList = (await items.json()).data || [];
    const roles = itemList.map(i => i.role).filter(Boolean);
    expect(roles).toContain('user');
    expect(roles).toContain('assistant');
  });
});

test.describe('live: NL2SQL data plane', () => {
  test('generateSqlFromNl returns real SQL for the active semantic store', async ({ request }) => {
    const stores = await request.get('/api/semantic-stores');
    expect(stores.status()).toBe(200);
    const active = ((await stores.json()).items || []).find(s => s.lifecycleState === 'ACTIVE');
    test.skip(!active, 'no ACTIVE semantic store in the tenancy');

    const res = await request.post('/api/nl2sql', {
      data: {
        inputNaturalLanguageQuery: 'How many orders are there in total?',
        semanticStoreId: active.id,
      },
      timeout: 120_000,
    });
    expect(res.status(), await res.text().catch(() => '')).toBe(200);
    const body = await res.json();
    expect(body.lifecycleState).toBe('SUCCEEDED');
    expect(body.sql.toUpperCase()).toContain('SELECT');
  });
});

test.describe('live: full UI chat', () => {
  test('user sends a message and the assistant answer renders', async ({ page }) => {
    await page.goto('/');
    const input = page.locator('textarea').first();
    await expect(input).toBeVisible({ timeout: 30_000 });

    await input.fill('Reply with exactly: WORKS');
    await input.press('Enter');

    // The user bubble appears immediately; the assistant text streams in after.
    await expect(page.getByText('WORKS', { exact: false }).nth(1))
      .toBeVisible({ timeout: 120_000 });

    // No error banner in the exchange.
    await expect(page.getByText(/mcp_auth_expired|OCI API Error|Stream closed/i))
      .toHaveCount(0);
  });
});
