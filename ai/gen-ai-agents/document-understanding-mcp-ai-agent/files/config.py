"""
OCI models configuration and general config
"""

DEBUG = False

MODEL_ID = "meta.llama-3.3-70b-instruct"

AUTH = "API_KEY"
SERVICE_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"

TEMPERATURE = 0.1
MAX_TOKENS = 1024
TOP_P = 0.9

# OCI general
COMPARTMENT_ID = "ocid1.compartm..."

# history management
MAX_MSGS_IN_HISTORY = 10
# low, cause we're generating code
MAX_ROWS_IN_SAMPLE = 10

# integration with RAG
# RAG_AGENT_ID = "ocid1.genaiagentendpoint.oc1.us-c..."
# RAG_AGENT_ENDPOINT = "https://agent-runtime.generativeai.us-chicago-1.oci.oraclecloud.com"
# switched to Ali Agent
RAG_AGENT_ID = "ocid1.genaiagentendpoint.oc1.uk-..."
RAG_AGENT_ENDPOINT = (
    "https://agent-runtime.generativeai.uk-london-1.oci.oraclecloud.com"
)


