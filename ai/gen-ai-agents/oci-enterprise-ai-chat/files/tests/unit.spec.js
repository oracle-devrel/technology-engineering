// Pure logic tests — no browser, no network. Run through Playwright's runner so
// the ESM `src/` modules get transpiled without needing "type": "module" or
// extra tooling. `npm test` runs these alongside the API and smoke specs.
import { test, expect } from '@playwright/test';
import { splitMcpFunctionName } from '../src/app/lib/mcp-fn-name.js';
import {
  signPayload,
  verifyPayload,
  tokenCookieName,
  generateCodeChallenge,
  generateCodeVerifier,
  fixMetadataUrls,
  basePrefix,
} from '../src/app/lib/mcp-oauth.js';
import { isReadOnlySql } from '../src/app/lib/sqlGuard.js';

test.describe('isReadOnlySql (NL2SQL execution guard)', () => {
  test('allows a single SELECT', () => {
    expect(isReadOnlySql('SELECT COUNT(*) FROM ADMIN.ORDERS')).toBe(true);
  });
  test('allows a WITH (CTE) query and a trailing semicolon', () => {
    expect(isReadOnlySql('WITH t AS (SELECT 1 FROM dual) SELECT * FROM t;')).toBe(true);
  });
  test('rejects DML/DDL', () => {
    expect(isReadOnlySql('DELETE FROM ADMIN.ORDERS')).toBe(false);
    expect(isReadOnlySql('UPDATE ADMIN.ORDERS SET status = 1')).toBe(false);
    expect(isReadOnlySql('DROP TABLE ADMIN.ORDERS')).toBe(false);
  });
  test('rejects multiple statements', () => {
    expect(isReadOnlySql('SELECT 1 FROM dual; SELECT 2 FROM dual')).toBe(false);
  });
  test('rejects empty and procedural input', () => {
    expect(isReadOnlySql('')).toBe(false);
    expect(isReadOnlySql('BEGIN NULL; END;')).toBe(false);
  });
});

test.describe('splitMcpFunctionName', () => {
  test('splits a simple server__tool name', () => {
    expect(splitMcpFunctionName('mcp__my_server__send_mail')).toEqual({
      serverLabel: 'my_server',
      toolName: 'send_mail',
    });
  });

  test('keeps double underscores inside the tool name', () => {
    expect(splitMcpFunctionName('mcp__srv__do__thing')).toEqual({
      serverLabel: 'srv',
      toolName: 'do__thing',
    });
  });

  test('resolves labels containing __ when they are known', () => {
    // sanitizeLabel("PPT & Mail") → "PPT___Mail": the naive first-__ split breaks
    // this, the known-labels path must not.
    expect(splitMcpFunctionName('mcp__PPT___Mail__create_deck', ['PPT___Mail'])).toEqual({
      serverLabel: 'PPT___Mail',
      toolName: 'create_deck',
    });
  });

  test('prefers the longest known label on shared prefixes', () => {
    expect(splitMcpFunctionName('mcp__srv_v2__run', ['srv', 'srv_v2'])).toEqual({
      serverLabel: 'srv_v2',
      toolName: 'run',
    });
  });

  test('returns null for non-MCP names and malformed input', () => {
    expect(splitMcpFunctionName('get_weather')).toBeNull();
    expect(splitMcpFunctionName('mcp__')).toBeNull();
    expect(splitMcpFunctionName('mcp__only_server')).toBeNull();
    expect(splitMcpFunctionName(undefined)).toBeNull();
  });
});

test.describe('signed cookie payloads', () => {
  test('sign → verify roundtrips the payload', async () => {
    const payload = { endpoint: 'https://mcp.example.com/mcp', refreshToken: 'r-123', expiresAt: 1234567890 };
    const signed = await signPayload(payload);
    expect(await verifyPayload(signed)).toEqual(payload);
  });

  test('rejects tampered payloads and garbage', async () => {
    const signed = await signPayload({ a: 1 });
    const [b64, sig] = [signed.slice(0, signed.lastIndexOf('.')), signed.slice(signed.lastIndexOf('.') + 1)];
    const tampered = Buffer.from(JSON.stringify({ a: 2 })).toString('base64url') + '.' + sig;
    expect(await verifyPayload(tampered)).toBeNull();
    expect(await verifyPayload(b64)).toBeNull();        // signature stripped
    expect(await verifyPayload('nonsense')).toBeNull();
    expect(await verifyPayload(null)).toBeNull();
  });
});

