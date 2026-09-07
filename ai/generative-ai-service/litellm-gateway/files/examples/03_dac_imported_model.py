#!/usr/bin/env python3
"""
Imported model on a Dedicated AI Cluster (DAC).

Models imported into OCI GenAI (e.g. Qwen 3 from Hugging Face) and hosted
on a DAC are served behind OCI's OpenAI-compatible endpoint. Two ways in:

  A) Through the gateway (recommended) - the `gpt-oss-120b-dac` entry in
     config.yaml maps to the DAC endpoint; clients don't need to know
     any OCIDs or OCI keys.

  B) Direct - useful to understand what the gateway does under the hood:
       base_url = https://inference.generativeai.<region>.oci.oraclecloud.com/20231130/actions/v1
       api_key  = an OCI GenAI API key ("sk-...", created in console/CLI)
       model    = the DAC *endpoint OCID*

    python 03_dac_imported_model.py
"""

import os

from openai import OpenAI

# --- A) Through the gateway --------------------------------------------------
gateway = OpenAI(
    base_url=os.getenv("GATEWAY_BASE_URL", "http://localhost:4000"),
    api_key=os.getenv("GATEWAY_API_KEY", "sk-change-me-admin-key"),
)

response = gateway.chat.completions.create(
    model="gpt-oss-120b-dac",
    messages=[{"role": "user", "content": "Say hello from a Dedicated AI Cluster."}],
    max_tokens=100,
)
print("[via gateway]", response.choices[0].message.content)

# --- B) Direct against the OCI OpenAI-compatible endpoint --------------------
# (this is exactly what the gateway's `gpt-oss-120b-dac` entry does internally)
if os.getenv("OCI_GENAI_API_KEY"):
    direct = OpenAI(
        base_url=os.environ["OCI_COMPAT_API_BASE"],
        api_key=os.environ["OCI_GENAI_API_KEY"],
    )
    response = direct.chat.completions.create(
        # model name = DAC endpoint OCID, e.g. from OCI_DAC_MODEL without
        # the "openai/" prefix
        model=os.environ["OCI_DAC_MODEL"].removeprefix("openai/"),
        messages=[{"role": "user", "content": "Say hello, directly this time."}],
        max_tokens=100,
    )
    print("[direct]     ", response.choices[0].message.content)
else:
    print("[direct]      skipped - set OCI_GENAI_API_KEY / OCI_COMPAT_API_BASE / OCI_DAC_MODEL")
