#!/usr/bin/env python3
"""
Automatic model routing (Stage 2).

Clients send model="auto" and the gateway's complexity router picks the
tier per request - token count, code presence, reasoning markers and
multi-step patterns are scored in sub-millisecond time (see the `auto`
entry in config/config.yaml). The model that actually served the request
comes back in the `x-litellm-model-name` response header (the body's
`model` field echoes the alias "auto").

    python 02_auto_routing.py
"""

import os

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("GATEWAY_BASE_URL", "http://localhost:4000"),
    api_key=os.getenv("GATEWAY_API_KEY", "sk-change-me-admin-key"),
)

# Prompts verified against the classifier's default weights/boundaries
# (litellm 1.95.0) so each one lands in its intended tier: the scorer keys on
# keyword signals (code terms, technical terms, explicit reasoning markers),
# not on how hard the task *feels* — a prompt with no keyword signals scores
# SIMPLE no matter how elaborate it reads.
PROMPTS = {
    "simple": "What is the capital of Sweden?",
    "medium": (
        "Write a SQL query that returns the top ten customers by total order "
        "value in the last quarter."
    ),
    "complex": (
        "Implement a Python function that queries our orders database with SQL, "
        "handles connection errors with retry logic, and exposes the result "
        "through a REST API endpoint. The architecture is distributed "
        "microservices on Kubernetes with strict latency and throughput "
        "requirements. Refactor for performance and optimize the query."
    ),
    "reasoning": (
        "Think through this step by step and explain your reasoning: "
        "A farmer has 17 sheep. All but 9 run away, then he buys twice as many "
        "as remain, and sells a third of the total. Analyze this carefully, "
        "break down each stage, and conclude with the final count."
    ),
}

for label, prompt in PROMPTS.items():
    raw = client.chat.completions.with_raw_response.create(
        model="auto",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
    )
    routed_to = raw.headers.get("x-litellm-model-name", "?")
    cost = raw.headers.get("x-litellm-response-cost", "?")
    response = raw.parse()
    print(f"[{label:9s}] routed to: {routed_to}  (cost ${cost})")
    print(f"            {response.choices[0].message.content[:120]!r}...\n")

# You can also pin deployments with tags instead of full auto-routing
# (router_settings.enable_tag_filtering in config.yaml):
response = client.chat.completions.create(
    model="grok-4-fast",
    messages=[{"role": "user", "content": "hello"}],
    extra_body={"tags": ["oci"]},  # only deployments tagged "oci" are considered
)
print("[tag-routed]", response.choices[0].message.content[:80])
