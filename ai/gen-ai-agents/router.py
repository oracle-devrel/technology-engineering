"""
By Omar Salem
router.py - Routes requests to the correct tools.
"""

import json
from langchain_core.messages import HumanMessage
from oci_models import create_model_for_routing

# define all possible actions
STEP_OPTIONS = [
    "fetch_and_summarize",  # Fetch unread emails (1)
    "select_email",         # Select a specific email (2)
    "generate_reply_with_weather",  # Generate reply including weather (3a)
    "generate_reply_with_user_message_and_ai_response",  # Generate reply using HR policy (3b)
    "generate_reply_with_user_message_only",  # Generate reply using only user message (3c)
    "send_email",           # Send an email (5)
    "schedule_email",       # Schedule an email to be sent later (6)
    "ai_agent",             # Handle specific document-based policy queries (7)
    "llm_query",            # Handle general user queries (8)
    "weather_query",        # Fetch real-time weather information (9)
    "calculator",           # Evaluate mathematical expressions (10)
    "book_meeting"          # Books meetings
]

ROUTER_PROMPT_TEMPLATE = """
You are an AI assistant managing Gmail tasks, AI queries, weather updates, and a calculator.
Identify **all applicable actions** based on the user request.

### **Options:**
📩 **Gmail Tasks**
- **fetch_and_summarize** → If the user wants to **read all unread emails**.
- **select_email** → If the user wants to **read a specific email**, such as "Show me email 3".

✉️ **Generating Email Replies**
- **generate_reply_with_user_message_and_ai_response** → If the user wants an **AI-suggested email reply** using HR policy.
- **generate_reply_with_user_message_only** → If the user wants a **reply using only their message** (without HR policy).
- **send_email** → If the user wants to **send an email immediately**.
- **schedule_email** → If the user wants to **send an email later** (e.g., "Send in 5 minutes").

📅 **Calendar & Meeting Scheduling**
- **book_meeting** → If the user wants to **schedule a meeting** via Google Calendar (e.g., "Book a meeting for tomorrow at 3 PM with Alice and Bob").

📑 **AI Knowledge & Document Queries**
- **ai_agent** → If the user asks about a **policy that requires referencing** (e.g., "How many vacation days do I get?").
- **llm_query** → If the user asks a **general question**, such as:
  - Saying **Hi**.
  - **Translating** an email.+
  - **Explaining** an email.
  - Asking how to **use the assistant**.
  - **General explanations like who is lionel messi, where is china etc**.

🌦️ **Weather Queries**
- **weather_query** → If the user asks for the **weather in a city** (e.g., "What's the weather in London?").

🧮 **Calculator**
- **calculator** → If the user asks to **solve a math expression** (e.g., "Calculate 5 + 3 * 2").

---
### **User Request:**
"{query}"

Return ALL necessary actions in **JSON format** in order of execution:
{{"steps": ["fetch_and_summarize", "schedule_email"]}}
"""



class Router:
    """Routes user requests to multiple tools if needed"""

    def __init__(self):
        self.llm_router = create_model_for_routing()

    def route(self, state):
        """Routes the input query to one or more tools."""
        prompt = ROUTER_PROMPT_TEMPLATE.format(query=state["input"])

        try:
            response = self.llm_router.invoke([HumanMessage(content=prompt)])

            # extract content from AIMessage
            raw_content = response.content
            print(f"Raw LLM Response: {raw_content}")  # Debugging print

            # ensure the response is valid JSON
            decision = json.loads(raw_content)

            # validate that "steps" is present and contains valid actions
            if "steps" not in decision or not isinstance(decision["steps"], list):
                raise KeyError(f"Invalid step format returned: {decision}")

            # filter out invalid steps
            valid_steps = [step for step in decision["steps"] if step in STEP_OPTIONS]

            return {"decisions": valid_steps}  # now returns a list of actions

        except json.JSONDecodeError:
            print(f"Router Error: Model response is not valid JSON: {raw_content}")
            return {"decisions": ["fetch_and_summarize"]}  # default fallback

        except Exception as e:
            print(f"Router Error: {e}")
            return {"decisions": ["fetch_and_summarize"]}  # default fallback

