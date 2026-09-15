#!/usr/bin/env python3
"""
Agentic workflow + observability (Stage 4).

A small tool-calling agent loop that runs entirely through the gateway.
With `callbacks: ["langfuse_otel"]` enabled in config.yaml (and LANGFUSE_*
set in .env), every LLM call in the loop lands in Langfuse as part of one
trace: prompts, tool calls, token usage, latency and cost - per virtual
key, so you can see which team/app spent what.

The trace metadata below groups the calls; no Langfuse SDK is needed in
the client, the gateway reports server-side.

    python 05_agentic_observability.py
"""

import json
import os

from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("GATEWAY_BASE_URL", "http://localhost:4000"),
    api_key=os.getenv("GATEWAY_API_KEY", "sk-change-me-admin-key"),
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_compute_shapes",
            "description": "List OCI compute shapes matching a minimum OCPU count.",
            "parameters": {
                "type": "object",
                "properties": {
                    "min_ocpus": {"type": "integer", "description": "Minimum OCPUs"}
                },
                "required": ["min_ocpus"],
            },
        },
    }
]


def get_compute_shapes(min_ocpus: int) -> str:
    shapes = {
        "VM.Standard.E5.Flex": 94,
        "VM.Standard3.Flex": 32,
        "BM.Standard.E5.192": 192,
    }
    return json.dumps({k: v for k, v in shapes.items() if v >= min_ocpus})


# Metadata that groups all calls of this run into one Langfuse trace
TRACE = {
    "metadata": {
        "trace_name": "shape-advisor-agent",
        "trace_user_id": "demo-user",
        "tags": ["agentic", "demo"],
    }
}

messages = [
    {"role": "system", "content": "You are an OCI sizing assistant. Use tools when helpful."},
    {"role": "user", "content": "Which shapes support at least 64 OCPUs? Recommend one for a database."},
]

for step in range(5):  # simple agent loop
    response = client.chat.completions.create(
        model="grok-4-fast",
        messages=messages,
        tools=TOOLS,
        extra_body=TRACE,
    )
    message = response.choices[0].message

    if not message.tool_calls:
        print("Final answer:\n", message.content)
        break

    messages.append(message.model_dump(exclude_none=True))
    for tool_call in message.tool_calls:
        args = json.loads(tool_call.function.arguments)
        print(f"[step {step}] tool call: {tool_call.function.name}({args})")
        result = get_compute_shapes(**args)
        messages.append(
            {"role": "tool", "tool_call_id": tool_call.id, "content": result}
        )
