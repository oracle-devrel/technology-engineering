"""
By Omar Salem
tools.py - many tools that can be used by assistant
"""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from oci_models import create_model_for_routing
from state import State

# SCOPES: defines what google permissions we need
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events"
]

# initialize LLM for AI-based summarization & replies
llm = create_model_for_routing()


# ========================
# 1. AUTHENTICATION TOOL
# ========================
def authenticate_google_services():
    """Authenticate and return credentials for both Gmail & Google Calendar."""
    creds = None

    # load existing credentials from token.json
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # refresh expired token or authenticate new user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # refresh token if available
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        # save credentials for future use
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    print("✅ Google Authentication Successful!")
    return creds  # return the authenticated credentials

def authenticate_gmail():
    """Authenticate and return the Gmail service."""
    creds = authenticate_google_services()  # ✅ use shared authentication
    return build("gmail", "v1", credentials=creds)

def authenticate_google_calendar():
    """Authenticate and return the Google Calendar service."""
    creds = authenticate_google_services()  # ✅ use shared authentication
    return build("calendar", "v3", credentials=creds)

# ========================
# 2. FETCH UNREAD EMAILS TOOL (Numbered Emails)
# ========================

import base64

def summarize_email(email_text: str) -> str:
    """Generate a summary of the email using OCI GenAI."""
    if not email_text.strip():
        return "No summary available."
    prompt = f"Summarize this email in a few sentences: {email_text}"
    try:
        return llm.invoke([prompt]).content
    except Exception as e:
        return f"Error in summarization: {str(e)}"

def fetch_unread_emails(max_results=5):
    """Fetch unread emails and return a summarized list."""
    service = authenticate_gmail()
    try:
        results = service.users().messages().list(
            userId="me", maxResults=max_results, labelIds=["INBOX"], q="is:unread"
        ).execute()
        messages = results.get("messages", [])
    except Exception as e:
        return [{"error": f"Failed to fetch emails: {str(e)}"}]

    email_data = []
    for index, msg in enumerate(messages, start=1):
        try:
            msg_id = msg["id"]
            msg_detail = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
            headers = msg_detail["payload"]["headers"]

            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")
            snippet = msg_detail.get("snippet", "")
            short_summary = summarize_email(snippet)[:300]

            # store msg_id to fetch body later when selected
            email_data.append({
                "index": index,
                "id": msg_id,  # Store msg_id for later use
                "from_email": sender,
                "date": date,
                "summary": short_summary
            })
        except Exception as e:
            email_data.append({"error": f"Failed to process email {msg_id}: {str(e)}"})

    return email_data if email_data else [{"message": "No unread emails found."}]

def handle_fetch_gmail(state: State, max_results=5):
    """Handles fetching and summarizing unread emails with sender, date, and summary."""
    emails = fetch_unread_emails(max_results=max_results)
    state["emails"] = emails
    state["decision"] = "fetch_gmail"

    # show summary, but NOT the full body
    state["output"] = "\n\n".join(
        [
            f"{email['index']}. **From:** {email['from_email']} \n"
            f"   **Date:** {email['date']} \n"
            f"   **Summary:** {email.get('summary', 'No summary available.')}"
            for email in emails
        ]
    )

    return {"output": state["output"], "output_tool": "fetch_gmail"}

# ========================
# 3. SELECT EMAIL TOOL
# ========================

from state import State
from oci_models import create_model_for_routing
import base64

# Initialize the LLM
llm = create_model_for_routing()


def extract_email_index(user_input: str) -> int:
    """Uses LLM to extract the email index from user input."""
    prompt = f"""
    Extract the email number from the following user request:

    Input: "{user_input}"

    Output (only return the number, nothing else):
    """

    try:
        response = llm.invoke([prompt]).content.strip()
        return int(response)
    except Exception as e:
        return f"Error extracting email index: {str(e)}"


def get_email_body(service, msg_id):
    """Retrieve the full email body from Gmail API."""
    try:
        msg_detail = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        payload = msg_detail.get("payload", {})
        parts = payload.get("parts", [])

        if parts:
            for part in parts:
                if part.get("mimeType") == "text/plain":
                    body_data = part.get("body", {}).get("data", "")
                    return base64.urlsafe_b64decode(body_data).decode("utf-8") if body_data else "No body available."
        return "No body available."
    except Exception as e:
        return f"Error retrieving email body: {str(e)}"


