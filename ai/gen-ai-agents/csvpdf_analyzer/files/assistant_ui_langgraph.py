"""
File name: assistant_ui.py
Author: Luigi Saetta & Omar Salem
Date last modified: 2025-04-18
Python Version: 3.11

Usage:
    streamlit run assistant_ui.py

License:
    This code is released under the MIT License.

Notes:
    This is part of a series of demos developed using OCI GenAI and LangChain.

Warnings:
    This module is in development, may change in future versions.
"""

from typing import List, Union
import time
import streamlit as st
import pandas as pd
import tempfile
from langchain_core.messages import HumanMessage, AIMessage

# for APM integration
# from py_zipkin.zipkin import zipkin_span
# from py_zipkin import Encoding

from csv_analyzer_agent import State, MultiAgent
from utils import get_console_logger
from config import DEBUG

# Constants
AGENT_NAME = "AI_DATA_ANALYZER"

# User and assistant roles
USER = "user"
ASSISTANT = "assistant"

logger = get_console_logger()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "df" not in st.session_state:
    st.session_state.df = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "extracted_information" not in st.session_state:
    st.session_state.extracted_information = None
if "agent" not in st.session_state:
    # Initialize the multi-agent system
    st.session_state.agent = MultiAgent()

def display_msg_on_rerun(chat_hist: List[Union[HumanMessage, AIMessage]]) -> None:
    """Display all messages on rerun."""
    for msg in chat_hist:
        role = USER if isinstance(msg, HumanMessage) else ASSISTANT
        with st.chat_message(role):
            st.markdown(msg.content)

def reset_conversation():
    st.session_state.chat_history = []

def add_to_chat_history(msg):
    st.session_state.chat_history.append(msg)

def get_chat_history():
    return st.session_state.chat_history

def display_extracted_data():
    if st.session_state.extracted_information:
        st.sidebar.subheader("📄 Extracted PDF Information")
        extracted = st.session_state.extracted_information.data
        for key, value in extracted.items():
            label = f"**{key.replace('_', ' ').title()}:**"
            if isinstance(value, (dict, list)):
                st.sidebar.markdown(label)
                st.sidebar.json(value)
            else:
                st.sidebar.markdown(f"{label} {value}")

st.title("AI Data Analyzer")

if st.sidebar.button("Clear Chat History"):
    reset_conversation()

st.sidebar.header("Options")

model_id = st.sidebar.selectbox("Select the Chat Model", ["meta.llama3.3-70B"])

# Upload CSV
uploaded_file = st.sidebar.file_uploader("Load a CSV file", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        st.session_state.df = df
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error reading the CSV file: {e}")
else:
    st.session_state.df = None

# Upload PDF
uploaded_pdf = st.sidebar.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_pdf:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(uploaded_pdf.getvalue())
            temp_pdf_path = temp_pdf.name

        st.session_state.pdf_path = temp_pdf_path
        st.session_state.extracted_information = None

        pdf_state = State(
            user_request="",
            pdf_path=temp_pdf_path,
            extracted_information=None,
            input_df=st.session_state.df,
            chat_history=st.session_state.chat_history,
            previous_error=None,
            error=None,
        )

        extracted_info = st.session_state.agent.process_pdf_node(pdf_state)

        if extracted_info["extracted_information"]:
            st.session_state.extracted_information = extracted_info["extracted_information"]
            st.toast("✅ PDF Processed Successfully!")
        else:
            st.error("⚠️ Failed to extract information from PDF.")

    except Exception as e:
        st.error(f"Error during PDF processing: {e}")
else:
    st.session_state.extracted_information = None
    st.session_state.pdf_path = None

# DISPLAY PDF INFO in sidebar always if available
display_extracted_data()

#DISPLAY CHAT HISTORY
display_msg_on_rerun(get_chat_history())

#
# Chat Input Handling
#
if question := st.chat_input("Hello, how can I help you?"):
    st.chat_message(USER).markdown(question)
    add_to_chat_history(HumanMessage(content=question))  # ✅ Store user message

    try:
        with st.spinner("Calling AI..."):
            time_start = time.time()

            app = st.session_state.agent.create_workflow()

            state = State(
                user_request=question,
                input_df=st.session_state.df,
                extracted_information=st.session_state.extracted_information or {},
                pdf_path=st.session_state.pdf_path,
                chat_history=st.session_state.chat_history.copy(),
                error=None,
                previous_error=None,
            )

            results = []
            error = None
            #uncomment to use zipkin however makes it slower.
            # with zipkin_span(
            #     service_name=AGENT_NAME,
            #     span_name="call",
            #     transport_handler=http_transport,
            #     encoding=Encoding.V2_JSON,
            #     sample_rate=100,
            # ):

            for event in app.stream(state):
                for key, value in event.items():
                    logger.info(f"Completed: {key}")
                    st.toast(f"Completed: {key}")
                    results.append(value)
                    error = value.get("error")

                    if key == "CodeGenerator" and error is None:
                        st.sidebar.header("Generated Code:")
                        st.sidebar.code(value["code_generated"], language="python")

            if error is None:
                final_result = results[-1]["final_output"]
                if isinstance(final_result, pd.DataFrame):
                    st.dataframe(final_result)
                    if DEBUG:
                        logger.info(final_result.head(10))
                else:
                    with st.chat_message(ASSISTANT):
                        st.markdown(final_result)
                    add_to_chat_history(AIMessage(content=final_result))  # Store AI response

            else:
                st.error(error)

            elapsed_time = round((time.time() - time_start), 1)
            logger.info(f"Elapsed time: {elapsed_time} sec.")

    except Exception as e:
        logger.error(f"Error occurred: {e}")
        st.error(f"An error occurred: {e}")