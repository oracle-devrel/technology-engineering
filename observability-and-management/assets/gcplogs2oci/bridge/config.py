"""
Configuration management for the GCP → OCI bridge.

All settings are read from environment variables (loaded from .env.local
for local development). No secrets are embedded in source.
"""

import os
import re
import textwrap

from dotenv import load_dotenv


def load_env():
    """Load environment from .env.local (preferred) or .env, searching upward."""
    candidates = [
        os.path.join(os.getcwd(), ".env.local"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(__file__), "..", ".env.local"),
        os.path.join(os.path.dirname(__file__), "..", ".env"),
    ]
    for path in candidates:
        if os.path.exists(path):
            load_dotenv(path)
            return path
    return None


def parse_key(key_input: str) -> str:
    """Parse OCI private key from single-line or multi-line PEM format."""
    normalized = (key_input or "").replace("\\n", "\n").strip()

    begin_match = re.search(r"-----BEGIN [A-Z ]+-----", normalized)
    end_match = re.search(r"-----END [A-Z ]+-----", normalized)
    if not begin_match or not end_match:
        raise ValueError("PEM BEGIN/END markers not found in key_content")

    begin_line = begin_match.group()
    end_line = end_match.group()
    key_block = normalized[begin_match.end():end_match.start()]

    # Preserve encryption headers if present
    encr_lines = ""
    for pattern in (r"Proc-Type: [^\n]+", r"DEK-Info: [^\n]+"):
        m = re.search(pattern, key_block)
        if m:
            encr_lines += m.group().strip() + "\n"
            key_block = key_block.replace(m.group(), "")

    body_compact = re.sub(r"\s+", "", key_block)
    wrapped_body = "\n".join(textwrap.wrap(body_compact, 64))

    parts = [begin_line]
    if encr_lines:
        parts.append(encr_lines.rstrip("\n"))
    parts.append(wrapped_body)
    parts.append(end_line)
    return "\n".join(parts)


def mask(value: str, keep: int = 6) -> str:
    """Mask a secret for safe logging."""
    if not value:
        return ""
    if len(value) <= keep:
        return "***"
    return f"{value[:keep]}...***"


# ── GCP settings ──────────────────────────────────────────────

def gcp_project_id() -> str:
    return os.environ["GCP_PROJECT_ID"]


def gcp_subscription() -> str:
    return os.environ["GCP_PUBSUB_SUBSCRIPTION"]


def gcp_topic() -> str:
    return os.environ.get("GCP_PUBSUB_TOPIC", "oci-log-export-topic")


# ── OCI settings ─────────────────────────────────────────────

def oci_config() -> dict:
    """Build an OCI SDK configuration dict from environment variables.

    Supports two modes for the private key:
      - OCI_KEY_FILE: path to a PEM file (preferred for local dev)
      - OCI_KEY_CONTENT: inline PEM string (for CI / container deployments)
    """
    key_file = os.environ.get("OCI_KEY_FILE")
    key_content = os.environ.get("OCI_KEY_CONTENT")

    if key_file:
        with open(os.path.expanduser(key_file)) as f:
            key_pem = f.read()
        # Strip anything after the END marker (some files have trailing labels)
        key_pem = parse_key(key_pem)
    elif key_content:
        key_pem = parse_key(key_content)
    else:
        raise RuntimeError("Set either OCI_KEY_FILE or OCI_KEY_CONTENT")

    return {
        "user": os.environ["OCI_USER_OCID"],
        "key_content": key_pem,
        "pass_phrase": os.environ.get("OCI_KEY_PASSPHRASE", ""),
        "fingerprint": os.environ["OCI_FINGERPRINT"],
        "tenancy": os.environ["OCI_TENANCY_OCID"],
        "region": os.environ["OCI_REGION"],
    }


def oci_message_endpoint() -> str:
    return os.environ["OCI_MESSAGE_ENDPOINT"]


def oci_stream_ocid() -> str:
    ocid = os.environ["OCI_STREAM_OCID"]
    if "streampool" in ocid:
        raise RuntimeError(
            "OCI_STREAM_OCID points to a Stream Pool. "
            "Use the Stream OCID (ocid1.stream...) instead."
        )
    return ocid


def max_batch_size() -> int:
    return int(os.environ.get("MAX_BATCH_SIZE", 100))


def max_batch_bytes() -> int:
    return int(os.environ.get("MAX_BATCH_BYTES", 1024 * 1024))


def ack_deadline_seconds() -> int:
    return int(os.environ.get("ACK_DEADLINE_SECONDS", 60))


def pull_max_messages() -> int:
    return int(os.environ.get("PULL_MAX_MESSAGES", 1000))


def inactivity_timeout() -> int:
    return int(os.environ.get("INACTIVITY_TIMEOUT", 30))