def handle_select_email(state: State):
    """Select an email and display the full email body instead of just the subject."""
    if "emails" not in state or not state["emails"]:
        return {"output": "Error: No emails available to select.", "output_tool": "select_email"}

    user_input = state["input"].strip()

    # Step 1: Use LLM to extract the email index
    email_index = extract_email_index(user_input)

    if isinstance(email_index, str) and "Error" in email_index:
        return {"output": email_index, "output_tool": "select_email"}

    email_index -= 1  # Convert to 0-based index

    if 0 <= email_index < len(state["emails"]):
        selected_email = state["emails"][email_index]
        email_id = selected_email["id"]  # Retrieve stored msg_id

        # ✅ Fetch the full email body when selecting an email
        service = authenticate_gmail()
        email_body = get_email_body(service, email_id)

        # ✅ Store the full body in selected_email
        selected_email["body"] = email_body

        state["selected_email"] = selected_email
        state["decision"] = "select_email"

        # Display full body instead of subject
        state["output"] = (
            f"📩 **Selected Email:**\n"
            f"- **From:** {selected_email['from_email']}\n"
            f"- **Date:** {selected_email['date']}\n\n"
            f"📜 **Full Email Body:**\n{email_body}"
        )

        return {"output": state["output"], "output_tool": "select_email"}

    return {"output": "Error: Invalid email index.", "output_tool": "select_email"}

# ========================
# 4. DRAFT REPLY TOOL
# ========================

def generate_reply_with_user_message_and_ai_response(email_text, user_message="", ai_response=""):
    """Generate a reply using both the user message and AI-extracted policy information."""

    prompt = f"""
    You are an AI email assistant. Below is an email received from a user.
    Generate a polite and relevant response using both the user's request and company policy information.

    **Email Received:**
    {email_text}

    **User Request for Reply:**
    {user_message if user_message else "Generate a general reply."}

    **Company Policy Information:**
    {ai_response}

    **Response Guidelines:**
    - Be polite and professional.
    - Address the sender appropriately.
    - Keep the response concise and relevant.
    - Ensure the response aligns with the provided policy information.

    **Generated Reply:**
    """

    return llm.invoke([prompt]).content


def generate_reply_with_user_message_only(email_text, user_message=""):
    """Generate a reply using only the user-provided message (no AI policy data)."""

    prompt = f"""
    You are an AI email assistant. Below is an email received from a user.
    Generate a polite and relevant response based on the user's request.

    **Email Received:**
    {email_text}

    **User Request for Reply:**
    {user_message if user_message else "Generate a general reply."}

    **Response Guidelines:**
    - Be polite and professional.
    - Address the sender appropriately.
    - Keep the response concise and relevant.

    **Generated Reply:**
    """

    return llm.invoke([prompt]).content


def handle_generate_reply_with_user_message_and_ai_response(state: State):
    """Handles generating a reply using both the user message and AI-extracted policy data."""

    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No email selected for reply.",
                "output_tool": "generate_reply_with_user_message_and_ai_response"}

    email_text = state["selected_email"].get("summary", "")
    user_message = state.get("input", "").strip()
    ai_response = state.get("ai_response", "")

    if not email_text:
        return {"output": "Error: No email content available.",
                "output_tool": "generate_reply_with_user_message_and_ai_response"}

    if not ai_response:
        return {"output": "Error: No AI policy data available.",
                "output_tool": "generate_reply_with_user_message_and_ai_response"}

    # generate reply including AI policy data and user message
    reply = generate_reply_with_user_message_and_ai_response(email_text, user_message, ai_response)

    # store the generated reply in state
    state["output"] = reply
    state["decision"] = "generate_reply_with_user_message_and_ai_response"

    return {"output": f" Generated Reply with AI Response and User Query:\n\n{reply}",
            "output_tool": "generate_reply_with_user_message_and_ai_response"}


