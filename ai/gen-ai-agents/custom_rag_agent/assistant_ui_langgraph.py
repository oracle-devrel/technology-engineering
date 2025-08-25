"""
File name: assistant_ui.py
Author: Luigi Saetta
Date created: 2024-12-04
Date last modified: 2025-07-01
Python Version: 3.11

Description:
    This module provides the UI for the RAG demo

Usage:
    streamlit run assistant_ui_langgraph.py

License:
    This code is released under the MIT License.

Notes:
    This is part of a  demo for a RAG solution implemented
    using LangGraph

Warnings:
    This module is in development, may change in future versions.
"""

import uuid
from typing import List, Union
import time
import streamlit as st

from langchain_core.messages import HumanMessage, AIMessage

# for APM integration
from py_zipkin.zipkin import zipkin_span
from py_zipkin import Encoding

from rag_agent import State, create_workflow
from rag_feedback import RagFeedback
from transport import http_transport
from utils import get_console_logger

# changed to better manage ENABLE_TRACING (can be enabled from UI)
import config

# Constant

# name for the roles
USER = "user"
ASSISTANT = "assistant"

logger = get_console_logger()


# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "workflow" not in st.session_state:
    # the agent instance
    st.session_state.workflow = create_workflow()
if "thread_id" not in st.session_state:
    # generate a new thread_Id
    st.session_state.thread_id = str(uuid.uuid4())
if "model_id" not in st.session_state:
    st.session_state.model_id = "meta.llama3.3-70B"
if "main_language" not in st.session_state:
    st.session_state.main_language = "en"
if "enable_reranker" not in st.session_state:
    st.session_state.enable_reranker = True
if "collection_name" not in st.session_state:
    st.session_state.collection_name = config.COLLECTION_LIST[0]

# to manage feedback
if "get_feedback" not in st.session_state:
    st.session_state.get_feedback = False


#
# supporting functions
#
def display_msg_on_rerun(chat_hist: List[Union[HumanMessage, AIMessage]]) -> None:
    """Display all messages on rerun."""
    for msg in chat_hist:
        role = USER if isinstance(msg, HumanMessage) else ASSISTANT
        with st.chat_message(role):
            st.markdown(msg.content)


# when push the button reset the chat_history
def reset_conversation():
    """Reset the chat history."""
    st.session_state.chat_history = []

    # change thread_id
    st.session_state.thread_id = str(uuid.uuid4())


def add_to_chat_history(msg):
    """
    add the msg to chat history
    """
    st.session_state.chat_history.append(msg)


def get_chat_history():
    """return the chat history from the session"""
    return (
        st.session_state.chat_history[-config.MAX_MSGS_IN_HISTORY :]
        if config.MAX_MSGS_IN_HISTORY > 0
        else st.session_state.chat_history
    )


def register_feedback():
    """
    Register the feedback.
    """
    # number of stars, start at 0
    n_stars = st.session_state.feedback + 1
    logger.info("Feedback: %d %s", n_stars, "stars")
    logger.info("")

    # register the feedback in DB
    rag_feedback = RagFeedback()

    rag_feedback.insert_feedback(
        question=st.session_state.chat_history[-2].content,
        answer=st.session_state.chat_history[-1].content,
        feedback=n_stars,
    )

    st.session_state.get_feedback = False


#
# Main
#
st.title("OCI Custom RAG Agent")

# Reset button
if st.sidebar.button("Clear Chat History"):
    reset_conversation()


st.sidebar.header("Options")

st.sidebar.text_input(label="Region", value=config.REGION, disabled=True)

# the collection used for semantic search
st.session_state.collection_name = st.sidebar.selectbox(
    "Collection name",
    config.COLLECTION_LIST,
)

st.session_state.main_language = st.sidebar.selectbox(
    "Select the language for the answer",
    config.LANGUAGE_LIST,
)
st.session_state.model_id = st.sidebar.selectbox(
    "Select the Chat Model",
    config.MODEL_LIST,
)
st.session_state.enable_reranker = st.sidebar.checkbox(
    "Enable Reranker", value=True, disabled=False
)
config.ENABLE_TRACING = st.sidebar.checkbox(
    "Enable tracing", value=False, disabled=False
)


#
# Here the code where react to user input
#

# Display chat messages from history on app rerun
display_msg_on_rerun(get_chat_history())

if question := st.chat_input("Hello, how can I help you?"):
    # Display user message in chat message container
    st.chat_message(USER).markdown(question)

    try:
        with st.spinner("Calling AI..."):
            time_start = time.time()

            # get the chat history to give as input to LLM
            _chat_history = get_chat_history()

            # modified to be more responsive, show result asap
            try:
                input_state = State(
                    user_request=question,
                    chat_history=_chat_history,
                    error=None,
                )

                # collect the results of all steps
                results = []
                ERROR = None

                # integration with tracing, start the trace
                with zipkin_span(
                    service_name=config.AGENT_NAME,
                    span_name="stream",
                    transport_handler=http_transport,
                    encoding=Encoding.V2_JSON,
                    sample_rate=100,
                ) as span:
                    # set the agent config
                    agent_config = {
                        "configurable": {
                            "model_id": st.session_state.model_id,
                            "embed_model_type": config.EMBED_MODEL_TYPE,
                            "enable_reranker": st.session_state.enable_reranker,
                            "enable_tracing": config.ENABLE_TRACING,
                            "main_language": st.session_state.main_language,
                            "collection_name": st.session_state.collection_name,
                            "thread_id": st.session_state.thread_id,
                        }
                    }

                    if config.DEBUG:
                        logger.info("Agent config: %s", agent_config)

                    # loop to manage streaming
                    for event in st.session_state.workflow.stream(
                        input_state,
                        config=agent_config,
                    ):
                        for key, value in event.items():
                            MSG = f"Completed: {key}!"
                            logger.info(MSG)
                            st.toast(MSG)
                            results.append(value)

                            # to see if there has been an error
                            ERROR = value["error"]

                            # update UI asap
                            if key == "QueryRewrite":
                                st.sidebar.header("Standalone question:")
                                st.sidebar.write(value["standalone_question"])
                            if key == "Rerank":
                                st.sidebar.header("References:")
                                st.sidebar.write(value["citations"])

                # process final result from agent
                if ERROR is None:
                    # visualize the output
                    answer_generator = results[-1]["final_answer"]

                    # Stream
                    with st.chat_message(ASSISTANT):
                        response_container = st.empty()
                        FULL_RESPONSE = ""

                        for chunk in answer_generator:
                            FULL_RESPONSE += chunk.content
                            response_container.markdown(FULL_RESPONSE + "▌")

                        response_container.markdown(FULL_RESPONSE)

                    elapsed_time = round((time.time() - time_start), 1)
                    logger.info("Elapsed time: %s sec.", elapsed_time)
                    logger.info("")

                    if config.ENABLE_USER_FEEDBACK:
                        st.session_state.get_feedback = True

                else:
                    st.error(ERROR)

                # Add user/assistant message to chat history
                add_to_chat_history(HumanMessage(content=question))
                add_to_chat_history(AIMessage(content=FULL_RESPONSE))

                # get the feedback
                if st.session_state.get_feedback:
                    st.feedback("stars", key="feedback", on_change=register_feedback)

            except Exception as e:
                ERR_MSG = f"Error in assistant_ui, generate_and_exec {e}"
                logger.error(ERR_MSG)
                st.error(ERR_MSG)

    except Exception as e:
        ERR_MSG = "An error occurred: " + str(e)
        logger.error(ERR_MSG)
        st.error(ERR_MSG)
