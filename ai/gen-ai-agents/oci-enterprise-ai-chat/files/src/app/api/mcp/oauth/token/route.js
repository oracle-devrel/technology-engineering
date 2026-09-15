import { NextResponse } from 'next/server';
import { verifyPayload, signPayload, mintAccessToken, tokenCookieName } from '../../../../lib/mcp-oauth';
import { createLogger } from '../../../../lib/logger';

/**
 * GET /api/mcp/oauth/token?endpoint=...
 * Returns the current access token for a given MCP endpoint.
 * Used by the frontend to pass the token to OCI Responses API.
 */
export async function GET(request) {
  const log = createLogger('mcp-oauth-token');
  const endpoint = new URL(request.url).searchParams.get('endpoint');
  if (!endpoint) {
    return NextResponse.json({ error: 'endpoint is required' }, { status: 400 });
  }

  const cookieName = tokenCookieName(endpoint);
  const tokenCookie = request.cookies.get(cookieName)?.value;
  const tokens = await verifyPayload(tokenCookie);

  if (!tokens || (!tokens.refreshToken && !tokens.accessToken)) {
    log.info('No usable token', { endpoint: endpoint.slice(0, 60), hasCookie: !!tokenCookie, verified: !!tokens });
    return NextResponse.json({ hasToken: false });
  }

  // Access-token-only cookie: the provider issued no refresh token (GitHub OAuth
  // apps, Slack without rotation). Serve the stored token while it's valid;
  // once expired there is nothing to mint from — the user must re-authorize.
  if (!tokens.refreshToken) {
    const valid = tokens.expiresAt > Date.now() + 30000;
    if (new URL(request.url).searchParams.get('probe') === 'true') {
      return NextResponse.json({ hasToken: valid });
    }
    return valid
      ? NextResponse.json({ hasToken: true, accessToken: tokens.accessToken })
      : NextResponse.json({ hasToken: false });
  }

  // Settings status probe. It used to only check that the cookie EXISTS, which
  // showed "Authorized" while the refresh token was already dead — the user then
  // hit the auth banner on the very next message. Verify mintability for real;
  // the shared mint cache makes this one IdP roundtrip per token lifetime.
  if (new URL(request.url).searchParams.get('probe') === 'true') {
    try {
      await mintAccessToken(tokens.tokenEndpoint, tokens.refreshToken, tokens.clientId, tokens.clientSecret);
      return NextResponse.json({ hasToken: true });
    } catch (err) {
      log.error('Probe mint failed', { endpoint: endpoint.slice(0, 60), error: (err?.message || '').slice(0, 200) });
      return NextResponse.json({ hasToken: false });
    }
  }

  // The cookie stores ONLY the refresh token (the IDCS access JWT is ~3KB and would
  // blow past the browser's ~4KB cookie limit). Always mint a fresh access token
  // from the refresh token, and persist the (possibly rotated) refresh token.
  try {
    const minted = await mintAccessToken(
      tokens.tokenEndpoint, tokens.refreshToken, tokens.clientId, tokens.clientSecret
    );
    tokens.refreshToken = minted.refreshToken;
    tokens.expiresAt = minted.expiresAt;
    log.info('Access token served', { endpoint: endpoint.slice(0, 60) });

    const response = NextResponse.json({ hasToken: true, accessToken: minted.accessToken });
    const isHttps = (request.headers.get('x-forwarded-proto') || 'http') === 'https';
    response.cookies.set(cookieName, await signPayload(tokens), {
      httpOnly: true,
      secure: isHttps,
      sameSite: 'lax',
      maxAge: 30 * 24 * 60 * 60,
      path: '/',
    });
    return response;
  } catch (err) {
    // Surface the IdP's actual error — a silent hasToken:false here made the
    // Nl2Sql (Text-to-SQL) tool quietly drop out of requests with no trace of why.
    log.error('Refresh failed', { endpoint: endpoint.slice(0, 60), error: (err?.message || '').slice(0, 300) });
    return NextResponse.json({ hasToken: false });
  }
}
