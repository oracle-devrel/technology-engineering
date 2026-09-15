import { NextResponse } from 'next/server';
import { createLogger } from '../../../../lib/logger';

/**
 * POST /api/mcp/oauth2-cc/token
 * Body: { tokenUrl, clientId, clientSecret, scope? }
 *
 * OAuth 2.0 Client Credentials Grant (RFC 6749 §4.4).
 * Server-side because browsers usually can't reach the token endpoint due to CORS,
 * and Basic Auth credentials shouldn't leave through the browser fetch.
 *
 * Tokens are cached in-process by (tokenUrl, clientId, scope) until ~60s before expiry.
 */

// In-memory cache shared across requests in the same Node process
// Key: `${tokenUrl}::${clientId}::${scope || ''}`
// Value: { accessToken, expiresAt }
const tokenCache = new Map();
const REFRESH_BUFFER_MS = 60_000; // refresh 60s before actual expiry

export async function POST(request) {
  const log = createLogger('mcp-oauth2-cc');

  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { tokenUrl, clientId, clientSecret, scope } = body || {};

  if (!tokenUrl || !clientId || !clientSecret) {
    return NextResponse.json(
      { error: 'tokenUrl, clientId and clientSecret are required' },
      { status: 400 }
    );
  }

  const cacheKey = `${tokenUrl}::${clientId}::${scope || ''}`;
  const cached = tokenCache.get(cacheKey);
  if (cached && cached.expiresAt > Date.now() + REFRESH_BUFFER_MS) {
    return NextResponse.json({
      accessToken: cached.accessToken,
      expiresAt: cached.expiresAt,
      cached: true,
    });
  }

  // Build form body. Many enterprise IdPs (IDCS included) reject Basic Auth and
  // only accept creds in the body. Use body-creds for max compatibility — same
  // pattern as the working /api/mcp proxy.
  const params = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: clientId,
    client_secret: clientSecret,
  });
  if (scope) params.set('scope', scope);

  let res;
  try {
    res = await fetch(tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
      },
      body: params.toString(),
    });
  } catch (err) {
    log.error('Token endpoint unreachable', { tokenUrl, error: err.message });
    return NextResponse.json(
      { error: `Token endpoint unreachable: ${err.message}` },
      { status: 502 }
    );
  }

  if (!res.ok) {
    const errText = await res.text().catch(() => '');
    log.warn('Token request failed', { tokenUrl, status: res.status, body: errText.slice(0, 500) });
    return NextResponse.json(
      { error: `Token request failed (${res.status}): ${errText.slice(0, 300)}` },
      { status: res.status }
    );
  }

  const data = await res.json().catch(() => null);
  if (!data || !data.access_token) {
    return NextResponse.json(
      { error: 'Token endpoint did not return access_token' },
      { status: 502 }
    );
  }

  const expiresInMs = (typeof data.expires_in === 'number' ? data.expires_in : 3600) * 1000;
  const expiresAt = Date.now() + expiresInMs;

  tokenCache.set(cacheKey, { accessToken: data.access_token, expiresAt });
  log.info('Token issued', { tokenUrl, clientId, expiresInMs });

  return NextResponse.json({
    accessToken: data.access_token,
    expiresAt,
    tokenType: data.token_type || 'Bearer',
    cached: false,
  });
}
