import { NextResponse } from 'next/server';
import crypto from 'crypto';
import { ociRequest, toNextResponse } from '../../lib/oci-proxy';
import { createLogger } from '../../lib/logger';

// GET /api/files → list files
export async function GET() {
  try {
    return toNextResponse(await ociRequest('GET', '/files'));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// POST /api/files → upload file (multipart/form-data)
export async function POST(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('files-api', { requestId });

  try {
    const formData = await request.formData();
    const file = formData.get('file');
    const purpose = formData.get('purpose') || 'user_data';

    if (!file) return NextResponse.json({ error: 'file is required' }, { status: 400 });

    const fileBuffer = Buffer.from(await file.arrayBuffer());
    const boundary = `----FormBoundary${crypto.randomBytes(16).toString('hex')}`;

    const body = Buffer.concat([
      Buffer.from(
        `--${boundary}\r\n` +
        `Content-Disposition: form-data; name="file"; filename="${file.name}"\r\n` +
        `Content-Type: ${file.type || 'application/octet-stream'}\r\n\r\n`
      ),
      fileBuffer,
      Buffer.from(
        `\r\n--${boundary}\r\n` +
        `Content-Disposition: form-data; name="purpose"\r\n\r\n` +
        `${purpose}\r\n--${boundary}--\r\n`
      ),
    ]);

    const response = await ociRequest('POST', '/files', {
      binaryBody: body,
      extraHeaders: {
        'content-type': `multipart/form-data; boundary=${boundary}`,
        'content-length': body.length.toString(),
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      log.error('File upload error', { status: response.status, error: errorText });
      return NextResponse.json({ error: errorText }, { status: response.status });
    }
    return NextResponse.json(await response.json());
  } catch (error) {
    log.error('File upload error', { error: error.message });
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

// DELETE /api/files?id=FILE_ID → delete file
export async function DELETE(request) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'id is required' }, { status: 400 });
    return toNextResponse(await ociRequest('DELETE', `/files/${id}`));
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
