import base64
import streamlit as st


def make_sidebar(config):
    processed = st.session_state.get("processed", False)

    with st.sidebar:
        # --- Title block (styled by .stSidebar / h3) ---
        st.markdown("### Audio Call Analyzer")

        # --- Page selector (view) ---
        st.markdown("#### Analysis view")
        page = st.radio(
            "",
            ("Per-call view", "Batch overview"),
            index=0,
            help="Switch between single-call inspection and batch-level insights.",
        )

        if not processed and page == "Batch overview":
            st.caption(
                "ℹ️ Batch overview unlocks after you process at least one batch."
            )

        # --- Upload & model selection ---
        st.markdown("#### Input")
        uploaded_files = st.file_uploader(
            "Audio file(s)",
            type=["wav", "mp3", "m4a"],
            accept_multiple_files=True,
        )

        st.markdown("#### Model")
        selected_model = st.selectbox(
            "Oracle Generative AI model",
            config.LIST_GENAI_MODELS,
        )

        run_button = st.button("Run")

        # Sidebar info card using .sidebar-tips / .param-display styles
        st.markdown(
            """
            <div class="sidebar-tips">
                <h5>Tips</h5>
                <ul style="padding-left:1.1rem;margin:0;">
                    <li>Select multiple files to process a batch.</li>
                    <li>Per-call view shows detailed transcripts and summaries.</li>
                    <li>Batch overview aggregates statistics across calls.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if uploaded_files:
            file_count = len(uploaded_files)
            st.markdown(
                f"""
                <div class="param-display">
                    <div class="param-row">
                        <span class="param-label">Files selected</span>
                        <span class="param-value">{file_count}</span>
                    </div>
                    <div class="param-row">
                        <span class="param-label">Model</span>
                        <span class="param-value">{selected_model}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        return uploaded_files, run_button, selected_model, page
