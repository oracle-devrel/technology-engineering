import { NextResponse } from 'next/server';
import { verifyPayload, signPayload, refreshAccessToken, tokenCookieName } from '../../../../lib/mcp-oauth';

/**
 * GET /api/mcp/oauth/token?endpoint=...
 * Returns the current access token for a given MCP endpoint.
 * Used by the frontend to pass the token to OCI Responses API.
 */
export async function GET(request) {
  const endpoint = new URL(request.url).searchParams.get('endpoint');
  if (!endpoint) {
    return NextResponse.json({ error: 'endpoint is required' }, { status: 400 });
  }

  const cookieName = tokenCookieName(endpoint);
  const tokenCookie = request.cookies.get(cookieName)?.value;
  const tokens = await verifyPayload(tokenCookie);

  if (!tokens || !tokens.refreshToken) {
    return NextResponse.json({ hasToken: false });
  }

  // Lightweight presence check (used by Settings to show authorized/needs_auth).
  // Does NOT consume the refresh token.
  if (new URL(request.url).searchParams.get('probe') === 'true') {
    return NextResponse.json({ hasToken: true });
  }

  // The cookie stores ONLY the refresh token (the IDCS access JWT is ~3KB and would
  // blow past the browser's ~4KB cookie limit). Always mint a fresh access token
  // from the refresh token, and persist the (possibly rotated) refresh token.
  try {
    const refreshed = await refreshAccessToken(
      tokens.tokenEndpoint, tokens.refreshToken, tokens.clientId, tokens.clientSecret
    );
    tokens.refreshToken = refreshed.refresh_token || tokens.refreshToken;
    tokens.expiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;

    const response = NextResponse.json({ hasToken: true, accessToken: refreshed.access_token });
    const isHttps = (request.headers.get('x-forwarded-proto') || 'http') === 'https';
    response.cookies.set(cookieName, await signPayload(tokens), {
      httpOnly: true,
      secure: isHttps,
      sameSite: 'lax',
      maxAge: 30 * 24 * 60 * 60,
      path: '/',
    });
    return response;
  } catch {
    return NextResponse.json({ hasToken: false });
  }
}
