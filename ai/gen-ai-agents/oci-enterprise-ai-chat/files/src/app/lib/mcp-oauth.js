import { createHash, randomBytes } from 'crypto';

const SESSION_SECRET = process.env.SESSION_SECRET || 'change-me-in-production';

// ── Base path (OCI Hosted Deployment) ────────────────────────────────────────
// OCI strips the /.../actions/invoke prefix before requests reach us and injects
// it as APPLICATION_BASE_URL. Server-built browser-facing URLs (OAuth
// redirect_uri, post-login returnTo) must re-add it so the browser can route
// back through the gateway. Empty for dev / root (Container Instance) deploys.
export function basePrefix() {
  return (process.env.APPLICATION_BASE_URL || process.env.BASE_PATH || '').replace(/\/+$/, '');
}

// ── PKCE ────────────────────────────────────────────────────────────────────

export function generateCodeVerifier() {
  return randomBytes(32).toString('base64url');
}

export function generateCodeChallenge(verifier) {
  return createHash('sha256').update(verifier).digest('base64url');
}

// ── Signed cookies ──────────────────────────────────────────────────────────

async function hmacSign(data) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', encoder.encode(SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(data));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function signPayload(payload) {
  const b64 = Buffer.from(JSON.stringify(payload)).toString('base64url');
  const sig = await hmacSign(b64);
  return `${b64}.${sig}`;
}

export async function verifyPayload(signed) {
  if (!signed) return null;
  const dotIdx = signed.lastIndexOf('.');
  if (dotIdx === -1) return null;
  const b64 = signed.slice(0, dotIdx);
  const sig = signed.slice(dotIdx + 1);
  const expected = await hmacSign(b64);
  if (expected !== sig) return null;
  try {
    return JSON.parse(Buffer.from(b64, 'base64url').toString());
  } catch {
    return null;
  }
}

// ── Cookie names ────────────────────────────────────────────────────────────

export function endpointHash(endpoint) {
  return createHash('sha256').update(endpoint).digest('hex').slice(0, 16);
}

export function tokenCookieName(endpoint) {
  return `mcp-tok-${endpointHash(endpoint)}`;
}

export const PENDING_COOKIE = 'mcp-oauth-pending';

// ── OAuth metadata ──────────────────────────────────────────────────────────

/**
 * Fetch and fix the MCP server's OAuth 2.1 metadata.
 * Some servers return endpoint URLs missing the MCP base path — we detect and fix that.
 */
export async function fetchOAuthMetadata(mcpEndpoint) {
  // RFC 9728 (OAuth Protected Resource Metadata) — the modern MCP pattern used by
  // e.g. the OCI DBTools/NL2SQL MCP server. The MCP endpoint exposes a
  // protected-resource document at {origin}/.well-known/oauth-protected-resource{path}
  // that points to a SEPARATE authorization server (e.g. an IAM Identity Domain),
  // whose own metadata holds the authorize/token/registration endpoints.
  const u = new URL(mcpEndpoint);
  const resourcePath = u.pathname.replace(/\/$/, '');
  const prCandidates = [
    `${u.origin}/.well-known/oauth-protected-resource${resourcePath}`, // path-based (DBTools)
    `${u.origin}/.well-known/oauth-protected-resource`,                // origin-based
  ];
  for (const prUrl of prCandidates) {
    try {
      const pr = await fetch(prUrl);
      if (!pr.ok) continue;
      const prMeta = await pr.json();
      const authServer = (prMeta.authorization_servers || [])[0];
      if (!authServer) continue;
      const asMeta = await fetchAuthServerMetadata(authServer);
      if (!asMeta) continue;
      // The resource's own scopes_supported tells us exactly what to request.
      return { ...asMeta, scopes_supported: prMeta.scopes_supported || asMeta.scopes_supported };
    } catch { /* try next candidate */ }
  }

  // Fallback: some MCP servers serve the authorization-server metadata directly
  // under the MCP endpoint (older one-level pattern).
  const base = mcpEndpoint.replace(/\/$/, '');
  const res = await fetch(`${base}/.well-known/oauth-authorization-server`);
  if (!res.ok) return null;
  const metadata = await res.json();
  return fixMetadataUrls(metadata, mcpEndpoint);
}

/** Fetch an authorization server's metadata (RFC 8414 or OIDC discovery). */
async function fetchAuthServerMetadata(authServer) {
  const root = authServer.replace(/\/$/, '');
  for (const path of ['/.well-known/oauth-authorization-server', '/.well-known/openid-configuration']) {
    try {
      const r = await fetch(`${root}${path}`);
      if (r.ok) return await r.json();
    } catch { /* try next */ }
  }
  return null;
}

