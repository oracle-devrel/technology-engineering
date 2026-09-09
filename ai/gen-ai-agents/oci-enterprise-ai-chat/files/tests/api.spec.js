// API route contract tests. These run against the dev server (webServer in
// playwright.config.js) and only exercise paths that need NO OCI credentials:
// input validation, auth guards, and error shaping.
import { test, expect } from '@playwright/test';

test.describe('/api/responses', () => {
  test('rejects missing input with a 400 JSON error', async ({ request }) => {
    const res = await request.post('/api/responses', { data: {} });
    expect(res.status()).toBe(400);
    expect((await res.json()).error).toContain('Input is required');
  });

  test('returns a JSON error (not an HTML 500) on malformed body', async ({ request }) => {
    // Regression: the catch block referenced try-scoped LangFuse vars, so a
    // malformed body died with a ReferenceError → opaque Next 500 page.
    // Buffer keeps the body raw — a string here gets re-serialized to valid JSON.
    const res = await request.post('/api/responses', {
      headers: { 'Content-Type': 'application/json' },
      data: Buffer.from('{not json'),
    });
    expect(res.status()).toBe(500);
    const body = await res.json(); // throws if the response is Next's HTML error page
    expect(typeof body.error).toBe('string');
    expect(body.error.length).toBeGreaterThan(0);
  });
});

test.describe('/api/mcp', () => {
  test('rejects missing endpoint and missing method', async ({ request }) => {
    const noEndpoint = await request.post('/api/mcp', { data: {} });
    expect(noEndpoint.status()).toBe(400);
    expect((await noEndpoint.json()).error).toContain('endpoint');

    const noMethod = await request.post('/api/mcp', { data: { endpoint: 'https://x.example.com/mcp' } });
    expect(noMethod.status()).toBe(400);
    expect((await noMethod.json()).error).toContain('method');
  });

  for (const authType of ['oauth2.1', 'oauth2-user']) {
    test(`asks for auth when no token cookie exists (${authType})`, async ({ request }) => {
      const res = await request.post('/api/mcp', {
        data: {
          endpoint: 'https://never-authorized.example.com/mcp',
          method: 'tools/list',
          authType,
        },
      });
      expect(res.status()).toBe(401);
      const body = await res.json();
      expect(body.error).toBe('needs_auth');
      expect(body.authorizeUrl).toContain('/api/mcp/oauth/authorize?endpoint=');
    });
  }
});

test.describe('/api/mcp/oauth/token', () => {
  test('requires the endpoint param', async ({ request }) => {
    const res = await request.get('/api/mcp/oauth/token');
    expect(res.status()).toBe(400);
  });

  test('reports hasToken:false without a cookie (plain and probe)', async ({ request }) => {
    const endpoint = encodeURIComponent('https://never-authorized.example.com/mcp');
    for (const probe of ['', '&probe=true']) {
      const res = await request.get(`/api/mcp/oauth/token?endpoint=${endpoint}${probe}`);
      expect(res.status()).toBe(200);
      expect(await res.json()).toEqual({ hasToken: false });
    }
  });
});

test.describe('/api/mcp/oauth/authorize', () => {
  test('requires the endpoint param', async ({ request }) => {
    const res = await request.get('/api/mcp/oauth/authorize');
    expect(res.status()).toBe(400);
    expect((await res.json()).error).toContain('endpoint');
  });
});
