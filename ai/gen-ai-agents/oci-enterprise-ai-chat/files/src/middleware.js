import { NextResponse } from 'next/server';

const SESSION_SECRET = process.env.SESSION_SECRET || 'change-me-in-production';

async function hmacSign(data) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw', encoder.encode(SESSION_SECRET), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
  );
  const sig = await crypto.subtle.sign('HMAC', key, encoder.encode(data));
  return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
}

async function verifySession(cookie) {
  if (!cookie) return null;
  const dotIdx = cookie.lastIndexOf('.');
  if (dotIdx === -1) return null;

  const b64 = cookie.slice(0, dotIdx);
  const sig = cookie.slice(dotIdx + 1);
  const expected = await hmacSign(b64);
  if (expected !== sig) return null;

  try {
    const payload = JSON.parse(atob(b64));
    if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) return null;
    return payload;
  } catch {
    return null;
  }
}

export async function middleware(request) {
  // Readiness + liveness endpoints for OCI Hosted Deployments
  if (request.nextUrl.pathname === '/ready' || request.nextUrl.pathname === '/health') {
    return NextResponse.json({ status: 'ok' }, { status: 200 });
  }

  const idcsConfigured = !!(process.env.IDCS_DOMAIN_URL && process.env.IDCS_CLIENT_ID && process.env.IDCS_CLIENT_SECRET);

  // Auth disabled if IDCS not configured
  if (!idcsConfigured) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;

  // Skip auth for login page, auth API, and static assets
  if (
    pathname === '/login' ||
    pathname.startsWith('/api/auth/') ||
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    pathname.endsWith('.svg') ||
    pathname.endsWith('.png') ||
    pathname.endsWith('.ico') ||
    pathname.endsWith('.mjs')
  ) {
    return NextResponse.next();
  }

  const session = await verifySession(request.cookies.get('auth-session')?.value);

  if (!session) {
    if (pathname.startsWith('/api/')) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image).*)'],
};
