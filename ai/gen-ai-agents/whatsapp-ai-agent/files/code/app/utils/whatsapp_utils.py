import logging
from flask import current_app, jsonify
import json
import requests
import re
from dotenv import load_dotenv


from langchain_community.chat_models import ChatOCIGenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
import oci

import os

config = oci.config.from_file()

load_dotenv()
GENERATE_MODEL = os.getenv("GENERATE_MODEL")
ENDPOINT = os.getenv("ENDPOINT")
AGENT_ENDPOINT_OCID = os.getenv("AGENT_ENDPOINT_OCID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")


GENAI_AGENT_RUNTIME_CLIENT = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
    config=config,
    service_endpoint=ENDPOINT
)

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

SESSION_STORE = {}

def generate_response(prompt: str, user_id: str) -> str:
    """
    Calls OCI Generative AI Agent Runtime to create (if needed) or reuse
    a session for this user, then sends the user prompt. Returns the answer.
    """
    try:
        # Check if we already have a session ID for this user
        session_id = SESSION_STORE.get(user_id)

        # If no session for this user, create a new one
        if not session_id:
            resp = GENAI_AGENT_RUNTIME_CLIENT.create_session(
                agent_endpoint_id=AGENT_ENDPOINT_OCID,
                create_session_details=oci.generative_ai_agent_runtime.models.CreateSessionDetails(
                    description='session',
                    display_name='session'
                )
            )
            session_id = resp.data.id
            # Store the session ID in our global dictionary
            SESSION_STORE[user_id] = session_id

        # Now always call chat with the existing or newly created session ID
        resp_chat = GENAI_AGENT_RUNTIME_CLIENT.chat(
            agent_endpoint_id=AGENT_ENDPOINT_OCID,
            chat_details=oci.generative_ai_agent_runtime.models.ChatDetails(
                session_id=session_id,
                user_message=prompt
            )
        )
        
        # The agent's response text:
        assistant_answer = resp_chat.data.message.content.text
        citations = resp_chat.data.message.content.citations

        # Build a simple string of citations
        citations_text = ""
        for i, c in enumerate(citations, start=1):
            t = getattr(c, "title", "N/A")
            p = getattr(c, "page_numbers", "N/A")
            
            citations_text += (
                f"Citation {i}:\n"
                f"  Title: {t}\n"
                f"  Page Numbers: {p}\n"
            )
        
        # Combine the answer with the citations
        return f"{assistant_answer}\n\n\n{citations_text}"

    except Exception as e:
        logging.error(f"Error generating response via OCI Agent: {e}")
        return "I'm sorry, but I couldn't process your request at this time."


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    # TODO: implement custom function here
    #response = generate_response(message_body)
    response = generate_response(message_body, user_id=wa_id)


    # OpenAI Integration
    # response = generate_response(message_body, wa_id, name)
    # response = process_text_for_whatsapp(response)

    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
