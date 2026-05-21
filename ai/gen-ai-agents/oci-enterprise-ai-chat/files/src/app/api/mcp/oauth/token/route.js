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

  if (!tokens) {
    return NextResponse.json({ hasToken: false });
  }

  // Force refresh if requested, or if expiring within 30s
  const forceRefresh = new URL(request.url).searchParams.get('refresh') === 'true';
  if (forceRefresh || tokens.expiresAt < Date.now() + 30000) {
    try {
      const refreshed = await refreshAccessToken(
        tokens.tokenEndpoint, tokens.refreshToken, tokens.clientId, tokens.clientSecret
      );
      tokens.accessToken = refreshed.access_token;
      tokens.refreshToken = refreshed.refresh_token || tokens.refreshToken;
      tokens.expiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;

      const response = NextResponse.json({ hasToken: true, accessToken: tokens.accessToken });
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

  return NextResponse.json({ hasToken: true, accessToken: tokens.accessToken });
}
