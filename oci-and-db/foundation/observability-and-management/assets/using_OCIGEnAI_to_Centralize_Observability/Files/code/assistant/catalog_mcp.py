"""Read-only project MCP for the OCI GenAI model catalog in the configured region."""
import os
import oci
from mcp.server.fastmcp import FastMCP
from .model import config_and_signer

server = FastMCP('db-assistant-model-catalog')


def pages(client, method, compartment, **filters):
    items, page, seen = [], None, set()
    for _ in range(30):
        response = method(compartment,page=page,limit=100,**filters)
        items.extend(response.data.get('items',[]))
        page = response.headers.get('opc-next-page')
        if not page:
            return items
        if page in seen:
            raise ValueError('OCI returned a repeated catalog page token')
        seen.add(page)
    raise ValueError('OCI catalog exceeded the pagination limit; no complete catalog returned')


@server.tool()
def list_offered_models() -> dict:
    """Read regional model discovery plus active Chat model IDs. No inference or changes."""
    compartment = os.environ['GENAI_COMPARTMENT_ID']
    region = os.getenv('OCI_REGION','eu-frankfurt-1')
    config, signer = config_and_signer()
    # Keep discovery as JSON: this SDK release references enum models that are
    # absent from its generated model map. No response fields are discarded.
    client = oci.generative_ai.GenerativeAiClient(config,signer=signer,
        service_endpoint=f'https://generativeai.{region}.oci.oraclecloud.com',
        timeout=(10,45),retry_strategy=oci.retry.NoneRetryStrategy(),skip_deserialization=True)
    discovery = pages(client,client.list_model_discovery,compartment,region=[region])
    inventory = pages(client,client.list_models,compartment,lifecycle_state='ACTIVE')
    return {'region':region,'discovery':discovery,'inventory':inventory,
        'note':'Catalog visibility is not proof of model inference entitlement or tool-call compatibility.'}


if __name__ == '__main__':
    server.run(transport='stdio')
