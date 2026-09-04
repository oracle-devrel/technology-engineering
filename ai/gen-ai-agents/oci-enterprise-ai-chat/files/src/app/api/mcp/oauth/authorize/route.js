import { NextResponse } from 'next/server';
import {
  fetchOAuthMetadata,
  registerClient,
  generateCodeVerifier,
  generateCodeChallenge,
  signPayload,
  basePrefix,
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
    // basePrefix() re-adds the OCI Hosted Deployment prefix OCI stripped, so the
    // redirect_uri is routable when the IdP sends the browser back. It's stored in
    // the PENDING cookie and reused verbatim for the token exchange (callback).
    const redirectUri = `${baseUrl}${basePrefix()}/api/mcp/oauth/callback`;

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

      // 2. Determine the OAuth client. The discovery above already yielded the
      //    authorize/token endpoints (works for both one-level and RFC 9728).
      scopeList = metadata.scopes_supported || ['read', 'write', 'generate'];
      authorizationEndpoint = metadata.authorization_endpoint;
      tokenEndpoint = metadata.token_endpoint;

      if (metadata.registration_endpoint) {
        // 2a. Dynamic client registration (RFC 7591)
        const registration = await registerClient(metadata.registration_endpoint, redirectUri, scopeList);
        log.info('Client registered', { clientId: registration.client_id });
        clientId = registration.client_id;
        clientSecret = registration.client_secret;
      } else {
        // 2b. No dynamic registration (OCI IAM Identity Domains don't expose it).
        // Use a pre-registered confidential client supplied via env. Wired for the
        // NL2SQL MCP endpoint; the secret stays server-side (never hits the browser).
        const nl2sqlUrl = process.env.NEXT_PUBLIC_NL2SQL_MCP_URL || process.env.NL2SQL_MCP_URL || '';
        const envClientId = process.env.NL2SQL_OAUTH_CLIENT_ID;
        const envClientSecret = process.env.NL2SQL_OAUTH_CLIENT_SECRET || '';
        if (envClientId && nl2sqlUrl && endpoint === nl2sqlUrl) {
          clientId = envClientId;
          clientSecret = envClientSecret;
          // IDCS only returns a refresh_token when offline_access is requested.
          if (!scopeList.includes('offline_access')) scopeList = [...scopeList, 'offline_access'];
          log.info('OAuth (pre-registered confidential client) authorize', { endpoint });
        } else {
          return NextResponse.json({
            error: "This authorization server has no dynamic client registration. Set NL2SQL_OAUTH_CLIENT_ID / NL2SQL_OAUTH_CLIENT_SECRET (a pre-registered confidential app) to enable it.",
            code: 'no_dynamic_registration',
          }, { status: 502 });
        }
      }
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
