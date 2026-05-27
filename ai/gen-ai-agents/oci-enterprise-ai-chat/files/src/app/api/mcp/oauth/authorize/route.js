import { NextResponse } from 'next/server';
import {
  fetchOAuthMetadata,
  registerClient,
  generateCodeVerifier,
  generateCodeChallenge,
  signPayload,
  PENDING_COOKIE,
} from '../../../../lib/mcp-oauth';
import { createLogger } from '../../../../lib/logger';

function getBaseUrl(request) {
  let host = request.headers.get('x-forwarded-host') || request.headers.get('host');
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  host = host.replace(/:80$/, '').replace(/:443$/, '');
  return `${proto}://${host}`;
}

export async function GET(request) {
  const log = createLogger('mcp-oauth-authorize');

  try {
    const params = new URL(request.url).searchParams;
    const endpoint = params.get('endpoint');
    const returnTo = params.get('returnTo') || '/settings';
    if (!endpoint) {
      return NextResponse.json({ error: 'endpoint query param is required' }, { status: 400 });
    }

    // Static-client mode (authType `oauth2-user`): the caller supplies the
    // pre-registered OAuth credentials in the query string. We skip discovery
    // and dynamic client registration entirely and just run PKCE.
    const staticClientId = params.get('clientId');
    const staticClientSecret = params.get('clientSecret') || '';
    const staticAuthorizeUrl = params.get('authorizeUrl');
    const staticTokenUrl = params.get('tokenUrl');
    const staticScope = params.get('scope') || '';
    const useStatic = !!(staticClientId && staticAuthorizeUrl && staticTokenUrl);

    const baseUrl = getBaseUrl(request);
    const redirectUri = `${baseUrl}/api/mcp/oauth/callback`;

    let clientId, clientSecret, authorizationEndpoint, tokenEndpoint, scopeList;

    if (useStatic) {
      clientId = staticClientId;
      clientSecret = staticClientSecret;
      authorizationEndpoint = staticAuthorizeUrl;
      tokenEndpoint = staticTokenUrl;
      scopeList = staticScope.split(/\s+/).filter(Boolean);
      log.info('OAuth (static client) authorize', { endpoint, authorizationEndpoint });
    } else {
      // 1. Discover OAuth metadata from MCP server (oauth2.1 flow)
      const metadata = await fetchOAuthMetadata(endpoint);
      if (!metadata) {
        return NextResponse.json({ error: 'MCP server does not support OAuth 2.1' }, { status: 502 });
      }
      log.info('OAuth metadata fetched', { endpoint });

      // 2. Register this app as an OAuth client (dynamic registration)
      scopeList = metadata.scopes_supported || ['read', 'write', 'generate'];
      const registration = await registerClient(metadata.registration_endpoint, redirectUri, scopeList);
      log.info('Client registered', { clientId: registration.client_id });

      clientId = registration.client_id;
      clientSecret = registration.client_secret;
      authorizationEndpoint = metadata.authorization_endpoint;
      tokenEndpoint = metadata.token_endpoint;
    }

    // 3. Generate PKCE pair
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = generateCodeChallenge(codeVerifier);
    const state = crypto.randomUUID();

    // 4. Store pending state in a signed cookie
    const pending = await signPayload({
      endpoint,
      clientId,
      clientSecret,
      codeVerifier,
      state,
      tokenEndpoint,
      redirectUri,
      returnTo,
    });

    // 5. First set the cookie, then redirect via an HTML page
    //    (direct 307 redirect may not persist cookies in all browsers)
    const authUrl = new URL(authorizationEndpoint);
    authUrl.searchParams.set('client_id', clientId);
    authUrl.searchParams.set('redirect_uri', redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    if (scopeList.length > 0) authUrl.searchParams.set('scope', scopeList.join(' '));
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('state', state);
    // Google requires these to issue a refresh_token + force the consent prompt
    // the first time. Harmless for other providers (they'll just ignore unknown params).
    if (useStatic) {
      authUrl.searchParams.set('access_type', 'offline');
      authUrl.searchParams.set('prompt', 'consent');
    }

    const html = `<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0;url=${authUrl.toString()}"></head><body>Redirecting...</body></html>`;
    const response = new Response(html, {
      status: 200,
      headers: { 'Content-Type': 'text/html' },
    });
    // Only emit Secure when serving over HTTPS — http://localhost rejects Secure cookies
    const isHttps = (request.headers.get('x-forwarded-proto') || 'http') === 'https';
    const cookieFlags = `Path=/; Max-Age=600; HttpOnly; SameSite=Lax${isHttps ? '; Secure' : ''}`;
    response.headers.append('Set-Cookie', `${PENDING_COOKIE}=${pending}; ${cookieFlags}`);
    return response;
  } catch (error) {
    log.error('OAuth authorize failed', { error: error.message });
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
