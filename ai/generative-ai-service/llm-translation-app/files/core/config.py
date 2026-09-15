import os

COMPARTMENT_ID = os.environ.get("OCI_COMPARTMENT_ID", "")

ENDPOINT = os.environ.get(
    "OCI_GENAI_ENDPOINT",
    "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
)

CHAT_PATH = "/20231130/actions/chat"

DEFAULT_MODEL = os.environ.get(
    "OCI_DEFAULT_MODEL",
    "cohere.command-a-03-2025",
)

OCI_CONFIG_FILE = os.environ.get("OCI_CONFIG_FILE", "~/.oci/config")
OCI_CONFIG_PROFILE = os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT")

SUPPORTED_LANGUAGES = {"english", "german", "spanish-mx", "polish", "portuguese-br", "swedish"}

# Every allowed translation pair (order-independent: each pair works in both directions)
ALLOWED_PAIRS: set[frozenset[str]] = {
    # English ↔ …
    frozenset({"english", "german"}),
    frozenset({"english", "spanish-mx"}),
    frozenset({"english", "polish"}),
    frozenset({"english", "portuguese-br"}),
    frozenset({"english", "swedish"}),
    # German ↔ …
    frozenset({"german", "polish"}),
    frozenset({"german", "swedish"}),
    frozenset({"german", "spanish-mx"}),
    frozenset({"german", "portuguese-br"}),
    # Spanish ↔ …
    frozenset({"spanish-mx", "polish"}),
    frozenset({"spanish-mx", "swedish"}),
}

MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.0"))
TOP_P = float(os.environ.get("TOP_P", "0.8"))