test.describe('tokenCookieName', () => {
  test('is deterministic and endpoint-scoped', () => {
    const a = tokenCookieName('https://a.example.com/mcp');
    expect(a).toBe(tokenCookieName('https://a.example.com/mcp'));
    expect(a).toMatch(/^mcp-tok-[0-9a-f]{16}$/);
    expect(a).not.toBe(tokenCookieName('https://b.example.com/mcp'));
  });
});

test.describe('PKCE', () => {
  test('S256 challenge matches the RFC 7636 appendix B vector', () => {
    expect(generateCodeChallenge('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'))
      .toBe('E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM');
  });

  test('verifier is base64url and long enough', () => {
    const v = generateCodeVerifier();
    expect(v).toMatch(/^[A-Za-z0-9_-]{43,128}$/);
  });
});

test.describe('fixMetadataUrls', () => {
  const endpoint = 'https://mcp.example.com/sdd/mcp';

  test('prefixes endpoints missing the MCP base path', () => {
    const fixed = fixMetadataUrls({
      registration_endpoint: 'https://mcp.example.com/register',
      authorization_endpoint: 'https://mcp.example.com/authorize',
      token_endpoint: 'https://mcp.example.com/token',
    }, endpoint);
    expect(fixed.registration_endpoint).toBe('https://mcp.example.com/sdd/mcp/register');
    expect(fixed.authorization_endpoint).toBe('https://mcp.example.com/sdd/mcp/authorize');
    expect(fixed.token_endpoint).toBe('https://mcp.example.com/sdd/mcp/token');
  });

  test('leaves already-correct metadata untouched', () => {
    const metadata = {
      registration_endpoint: 'https://mcp.example.com/sdd/mcp/register',
      authorization_endpoint: 'https://mcp.example.com/sdd/mcp/authorize',
      token_endpoint: 'https://mcp.example.com/sdd/mcp/token',
    };
    expect(fixMetadataUrls(metadata, endpoint)).toEqual(metadata);
  });

  test('does not crash when registration_endpoint is absent (IDCS)', () => {
    const fixed = fixMetadataUrls({
      authorization_endpoint: 'https://idcs.example.com/oauth2/v1/authorize',
      token_endpoint: 'https://idcs.example.com/oauth2/v1/token',
    }, endpoint);
    // Probe falls back to authorization_endpoint; the IDCS URLs get the base path
    // prefixed (the documented one-level-metadata behavior).
    expect(fixed.authorization_endpoint).toBe('https://idcs.example.com/sdd/mcp/oauth2/v1/authorize');
  });

  test('returns metadata unchanged when the MCP endpoint has no path', () => {
    const metadata = { authorization_endpoint: 'https://x.example.com/authorize' };
    expect(fixMetadataUrls(metadata, 'https://mcp.example.com')).toEqual(metadata);
  });
});

test.describe('basePrefix', () => {
  test('strips trailing slashes and prefers APPLICATION_BASE_URL', () => {
    const prevApp = process.env.APPLICATION_BASE_URL;
    const prevBase = process.env.BASE_PATH;
    try {
      process.env.APPLICATION_BASE_URL = '/apps/123/actions/invoke/';
      process.env.BASE_PATH = '/other';
      expect(basePrefix()).toBe('/apps/123/actions/invoke');
      delete process.env.APPLICATION_BASE_URL;
      expect(basePrefix()).toBe('/other');
      delete process.env.BASE_PATH;
      expect(basePrefix()).toBe('');
    } finally {
      if (prevApp !== undefined) process.env.APPLICATION_BASE_URL = prevApp; else delete process.env.APPLICATION_BASE_URL;
      if (prevBase !== undefined) process.env.BASE_PATH = prevBase; else delete process.env.BASE_PATH;
    }
  });
});
