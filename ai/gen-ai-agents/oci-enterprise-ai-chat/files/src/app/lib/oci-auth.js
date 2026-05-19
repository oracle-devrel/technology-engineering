import * as oci from 'oci-sdk';
import crypto from 'crypto';

let authProvider = null;
let signer = null;
let initPromise = null;

async function initAuth() {
  if (authProvider) return;

  const useResourcePrincipal = process.env.USE_RESOURCE_PRINCIPAL === 'true';

  if (useResourcePrincipal) {
    authProvider = oci.common.ResourcePrincipalAuthenticationDetailsProvider.builder();
  } else {
    authProvider = new oci.ConfigFileAuthenticationDetailsProvider(
      process.env.OCI_CONFIG_FILE || '~/.oci/config',
      process.env.OCI_CONFIG_PROFILE || 'DEFAULT'
    );
  }
}

export async function getOCIAuth() {
  if (!initPromise) {
    initPromise = initAuth();
  }
  await initPromise;
  return authProvider;
}

export async function getSigner() {
  if (!signer) {
    const auth = await getOCIAuth();
    signer = new oci.DefaultRequestSigner(auth);
  }
  return signer;
}

/**
 * Sign a request with a string/JSON body using the OCI SDK signer.
 * For binary bodies (Buffer), use signRequestBinary() instead.
 */
export async function signRequest(method, url, headersObj, body = null) {
  const requestSigner = await getSigner();
  const parsedUrl = new URL(url);

  const headers = new Headers();
  for (const [key, value] of Object.entries(headersObj)) {
    headers.set(key, value);
  }

  const request = {
    method: method,
    headers: headers,
    uri: parsedUrl.pathname + parsedUrl.search,
    path: parsedUrl.pathname + parsedUrl.search,
    body: body,
  };

  await requestSigner.signHttpRequest(request);

  const signedHeaders = {};
  request.headers.forEach((value, key) => {
    signedHeaders[key] = value;
  });

  return signedHeaders;
}

/**
 * Sign a request with a binary body (Buffer).
 * Bypasses the OCI SDK signer which corrupts binary data during SHA256 hashing.
 * Manually builds the OCI HTTP Signature using Node's crypto module.
 * Works with both ConfigFile and ResourcePrincipal auth.
 */
export async function signRequestBinary(method, url, headersObj, bodyBuffer) {
  const auth = await getOCIAuth();

  const keyId = await auth.getKeyId();
  const privateKeyPem = auth.getPrivateKey();
  const passphrase = auth.getPassphrase ? auth.getPassphrase() : null;

  const parsedUrl = new URL(url);
  const requestTarget = `${method.toLowerCase()} ${parsedUrl.pathname}${parsedUrl.search}`;

  // Compute x-content-sha256 from raw bytes
  const contentSha256 = crypto.createHash('sha256').update(bodyBuffer).digest('base64');

  // Set required headers
  const xDate = new Date().toUTCString();
  const headers = { ...headersObj };
  headers['x-date'] = xDate;
  headers['x-content-sha256'] = contentSha256;
  if (!headers['content-length']) {
    headers['content-length'] = bodyBuffer.length.toString();
  }

  // OCI HTTP Signature: for POST, sign these headers
  const headersToSign = ['x-date', '(request-target)', 'host', 'content-type', 'content-length', 'x-content-sha256'];

  const signingString = headersToSign.map(h => {
    if (h === '(request-target)') return `(request-target): ${requestTarget}`;
    return `${h}: ${headers[h]}`;
  }).join('\n');

  // RSA-SHA256 sign
  const sign = crypto.createSign('RSA-SHA256');
  sign.update(signingString);
  const signature = sign.sign(
    passphrase ? { key: privateKeyPem, passphrase } : privateKeyPem,
    'base64'
  );

  // Build OCI Authorization header
  headers['authorization'] = `Signature version="1",keyId="${keyId}",algorithm="rsa-sha256",headers="${headersToSign.join(' ')}",signature="${signature}"`;

  return headers;
}
