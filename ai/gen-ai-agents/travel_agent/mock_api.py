"""
mock_api.py

A simplified mock FastAPI server with two endpoints:
- /search/transport
- /search/hotels

mock data in mock_data.py
"""

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from mock_data import hotels_by_city, transport_data

app = FastAPI()


@app.get("/search/transport")
def search_transport(
    destination: str = Query(...),
    start_date: str = Query(...),
    transport_type: str = Query(...),
):
    """
    Mock endpoint to simulate transport search from Rome.
    Args:
        destination (str): Destination city.
        start_date (str): Start date of the trip in 'YYYY-MM-DD' format.
        transport_type (str): Type of transport ("airplane" or "train").
    Returns:
        JSONResponse: Mocked transport options.
    """
    key = destination.strip().lower()
    option = transport_data.get(key, {}).get(transport_type.lower())

    if not option:
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
        return JSONResponse(content={"hotels": []}, status_code=404)

    hotel["stars"] = stars
    return JSONResponse(content={"hotels": [hotel]})
