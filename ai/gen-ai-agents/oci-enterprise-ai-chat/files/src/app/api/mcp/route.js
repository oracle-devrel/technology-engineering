import { NextResponse } from 'next/server';
import { createLogger } from '../../lib/logger';
import { verifyPayload, signPayload, refreshAccessToken, tokenCookieName } from '../../lib/mcp-oauth';

// Store session IDs per endpoint (in production, use Redis or similar)
const sessionIds = new Map();

// Cache OAuth tokens per token URL + client ID
const oauthTokenCache = new Map();

async function getOAuthToken(tokenUrl, clientId, clientSecret, scope) {
  const cacheKey = `${tokenUrl}:${clientId}`;
  const cached = oauthTokenCache.get(cacheKey);
  if (cached && cached.expiresAt > Date.now() + 30000) {
    return cached.accessToken;
  }

  const body = new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: clientId,
    client_secret: clientSecret,
  });
  if (scope) body.set('scope', scope);

  const res = await fetch(tokenUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`OAuth token request failed: ${res.status} ${errText}`);
  }

  const data = await res.json();
  if (!data.access_token) {
    throw new Error(`OAuth token response missing access_token: ${JSON.stringify(data).slice(0, 200)}`);
  }
  oauthTokenCache.set(cacheKey, {
    accessToken: data.access_token,
    expiresAt: Date.now() + (data.expires_in || 3600) * 1000,
  });

  return data.access_token;
}

export async function POST(request) {
  try {
    const { endpoint, method, params = {}, sessionId, authType, authKey, oauth } = await request.json();

    if (!endpoint) {
      return NextResponse.json({ error: 'endpoint is required' }, { status: 400 });
    }

    if (!method) {
      return NextResponse.json({ error: 'method is required' }, { status: 400 });
    }

    const url = endpoint;

    // Build JSON-RPC request
    const jsonRpcRequest = {
      jsonrpc: '2.0',
      id: Date.now(),
      method: method,
      params: params
    };

    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/event-stream'
    };

    // Add auth headers if provided
    let updatedTokenCookie = null; // set if oauth2.1 token was refreshed

    if (authType === 'oauth2.1') {
      // Read tokens from httpOnly cookie set by /api/mcp/oauth/callback
      const cookieName = tokenCookieName(endpoint);
      const tokenCookie = request.cookies.get(cookieName)?.value;
      const tokens = await verifyPayload(tokenCookie);

      if (!tokens) {
        return NextResponse.json({
          error: 'needs_auth',
          authorizeUrl: `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(endpoint)}`,
        }, { status: 401 });
      }

      // Refresh if token expires within 30s
      if (tokens.expiresAt < Date.now() + 30000) {
        try {
          const refreshed = await refreshAccessToken(
            tokens.tokenEndpoint, tokens.refreshToken, tokens.clientId, tokens.clientSecret
          );
          tokens.accessToken = refreshed.access_token;
          tokens.refreshToken = refreshed.refresh_token || tokens.refreshToken;
          tokens.expiresAt = Date.now() + (refreshed.expires_in || 3600) * 1000;
          updatedTokenCookie = { name: cookieName, value: await signPayload(tokens) };
        } catch {
          return NextResponse.json({
            error: 'needs_auth',
            authorizeUrl: `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(endpoint)}`,
          }, { status: 401 });
        }
      }

      headers['Authorization'] = `Bearer ${tokens.accessToken}`;
    } else if (authType === 'oauth2' && oauth) {
      const token = await getOAuthToken(oauth.tokenUrl, oauth.clientId, oauth.clientSecret, oauth.scope);
      headers['Authorization'] = `Bearer ${token}`;
    } else if (authType && authKey) {
      if (authType === 'api-key') {
        headers['X-API-KEY'] = authKey;
      } else if (authType === 'bearer') {
        headers['Authorization'] = `Bearer ${authKey}`;
      }
    }

    // Add session ID if provided (for subsequent requests after initialize)
    if (sessionId && method !== 'initialize') {
      headers['Mcp-Session-Id'] = sessionId;
    }

    const log = createLogger('mcp-proxy');
    log.info('MCP request', { method, params: JSON.stringify(params).slice(0, 200) });

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(jsonRpcRequest)
    });

    // Check for session ID in response headers
    const newSessionId = response.headers.get('Mcp-Session-Id');
    if (newSessionId) {
      log.debug('MCP session ID', { sessionId: newSessionId });
    }

    const responseText = await response.text();
    log.debug('MCP raw response', { body: responseText.slice(0, 500) });

    if (!response.ok) {
      log.error('MCP server error', { status: response.status, body: responseText.slice(0, 500) });

      // If the MCP server rejects our OAuth 2.1 token, clear it and ask for re-auth
      if (authType === 'oauth2.1' && response.status === 401) {
        const clearResponse = NextResponse.json({
          error: 'needs_auth',
          authorizeUrl: `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(endpoint)}`,
        }, { status: 401 });
        clearResponse.cookies.delete(tokenCookieName(endpoint));
        return clearResponse;
      }

      return NextResponse.json(
        { error: `MCP Error: ${response.status}`, details: responseText },
        { status: response.status }
      );
    }

    // Try to parse as JSON, handle different formats
    let data;
    try {
      data = JSON.parse(responseText);
    } catch (e) {
      // Response might be in a different format (e.g., "id: xxx\ndata: {...}")
      // Try to extract JSON from SSE-like format
      const lines = responseText.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            data = JSON.parse(line.slice(6));
            break;
          } catch (e2) {
            // Continue trying
          }
        }
      }
      if (!data) {
        // Return raw text if can't parse
        data = { raw: responseText };
      }
    }

    log.debug('MCP parsed response', { result: JSON.stringify(data).slice(0, 500) });

    // Include session ID in response if present
    if (newSessionId) {
      data._sessionId = newSessionId;
    }

    // Return the result, persisting refreshed token if needed
    const jsonResponse = NextResponse.json(data);
    if (updatedTokenCookie) {
      const isHttps = (request.headers.get('x-forwarded-proto') || 'http') === 'https';
      jsonResponse.cookies.set(updatedTokenCookie.name, updatedTokenCookie.value, {
        httpOnly: true,
        secure: isHttps,
        sameSite: 'lax',
        maxAge: 30 * 24 * 60 * 60,
        path: '/',
      });
    }
    return jsonResponse;

  } catch (error) {
    const log = createLogger('mcp-proxy');
    log.error('MCP proxy error', { error: error.message });
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
