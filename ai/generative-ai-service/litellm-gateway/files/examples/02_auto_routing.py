#!/usr/bin/env python3
"""
Automatic model routing (Stage 2).

Clients send model="auto" and the gateway's complexity router picks the
tier per request - token count, code presence, reasoning markers and
multi-step patterns are scored in sub-millisecond time (see the `auto`
entry in config/config.yaml). The model that actually served the request
comes back in the `x-litellm-model` response header.

    python 02_auto_routing.py
"""

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("GATEWAY_BASE_URL", "http://localhost:4000"),
    api_key=os.getenv("GATEWAY_API_KEY", "sk-change-me-admin-key"),
)

PROMPTS = {
    "simple": "What is the capital of Sweden?",
    "complex": (
        "Design a multi-region disaster recovery architecture for a bank on OCI. "
        "Cover RPO/RTO targets, data replication between Frankfurt and Zurich, "
        "failover automation, and how you would test it quarterly. "
        "Then write Terraform pseudocode for the DNS failover piece."
    ),
    "reasoning": (
        "A farmer has 17 sheep. All but 9 run away, then he buys twice as many as "
        "remain, and sells a third of the total. Reason step by step: how many "
        "sheep does he have?"
    ),
}

for label, prompt in PROMPTS.items():
    raw = client.chat.completions.with_raw_response.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    routed_to = raw.headers.get("x-litellm-model", "?")
    response = raw.parse()
    print(f"[{label:9s}] routed to: {routed_to}")
    print(f"            {response.choices[0].message.content[:120]!r}...\n")

# You can also pin deployments with tags instead of full auto-routing
# (router_settings.enable_tag_filtering in config.yaml):
response = client.chat.completions.create(
    model="grok-4-fast",
    messages=[{"role": "user", "content": "hello"}],
    extra_body={"tags": ["oci"]},  # only deployments tagged "oci" are considered
)
print("[tag-routed]", response.choices[0].message.content[:80])
