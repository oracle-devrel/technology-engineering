import base64
import io
import os
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image


load_dotenv()


def _resolve_openai_base_url(base_url: str) -> str:
    root = base_url.rstrip("/")
    if root.endswith("/openai/v1"):
        return root
    return f"{root}/openai/v1"


def _decode_image_result(result) -> Image.Image:
    image_item = result.data[0]
    if image_item.b64_json:
        image_bytes = base64.b64decode(image_item.b64_json)
        return Image.open(io.BytesIO(image_bytes))
    response = requests.get(image_item.url, timeout=60)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content))


def generate_grok_image(
    prompt: str, base_url: str, api_key: str, project: str, reference_image_path: Optional[str] = None
) -> Image.Image:
    client = OpenAI(base_url=_resolve_openai_base_url(base_url), api_key=api_key, project=project)

    if reference_image_path:
        image_path = Path(reference_image_path)
        with image_path.open("rb") as image_file:
            try:
                # Primary path: model-guided edit with user photo input.
                result = client.images.edit(
                    model="xai.grok-imagine-image",
                    prompt=prompt,
                    image=image_file,
                )
                return _decode_image_result(result)
            except Exception:
                image_file.seek(0)
                # Fallback for providers exposing image input via extra body.
                image_b64 = base64.b64encode(image_file.read()).decode("utf-8")
                result = client.images.generate(
                    model="xai.grok-imagine-image",
                    prompt=prompt,
                    extra_body={"input_image": image_b64},
                )
                return _decode_image_result(result)

    result = client.images.generate(model="xai.grok-imagine-image", prompt=prompt)
    return _decode_image_result(result)


def generate_from_env(prompt: str, reference_image_path: Optional[str] = None) -> Image.Image:
    base_url = os.getenv("ENDPOINT", "")
    api_key = (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OCI_GENAI_API_KEY")
        or os.getenv("OCI_IMAGE_API_KEY")
        or ""
    )
    project = (os.getenv("OCI_PROJECT_ID") or os.getenv("COMPARTMENT_ID") or "").strip()
    return generate_grok_image(
        prompt=prompt,
        base_url=base_url,
        api_key=api_key,
        project=project,
        reference_image_path=reference_image_path,
    )
