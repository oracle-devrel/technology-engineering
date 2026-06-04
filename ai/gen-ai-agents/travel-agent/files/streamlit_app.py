"""
Streamlit UI for the prototype
"""

import uuid
import asyncio
import pydeck as pdk
import streamlit as st
from run_agent import run_agent
from translations import TRANSLATIONS
from utils import get_console_logger
from config import DEBUG, MAP_STYLE, SUPPORTED_LANGUAGES, SUPPORTED_LANGUAGES_LONG

logger = get_console_logger("streamlit_app")


def visualize_hotel_on_map(_session_state):
    """
    Display the position of the hotel on a map using pydeck.
    """
    if hasattr(_session_state, "hotel_options") and _session_state.hotel_options:
        # get Hotel location
        hotel = _session_state.hotel_options[0]

        if hotel:
            lat = hotel.get("latitude")
            lon = hotel.get("longitude")

            if lat and lon:
                # the size of the circle in pixels
                RADIUS = 60

                layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=[{"position": [lon, lat]}],
                    get_position="position",
                    get_radius=RADIUS,
                    get_fill_color=[255, 0, 0],
                    pickable=True,
                )

                view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=14)

                st.pydeck_chart(
                    pdk.Deck(
                        layers=[layer],
                        initial_view_state=view_state,
                        map_style=MAP_STYLE,
                    )
                )


st.set_page_config(page_title="AI Travel Planner", layout="centered")

if "language" not in st.session_state:
    st.session_state.language = "EN"  # Default language

# --- Sidebar for language selection ---
with st.sidebar:
    lang_code = st.selectbox(
        "🌍 Language",
        options=SUPPORTED_LANGUAGES,
        index=SUPPORTED_LANGUAGES.index(st.session_state.language),
        format_func=lambda code: SUPPORTED_LANGUAGES_LONG.get(code, code),
    )
    st.session_state.language = lang_code

# get the translations for the selected language
t = TRANSLATIONS[st.session_state.language]

st.title(t["title"])

# --- Initialize session state ---
if "conversation" not in st.session_state:
    # stores (speaker, message)
    st.session_state.conversation = []
if "clarification_mode" not in st.session_state:
    st.session_state.clarification_mode = False
if "last_input" not in st.session_state:
    st.session_state.last_input = ""

# --- User input box ---
user_input = st.text_area(
    label=t["input_label"],
    height=200,
    placeholder=t["input_placeholder"],
)
# to have the buttons below the text area on the same line
col1, col2 = st.columns([1, 1])

with col1:
    if st.button(t["send"]) and user_input.strip():
        # Combine clarification with last input
        if st.session_state.clarification_mode:
            combined_input = st.session_state.last_input + " " + user_input
        else:
            combined_input = user_input

        st.session_state.conversation.append(("user", user_input))
        st.session_state.last_input = combined_input

        # Run the agent
        with st.spinner(t["spinner"]):
            # language is injected through the config
            REQUEST_ID = str(uuid.uuid4())
            my_config = {
                "configurable": {
                    "language": st.session_state.language,
                    "thread_id": REQUEST_ID,
                }
            }

            logger.info("Running agent with request ID: %s", REQUEST_ID)

            result = asyncio.run(run_agent(combined_input, config=my_config))

            if DEBUG:
                logger.info("Final result from agent:")
                logger.info(result)

            # this is not streaming
            AGENT_MSG = ""
            if result:
                AGENT_MSG = result.get("final_plan", "") + result.get("itinerary", "")
            st.session_state.conversation.append(("agent", AGENT_MSG))
            st.session_state.hotel_options = result["hotel_options"]
            st.session_state.clarification_mode = result.get(
                "clarification_needed", False
            )


with col2:
    if st.button(t["clear"]):
        st.session_state.conversation = []
        st.session_state.clarification_mode = False
        st.session_state.last_input = ""
        st.rerun()

# --- Display only last two messages ---
if len(st.session_state.conversation) >= 2:
    last_user_msg = st.session_state.conversation[-2]
    last_agent_msg = st.session_state.conversation[-1]

    if last_user_msg[0] == "user":
        st.markdown(f"**🧑 {t['user']}:** {last_user_msg[1]}")
    if last_agent_msg[0] == "agent":
        st.markdown(f"**🤖 {t['planner']}:**")
        st.markdown(last_agent_msg[1])

        # Visualize Hotel on map if available
        visualize_hotel_on_map(st.session_state)
