import { NextResponse } from 'next/server';
import {
  verifyPayload,
  signPayload,
  exchangeCode,
  tokenCookieName,
  PENDING_COOKIE,
} from '../../../../lib/mcp-oauth';
import { createLogger } from '../../../../lib/logger';

function returnUrl(request, result, pending) {
  const dest = pending?.returnTo || '/settings';
  let host = request.headers.get('x-forwarded-host') || request.headers.get('host');
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  host = host.replace(/:80$/, '').replace(/:443$/, '');
  const base = `${proto}://${host}`;
  const url = new URL(dest, base);
  url.searchParams.set('mcp_auth', result);
  return url.toString();
}

export async function GET(request) {
  const log = createLogger('mcp-oauth-callback');

  try {
    const params = new URL(request.url).searchParams;
    const code = params.get('code');
    const state = params.get('state');
    const error = params.get('error');

    if (error) {
      log.error('Authorization denied', { error, description: params.get('error_description') });
      return NextResponse.redirect(returnUrl(request, 'error', pending));
    }

    if (!code) {
      log.error('Missing code');
      return NextResponse.redirect(returnUrl(request, 'error', null));
    }

    // 1. Read pending state from cookie
    const pendingCookie = request.cookies.get(PENDING_COOKIE)?.value;
    const pending = await verifyPayload(pendingCookie);

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
    const tokens = await signPayload({
      endpoint: pending.endpoint,
      clientId: pending.clientId,
      clientSecret: pending.clientSecret,
      tokenEndpoint: pending.tokenEndpoint,
      accessToken: tokenData.access_token,
      refreshToken: tokenData.refresh_token,
      expiresAt: Date.now() + (tokenData.expires_in || 3600) * 1000,
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
    return NextResponse.redirect(returnUrl(request, 'error', pending));
  }
}
