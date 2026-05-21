/**
 * Shared OCI proxy client for all API routes.
 *
 * OCI GenAI has two hosts:
 * - Control plane (generativeai.region...) — vector store CRUD, uses compartment ID only
 * - Inference (inference.generativeai.region...) — responses, files, VS files/search, uses project ID
 *
 * This module provides a single `ociRequest()` function that handles:
 * - URL construction for both hosts
 * - Correct headers per host type
 * - Request signing (string bodies via SDK, binary bodies via manual RSA)
 * - Response handling with consistent error format
 */

import { NextResponse } from 'next/server';
import crypto from 'crypto';
import { signRequest, signRequestBinary } from './oci-auth';
import { createLogger } from './logger';

const log = createLogger('oci-proxy');

const region = () => process.env.OCI_REGION || 'us-chicago-1';

const HOSTS = {
  inference: {
    base: () => `https://inference.generativeai.${region()}.oci.oraclecloud.com/openai/v1`,
    host: () => `inference.generativeai.${region()}.oci.oraclecloud.com`,
    headers: () => {
      const h = {};
      const projectId = process.env.OCI_GENAI_PROJECT_ID;
      if (projectId) h['openai-project'] = projectId;
      const compartmentId = process.env.OCI_COMPARTMENT_ID;
      if (compartmentId) h['opc-compartment-id'] = compartmentId;
      return h;
    },
  },
  controlPlane: {
    base: () => `https://generativeai.${region()}.oci.oraclecloud.com/20231130/openai/v1`,
    host: () => `generativeai.${region()}.oci.oraclecloud.com`,
    headers: () => {
      const compartmentId = process.env.OCI_COMPARTMENT_ID;
      if (!compartmentId) throw new Error('OCI_COMPARTMENT_ID is required');
      return { 'opc-compartment-id': compartmentId };
    },
  },
};

/**
 * Make a signed request to OCI GenAI.
 *
 * @param {string} method - HTTP method (GET, POST, PUT, DELETE)
 * @param {string} path - API path (e.g. '/vector_stores', '/files')
 * @param {object} options
 * @param {'inference'|'controlPlane'} options.host - Which OCI host to use (default: inference)
 * @param {object|null} options.body - JSON body (for POST/PUT)
 * @param {Buffer|null} options.binaryBody - Raw binary body (for multipart uploads)
 * @param {object} options.extraHeaders - Additional headers to merge
 * @param {string} options.basePath - Override the default base path (e.g. '/v1' instead of '/openai/v1')
 * @returns {Promise<Response>} Raw fetch response
 */
export async function ociRequest(method, path, options = {}) {
  const { host = 'inference', body = null, binaryBody = null, extraHeaders = {}, basePath } = options;
  const hostConfig = HOSTS[host];
  const baseUrl = basePath
    ? `https://${hostConfig.host()}${basePath}`
    : hostConfig.base();
  const endpoint = `${baseUrl}${path}`;

  const headers = {
    'accept': 'application/json',
    'host': hostConfig.host(),
    ...hostConfig.headers(),
    ...extraHeaders,
  };

  // Binary body (multipart file upload) — use manual RSA signing
  if (binaryBody) {
    const signedHeaders = await signRequestBinary(method, endpoint, headers, binaryBody);
    return fetch(endpoint, { method, headers: signedHeaders, body: binaryBody });
  }

  // JSON body (POST/PUT)
  if (body !== null) {
    const bodyString = JSON.stringify(body);
    headers['content-type'] = 'application/json';
    headers['x-content-sha256'] = crypto.createHash('sha256').update(bodyString).digest('base64');
    headers['content-length'] = Buffer.byteLength(bodyString).toString();
    const signedHeaders = await signRequest(method, endpoint, headers, bodyString);
    return fetch(endpoint, { method, headers: signedHeaders, body: bodyString });
  }

  // No body (GET/DELETE)
  const signedHeaders = await signRequest(method, endpoint, headers);
  return fetch(endpoint, { method, headers: signedHeaders });
}

/**
 * Convert a fetch Response into a NextResponse with consistent error handling.
 */
export async function toNextResponse(response) {
  if (!response.ok) {
    const errorText = await response.text();
    log.error('OCI API error', { status: response.status, body: errorText.slice(0, 500) });
    return NextResponse.json({ error: errorText }, { status: response.status });
  }
  if (response.status === 204) {
    return NextResponse.json({ deleted: true });
  }
  return NextResponse.json(await response.json());
}
