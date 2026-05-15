# Developed by: Brona Nilsson
"""
OCI Authentication, LLM Chat, and Knowledge Base Search

Self-contained OCI helpers for the standalone DOCX report MCP server.
Handles Instance Principals (on compute) and ~/.oci/config (local dev).
"""

import os
import json
import logging

import oci
import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OCI Auth — Instance Principals with ~/.oci/config fallback
# ---------------------------------------------------------------------------

try:
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    config = {"region": signer.region, "tenancy": signer.tenancy_id}
    logger.info("oci_auth: using Instance Principals")
except Exception:
    _profile = os.getenv("OCI_CLI_PROFILE", "DEFAULT")
    config = oci.config.from_file(profile_name=_profile)
    signer = oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )
    logger.info("oci_auth: using ~/.oci/config (profile=%s)", _profile)


# ---------------------------------------------------------------------------
# LLM Chat — OCI GenAI chat endpoint
# ---------------------------------------------------------------------------

def llm_chat(prompt, max_tokens=4000):
    """Call OCI GenAI chat with a configurable maxTokens limit.

    Uses env vars:
        COMPARTMENT_OCID (fallback TF_VAR_compartment_ocid)
        OCI_REGION       (fallback TF_VAR_region)
        GENAI_MODEL      (fallback TF_VAR_genai_meta_model)
    """
    compartment_id = os.getenv("COMPARTMENT_OCID", os.getenv("TF_VAR_compartment_ocid"))
    region = os.getenv("OCI_REGION", os.getenv("TF_VAR_region"))
    model = os.getenv("GENAI_MODEL", os.getenv("TF_VAR_genai_model"))
    endpoint = (
        f"https://inference.generativeai.{region}.oci.oraclecloud.com"
        "/20231130/actions/chat"
    )

    body = {
        "compartmentId": compartment_id,
        "servingMode": {
            "modelId": model,
            "servingType": "ON_DEMAND",
        },
        "chatRequest": {
            "apiFormat": "GENERIC",
            "maxTokens": max_tokens,
            "temperature": 0,
            "topP": 0.75,
            "topK": 0,
            "messages": [
                {
                    "role": "USER",
                    "content": [{"type": "TEXT", "text": prompt}],
                }
            ],
        },
    }

    resp = requests.post(endpoint, json=body, auth=signer)
    resp.raise_for_status()
    j = resp.json()

    chat_response = j["chatResponse"]
    if chat_response.get("text"):
        s = chat_response["text"]
    else:
        s = chat_response["choices"][0]["message"]["content"][0]["text"]

    # Strip code-fence wrapper if present
    if s.startswith("```json"):
        start = s.find("{")
        end = s.rfind("}") + 1
        if start != -1 and end > start:
            s = s[start:end]

    return s


# ---------------------------------------------------------------------------
# KB Search — OCI Agent Runtime API
# ---------------------------------------------------------------------------

def kb_search(question):
    """Search the OCI GenAI Agent Knowledge Base and return the response text.

    Uses env vars:
        AGENT_ENDPOINT_OCID (fallback TF_VAR_agent_endpoint_ocid)
        AGENT_REGION        (fallback OCI_REGION, then TF_VAR_region)
    """
    agent_endpoint_ocid = os.getenv(
        "AGENT_ENDPOINT_OCID", os.getenv("TF_VAR_agent_endpoint_ocid")
    )
    region = os.getenv(
        "AGENT_REGION", os.getenv("OCI_REGION", os.getenv("TF_VAR_region"))
    )

    try:
        runtime_client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
            config=config,
            signer=signer,
            service_endpoint=f"https://agent-runtime.generativeai.{region}.oci.oraclecloud.com",
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

        # Create session
        create_session_details = oci.generative_ai_agent_runtime.models.CreateSessionDetails(
            display_name="session", description="description"
        )
        session_resp = runtime_client.create_session(
            create_session_details, agent_endpoint_ocid
        )
        session_id = session_resp.data.id

        # Chat
        chat_details = oci.generative_ai_agent_runtime.models.ChatDetails(
            user_message=str(question),
            should_stream=False,
            session_id=session_id,
        )
        chat_resp = runtime_client.chat(agent_endpoint_ocid, chat_details)

        if chat_resp.status == 200:
            if chat_resp.data.message and chat_resp.data.message.content:
                return chat_resp.data.message.content.text or ""
        return ""
    except Exception as e:
        logger.warning("KB search failed for '%s': %s", question, e)
        return ""