def handle_generate_reply_with_user_message_only(state: State):
    """Handles generating a reply using only the user message (without AI policy data)."""

    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No email selected for reply.", "output_tool": "generate_reply_with_user_message_only"}

    email_text = state["selected_email"].get("summary", "")
    user_message = state.get("input", "").strip()

    if not email_text:
        return {"output": "Error: No email content available.", "output_tool": "generate_reply_with_user_message_only"}

    # generate reply based on user message only
    reply = generate_reply_with_user_message_only(email_text, user_message)

    # store the generated reply in state
    state["output"] = reply
    state["decision"] = "generate_reply_with_user_message_only"

    return {"output": f"✅ Generated Reply with User Query Only:\n\n{reply}",
            "output_tool": "generate_reply_with_user_message_only"}

# ========================
# 5. SEND EMAIL TOOL
# ========================

def create_email_message(recipient: str, subject: str, body: str) -> str:
    """Creates a properly formatted email message in RFC 2822 format."""
    message = MIMEText(body)
    message["To"] = recipient
    message["Subject"] = subject
    message["MIME-Version"] = "1.0"
    message["Content-Type"] = "text/plain; charset=UTF-8"

    # encode message in base64 as required by Gmail API
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return raw_message


def send_email(recipient: str, subject: str, body: str):
    """Sends an email using Gmail API"""
    service = authenticate_gmail()

    # generate a properly formatted message
    raw_message = create_email_message(recipient, subject, body)

    # send the email using Gmail API
    try:
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return "Email sent successfully"
    except Exception as e:
        return f"Failed to send email: {str(e)}"


def handle_send_email(state: State):
    """Handles sending an email using the Gmail API."""
    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No selected email to reply to.", "output_tool": "send_email"}

    recipient = state["selected_email"]["from_email"]
    subject = f"Re: {state['selected_email'].get('subject', '[No Subject]')}"
    body = state.get("output", "")  # use the previously generated reply

    if not recipient or not body:
        return {"output": "Error: Missing recipient or email body.", "output_tool": "send_email"}

    send_status = send_email(recipient, subject, body)
    state["output"] = send_status
    state["decision"] = "send_email"

    return {"output": send_status, "output_tool": "send_email"}


# ========================
# 6.RAG (AI AGENTS)
# ========================

import logging
import oci
from state import State

# initialize OCI LLM and RAG client
rag_agent_endpoint_id = "ocid1.genaiagentend...."
rag_config = oci.config.from_file()
rag_agent_client = oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
    rag_config,
    service_endpoint="https://agent-runtime.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
)

# employee Data Mapping (Email → Country)
EMPLOYEE_DATA = {
    "omar salem <omar.ksalem02@gmail.com>": "Netherlands",
    "dana@gmail.com": "Poland",
    "mostafa@gmail.com": "Italy"
}

def create_rag_session():
    """Create a RAG session for querying the Oracle RAG agent."""
    try:
        session_details = oci.generative_ai_agent_runtime.models.CreateSessionDetails(
            display_name="RAG Agent Session",
            description="Session for AI agent queries"
        )
        session_response = rag_agent_client.create_session(
            create_session_details=session_details,
            agent_endpoint_id=rag_agent_endpoint_id,
            opc_retry_token="unique-retry-token-123",
            opc_request_id="unique-request-id-123"
        )
        return session_response.data.id
    except Exception as e:
        logging.error(f"Error creating RAG session: {e}")
        return None

# ensure RAG session is initialized
rag_session_id = create_rag_session()
if not rag_session_id:
    logging.error("Failed to initialize RAG session. Exiting.")
    raise SystemExit("RAG session creation failed. Check configuration and credentials.")

