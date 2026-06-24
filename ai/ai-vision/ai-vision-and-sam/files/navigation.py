import base64
import streamlit as st
import config

def make_sidebar():
    with open(config.ORACLE_LOGO, "rb") as f:
        icon_base64 = base64.b64encode(f.read()).decode()
    with st.sidebar:
        
        st.markdown(
            f"""
            <div style="display: flex; align-items: left; gap: 10px;">
                <img src="data:image/png;base64,{icon_base64}" 
                    width="90" style="border-radius: 8px;">
                <span style="font-size: 30px; font-weight: 600;">Upload & Run</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("""
            <style>
                .stButton>button {
                    background-color: #F80000;
                    color: white;
                    padding: 0.5em 1em;
                    font-size: 16px;
                    border-radius: 5px;
                }
            </style>
        """, unsafe_allow_html=True)

        st.write("")
        st.write("")

        uploaded_file = st.sidebar.file_uploader("Upload an Image", type=['png', 'jpg'])
        run_button = st.sidebar.button("Run")

        st.write("")
        st.write("")

        return uploaded_file, run_button

