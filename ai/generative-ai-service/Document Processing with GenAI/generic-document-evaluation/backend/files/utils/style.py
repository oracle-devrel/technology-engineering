# pages/utils/utils.py
import streamlit as st
from PIL import Image

def set_page_config():
    favicon = Image.open("./pages/utils/oracle.webp")
    st.set_page_config(
        page_title="OCI gen AI Applications",
        page_icon=favicon,
        layout="wide",
        initial_sidebar_state="auto",
    )

    hide_streamlit_style = """
        <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