def handle_ai_agent_query(state: State):
    """Handles AI-based queries using Oracle RAG with stronger country emphasis."""
    print("🔹 AI Agent Tool Invoked.")

    # extract user query from state
    user_query = state.get("input", "")

    if not user_query:
        return {"output": "Error: No valid query provided.", "output_tool": "ai_agent"}

    # extract selected email details
    selected_email = state.get("selected_email", {})
    email = selected_email.get("from_email", "").strip().lower()

    # match email to country
    country = EMPLOYEE_DATA.get(email, "Unknown")

    # debugging log to check if country is correctly matched
    print(f"🛠️ Extracted Email: {email}")
    print(f"🌍 Matched Country: {country}")

    # stronger Prompt Engineering
    if country != "Unknown":
        user_query = f"""
        You are an AI assistant specializing in labor laws and company policies. 
        The user is asking about policies for employees in {country}. 
        **Please provide information specific to {country}, not general policies.** 

        **User Question:** {user_query}
        """

    print(f"📩 Final AI Query: {user_query}")  # debugging log to verify final query

    try:
        # send the updated user query to the RAG Agent
        chat_details = oci.generative_ai_agent_runtime.models.ChatDetails(
            user_message=user_query,
            should_stream=False,
            session_id=rag_session_id
        )
        chat_response = rag_agent_client.chat(
            agent_endpoint_id=rag_agent_endpoint_id,
            chat_details=chat_details
        )

        # extract the response content
        rag_message = getattr(chat_response.data, "message", None)
        ai_response = "No relevant information found."

        if rag_message:
            # handle structured response: MessageContent object
            if hasattr(rag_message, "content") and isinstance(rag_message.content, oci.generative_ai_agent_runtime.models.MessageContent):
                content_obj = rag_message.content
                ai_response = getattr(content_obj, "text", ai_response)

                # process citations (if available) and remove duplicates
                citations = getattr(content_obj, "citations", [])
                citation_urls = list(set(  # convert to set to remove duplicates, then back to list
                    citation.source_location.url
                    for citation in citations
                    if hasattr(citation, "source_location") and hasattr(citation.source_location, "url")
                ))

                if citation_urls:
                    state["citations"] = citation_urls  # store unique citations
                    ai_response += "\n\nCitations:\n" + "\n".join(citation_urls)

        # store AI-generated response in the state
        state["ai_response"] = ai_response
        state["output"] = ai_response
        state["decision"] = "ai_agent"

        return {"output": ai_response, "output_tool": "ai_agent"}

    except Exception as e:
        error_message = f"Error contacting the RAG agent: {str(e)}"
        state["output"] = error_message
        state["decision"] = "ai_agent"
        return {"output": error_message, "output_tool": "ai_agent"}

# ========================
# 7. Event tool (alarm)
# ========================

import threading
import time
from state import State

def schedule_email_sending(state: State, delay_seconds: int = 300):
    """
    Schedules an email to be sent after a delay.

    :param state: The LangGraph state dictionary containing email details.
    :param delay_seconds: The time in seconds before sending the email (default: 300s = 5 mins).
    """
    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No selected email to reply to.", "output_tool": "event_trigger"}

    recipient = state["selected_email"]["from_email"]
    subject = f"Re: {state['selected_email']['subject']}"
    body = state.get("output", "")

    if not recipient or not body:
        return {"output": "Error: Missing recipient or email body.", "output_tool": "event_trigger"}

    def delayed_send():
        """Executes email sending after the delay."""
        time.sleep(delay_seconds)
        send_status = send_email(recipient, subject, body)
        state["output"] = send_status
        state["decision"] = "send_email"

    # start the delayed email sending in a background thread
    threading.Thread(target=delayed_send, daemon=True).start()

    return {
        "output": f"✅ Email scheduled to be sent in {delay_seconds // 60} minutes.",
        "output_tool": "event_trigger"
    }

def handle_schedule_email(state: State):
    """
    Handles scheduling an email to be sent after a delay.
    """
    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No selected email to schedule.", "output_tool": "schedule_email"}

    recipient = state["selected_email"]["from_email"]
    subject = f"Re: {state['selected_email']['subject']}"
    body = state.get("output", "")

    if not recipient or not body:
        return {"output": "Error: Missing recipient or email body.", "output_tool": "schedule_email"}

    # extract delay from user input (default: 5 minutes)
    delay_seconds = 300  # Default 5 minutes
    user_input = state.get("input", "").lower()

    match = re.search(r"send in (\d+) (seconds|minutes|hours)", user_input)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)

        if unit == "minutes":
            delay_seconds = amount * 60
        elif unit == "hours":
            delay_seconds = amount * 3600
        else:
            delay_seconds = amount  # Seconds

    # call the scheduling function
    schedule_email_sending(state, delay_seconds)

    return {
        "output": f"✅ Email scheduled to be sent in {delay_seconds // 60} minutes.",
        "output_tool": "schedule_email"
    }

# ========================
# 8. Help tool Fallback general llm
# ========================

