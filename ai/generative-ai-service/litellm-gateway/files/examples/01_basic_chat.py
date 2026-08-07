#!/usr/bin/env python3
"""
Basic chat through the gateway.

Every model behind the gateway - OCI on-demand, DAC imported, external -
speaks the same OpenAI API with the same virtual key. Point any existing
OpenAI-SDK application at the gateway and it just works.

    export GATEWAY_BASE_URL=http://localhost:4000
    export GATEWAY_API_KEY=sk-...   # virtual key or master key
    python 01_basic_chat.py
"""

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("GATEWAY_BASE_URL", "http://localhost:4000"),
    api_key=os.getenv("GATEWAY_API_KEY", "sk-change-me-admin-key"),
)

# List every model the gateway exposes
print("Models on the gateway:")
for model in client.models.list():
    print(f"  - {model.id}")

# Non-streaming
response = client.chat.completions.create(
    model="grok-4-fast",
    messages=[{"role": "user", "content": "In one sentence: what is OCI Generative AI?"}],
)
print("\n[grok-4-fast]", response.choices[0].message.content)
print("Tokens:", response.usage.total_tokens)

# Streaming
print("\n[llama-4-scout, streaming] ", end="", flush=True)
stream = client.chat.completions.create(
    model="llama-4-scout",
    messages=[{"role": "user", "content": "Write a haiku about Oracle Cloud."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