export function fixMetadataUrls(metadata, mcpEndpoint) {
  const basePath = new URL(mcpEndpoint).pathname.replace(/\/$/, '');
  if (!basePath) return metadata;

  // Probe with the registration URL when present, else the authorize URL —
  // metadata without registration_endpoint is valid (IDCS has none) and
  // `new URL(undefined)` would throw.
  const probeUrl = metadata.registration_endpoint || metadata.authorization_endpoint;
  if (!probeUrl) return metadata;

  // If the probe URL already includes the base path, metadata is correct
  const regPath = new URL(probeUrl).pathname;
  if (regPath.startsWith(basePath)) return metadata;

  // Prepend the MCP base path to all OAuth endpoints
  const fix = (url) => {
    if (!url) return url;
    const u = new URL(url);
    u.pathname = basePath + u.pathname;
    return u.toString();
  };

  return {
    ...metadata,
    registration_endpoint: fix(metadata.registration_endpoint),
    authorization_endpoint: fix(metadata.authorization_endpoint),
    token_endpoint: fix(metadata.token_endpoint),
    revocation_endpoint: metadata.revocation_endpoint ? fix(metadata.revocation_endpoint) : undefined,
  };
}

// ── Dynamic Client Registration (RFC 7591) ──────────────────────────────────

export async function registerClient(registrationEndpoint, redirectUri, scopes) {
  const res = await fetch(registrationEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      client_name: 'OCI Agent Hub',
      redirect_uris: [redirectUri],
      grant_types: ['authorization_code', 'refresh_token'],
      response_types: ['code'],
      token_endpoint_auth_method: 'client_secret_post',
      scope: scopes.join(' '),
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Client registration failed: ${res.status} ${err}`);
  }
  return res.json();
}

// ── Token exchange & refresh ────────────────────────────────────────────────

export async function exchangeCode(tokenEndpoint, code, codeVerifier, clientId, clientSecret, redirectUri) {
  const params = {
    grant_type: 'authorization_code',
    code,
    redirect_uri: redirectUri,
    client_id: clientId,
    client_secret: clientSecret,
  };
  if (codeVerifier) params.code_verifier = codeVerifier;

  const res = await fetch(tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams(params),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Token exchange failed: ${res.status} ${err}`);
  }
  return res.json();
}

// ── Minted-token cache + single-flight ──────────────────────────────────────
// IDCS rotates refresh tokens and invalidates the consumed one ("invalid_grant:
// The token has already been consumed"). We mint in several places per message
// (pre-send probe, client-side chain executor, Settings probes); minting fresh
// every time both wasted an IdP roundtrip and raced rotation — two mints with
// the same refresh token permanently killed the grant. Cache the minted access
// token for its lifetime, single-flight concurrent mints, and index the cache
// under BOTH the old and rotated refresh tokens (the cookie update may lag).
// globalThis: each Next route compiles as its own module instance (turbopack),
// so plain module state gave every route a PRIVATE cache — two routes minting
// with the same refresh token raced anyway and killed the rotation. globalThis
// is shared per Node process and survives dev hot-reloads.
const _mintCache = (globalThis.__mcpMintCache ||= new Map());       // rtKey → entry
const _mintInFlight = (globalThis.__mcpMintInFlight ||= new Map()); // rtKey → Promise<entry>
const _rtKey = (rt) => createHash('sha256').update(rt).digest('hex').slice(0, 16);

export async function mintAccessToken(tokenEndpoint, refreshToken, clientId, clientSecret) {
  const key = _rtKey(refreshToken);
  const cached = _mintCache.get(key);
  if (cached && cached.expiresAt > Date.now() + 60_000) return cached;
  if (_mintInFlight.has(key)) return _mintInFlight.get(key);

  const inFlight = (async () => {
    try {
      const refreshed = await refreshAccessToken(tokenEndpoint, refreshToken, clientId, clientSecret);
      const entry = {
        accessToken: refreshed.access_token,
        refreshToken: refreshed.refresh_token || refreshToken,
        expiresAt: Date.now() + (refreshed.expires_in || 3600) * 1000,
      };
      _mintCache.set(key, entry);
      if (refreshed.refresh_token && refreshed.refresh_token !== refreshToken) {
        _mintCache.set(_rtKey(refreshed.refresh_token), entry);
      }
      return entry;
    } finally {
      _mintInFlight.delete(key);
    }
  })();
  _mintInFlight.set(key, inFlight);
  return inFlight;
}

export async function refreshAccessToken(tokenEndpoint, refreshToken, clientId, clientSecret) {
  const res = await fetch(tokenEndpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'refresh_token',
      refresh_token: refreshToken,
      client_id: clientId,
      client_secret: clientSecret,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Token refresh failed: ${res.status} ${err}`);
  }
  return res.json();
}
