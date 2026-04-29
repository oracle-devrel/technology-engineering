"""Image generation clients for OCI Generative AI.

Two auth paths are used side-by-side:
- Grok use the stock openai SDK against the OCI OpenAI-compatible
  endpoint (.../openai/v1) with an OCI GenAI API key and project OCID.
- Qwen runs on a DAC in image-edit mode, which requires a reference image.
  That call uses oci.signer.Signer + requests with multipart form-data against
  the legacy DAC path (.../20231130/actions/v1/openai/v1/images/edits).
"""
import base64
import io

import requests
from oci.config import from_file
from oci.signer import Signer
from openai import OpenAI
from PIL import Image


# OpenAI-SDK client for Grok — path /openai/v1 is appended if missing
def _client(host: str, api_key: str, project: str) -> OpenAI:
    base_url = host.rstrip("/")
    if not base_url.endswith("/openai/v1"):
        base_url = f"{base_url}/openai/v1"
    return OpenAI(base_url=base_url, api_key=api_key, project=project)


# Request signer for the legacy DAC path (used by Qwen only)
def _signer(profile: str):
    config = from_file(profile_name=profile)
    return Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
    )


# Decode an OpenAI-SDK image result into a PIL image
def _decode_sdk(result) -> Image.Image:
    if not result.data:
        raise ValueError("Empty image response")
    item = result.data[0]
    if getattr(item, "b64_json", None):
        return Image.open(io.BytesIO(base64.b64decode(item.b64_json)))
    if getattr(item, "url", None):
        r = requests.get(item.url, timeout=60)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    raise ValueError("Image response contained neither b64_json nor url")


# Decode a raw JSON image response into a PIL image
def _decode_raw(payload: dict) -> Image.Image:
    if not payload.get("data"):
        raise ValueError(f"Empty image response: {payload}")
    item = payload["data"][0]
    if item.get("b64_json"):
        return Image.open(io.BytesIO(base64.b64decode(item["b64_json"])))
    if item.get("url"):
        r = requests.get(item["url"], timeout=60)
        r.raise_for_status()
        return Image.open(io.BytesIO(r.content))
    raise ValueError(f"Unrecognized response keys: {list(item.keys())}")


# Qwen-Image-Edit on DAC — reference image required, single `image` field (multi-image fails routing)
def generate_qwen(
    prompt: str,
    reference_image_bytes: bytes,
    reference_image_name: str,
    profile: str,
    compartment_id: str,
    dac_endpoint: str,
    dac_endpoint_ocid: str,
    size: str = "1024x1024",
) -> Image.Image:
    signer = _signer(profile)
    url = f"{dac_endpoint.rstrip('/')}/openai/v1/images/edits"

    files = {"image": (reference_image_name, reference_image_bytes)}
    data = {
        "model": dac_endpoint_ocid,
        "apiIdentifier": dac_endpoint_ocid,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
    }
    headers = {
        "opc-compartment-id": compartment_id,
        "CompartmentId": compartment_id,
        # Content-Type intentionally unset so requests sets the multipart boundary
    }

    resp = requests.post(url, files=files, data=data, headers=headers, auth=signer, timeout=300)
    resp.raise_for_status()
    return _decode_raw(resp.json())


# Grok image generation — OCI on-demand via OpenAI SDK
def generate_grok(
    prompt: str,
    host: str,
    api_key: str,
    project: str,
) -> Image.Image:
    client = _client(host, api_key, project)
    result = client.images.generate(
        model="xai.grok-imagine-image",
        prompt=prompt,
    )
    return _decode_sdk(result)
