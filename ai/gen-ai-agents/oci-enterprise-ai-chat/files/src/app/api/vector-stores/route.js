import { NextResponse } from 'next/server';
import { ociRequest, toNextResponse } from '../../lib/oci-proxy';

// GET /api/vector-stores              → list all vector stores
// GET /api/vector-stores?id=X         → get one vector store
// GET /api/vector-stores?id=X&files=1 → list files in vector store
export async function GET(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const files = searchParams.get('files');

    if (id && files) {
      return toNextResponse(await ociRequest('GET', `/vector_stores/${id}/files`));
    }
    if (id) {
      return toNextResponse(await ociRequest('GET', `/vector_stores/${id}`, { host: 'controlPlane' }));
    }
    return toNextResponse(await ociRequest('GET', '/vector_stores', { host: 'controlPlane' }));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// POST /api/vector-stores                          → create vector store
// POST /api/vector-stores?id=X&action=attach-file  → attach file to vector store
// POST /api/vector-stores?id=X&action=search       → search vector store
export async function POST(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const action = searchParams.get('action');

    if (id && action === 'attach-file') {
      const { file_id, attributes, chunking_strategy } = await request.json();
      if (!file_id) return NextResponse.json({ error: 'file_id is required' }, { status: 400 });
      const body = { file_id };
      if (attributes) body.attributes = attributes;
      if (chunking_strategy) body.chunking_strategy = chunking_strategy;
      return toNextResponse(await ociRequest('POST', `/vector_stores/${id}/files`, { body }));
    }

    if (id && action === 'attach-batch') {
      const { file_ids, attributes, chunking_strategy } = await request.json();
      if (!Array.isArray(file_ids) || file_ids.length === 0) {
        return NextResponse.json({ error: 'file_ids array is required' }, { status: 400 });
      }
      const body = { file_ids };
      if (attributes) body.attributes = attributes;
      if (chunking_strategy) body.chunking_strategy = chunking_strategy;
      return toNextResponse(await ociRequest('POST', `/vector_stores/${id}/file_batches`, { body }));
    }

    if (id && action === 'search') {
      const { query, max_num_results, filters, ranking_options } = await request.json();
      if (!query) return NextResponse.json({ error: 'query is required' }, { status: 400 });
      const body = { query };
      if (max_num_results) body.max_num_results = max_num_results;
      if (filters) body.filters = filters;
      if (ranking_options) body.ranking_options = ranking_options;
      return toNextResponse(await ociRequest('POST', `/vector_stores/${id}/search`, { body }));
    }

    // Create vector store (control plane)
    const { name, description, file_ids, chunking_strategy, expires_after, metadata } = await request.json();
    if (!name) return NextResponse.json({ error: 'name is required' }, { status: 400 });
    const body = { name };
    if (description) body.description = description;
    if (file_ids?.length > 0) body.file_ids = file_ids;
    if (chunking_strategy) body.chunking_strategy = chunking_strategy;
    if (expires_after) body.expires_after = expires_after;
    if (metadata && Object.keys(metadata).length > 0) body.metadata = metadata;
    return toNextResponse(await ociRequest('POST', '/vector_stores', { host: 'controlPlane', body }));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// PUT /api/vector-stores?id=X            → update vector store (name, metadata, expires_after)
// PUT /api/vector-stores?id=X&file_id=F  → update file attributes
// Note: OCI uses POST (not PUT) for updates on the OpenAI-compatible API
export async function PUT(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const fileId = searchParams.get('file_id');
    if (!id) return NextResponse.json({ error: 'id is required' }, { status: 400 });

    if (fileId) {
      const { attributes } = await request.json();
      return toNextResponse(await ociRequest('POST', `/vector_stores/${id}/files/${fileId}`, { body: { attributes } }));
    }

    const { name, metadata, expires_after } = await request.json();
    const body = {};
    if (name !== undefined) body.name = name;
    if (metadata !== undefined) body.metadata = metadata;
    if (expires_after !== undefined) body.expires_after = expires_after;
    return toNextResponse(await ociRequest('POST', `/vector_stores/${id}`, { host: 'controlPlane', body }));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// DELETE /api/vector-stores?id=X            → delete vector store
// DELETE /api/vector-stores?id=X&file_id=F  → remove file from vector store
export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const fileId = searchParams.get('file_id');
    if (!id) return NextResponse.json({ error: 'id is required' }, { status: 400 });

    if (fileId) {
      return toNextResponse(await ociRequest('DELETE', `/vector_stores/${id}/files/${fileId}`));
    }
    return toNextResponse(await ociRequest('DELETE', `/vector_stores/${id}`, { host: 'controlPlane' }));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
