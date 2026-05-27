import { NextResponse } from 'next/server';
import { isAuthEnabled, getIDCSConfig, verifySessionCookie } from '../../../lib/auth';

export async function GET(request) {
  const cookie = request.cookies.get('auth-session')?.value;
  const session = await verifySessionCookie(cookie);

  // Clear cookies first
  const clearCookies = (res) => {
    res.cookies.set('auth-session', '', { path: '/', maxAge: 0 });
    res.cookies.set('auth-token', '', { path: '/', maxAge: 0 });
    return res;
  };

  // If IDCS is configured and we have an id_token, do proper IDCS logout
  if (isAuthEnabled() && session?.id_token) {
    const idcs = getIDCSConfig();
    const postLogoutUrl = new URL('/login', request.url).toString();
    const logoutUrl = `${idcs.logoutUrl}?id_token_hint=${encodeURIComponent(session.id_token)}&post_logout_redirect_uri=${encodeURIComponent(postLogoutUrl)}`;
    return clearCookies(NextResponse.redirect(logoutUrl));
  }

  return clearCookies(NextResponse.redirect(new URL('/login', request.url)));
}

export async function POST(request) {
  const response = NextResponse.json({ ok: true });
  response.cookies.set('auth-session', '', { path: '/', maxAge: 0 });
  response.cookies.set('auth-token', '', { path: '/', maxAge: 0 });
  return response;
}
