"""
OCI GenAI image generation client.
Wraps the oci_openai SDK call and returns raw PNG bytes.
"""

import base64
from oci_openai import OciOpenAI, OciUserPrincipalAuth
from typing import Optional, Tuple

# OCI settings — update compartment_id and profile as needed
COMPARTMENT_ID = "Add your compartment OCID here"
PROFILE_NAME   = "CHICAGO"
REGION         = "us-chicago-1"
MODEL          = "Add your model name here"
SIZE           = "1024x1024"


def generate_image(prompt: str) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Calls OCI image generation and returns (png_bytes, error_string).
    One of the two will always be None.
    """
    try:

        client = OciOpenAI(
            auth=OciUserPrincipalAuth(profile_name=PROFILE_NAME),
            compartment_id=COMPARTMENT_ID,
            region=REGION,
        )

        response = client.images.generate(
            model=MODEL,
            prompt=prompt,
            size=SIZE,
            output_format="png",
        )

        png_bytes = base64.b64decode(response.data[0].b64_json)
        return png_bytes, None

    except ImportError:
        return None, "oci_openai package not installed. Run: pip install oci-openai"
    except Exception as e:
        return None, str(e)
