"""
This file contains all the translations for the OCI AI Travel Planner application.
The translations are stored in a dictionary format, where each key is a language code
(e.g., "EN" for English, "IT" for Italian) and the value is another dictionary containing
the translated strings for that language.

clarification_keywords: Keywords that indicate a need for clarification in user input.
clarification_prompt_template: Template for generating a clarification prompt
based on missing fields.
"""

TRANSLATIONS = {
    "EN": {
        "title": "✈️ OCI AI Travel Planner",
        "input_label": "Tell me about your trip (or respond to clarification):",
        "input_placeholder": """I want to go to Valencia from June 12 to June 18 with my girlfriend.
        I want to leave from Rome.
        Prefer train and a central hotel.""",
        "send": "Send",
        "clear": "🧹 Clear",
        "user": "User",
        "planner": "Planner",
        "spinner": "Processing...",
        "clarification_keywords": [
            "missing",
            "please provide",
            "provide",
            "clarification",
        ],
        "clarification_prompt_template": (
            "The following fields are missing from the user's message: {fields}. "
            "Please formulate a polite question to request this information."
        ),
        "itinerary_prompt_template": (
            "You are a travel assistant. Create a {num_days}-day travel itinerary "
            "for a trip to {destination}, "
            "staying at {hotel} in a {location} area. Suggest realistic, "
            "enjoyable activities for each day."
        ),
        "suggested_itinerary_title": "### 🗓️ Suggested Itinerary",
    },
    "IT": {
        "title": "✈️ OCI AI Travel Planner",
        "input_label": "Parlami del tuo viaggio (o rispondi alla richiesta di chiarimento):",
        "input_placeholder": """Voglio andare a Valencia dal 12 al 18 giugno con la mia ragazza.
        Voglio partire da Roma.
        Preferisco il treno e un hotel centrale.""",
        "send": "Invia",
        "clear": "🧹 Cancella",
        "user": "Utente",
        "planner": "Assistente",
        "spinner": "Sto elaborando...",
        "clarification_keywords": [
            "manca",
            "per favore fornisci",
            "inserisci",
            "richiesta di chiarimento",
        ],
        "clarification_prompt_template": (
            "Nel messaggio dell'utente mancano le seguenti informazioni: {fields}. "
            "Formula una domanda per richiedere questi dettagli."
        ),
        "itinerary_prompt_template": (
            "Sei un assistente di viaggio. Crea un itinerario di {num_days} giorni "
            "a {destination}, "
            "con soggiorno presso {hotel} in una zona {location}. "
            "Suggerisci attività piacevoli e realistiche per ogni giorno."
        ),
        "suggested_itinerary_title": "### 🗓️ Itinerario Consigliato",
    },
}
