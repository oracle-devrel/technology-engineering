"""
General configuration options
"""

#
# application configs
#
# in secs
SLEEP_TIME = 1
DEBUG = False

# this is only for the UI
SUPPORTED_LANGUAGES = ["EN", "IT"]
SUPPORTED_LANGUAGES_LONG = {"EN": "English", "IT": "Italiano"}

# this is the list of the mandatory fields in user input
# if any of these fields is missing, the agent will ask for clarification
REQUIRED_FIELDS = [
    "place_of_departure",
    "destination",
    "start_date",
    "end_date",
    "num_persons",
    "transport_type",
]

# OCI GenAI services configuration

# can be also INSTANCE_PRINCIPAL
AUTH_TYPE = "API_KEY"

REGION = "eu-frankfurt-1"
# REGION = "us-chicago-1"
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# seems to work fine with both models
MODEL_ID = "meta.llama-3.3-70b-instruct"
# MODEL_ID = "cohere.command-a-03-2025"

MAX_TOKENS = 2048

#
# Map configuration
# Hotel Map
MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"

#
# Mock API (Hotel and transport)
#
HOST_API = "localhost"
PORT_MOCK_API = 8000
HOTEL_API_URL = f"http://{HOST_API}:{PORT_MOCK_API}/search/hotels"
TRANSPORT_API_URL = f"http://{HOST_API}:{PORT_MOCK_API}/search/transport"

#
# AGENT API
#
PORT_AGENT = 8080
AGENT_API_URL = f"http://{HOST_API}:{PORT_AGENT}/invoke"
