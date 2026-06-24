import { NextResponse } from 'next/server';
import { ociRequest } from '../../../../lib/oci-proxy';

// GET /api/files/[id]/content → fetch file content
//
// Strategy:
// 1. If ?vsId=xxx is provided, use /vector_stores/{vsId}/files/{fileId}/content
//    (returns parsed chunks, works for any file in the vector store regardless
//    of upload purpose). This is the path for files uploaded with purpose=user_data
//    which OCI/OpenAI policy blocks from direct /files/{id}/content download.
// 2. Otherwise, fall back to /files/{id}/content (raw file). Only works for files
//    uploaded with a downloadable purpose (e.g. "assistants").
//
// Query:
//   ?vsId=xxx          vector-store id (preferred)
//   ?download=1        sets attachment disposition
//   ?limit=N           cap response at N bytes (preview)
//   ?filename=name.txt filename for download
export async function GET(request, { params }) {
  try {
    const { id } = await params;
    if (!id) return NextResponse.json({ error: 'id is required' }, { status: 400 });

    const { searchParams } = new URL(request.url);
    const vsId = searchParams.get('vsId');
    const download = searchParams.get('download') === '1';
    const limit = parseInt(searchParams.get('limit') || '0', 10);
    const filename = searchParams.get('filename') || id;

    let body;
    let contentType = 'text/plain; charset=utf-8';

    if (vsId) {
      // Vector store content endpoint — returns JSON with chunks
      const response = await ociRequest('GET', `/vector_stores/${vsId}/files/${id}/content`);
      if (!response.ok) {
        const errorText = await response.text();
        return NextResponse.json({ error: errorText }, { status: response.status });
      }
      const data = await response.json();
      // OCI returns: { file_id, file_name, attributes, content: [{ type, text }, ...] }
      const chunks = Array.isArray(data?.content) ? data.content : [];
      const text = chunks
        .map((c) => (typeof c === 'string' ? c : c?.text || ''))
        .filter(Boolean)
        .join('');
      const sliced = limit > 0 ? text.slice(0, limit) : text;
      body = sliced;
    } else {
      // Raw file fallback
      const response = await ociRequest('GET', `/files/${id}/content`);
      if (!response.ok) {
        const errorText = await response.text();
        return NextResponse.json({ error: errorText }, { status: response.status });
      }
      contentType = response.headers.get('content-type') || 'application/octet-stream';
      const buffer = await response.arrayBuffer();
      body = limit > 0 ? buffer.slice(0, limit) : buffer;
    }

    const headers = { 'content-type': contentType };
    if (download) headers['content-disposition'] = `attachment; filename="${filename}"`;
    return new Response(body, { headers });
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
