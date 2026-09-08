// NL2SQL generation (guide §1.4.2 / §1.5 generate step).
//
// Generates SQL from a natural-language question using the OCI GenAI Semantic
// Store data-plane operation `generateSqlFromNl`, signed with the app's OWN OCI
// credentials (no user OAuth — that is only needed for the EXECUTION step, which
// runs the generated SQL through the DBTools MCP `sql_run` tool).
//
// This is the "generate" half of the two-step NL2SQL flow:
//   1. /api/nl2sql        → NL question  →  SQL          (this route, app creds)
//   2. /api/mcp sql_run   → SQL          →  rows (data)  (DBTools MCP, user token)
// The chain executor (useChat) orchestrates both when the model calls generate_sql.
import { NextResponse } from 'next/server';
import crypto from 'crypto';
import { signRequest } from '../../lib/oci-auth';
import { createLogger } from '../../lib/logger';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

const log = createLogger('nl2sql');

// generateSqlFromNl lives on the inference host under its own dated base path
// (NOT /openai/v1). Matches the guide's GenerateSQL example.
const API_VERSION = '20260325';

export async function POST(request) {
  let body;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const question = (body?.question || '').toString().trim();
  // The store id comes from the server env (OCI_NL2SQL_SEMANTIC_STORE_ID) so a
  // stale/wrong value in a browser's localStorage can't break generation. The
  // request value is only a last-resort fallback when the env isn't configured.
  const semanticStoreId = (process.env.OCI_NL2SQL_SEMANTIC_STORE_ID || body?.semanticStoreId || '').toString().trim();
  if (!question) return NextResponse.json({ error: 'Missing question' }, { status: 400 });
  if (!semanticStoreId) return NextResponse.json({ error: 'Missing semanticStoreId' }, { status: 400 });

  const region = process.env.OCI_REGION || 'us-chicago-1';
  const host = `inference.generativeai.${region}.oci.oraclecloud.com`;
  const url = `https://${host}/${API_VERSION}/semanticStores/${semanticStoreId}/actions/generateSqlFromNl`;

  const payload = JSON.stringify({
    displayName: 'chat-nl2sql',
    description: 'Generate SQL for chat Text-to-SQL',
    inputNaturalLanguageQuery: question,
  });

  const headers = {
    accept: 'application/json',
    'content-type': 'application/json',
    host,
    'x-content-sha256': crypto.createHash('sha256').update(payload).digest('base64'),
    'content-length': Buffer.byteLength(payload).toString(),
  };

  try {
    const signed = await signRequest('POST', url, headers, payload);
    const res = await fetch(url, { method: 'POST', headers: signed, body: payload });
    const text = await res.text();
    if (!res.ok) {
      log.error('generateSqlFromNl failed', { status: res.status, body: text.slice(0, 400) });
      return NextResponse.json({ error: text.slice(0, 600) }, { status: res.status });
    }

    let data;
    try { data = JSON.parse(text); } catch { data = text; }
    // The generated SQL is at jobOutput.content; keep fallbacks for shape drift.
    const sql = (
      data?.jobOutput?.content ??
      data?.sqlQuery ??
      data?.content ??
      ''
    ).toString().trim();

    if (!sql) {
      log.error('generateSqlFromNl returned no SQL', { keys: data && typeof data === 'object' ? Object.keys(data) : typeof data });
      return NextResponse.json({ error: 'No SQL generated', raw: data }, { status: 502 });
    }

    log.info('SQL generated', { chars: sql.length });
    return NextResponse.json({ sql, status: data?.lifecycleState || data?.status || 'SUCCEEDED' });
  } catch (err) {
    log.error('generateSqlFromNl error', { error: (err?.message || '').slice(0, 300) });
    return NextResponse.json({ error: (err?.message || 'generateSqlFromNl failed').slice(0, 300) }, { status: 500 });
  }
}
