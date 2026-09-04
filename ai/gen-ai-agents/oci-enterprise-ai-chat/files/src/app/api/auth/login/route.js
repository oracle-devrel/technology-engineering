import { NextResponse } from 'next/server';
import { isAuthEnabled, getIDCSConfig } from '../../../lib/auth';

function getBaseUrl(request) {
  let host = request.headers.get('x-forwarded-host') || request.headers.get('host');
  const proto = request.headers.get('x-forwarded-proto') || 'http';
  host = host.replace(/:80$/, '').replace(/:443$/, '');
  return `${proto}://${host}`;
}

export async function GET(request) {
  if (!isAuthEnabled()) {
    return NextResponse.redirect(new URL('/', getBaseUrl(request)));
  }

  const idcs = getIDCSConfig();
  const redirectUri = `${getBaseUrl(request)}/api/auth/callback/oci`;

  const params = new URLSearchParams({
    response_type: 'code',
    client_id: idcs.clientId,
    redirect_uri: redirectUri,
    scope: 'openid profile email',
    state: crypto.randomUUID(),
  });

  return NextResponse.redirect(`${idcs.authorizeUrl}?${params}`);
}
