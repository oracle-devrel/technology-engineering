"""
Mock data for API
"""

# Hotel data by city
hotels_by_city = {
    "valencia": {
        "name": "Hotel Vincci Lys",
        "price": 135.0,
        "stars": None,  # placeholder, updated dynamically
        "location": "Central district",
        "amenities": ["WiFi", "Breakfast"],
        "latitude": 39.4702,
        "longitude": -0.3750,
    },
    "barcelona": {
        "name": "Hotel Jazz",
        "price": 160.0,
        "stars": None,
        "location": "Eixample",
        "amenities": ["WiFi", "Rooftop pool"],
        "latitude": 41.3849,
        "longitude": 2.1675,
    },
    "madrid": {
        "name": "Only YOU Hotel Atocha",
        "price": 170.0,
        "stars": None,
        "location": "Retiro",
        "amenities": ["WiFi", "Gym", "Restaurant"],
        "latitude": 40.4093,
        "longitude": -3.6828,
    },
    "florence": {
        "name": "Hotel L'Orologio Firenze",
        "price": 185.0,
        "stars": None,
        "location": "Santa Maria Novella",
        "amenities": ["WiFi", "Spa", "Bar"],
        "latitude": 43.7760,
        "longitude": 11.2486,
    },
    "amsterdam": {
        "name": "INK Hotel Amsterdam",
        "price": 190.0,
        "stars": None,
        "location": "City Center",
        "amenities": ["WiFi", "Breakfast", "Bar"],
        "latitude": 52.3745,
        "longitude": 4.8901,
    },
}

# Transport data from Rome to Rome and other cities
transport_data = {
    ("rome", "valencia"): {
        "train": {"provider": "TrainItalia", "duration_hours": 15, "price": 110.0},
        "airplane": {"provider": "Ryanair", "duration_hours": 2.5, "price": 140.0},
    },
    ("valencia", "rome"): {
        "train": {"provider": "TrainItalia", "duration_hours": 15, "price": 110.0},
        "airplane": {"provider": "Ryanair", "duration_hours": 2.5, "price": 140.0},
    },
    ("rome", "barcelona"): {
        "train": {"provider": "TrainItalia", "duration_hours": 13, "price": 100.0},
        "airplane": {"provider": "Vueling", "duration_hours": 2.0, "price": 130.0},
    },
    ("barcelona", "rome"): {
        "train": {"provider": "TrainItalia", "duration_hours": 13, "price": 100.0},
        "airplane": {"provider": "Vueling", "duration_hours": 2.0, "price": 130.0},
    },
    ("rome", "madrid"): {
        "train": {"provider": "TrainItalia", "duration_hours": 17, "price": 120.0},
        "airplane": {"provider": "Iberia", "duration_hours": 2.5, "price": 145.0},
    },
    ("madrid", "rome"): {
        "train": {"provider": "TrainItalia", "duration_hours": 17, "price": 120.0},
        "airplane": {"provider": "Iberia", "duration_hours": 2.5, "price": 145.0},
    },
    ("rome", "amsterdam"): {
        "train": {"provider": "Thalys", "duration_hours": 20, "price": 130.0},
        "airplane": {"provider": "KLM", "duration_hours": 2.5, "price": 160.0},
    },
    ("amsterdam", "rome"): {
        "train": {"provider": "Thalys", "duration_hours": 20, "price": 130.0},
        "airplane": {"provider": "KLM", "duration_hours": 2.5, "price": 160.0},
    },
    ("rome", "florence"): {
        "train": {"provider": "Frecciarossa", "duration_hours": 1.5, "price": 35.0},
        "airplane": {"provider": "ITA Airways", "duration_hours": 1.0, "price": 80.0},
    },
    ("florence", "rome"): {
        "train": {"provider": "Frecciarossa", "duration_hours": 1.5, "price": 35.0},
        "airplane": {"provider": "ITA Airways", "duration_hours": 1.0, "price": 80.0},
    },
}
