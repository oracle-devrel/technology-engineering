from __future__ import annotations
import time

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import base64
from io import BytesIO
import qrcode
import requests


import oci
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from oci.generative_ai_agent_runtime.models import ChatDetails, CreateSessionDetails, FunctionCallingPerformedAction

# ---------------------------------------------------------------------------
# Configuration UPDATE with your endpoint OCID and your Service Endpoint
# ---------------------------------------------------------------------------

AGENT_ENDPOINT_ID = "ocid1.genaiagentendpoint.oc1.eu-frankfurt-1."
SERVICE_ENDPOINT = "https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
PROFILE_NAME = "DEFAULT"  # profile in ~/.oci/config

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatAgent:

    def __init__(self) -> None:
        cfg = oci.config.from_file("~/.oci/config", profile_name=PROFILE_NAME)
        self.client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
            config=cfg,
            service_endpoint=SERVICE_ENDPOINT,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )
        self.session_id: Optional[str] = None
        self.current_user: Optional[str] = None
    # ------------------------------------------------------------------
    def _create_session(self, *, user: str) -> str:
        details = CreateSessionDetails(
            display_name=f"Flask-session for {user}",
            description="Session created by flask_chat_server.py",
        )
        resp = self.client.create_session(details, AGENT_ENDPOINT_ID)
        self.session_id = resp.data.id
        self.current_user = user
        logger.debug("Created new session %s for %s", self.session_id, user)
        return self.session_id

    # ------------------------------------------------------------------
    # QR
    @staticmethod
    def generate_qr_code(url: str, size: int = 200) -> dict:
        """Generates a QR code for the given URL and returns it as a base64-encoded PNG."""
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white").resize((size, size))
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()
        return {"image_base64": b64}
    
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_text(message_obj: Any) -> str:
        try:
            content_list = getattr(message_obj, "content", None)
            if content_list:
                first = content_list[0] if isinstance(content_list, list) else content_list
                return getattr(first, "text", str(first))
            return str(message_obj)
        except Exception as exc:
            logger.warning("Failed to extract text: %s", exc)
            return str(message_obj)

    def convert_sql_to_human_readable(self, sql_output: str, user: str) -> str:
        """Convert SQL output to human readable format using OCI LLM."""
        try:
            if len(sql_output) > 1000:
                return f"Hi {user}, the data you requested is quite large. Could you please specify what specific information you're looking for? This will help me provide you with a more focused and useful response."

            prompt = f"""Please convert this SQL output into a friendly, human-readable format. 
            Address the user as '{user}' once and present the information in a clear, conversational way.
            If it's a list or table, format it nicely Please do not provide in the answer SQL query that was passed only human nice language. 
            Here's the SQL output:
            {sql_output}"""

            chat_details = ChatDetails(
                user_message=prompt,
                session_id=self.session_id,
                should_stream=False
            )
            reply = self.client.chat(AGENT_ENDPOINT_ID, chat_details)
            return self._extract_text(reply.data.message)

        except Exception as e:
            logger.error(f"Error converting SQL output: {e}")
            return f"Hi {user}, I encountered an error while processing your data. Please try again."

    def _is_sql_output(self, text: str) -> bool:
        """Check if the text appears to be SQL output."""
        sql_indicators = [
            "SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY",
            "INSERT INTO", "UPDATE", "DELETE FROM", "CREATE TABLE"
        ]
        return any(indicator in text.upper() for indicator in sql_indicators)

    # ------------------------------------------------------------------
    def send(self, *, prompt: str, user: str, max_tokens: Optional[int] = None) -> str:
        if self.session_id is None or self.current_user != user:
            self._create_session(user=user)

        weather_response = self.process_weather_query(prompt)
        if weather_response:
            return weather_response

        filter_conditions: Dict[str, Any] = {
            "filterConditions": [
                {
                    "field": "person",
                    "field_type": "list_of_string",
                    "operation": "contains",
                    "value": user,
                }
            ]
        }

        logger.info("Applying RAG filter with author='%s'", user)

        tool_params: Dict[str, str] = {"rag": json.dumps(filter_conditions)}
        if max_tokens is not None:
            tool_params["max_tokens"] = str(max_tokens)

        chat_details = ChatDetails(
            user_message=prompt,
            session_id=self.session_id,
            should_stream=False,
            tool_parameters=tool_params,
        )
        reply = self.client.chat(AGENT_ENDPOINT_ID, chat_details)
        data = reply.data

        response_text = self._extract_text(data.message)

        if self._is_sql_output(response_text):
            return self.convert_sql_to_human_readable(response_text, user)

        if getattr(data, "required_actions", None):
            action = data.required_actions[0]
            func_call = action.function_call
            args = json.loads(func_call.arguments)
            if func_call.name == "generateQrCode":
                result = self.generate_qr_code(**args)
                performed = FunctionCallingPerformedAction(
                    action_id=action.action_id,
                    function_call_output=json.dumps(result)
                )
                final_reply = self.client.chat(
                    AGENT_ENDPOINT_ID,
                    ChatDetails(
                        session_id=self.session_id,
                        user_message="",
                        performed_actions=[performed],
                        should_stream=False,
                        tool_parameters=tool_params,
                    )
                )

                raw = self._extract_text(final_reply.data.message)
                payload = result["image_base64"]
                if payload in raw:
                    raw = raw.replace(payload, "").strip()
                if not raw:
                    raw = "Here's your QR code!"
                return {
                    "message": raw,
                    "qr_image_base64": payload
                }

        return self._extract_text(reply.data.message)


# ---------------------------------------------------------------------------
# Flask wiring
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app)
chat_agent = ChatAgent()

@app.route("/")
def index():
    return send_from_directory(Path(app.root_path), "index.html")

@app.route("/config.js")
def config_js():
    return send_from_directory(Path(app.root_path), "config.js")

@app.route("/chat", methods=["POST"])
def chat() -> tuple[Any, int] | Any:
    data = request.get_json(silent=True) or {}
    prompt_raw = str(data.get("message", "").strip())
    user_raw = str(data.get("user", "anonymous").strip() or "anonymous")

    #user = user_raw[0].upper() + user_raw[1:] if user_raw else user_raw
    user = user_raw
    max_tokens_raw = data.get("max_tokens")

    if not prompt_raw:
        return jsonify({"error": "Missing 'message'"}), 400

    try:
        max_tokens = int(max_tokens_raw) if max_tokens_raw is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "'max_tokens' must be an integer"}), 400

    try:
        reply = chat_agent.send(prompt=prompt_raw, user=user, max_tokens=max_tokens)
        if isinstance(reply, dict):
            return jsonify({"user": user, **reply})
        else:
            return jsonify({"user": user, "message": reply})
    except Exception as exc:
        logger.exception("/chat failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
