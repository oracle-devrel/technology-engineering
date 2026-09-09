"""
Simulate hotel options using an LLM.
This script uses an LLM to generate realistic hotel options
"""

from model_factory import get_chat_model
from utils import extract_json_from_text
from config import SERVICE_ENDPOINT, MODEL_ID


def simulate_hotel_with_llm(destination, start_date, num_days, stars):
    """
    Simulate a hotel option using an LLM.
    Args:
        destination (str): Destination city.
        start_date (str): Start date of the stay in YYYY-MM-DD format.
        num_days (int): Number of nights to stay.
        stars (int): Star rating of the hotel (1-5).
    Returns:
        dict: A dictionary containing the hotel option details.
        - name (str): Name of the hotel.
        - price (float): Price per night in EUR.
        - stars (int): Star rating of the hotel.
        - location (str): Location description.
        - amenities (list): List of amenities available at the hotel.
        - latitude (float): Approximate latitude of the hotel.
        - longitude (float): Approximate longitude of the hotel.
    """
    prompt = f"""
Simulate a realistic hotel option in {destination} starting on {start_date} for {num_days} nights.
The hotel should be rated {stars} stars.

Return a JSON object with the following fields:
- name
- price (EUR per night)
- stars
- location
- amenities (list of 2-3 amenities)
- latitude (approximate)
- longitude (approximate)
JSON must be enclosed in triple backticks

Return a **JSON object** with the following format:
```json
{{
  "name": "Hotel Example",
  "price": 150.0,
  "stars": 4,
  "location": "City Center",
  "amenities": ["WiFi", "Breakfast", "Gym"],
  "latitude": 40.7128,
  "longitude": -74.0060
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

    return data
