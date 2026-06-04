import time
from datetime import datetime

import backend.backend as backend
import backend.config as config
import streamlit as st

# Page Config
st.set_page_config(
    page_title="Oracle LLM Comparison",
    page_icon="🏛️",
    layout="wide",
    # initial_sidebar_state="expanded",
)

# Load external CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


local_css("static/styles.css")

# Session State Initialization
if "responses" not in st.session_state:
    st.session_state.responses = []

if "user_prompt" not in st.session_state:
    st.session_state.user_prompt = ""

if "prev_base_model" not in st.session_state:
    st.session_state.prev_base_model = None

if "prev_finetuned_model" not in st.session_state:
    st.session_state.prev_finetuned_model = None

# Header
st.markdown(
"""
<div class="main-header">
    <h1>LLM Performance Comparator</h1>
    <p>From base to tuned - measure, compare, decide.</p>
</div>
""",
    unsafe_allow_html=True,
)

# Sidebar - Model Selection
st.sidebar.markdown("### Model Configuration")
st.sidebar.markdown("#### Base Settings")
base_model = st.sidebar.selectbox("Base Model", config.BASE_MODELS, index=0)

st.sidebar.markdown("#### Fine tuning Settings")
available_finetuned = list(config.FINETUNED_MODELS.keys())
fine_tuned_model = st.sidebar.selectbox(
    "Fine-tuned Model", available_finetuned, index=0
)

# Reset if model changed
if st.session_state.prev_base_model is not None and (
    st.session_state.prev_base_model != base_model
    or st.session_state.prev_finetuned_model != fine_tuned_model
):
    st.session_state.responses = []
    st.session_state.user_prompt = ""

st.session_state.prev_base_model = base_model
st.session_state.prev_finetuned_model = fine_tuned_model

# Show FT Params
if fine_tuned_model:
    model_params = config.FINETUNED_MODELS[fine_tuned_model]
    st.sidebar.markdown("#### Fine-tuning Parameters")
    st.sidebar.markdown(
        f"""
    <div class="param-display">
        <div class="param-row"><span class="param-label">Training Method:</span><span class="param-value">{model_params["training_method"]}</span></div>
        <div class="param-row"><span class="param-label">Dataset:</span><span class="param-value">{model_params["dataset"]}</span></div>
        <div class="param-row"><span class="param-label">Training Epochs:</span><span class="param-value">{model_params["training_epochs"]}</span></div>
        <div class="param-row"><span class="param-label">Learning Rate:</span><span class="param-value">{model_params["learning_rate"]}</span></div>
        <div class="param-row"><span class="param-label">Batch Size:</span><span class="param-value">{model_params["batch_size"]}</span></div>
        <div class="param-row"><span class="param-label">Early Stopping Patience:</span><span class="param-value">{model_params["stopping_patience"]}</span></div>
        <div class="param-row"><span class="param-label">Early Stopping threshold:</span><span class="param-value">{model_params["stopping_threshold"]}</span></div>
        <div class="param-row"><span class="param-label">Log model metrics interval:</span><span class="param-value">{model_params["interval"]}</span></div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if model_params["training_method"] == "LoRA":
        st.sidebar.markdown("**LoRA Parameters:**")
        st.sidebar.markdown(
            f"""
        <div class="param-display">
            <div class="param-row"><span class="param-label">LoRA Rank (r):</span><span class="param-value">{model_params["lora_r"]}</span></div>
            <div class="param-row"><span class="param-label">LoRA Alpha:</span><span class="param-value">{model_params["lora_alpha"]}</span></div>
            <div class="param-row"><span class="param-label">LoRA Dropout:</span><span class="param-value">{model_params["lora_dropout"]}</span></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

# Prompt Input
st.markdown('<div class="comparison-container">', unsafe_allow_html=True)
st.session_state.user_prompt = st.text_area(
    "Enter your prompt:",
    height=100,
    # key="user_prompt",
    placeholder="Type your question or prompt to compare model responses...",
    help="Enter a prompt to evaluate both models",
)

# Generate Comparison
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    generate_button = st.button(
        "Generate Comparison", type="primary", use_container_width=True
    )

if generate_button and st.session_state.user_prompt:
    with st.spinner("Generating responses..."):
        progress_bar = st.progress(0)

        # Vanilla
        progress_bar.progress(30)
        start = time.time()
        vanilla_response = backend.call_model(st.session_state.user_prompt, base_model)
        end = time.time()
        vanilla_time = end - start

        # Fine-tuned
        progress_bar.progress(70)
        start = time.time()
        finetuned_response = backend.call_model(
            st.session_state.user_prompt, model_params["ft_model"]
        )
        end = time.time()
        finetuned_time = end - start

        progress_bar.progress(100)

        st.session_state.responses.append(
            {
                "timestamp": datetime.now(),
                "prompt": st.session_state.user_prompt,
                "vanilla_response": vanilla_response,
                "finetuned_response": finetuned_response,
                "vanilla_time": vanilla_time,
                "finetuned_time": finetuned_time,
                "base_model": base_model,
                "finetuned_model": fine_tuned_model,
            }
        )

        progress_bar.empty()

st.markdown("</div>", unsafe_allow_html=True)

# Results Display
if st.session_state.responses:
    latest = st.session_state.responses[-1]
    improvement = (
        (latest["vanilla_time"] - latest["finetuned_time"]) / latest["vanilla_time"]
    ) * 100

    # Responses
    st.markdown(
        f"""
    <div class="response-grid">
        <div class="response-card vanilla">
            <div class="response-header">
                <div class="model-name">Base Model</div>
                <div class="response-time">{latest["vanilla_time"]:.2f}s</div>
            </div>
            <div class="response-content">{latest["vanilla_response"]}</div>
            <div class="response-meta"><strong>Model:</strong> {latest["base_model"]}</div>
        </div>
        <div class="response-card finetuned">
            <div class="response-header">
                <div class="model-name">Fine-tuned Model</div>
                <div class="response-time">{latest["finetuned_time"]:.2f}s</div>
            </div>
            <div class="response-content">{latest["finetuned_response"]}</div>
            <div class="response-meta"><strong>Model:</strong> {latest["finetuned_model"]}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

# Footer
st.markdown(
    """
<div class="oracle-footer">
    Oracle Corporation | Technology Engineering | OCI Generative AI Services
</div>
""",
    unsafe_allow_html=True,
)