def handle_llm_query(state: State):
    """
    Handles general queries where the user is asking about an email, how to use the system,
    or greeting the assistant.
    """
    user_input = state.get("input", "").strip()

    # directly respond to greetings
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon"]
    if user_input.lower() in greetings:
        response = (
            "👋 Hi! I'm your AI assistant. I can help you with emails—fetching, summarizing, replying, "
            "and answering policy-related questions. Just ask me what you need!"
        )
        state["output"] = response
        state["decision"] = "llm_query"
        return {"output": response, "output_tool": "llm_query"}

    #if an email is selected, provide context for the query
    selected_email_info = ""
    if "selected_email" in state and state["selected_email"]:
        selected_email_info = (
            f"\n\n📩 **Selected Email:**\n"
            f"- **From:** {state['selected_email'].get('from_email', 'Unknown')}\n"
            f"- **Subject:** {state['selected_email'].get('subject', 'No subject')}\n"
            f"- **Summary:** {state['selected_email'].get('summary', 'No summary available')}"
        )

    # generate assistant response using LLM
    prompt = f"""
    You are an AI assistant helping a user manage emails.
    The user may ask about an email or need guidance on using the assistant.

    **User Request:** "{user_input}" {selected_email_info}

    - If the user refers to an email, provide an answer based on the selected email's details.
    - If the user needs help with the system, explain how it works.

    **Response:**
    """

    try:
        # extract only the text from the LLM response (ensuring JSON format doesn't interfere)
        raw_response = llm.invoke([prompt]).content
        response_text = raw_response.strip()

        # if the response is empty, provide a fallback message
        if not response_text:
            response_text = "I'm here to help! Could you clarify your question?"

        # store response in state
        state["output"] = response_text
        state["decision"] = "llm_query"
        return {"output": response_text, "output_tool": "llm_query"}

    except Exception as e:
        error_message = f"Error processing your query: {str(e)}"
        state["output"] = error_message
        state["decision"] = "llm_query"
        return {"output": error_message, "output_tool": "llm_query"}

# ========================
# 9. WEATHER TOOL
# ========================

from state import State
from oci_models import create_model_for_routing

# Initialize the LLM
llm = create_model_for_routing()

#get weather api free key from website
# Weather API Configuration
WEATHER_API_KEY = "8696cafd..."
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

def extract_city_from_input(user_input: str) -> str:
    """Uses LLM to extract the city name from user input."""
    prompt = f"""
    Extract the city name from the following user request:

    Input: "{user_input}"

    Output (only return the city name, nothing else):
    """

    try:
        response = llm.invoke([prompt]).content.strip()
        return response
    except Exception as e:
        return f"Error extracting city: {str(e)}"


def get_weather(city: str) -> str:
    """Fetches and returns current weather for a given city."""
    try:
        params = {
            "key": WEATHER_API_KEY,  # Weather API key
            "q": city
        }
        response = requests.get(WEATHER_API_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            weather = data["current"]["condition"]["text"].capitalize()
            temp = data["current"]["temp_c"]
            feels_like = data["current"]["feelslike_c"]
            return f"The weather in {city} is {weather}. The temperature is {temp}°C but feels like {feels_like}°C."
        else:
            return f"Could not fetch weather data. API returned status code {response.status_code}."
    except Exception as e:
        return f"Error retrieving weather data: {str(e)}"


def handle_weather_query(state: State):
    """Handles weather queries by extracting the city name and fetching weather data."""
    user_input = state.get("input", "").strip()

    # Step 1: Use LLM to extract the city
    city = extract_city_from_input(user_input)

    if "Error" in city:
        return {"output": city, "output_tool": "weather_query"}

    # Step 2: Fetch weather data
    weather_info = get_weather(city)

    # Store response in state
    state["output"] = weather_info
    state["decision"] = "weather_query"

    return {"output": weather_info, "output_tool": "weather_query"}
# ========================
# 10. CALCULATOR TOOL
# ========================

import ast
import operator

# Initialize the LLM
llm = create_model_for_routing()

# Safe mathematical operators
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod
}

