"""
General configuration options
"""

#
# application configs
#
DEBUG = False

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
SERVICE_ENDPOINT = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com"

# seems to work fine with both models
MODEL_ID = "meta.llama-3.3-70b-instruct"
# MODEL_ID = "cohere.command-a-03-2025"

MAX_TOKENS = 2048

# Mock API configuration
HOTEL_API_URL = "http://localhost:8000/search/hotels"
TRANSPORT_API_URL = "http://localhost:8000/search/transport"

# Hotel Map
MAP_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
