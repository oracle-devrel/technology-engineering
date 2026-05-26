import { NextResponse } from 'next/server';
import { getIDCSConfig, createSessionCookie } from '../../../../lib/auth';
import { createLogger } from '../../../../lib/logger';

function getBaseUrl(request) {
  let host = request.headers.get('x-forwarded-host') || request.headers.get('host');
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  host = host.replace(/:80$/, '').replace(/:443$/, '');
  return `${proto}://${host}`;
}

export async function GET(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('auth-callback', { requestId });

  const { searchParams } = new URL(request.url);
  const code = searchParams.get('code');
  const error = searchParams.get('error');
  const baseUrl = getBaseUrl(request);

  if (error) {
    log.error('IDCS OAuth error', { error, description: searchParams.get('error_description') });
    return NextResponse.redirect(new URL('/login?error=idcs_denied', baseUrl));
  }

  if (!code) {
    return NextResponse.redirect(new URL('/login?error=no_code', baseUrl));
  }

  const idcs = getIDCSConfig();
  const redirectUri = `${baseUrl}/api/auth/callback/oci`;

  // Exchange authorization code for tokens
  const tokenRes = await fetch(idcs.tokenUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Authorization': 'Basic ' + btoa(`${idcs.clientId}:${idcs.clientSecret}`),
    },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: redirectUri,
    }),
  });

  if (!tokenRes.ok) {
    const errText = await tokenRes.text();
    log.error('IDCS token exchange failed', { status: tokenRes.status, error: errText });
    return NextResponse.redirect(new URL('/login?error=token_failed', baseUrl));
  }

  const tokens = await tokenRes.json();

  // Get user info from IDCS
  const userinfoRes = await fetch(idcs.userinfoUrl, {
    headers: { 'Authorization': `Bearer ${tokens.access_token}` },
  });

  let userInfo = {};
  if (userinfoRes.ok) {
    userInfo = await userinfoRes.json();
  } else {
    // Fallback: decode id_token payload
    try {
      const parts = tokens.id_token.split('.');
      userInfo = JSON.parse(atob(parts[1]));
    } catch {
      userInfo = { sub: 'unknown', name: 'User' };
    }
  }

  const sessionCookie = await createSessionCookie(userInfo, tokens.id_token);

  const response = NextResponse.redirect(new URL('/', baseUrl));
  response.cookies.set('auth-session', sessionCookie, {
    httpOnly: true,
    secure: false,
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 7, // 7 days
  });

  return response;
}
