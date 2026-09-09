"""
UI Stramlit for streaming API
"""

# streamlit_client_tabs.py
import asyncio
import json
import streamlit as st
import httpx
from utils import get_console_logger
from config import AGENT_API_URL

logger = get_console_logger("streamlit_client_tabs_logger", level="INFO")

st.set_page_config(page_title="🧳 Travel Planner - Client with Tabs", layout="centered")
st.title("🌍 Travel Planner Streaming Client")

user_input = st.text_area(
    "Insert the details for your travel",
    placeholder="Esempio: Voglio andare a Madrid dal 10 al 15 luglio con mia moglie, in aereo...",
    height=200,
)

# Tabs containers
state_tab, transport_tab, hotel_tab, plan_tab, itinerary_tab = st.tabs(
    ["🔁 State", "✈️ Transport", "🏨 Hotel", "📋 Final plan", "✈️🏨Itinerary"]
)

if st.button("Send request"):
    if user_input.strip() == "":
        st.warning("Insert a valid message.")
    else:
        with st.spinner("⌛ Planning..."):
            # Containers dinamici per aggiornamento live
            state_placeholder = state_tab.empty()
            transport_placeholder = transport_tab.empty()
            hotel_placeholder = hotel_tab.empty()
            plan_placeholder = plan_tab.empty()
            itineray_palaceholder = itinerary_tab.empty()

            async def fetch_stream():
                """
                Fetch the streaming response from the agent API and update the UI dynamically.
                """
                transport_data = []
                hotel_data = []
                generic_state = {}
                plan_data = []
                itinerary_data = []

                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream(
                        "GET", AGENT_API_URL, params={"user_input": user_input}
                    ) as response:
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    data = json.loads(line)

                                    # Update local containers
                                    if "search_transport" in data.keys():
                                        logger.info("Update transport...")
                                        transport_data.append(data)
                                        transport_placeholder.json(transport_data)

                                    elif "search_hotel" in data.keys():
                                        logger.info("Update hotel...")
                                        hotel_data.append(data)
                                        hotel_placeholder.json(hotel_data)

                                    elif "synthesize_plan" in data.keys():
                                        logger.info("Update plan...")
                                        plan_data.append(data)
                                        plan_placeholder.json(plan_data)
                                    elif "generate_itinerary" in data.keys():
                                        logger.info("Update itinerary...")
                                        itinerary_data.append(data)
                                        itineray_palaceholder.json(itinerary_data)
                                    else:
                                        logger.info("Update generic state...")
                                        generic_state.update(data)
                                        state_placeholder.json(generic_state)

                                except json.JSONDecodeError:
                                    st.error(f"⚠️ Error in JSON parsing: {line}")

            asyncio.run(fetch_stream())
