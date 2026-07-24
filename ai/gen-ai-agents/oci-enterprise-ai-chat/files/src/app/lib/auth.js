const IDCS_DOMAIN_URL = process.env.IDCS_DOMAIN_URL || '';
const IDCS_CLIENT_ID = process.env.IDCS_CLIENT_ID || '';
const IDCS_CLIENT_SECRET = process.env.IDCS_CLIENT_SECRET || '';
const SESSION_SECRET = process.env.SESSION_SECRET || 'change-me-in-production';

export function isAuthEnabled() {
  return !!(IDCS_DOMAIN_URL && IDCS_CLIENT_ID && IDCS_CLIENT_SECRET);
}

export function getIDCSConfig() {
  return {
    domainUrl: IDCS_DOMAIN_URL.replace(/\/+$/, ''),
    clientId: IDCS_CLIENT_ID,
    clientSecret: IDCS_CLIENT_SECRET,
    authorizeUrl: `${IDCS_DOMAIN_URL.replace(/\/+$/, '')}/oauth2/v1/authorize`,
    tokenUrl: `${IDCS_DOMAIN_URL.replace(/\/+$/, '')}/oauth2/v1/token`,
    userinfoUrl: `${IDCS_DOMAIN_URL.replace(/\/+$/, '')}/oauth2/v1/userinfo`,
    logoutUrl: `${IDCS_DOMAIN_URL.replace(/\/+$/, '')}/oauth2/v1/userlogout`,
  };
}

// --- Session cookie helpers (HMAC-SHA256 signed JSON) ---

async function hmacSign(data) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', encoder.encode(SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(data));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function hmacVerify(data, signature) {
  const expected = await hmacSign(data);
  return expected === signature;
}

export async function createSessionCookie(userInfo, idToken) {
  const payload = JSON.stringify({
    sub: userInfo.sub || '',
    name: userInfo.name || userInfo.user_displayname || '',
    email: userInfo.email || '',
    id_token: idToken || '',
    exp: Math.floor(Date.now() / 1000) + 7 * 24 * 3600, // 7 days
  });
  const b64 = btoa(payload);
  const sig = await hmacSign(b64);
  return `${b64}.${sig}`;
}

export async function verifySessionCookie(cookie) {
  if (!cookie) return null;
  const dotIdx = cookie.lastIndexOf('.');
  if (dotIdx === -1) return null;

  const b64 = cookie.slice(0, dotIdx);
  const sig = cookie.slice(dotIdx + 1);

  if (!(await hmacVerify(b64, sig))) return null;

  try {
    const payload = JSON.parse(atob(b64));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}
