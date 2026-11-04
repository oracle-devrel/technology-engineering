"""Verify the dedicated endpoint supports what LabSense needs: uv run python scripts/probe_endpoint.py

Checks streaming chat, native function calling and image understanding through the
OpenAI-compatible route, signed with ~/.oci/config. Writes data/endpoint-capabilities.json.
"""
import base64
import io
import json
import os
import sys
from pathlib import Path

import httpx
import oci
from dotenv import load_dotenv
from oci._vendor import requests
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
REGION = os.getenv("OCI_REGION", "eu-frankfurt-1")
ENDPOINT_ID, COMPARTMENT_ID = os.environ["OCI_ENDPOINT_ID"], os.environ["OCI_COMPARTMENT_ID"]
URL = f"https://inference.generativeai.{REGION}.oci.oraclecloud.com/20231130/actions/v1/chat/completions"
signer = oci.generative_ai_inference.GenerativeAiInferenceClient(config=oci.config.from_file(profile_name=os.getenv("OCI_PROFILE", "DEFAULT"))).base_client.signer


def call(payload: dict, stream: bool = False):
    raw = json.dumps({**payload, "model": ENDPOINT_ID}).encode()
    signed = requests.Request("POST", URL, data=raw, headers={"Content-Type": "application/json", "CompartmentId": COMPARTMENT_ID}).prepare()
    signer(signed)
    with httpx.Client(timeout=300) as client:
        response = client.post(URL, content=raw, headers=dict(signed.headers))
        if stream:
            return response.status_code, response.text[:600]
        return response.status_code, response.json()


results = {}
status, data = call({"messages": [{"role": "user", "content": "Reply with the single word READY."}], "max_tokens": 50, "reasoning_effort": "none"})
results["chat"] = {"status": status, "text": data.get("choices", [{}])[0].get("message", {}).get("content") if status == 200 else data}
status, text = call({"messages": [{"role": "user", "content": "Count from 1 to 5."}], "max_tokens": 50, "stream": True, "reasoning_effort": "none"}, stream=True)
results["stream"] = {"status": status, "sse": text.startswith("data:")}
status, data = call({"messages": [{"role": "user", "content": "Patient had a CBC on 2026-09-20. Doctor orders CBC and TSH today. Call the tool."}],
                     "tools": [{"type": "function", "function": {"name": "evaluate_order", "parameters": {"type": "object", "properties": {"tests": {"type": "array", "items": {"type": "string"}}}, "required": ["tests"]}}}],
                     "tool_choice": "auto", "max_tokens": 600, "reasoning_effort": "low"})
results["tools"] = {"status": status, "tool_calls": data.get("choices", [{}])[0].get("message", {}).get("tool_calls") if status == 200 else data}
image = Image.new("RGB", (700, 200), "white"); ImageDraw.Draw(image).text((30, 60), "HbA1c 7.1 %   2026-08-02", fill="black", font_size=40)
buffer = io.BytesIO(); image.save(buffer, format="PNG")
status, data = call({"messages": [{"role": "user", "content": [{"type": "text", "text": "Transcribe this image exactly."}, {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()}}]}], "max_tokens": 200, "reasoning_effort": "none"})
results["vision"] = {"status": status, "text": data.get("choices", [{}])[0].get("message", {}).get("content") if status == 200 else data}

(ROOT / "data/endpoint-capabilities.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
for name, value in results.items():
    print(f"{name:7} HTTP {value['status']}  {json.dumps({k: v for k, v in value.items() if k != 'status'}, ensure_ascii=False)[:160]}")
sys.exit(0 if all(v["status"] == 200 for v in results.values()) else 1)
