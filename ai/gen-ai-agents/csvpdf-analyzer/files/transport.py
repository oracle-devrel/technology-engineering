"""
This file contains the pluggable component for the transport
to enable tracing to APM
"""

import requests
from utils import get_console_logger
from config import APM_PUBLIC_KEY, APM_BASE_URL, APM_CONTENT_TYPE, ENABLE_TRACING


logger = get_console_logger()


def http_transport(encoded_span):
    """
    Sends encoded tracing data to OCI APM using py-zipkin.

    Args:
        encoded_span (bytes): The encoded span data to send.

    Returns:
        requests.Response or None: The response from the APM service or None if tracing is disabled.
    """
    try:
        # Load config inside the function to avoid global dependency issues
        base_url = APM_BASE_URL
        content_type = APM_CONTENT_TYPE

        # Validate configuration
        if not base_url:
            raise ValueError("APM base URL is not configured")
        if not APM_PUBLIC_KEY:
            raise ValueError("APM public key is missing")

        # If tracing is disabled, do nothing
        if not ENABLE_TRACING:
            logger.info("Tracing is disabled. No data sent to APM.")
            return None

        # Construct endpoint dynamically
        apm_url = f"{base_url}/observations/public-span?dataFormat=zipkin&dataFormatVersion=2&dataKey={APM_PUBLIC_KEY}"

        response = requests.post(
            apm_url,
            data=encoded_span,
            headers={"Content-Type": content_type},
            timeout=30,
        )
        response.raise_for_status()  # Raise exception for HTTP errors

        return response
    except requests.RequestException as e:
        logger.error("Failed to send span to APM: %s", str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error in http_transport: %s", str(e))
        return None
