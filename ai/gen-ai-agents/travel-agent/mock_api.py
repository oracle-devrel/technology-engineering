"""
mock_api.py

A simplified mock FastAPI server with two endpoints:
- /search/transport
- /search/hotels

mock data in mock_data.py
"""

import logging
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# added to extend the range of options
from llm_travel_fallback import simulate_transport_with_llm
from llm_hotel_fallback import simulate_hotel_with_llm
from mock_data import hotels_by_city, transport_data
from utils import get_console_logger

app = FastAPI()
logger = get_console_logger("mock_api_logger", level=logging.INFO)


@app.get("/search/transport")
def search_transport(
    place_of_departure: str = Query(...),
    destination: str = Query(...),
    start_date: str = Query(...),
    transport_type: str = Query(...),
):
    """
    Mock endpoint to simulate transport search.
    Args:
        place_of_departure (str): Origin city.
        destination (str): Destination city.
        start_date (str): Date of travel (YYYY-MM-DD).
        transport_type (str): "airplane" or "train".
    Returns:
        JSONResponse: Mocked transport options.
    """
    key = (place_of_departure.strip().lower(), destination.strip().lower())
    option = transport_data.get(key, {}).get(transport_type.lower())

    if not option:
        # Fallback: use LLM to simulate a reasonable transport option
        logger.info("LLM fallback for: %s, type=%s", key, transport_type)
        try:
            simulated = simulate_transport_with_llm(
                place_of_departure, destination, start_date, transport_type
            )
            return JSONResponse(content={"options": [simulated]})
        except Exception as e:
            logger.error("LLM fallback failed: %s", e)
            return JSONResponse(content={"options": []}, status_code=404)

    departure_time = f"{start_date}T08:00"
    duration = option["duration_hours"]
    arrival_hour = 8 + int(duration)
    arrival_time = f"{start_date}T{arrival_hour:02}:00"

    return JSONResponse(
        content={
            "options": [
                {
                    "provider": option["provider"],
                    "price": option["price"],
                    "departure": departure_time,
                    "arrival": arrival_time,
                    "type": transport_type,
                }
            ]
        }
    )


@app.get("/search/hotels")
def search_hotels(
    destination: str = Query(...),
    start_date: str = Query(...),
    num_days: int = Query(1),
    stars: int = Query(3),
):
    """
    Mock endpoint to simulate hotel search.
    Args:
        destination (str): Destination city.
        stars (int): Number of stars for hotel preference.
    Returns:
        JSONResponse: Mocked hotel options.
    """
    hotel_key = destination.strip().lower()
    hotel = hotels_by_city.get(hotel_key)

    if not hotel:
        logger.info("LLM fallback for: %s", destination)

        try:
            hotel = simulate_hotel_with_llm(destination, start_date, num_days, stars)
        except Exception as e:
            logger.error("LLM hotel fallback failed: %s", e)
            return JSONResponse(content={"hotels": []}, status_code=404)
    else:
        hotel["stars"] = stars

    return JSONResponse(content={"hotels": [hotel]})
