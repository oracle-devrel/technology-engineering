import { NextResponse } from 'next/server';
import { verifySessionCookie, isAuthEnabled } from '../../../lib/auth';

export async function GET(request) {
  if (!isAuthEnabled()) {
    return NextResponse.json({ authenticated: false, authEnabled: false });
  }

  const cookie = request.cookies.get('auth-session')?.value;
  const session = await verifySessionCookie(cookie);

  if (!session) {
    return NextResponse.json({ authenticated: false, authEnabled: true });
  }

  return NextResponse.json({
    authenticated: true,
    authEnabled: true,
    user: {
      name: session.name,
      email: session.email,
    },
  });
}
