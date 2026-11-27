from mcp.server.fastmcp import FastMCP
import os
server=FastMCP('transport-test')

@server.tool()
def get_compartment(compartment_id:str)->dict:
    return {'id':compartment_id,'name':'Transport test','apm_key_present':'APM_DATA_KEY' in os.environ,
        'oci_profile':os.getenv('OCI_CONFIG_PROFILE'),'parent_token_present':'OCI_RESOURCE_PRINCIPAL_RPST' in os.environ,
        'app_secret_present':any(k in os.environ for k in ('SESSION_SECRET','CONNECTION_ENCRYPTION_KEY','OIDC_CLIENT_SECRET'))}

@server.tool()
def test_connection()->dict:
    return {'status':'synthetic fixture'}

@server.tool()
def run_query(query:str,compartment_id:str,include_subcompartments:bool,scope:str,time_start:str,time_end:str,max_results:int)->dict:
    assert include_subcompartments is False
    return {'data':{'columns':[{'name':'Records','type':'INTEGER'}],'rows':[[24]]},'is_partial':False}

if __name__=='__main__':
    server.run(transport='stdio')