def safe_eval(node):
    """Safely evaluates an arithmetic expression."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, tuple(SAFE_OPERATORS.keys())):
        return SAFE_OPERATORS[type(node.op)](safe_eval(node.left), safe_eval(node.right))
    elif isinstance(node, ast.Num):
        return node.n
    else:
        raise ValueError("Unsupported operation.")


def extract_math_expression(user_input: str) -> str:
    """Uses LLM to extract a clean mathematical expression from user input."""
    prompt = f"""
    Extract only the mathematical expression from this text:

    Input: "{user_input}"

    Output (only return the math expression, nothing else):
    """

    try:
        response = llm.invoke([prompt]).content.strip()
        return response
    except Exception as e:
        return f"Error extracting math expression: {str(e)}"


def evaluate_expression(expression: str) -> str:
    """Evaluates a mathematical expression safely."""
    try:
        node = ast.parse(expression, mode='eval').body
        result = safe_eval(node)
        return f"The result of {expression} is {result}."
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"


def handle_calculator(state: State):
    """Handles calculator queries by extracting and evaluating mathematical expressions."""
    user_input = state.get("input", "").strip()

    # Step 1: Use LLM to extract the math expression
    extracted_expression = extract_math_expression(user_input)

    if "Error" in extracted_expression:
        return {"output": extracted_expression, "output_tool": "calculator"}

    # Step 2: Evaluate the extracted expression
    result = evaluate_expression(extracted_expression)

    # Store response in state
    state["output"] = result
    state["decision"] = "calculator"

    return {"output": result, "output_tool": "calculator"}


# ========================
# 10. Meeting Bookings
# ========================

from dateutil import parser
from datetime import datetime, timedelta
import re
import requests
from state import State

# weather API Configuration
WEATHER_API_KEY = "8696cafd2...."
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"

# mapping of email addresses to default cities (Fallback)
EMPLOYEE_CITY_MAP = {
    "omar salem <omar.ksalem02@gmail.com>": "Amsterdam",
    "dana@gmail.com": "Warsaw",
    "mostafa@gmail.com": "Rome"
}

def extract_meeting_details(email_text: str):
    """Extracts date and time from the email content."""

    # detect YYYY-MM-DD format or natural language date (March 22nd, 2025)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", email_text)  # Detect YYYY-MM-DD
    natural_date_match = re.search(r"([A-Z][a-z]+ \d{1,2}(st|nd|rd|th)?,? \d{4})",
                                   email_text)  # detect "March 22nd, 2025"

    meeting_date = None
    if date_match:
        meeting_date = date_match.group(1)  # extracted YYYY-MM-DD date
    elif natural_date_match:
        try:
            clean_date = re.sub(r"(st|nd|rd|th)", "", natural_date_match.group(1))  # remove suffixes
            parsed_date = parser.parse(clean_date)  # convert to datetime object
            meeting_date = parsed_date.strftime("%Y-%m-%d")  # convert to YYYY-MM-DD format
        except Exception:
            meeting_date = None

    # detect time (12-hour format with AM/PM)
    time_match = re.search(r"(\d{1,2}:\d{2} (AM|PM|am|pm))", email_text)
    meeting_time = time_match.group(1) if time_match else None

    return {
        "date": meeting_date,
        "time": meeting_time
    }

def get_weather_forecast(city: str, date: str) -> str:
    """Fetches weather forecast for a given city and date (supports future dates up to 300 days ahead)."""
    try:
        forecast_date = datetime.strptime(date, '%Y-%m-%d')
        today = datetime.today()
        delta_days = (forecast_date - today).days

        # select appropriate API endpoint
        if 0 <= delta_days <= 14:
            params = {"key": WEATHER_API_KEY, "q": city, "days": delta_days + 1}
            url = WEATHER_API_URL  # standard forecast URL
        elif 14 < delta_days <= 300:
            url = "http://api.weatherapi.com/v1/future.json"  # future weather URL
            params = {"key": WEATHER_API_KEY, "q": city, "dt": date}
        else:
            return f"⚠️ Date {date} is out of the supported range (must be within 300 days)."

        # debugging: print the full API request
        print(f"\n🌍 API Request: {url}")
        print(f"📌 Request Params: {params}\n")

        # make the API request
        response = requests.get(url, params=params)

        if response.status_code == 200:
            data = response.json()
            if 'forecast' in data:
                forecast = data['forecast']['forecastday'][0]
                condition = forecast['day']['condition']['text'].capitalize()
                temp = forecast['day']['avgtemp_c']
                return f"🌤 The forecast for **{city}** on **{date}** is **{condition}** with an average temperature of **{temp}°C**."
            else:
                return f"⚠️ No forecast data available for {date}."
        else:
            return f"❌ API Error: {response.status_code}, Response: {response.text}"

    except Exception as e:
        return f"❌ Error retrieving weather data: {str(e)}"

def get_clothing_advice(weather_condition: str, temperature: float) -> str:
    """Provides clothing advice based on weather conditions and temperature."""
    if temperature == "Unknown":
        return "⚠️ No temperature data available to suggest clothing."

    if temperature < 5:
        return "🥶 It's really cold! Wear a heavy coat, scarf, and gloves."
    elif 5 <= temperature < 12:
        return "🧥 It's chilly! A warm jacket or sweater is recommended."
    elif 12 <= temperature < 18:
        return "👕 A light sweater or hoodie should be fine."
    elif 18 <= temperature < 25:
        return "🌞 Mild weather! A t-shirt and jeans are comfortable."
    else:
        return "🔥 It's hot! Wear light clothes, sunglasses, and stay hydrated!"

def get_weather_forecast_and_advice(city: str, date: str):
    """Fetches weather forecast and provides clothing advice."""
    weather_info = get_weather_forecast(city, date)

    match = re.search(r"(\d+(\.\d+)?)°C", weather_info)
    if match:
        temperature = float(match.group(1))
        condition_match = re.search(r"is \*\*(.*?)\*\* with", weather_info)
        weather_condition = condition_match.group(1) if condition_match else "Unknown"

        clothing_advice = get_clothing_advice(weather_condition, temperature)
        return (f"{weather_info}"
                f" \n \n👗 **Clothing Advice:** {clothing_advice}")

    return f"{weather_info}\n👗 **Clothing Advice:** Unable to determine clothing suggestions."


def create_google_calendar_event(meeting_details, sender_email, timezone="CET"):
    """Creates a Google Calendar event and provides weather-based clothing advice."""
    if not meeting_details["date"] or not meeting_details["time"]:
        return "Error: Missing meeting details."

    city = EMPLOYEE_CITY_MAP.get(sender_email, "Amsterdam")  # get city from sender email

    print(f"📍 City used for weather: {city}")  # debugging

    service = authenticate_google_calendar()

    event_start = datetime.strptime(f"{meeting_details['date']} {meeting_details['time']}", "%Y-%m-%d %I:%M %p")
    event_end = event_start + timedelta(minutes=30)

    event_data = {
        "summary": "Scheduled Meeting",
        "start": {"dateTime": event_start.isoformat(), "timeZone": timezone},
        "end": {"dateTime": event_end.isoformat(), "timeZone": timezone},
    }

    try:
        event = service.events().insert(calendarId="primary", body=event_data).execute()
        meeting_confirmation = (f"✅ Meeting successfully booked for {meeting_details['date']} at {meeting_details['time']} ({timezone}).\n \n"
                                f"📅 Event Link: {event.get('htmlLink')}")

        weather_advice = get_weather_forecast_and_advice(city, meeting_details["date"])
        return f"{meeting_confirmation}\n\n{weather_advice}"

    except Exception as e:
        return f"❌ Failed to book meeting. API Error: {str(e)}"

def handle_book_meeting(state: State):
    """Handles booking a meeting based on the selected email."""

    if "selected_email" not in state or not state["selected_email"]:
        return {"output": "Error: No email selected for booking.", "output_tool": "book_meeting"}

    email_content = state["selected_email"].get("summary", "").strip()
    sender_email = state["selected_email"].get("from_email", "").lower()

    print(f"📩 Sender Email: {sender_email}\n")

    meeting_details = extract_meeting_details(email_content)

    print(f"📅 Extracted Meeting Details: {meeting_details}\n")

    if not meeting_details["date"] or not meeting_details["time"]:
        return {"output": "Error: Could not extract date/time from the email.", "output_tool": "book_meeting"}

    booking_result = create_google_calendar_event(meeting_details, sender_email)

    state["output"] = booking_result
    state["decision"] = "book_meeting"

    return {"output": booking_result, "output_tool": "book_meeting"}

#human in the loop add
#add the llm query for also other stuff