"""Small project-owned identity MCP adapter, NOT Oracle's official identity server.

It returns identity evidence for configured compartments only. It is replaceable
with a compatible get_compartment tool from the official identity integration.
"""
import json
import os
from pathlib import Path
import oci
from mcp.server.fastmcp import FastMCP
from .model import config_and_signer

server = FastMCP('db-assistant-identity')


@server.tool()
def get_compartment(compartment_id: str) -> dict:
    """Verify a configured compartment with the OCI Identity service."""
    policy = json.loads((Path(os.getenv('CONFIG_DIR','/config'))/'access.json').read_text())
    allowed = {e['compartment_id'] for e in policy['environments'].values()}
    if compartment_id not in allowed:
        raise ValueError('Compartment is not configured')
    config, signer = config_and_signer()
    client = oci.identity.IdentityClient(config,signer=signer,timeout=(10,30))
    data = client.get_compartment(compartment_id).data
    return {'id':data.id,'name':data.name,'lifecycle_state':data.lifecycle_state,'compartment_id':data.compartment_id,'tenancy_id':config.get('tenancy')}


if __name__ == '__main__':
    server.run(transport='stdio')
