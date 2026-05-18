"""
Simulate transport options using an LLM.
"""

from model_factory import get_chat_model
from utils import extract_json_from_text
from config import SERVICE_ENDPOINT, MODEL_ID


def simulate_transport_with_llm(departure, destination, date, mode):
    """
    Simulate a transport option using an LLM.
    Args:
        departure (str): Place of departure.
        destination (str): Destination place.
        date (str): Date of travel in YYYY-MM-DD format.
        mode (str): Mode of transport (e.g., "airplane", "train").
    Returns:
        dict: A dictionary containing the transport option details.
        - provider (str): Name of the transport provider.
        - price (float): Price in EUR.
        - duration_hours (float): Duration of the trip in hours.
    """
    prompt = f"""
Simulate a realistic {mode} travel option between {departure} and {destination} for the date {date}.
Return JSON with the fields: provider, price (EUR), duration_hours.
JSON must be enclosed in triple backticks.

Return a **JSON object** with the following format:
```json
Example:
{{
  "provider": "Lufthansa",
  "price": 155.0,
  "departure": "2025-10-10T08:00",
  "duration_hours": 2.5
}}
```
"""

    llm = get_chat_model(
        model_id=MODEL_ID,
        service_endpoint=SERVICE_ENDPOINT,
        temperature=0.2,
        max_tokens=1000,
    )

    response = llm.invoke(prompt).content

    data = extract_json_from_text(response)

    # transform in the expected output format
    return {
        "provider": data["provider"],
        "price": data["price"],
        "departure": f"{date}T08:00",
        "arrival": f"{date}T{int(8 + data['duration_hours']):02}:00",
        "type": mode,
    }
