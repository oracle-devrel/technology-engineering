Copyright (c) 2025 Oracle and/or its affiliates.
"""
By Omar Salem
assistant.py - AI Assistant Chatbot (Dynamic Routing).
"""

from state import State
from router import Router
from tools import (
    handle_fetch_gmail,
    handle_send_email,
    handle_ai_agent_query,
    handle_select_email,
    handle_schedule_email,
    handle_llm_query,
    handle_weather_query,
    handle_calculator,
    # handle_generate_reply_with_weather,
    handle_generate_reply_with_user_message_and_ai_response,
    handle_generate_reply_with_user_message_only,
    handle_book_meeting
)
import json

# initialize router
router = Router()

# initialize State
state: State = {
    "input": "",
    "decisions": [],
    "output": "",
    "emails": [],
    "selected_email": None,
    "recipient": "",
    "subject": "",
    "body": "",
    "ai_response": "",
    "citations": [],
}

# dynamically map tools
TOOLS = {
    "fetch_and_summarize": handle_fetch_gmail,
    "send_email": handle_send_email,
    "ai_agent": handle_ai_agent_query,
    "select_email": handle_select_email,
    "schedule_email": handle_schedule_email,
    "llm_query": handle_llm_query,
    "weather_query": handle_weather_query,
    "calculator": handle_calculator,
    "generate_reply_with_user_message_only": handle_generate_reply_with_user_message_only,
    "generate_reply_with_user_message_and_ai_response": handle_generate_reply_with_user_message_and_ai_response,
    "book_meeting": handle_book_meeting,
}


def chatbot():
    """Interactive Chatbot for AI Assistant"""
    print("\n **AI Assistant** - Type 'exit' to quit.\n")

    while True:
        # get user input
        user_input = input("📝 You: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            print("\n👋 Exiting. Have a great day!")
            break

        # update State
        state["input"] = user_input

        # dynamic routing assignment
        routing_result = router.route(state)
        state["decisions"] = routing_result.get("decisions", [])

        print(f"\n🤖 **Routing Decisions:** `{state['decisions']}`\n")

        # store responses from multiple tools
        responses = []

        #dynamically execute tools
        for decision in state["decisions"]:
            tool = TOOLS.get(decision)
            if tool:
                result = tool(state)  # execute tool picked dynamically
                responses.append(result["output"])
            else:
                responses.append(f"❌ Invalid decision: `{decision}`.")

        # convert lists to formatted JSON strings before joining
        state["output"] = "\n\n".join(
            [json.dumps(resp, indent=2) if isinstance(resp, list) else str(resp) for resp in responses]
        )

        # display Output
        print(f"\n✅ **Response:**\n{state['output']}\n")


# run the Chatbot
if __name__ == "__main__":
    chatbot()
