# Copyright (c) 2025 Oracle and/or its affiliates.
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="HR Chatbots", layout="centered")

# st.title("HR Chatbots Demo")

# st.markdown("""
# Welcome to the HR Chatbots Demo. Use the sidebar to select one of the chatbot assistants:
# - **Goal Alignment Chatbot** Align your goals with your manager and your peers.
# - **Self-Assessment Chatbot** Prepare for your quarterly evaluation.
# - **Manager Meeting Preparation Chatbot** Prepare for your upcoming 1:1 meetings.
# - **Course Recommendation Chatbot** Choose the best course to pursue.

# Use the sidebar to begin.
# """)

pages = {
    "Organization": [
        st.Page(str(Path("org_chart.py")), title="Org Chart Visualizer"),
    ],
    "Employee": [
        st.Page(str(Path("pages") / "course_recommendation_chatbot.py")),
        st.Page(str(Path("pages") / "goal_alignment_chatbot.py")),
        st.Page(str(Path("pages") / "manager_meeting_chatbot.py")),
        st.Page(str(Path("pages") / "self_assessment_chatbot.py")),
    ],
}


pg = st.navigation(pages)
pg.run()
