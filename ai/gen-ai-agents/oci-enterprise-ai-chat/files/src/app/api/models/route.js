import { NextResponse } from 'next/server';
import * as oci from 'oci-sdk';
import { getOCIAuth } from '../../lib/oci-auth';
import { createLogger } from '../../lib/logger';

export async function GET() {
  const requestId = crypto.randomUUID();
  const log = createLogger('models-api', { requestId });

  try {
    const compartmentId = process.env.OCI_COMPARTMENT_ID;

    if (!compartmentId) {
      return NextResponse.json(
        { error: 'OCI_COMPARTMENT_ID is required' },
        { status: 500 }
      );
    }

    const auth = await getOCIAuth();
    const client = new oci.generativeai.GenerativeAiClient({
      authenticationDetailsProvider: auth,
    });

    // List models available in the compartment
    const response = await client.listModels({
      compartmentId: compartmentId,
    });

    // Filter and format models for the frontend
    const models = response.modelCollection.items
      .filter(model => model.lifecycleState === 'ACTIVE')
      .map(model => ({
        id: model.id,
        displayName: model.displayName,
        vendor: model.vendor,
        version: model.version,
        capabilities: model.capabilities,
        type: model.type,
      }));

    return NextResponse.json({ models });

  } catch (error) {
    log.error('Error listing models', { error: error.message });
    return NextResponse.json(
      { error: error.message || 'Failed to list models' },
      { status: 500 }
    );
  }
}
