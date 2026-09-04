/**
 * @deprecated Use oci-proxy.js ociRequest() instead. Only debug/route.js still imports this.
 *
 * OCI GenAI headers for inference endpoints.
 */

export function getProjectId() {
  const id = process.env.OCI_GENAI_PROJECT_ID;
  if (!id) throw new Error('OCI_GENAI_PROJECT_ID is required');
  return id;
}

export function getOciHeaders() {
  const headers = { 'openai-project': getProjectId() };
  const compartmentId = process.env.OCI_COMPARTMENT_ID;
  if (compartmentId) {
    headers['opc-compartment-id'] = compartmentId;
  }
  return headers;
}
