"""Initialize per-investigation Logan settings, then start its STDIO server."""
import json
import os
from pathlib import Path
import runpy

home=Path.home()/'.oci-logan-mcp'
home.mkdir(parents=True,exist_ok=True)
config=home/'config.yaml'
config.write_text(json.dumps({
    'read_only':True,
    'oci':{'config_path':os.environ['OCI_CONFIG_PATH'],
           'profile':os.environ.get('OCI_CONFIG_PROFILE','DEFAULT'),
           'auth_type':'config_file'},
    'log_analytics':{'namespace':os.environ['OCI_LA_NAMESPACE'],
                     'default_compartment_id':os.environ.get('OCI_LA_COMPARTMENT','')},
    'cache':{'enabled':False},
    'logging':{'query_logging':False},
}))
config.chmod(0o600)
os.environ['OCI_LA_MCP_CONFIG']=str(config)
runpy.run_module('oci_logan_mcp',run_name='__main__')
