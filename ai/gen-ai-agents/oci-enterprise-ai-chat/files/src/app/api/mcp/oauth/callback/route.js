import { NextResponse } from 'next/server';
import {
  verifyPayload,
  signPayload,
  exchangeCode,
  tokenCookieName,
  basePrefix,
  PENDING_COOKIE,
} from '../../../../lib/mcp-oauth';
import { createLogger } from '../../../../lib/logger';

function returnUrl(request, result, pending, detail) {
  // returnTo from the client already carries the deployment prefix (it's the
  // browser's window.location.pathname); only the fallback needs basePrefix().
  const dest = pending?.returnTo || `${basePrefix()}/settings`;
  let host = request.headers.get('x-forwarded-host') || request.headers.get('host');
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  host = host.replace(/:80$/, '').replace(/:443$/, '');
  const base = `${proto}://${host}`;
  const url = new URL(dest, base);
  url.searchParams.set('mcp_auth', result);
  if (detail) url.searchParams.set('mcp_error', String(detail).slice(0, 300));
  return url.toString();
}

export async function GET(request) {
  const log = createLogger('mcp-oauth-callback');

  // Declared at function scope so the catch block (and the early error paths)
  // can use it to build returnTo without a ReferenceError.
  let pending = null;
  try {
    const params = new URL(request.url).searchParams;
    const code = params.get('code');
    const error = params.get('error');

    // 1. Read pending state from cookie early — so returnTo works even when the
    //    IdP redirects back with ?error=... (e.g. unauthorized_client / bad scope).
    const pendingCookie = request.cookies.get(PENDING_COOKIE)?.value;
    pending = await verifyPayload(pendingCookie);

    if (error) {
      log.error('Authorization denied', { error, description: params.get('error_description') });
      return NextResponse.redirect(returnUrl(request, 'error', pending, params.get('error_description') || error));
    }

    if (!code) {
      log.error('Missing code');
      return NextResponse.redirect(returnUrl(request, 'error', pending, 'No authorization code returned'));
    }

    if (!pending) {
      log.error('Missing or invalid pending cookie', {
        hasCookie: !!pendingCookie,
        cookies: request.cookies.getAll().map(c => c.name),
      });
      return NextResponse.redirect(returnUrl(request, 'error', null));
    }

    // 2. Exchange authorization code for tokens
    const tokenData = await exchangeCode(
      pending.tokenEndpoint,
      code,
      pending.codeVerifier,
      pending.clientId,
      pending.clientSecret,
      pending.redirectUri,
    );
    log.info('Token exchange successful', { endpoint: pending.endpoint });

    // 3. Persist tokens in a signed cookie
    //
    // Two storage shapes depending on what the provider issued:
    // - refresh_token present (IDCS, Google with offline access): store ONLY the
    //   refresh token. The access JWT (~3KB for IDCS) would push the signed cookie
    //   past the browser's ~4KB limit and the cookie gets dropped (hasToken=false).
    //   /api/mcp/oauth/token mints a fresh access token on demand.
    // - NO refresh_token (GitHub OAuth apps, Slack without rotation): store the
    //   access token itself — those are small opaque strings, and without it the
    //   cookie would be unusable (nothing to mint from). When the provider also
    //   omits expires_in, the token is long-lived; cap it at the cookie's 30 days.
    const hasRefresh = !!tokenData.refresh_token;
    const expiresInMs = tokenData.expires_in
      ? tokenData.expires_in * 1000
      : (hasRefresh ? 3600 * 1000 : 30 * 24 * 60 * 60 * 1000);
    const tokens = await signPayload({
      endpoint: pending.endpoint,
      clientId: pending.clientId,
      clientSecret: pending.clientSecret,
      tokenEndpoint: pending.tokenEndpoint,
      refreshToken: tokenData.refresh_token || null,
      ...(hasRefresh ? {} : { accessToken: tokenData.access_token }),
      expiresAt: Date.now() + expiresInMs,
    });

    const response = NextResponse.redirect(returnUrl(request, 'success', pending));

    // Only mark Secure when the app is actually served over HTTPS — Chrome
    // rejects Secure cookies set during a redirect that lands on http://localhost.
    const isHttps = (request.headers.get('x-forwarded-proto') || 'http') === 'https';
    response.cookies.set(tokenCookieName(pending.endpoint), tokens, {
      httpOnly: true,
      secure: isHttps,
      sameSite: 'lax',
      maxAge: 30 * 24 * 60 * 60, // 30 days
      path: '/',
    });
    response.cookies.delete(PENDING_COOKIE);

    return response;
  } catch (error) {
    log.error('OAuth callback failed', { error: error.message });
    return NextResponse.redirect(returnUrl(request, 'error', pending, error.message));
  }
}
