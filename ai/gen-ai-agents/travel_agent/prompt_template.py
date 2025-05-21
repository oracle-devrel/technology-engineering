"""
Prompt templates for managing user input

These prompts don't need to be translated,
as they are used internally by the LangGraph workflow.
"""

from langchain_core.prompts import PromptTemplate

#
# Prompt template for extracting structured travel details from user input
#
input_parser_prompt = PromptTemplate.from_template(
    """
Today's date is: **{today}**

Extract structured travel details from the following user input. 

Return only a JSON, enclosed in triple backticks, with the keys:
- place_of_departure (str)
- destination (str)
- start_date (YYYY-MM-DD)
- end_date (YYYY-MM-DD)
- num_days (int)
- num_persons (int)
- transport_type (e.g., "airplane", "train", "other")
- hotel_preferences (dictionary with keys like "stars", "location", "amenities")

If some information is not clear, use null for the value.

## **User input:**
{user_input}

### **Output Format:**
Return a **JSON object** with the following format:
```json
{{
  "place_of_departure": "Rome",
  "destination": "Barcelona",
  "start_date": null,
  "end_date": null,
  "num_days": null,
  "num_persons": null,
  "transport_type": "train",
  "hotel_preferences": {{
    "stars": 4,
    "location": "central",
    "amenities": null
  }}
}}
```

Return:
"""
)

#
# Prompt template for classifying user intent (Routing)
#
router_prompt = PromptTemplate.from_template(
    """You are an intent classifier for a travel assistant.

    Classify the user request as either:
    - "booking": when the user wants to plan or book a trip
    - "info": when the user wants general travel information

    Return only "booking" or "info".

    User input:
    {user_input}
    """
)

#
# Prompt template for generating travel information
#
answer_prompt = PromptTemplate.from_template(
    """You are a helpful travel assistant.

    Based on the user question below, provide clear and useful travel information.

    Respond in markdown format (with bullet points or sections if needed).

    User question:
    {user_input}
    """
)
