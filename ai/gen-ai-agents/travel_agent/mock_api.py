"""
mock_api.py

A simplified mock FastAPI server with two endpoints:
- /search/transport
- /search/hotels
"""

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI()


@app.get("/search/transport")
def search_transport(
    destination: str = Query(...),
    start_date: str = Query(...),
    transport_type: str = Query(...),
):
    """
    Mock endpoint to simulate transport search.
    Args:
        destination (str): Destination city.
        start_date (str): Start date of the trip in 'YYYY-MM-DD' format.
        transport_type (str): Type of transport (e.g., "airplane", "train").
    Returns:
        JSONResponse: Mocked transport options.
    """
    return JSONResponse(
        content={
            "options": [
                {
                    "provider": (
                        "TrainItalia" if transport_type == "train" else "Ryanair"
                    ),
                    "price": 45.50,
                    "departure": f"{start_date}T09:00",
                    "arrival": f"{start_date}T13:00",
                    "type": transport_type,
                }
            ]
        }
    )


@app.get("/search/hotels")
def search_hotels(destination: str = Query(...), stars: int = Query(3)):
    """
    Mock endpoint to simulate hotel search.
    Args:
        destination (str): Destination city.
        stars (int): Number of stars for hotel preference.
    Returns:
        JSONResponse: Mocked hotel options.
    """
    hotels_by_city = {
        "valencia": {
            "name": "Hotel Vincci Lys",
            "price": 135.0,
            "stars": stars,
            "location": "Central district",
            "amenities": ["WiFi", "Breakfast"],
            "latitude": 39.4702,
            "longitude": -0.3750,
        },
        "barcelona": {
            "name": "Hotel Jazz",
            "price": 160.0,
            "stars": stars,
            "location": "Eixample",
            "amenities": ["WiFi", "Rooftop pool"],
            "latitude": 41.3849,
            "longitude": 2.1675,
        },
        "madrid": {
            "name": "Only YOU Hotel Atocha",
            "price": 170.0,
            "stars": stars,
            "location": "Retiro",
            "amenities": ["WiFi", "Gym", "Restaurant"],
            "latitude": 40.4093,
            "longitude": -3.6828,
        },
        "florence": {
            "name": "Hotel L'Orologio Firenze",
            "price": 185.0,
            "stars": stars,
            "location": "Santa Maria Novella",
            "amenities": ["WiFi", "Spa", "Bar"],
            "latitude": 43.7760,
            "longitude": 11.2486,
        },
        "amsterdam": {
            "name": "INK Hotel Amsterdam",
            "price": 190.0,
            "stars": stars,
            "location": "City Center",
            "amenities": ["WiFi", "Breakfast", "Bar"],
            "latitude": 52.3745,
            "longitude": 4.8901,
        },
    }

    hotel_key = destination.strip().lower()
    hotel = hotels_by_city.get(hotel_key)

    if not hotel:
        return JSONResponse(content={"hotels": []}, status_code=404)

    return JSONResponse(content={"hotels": [hotel]})
