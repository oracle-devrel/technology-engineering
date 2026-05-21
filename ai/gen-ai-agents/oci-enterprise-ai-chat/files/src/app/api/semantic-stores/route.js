import { NextResponse } from 'next/server';
import { ociRequest, toNextResponse } from '../../lib/oci-proxy';

// GET /api/semantic-stores — list semantic stores (structured vector stores)
export async function GET() {
  try {
    const compartmentId = process.env.OCI_COMPARTMENT_ID;
    const res = await ociRequest('GET', `/semanticStores?compartmentId=${compartmentId}`, {
      host: 'controlPlane',
      basePath: '/20231130',
    });
    return toNextResponse(res);
  } catch (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
