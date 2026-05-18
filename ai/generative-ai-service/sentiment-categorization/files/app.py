import json
import pandas as pd
import streamlit as st
import plotly.express as px
from backend.feedback_wrapper import FeedbackAgentWrapper

st.set_page_config(page_title="Feedback Dashboard", page_icon="📊", layout="wide")

def load_styles():
    try:
        with open("styles.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        st.markdown(
            "<style>.main-header{border-bottom:3px solid #C74634;padding:1rem 0}</style>",
            unsafe_allow_html=True,
        )

load_styles()

st.markdown(
    """
    <div class="main-header">
      <div class="header-content">
        <h1>Customer Feedback Dashboard</h1>
        <p>Analyze customer sentiment, insights, and trends across categories</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="stMarkdown"><h3>Data Input</h3></div>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Upload CSV (required columns: ID, Message)", type=["csv"])

data_list = None
df_uploaded = None
valid_file = False

if uploaded_file is not None:
    try:
        df_uploaded = pd.read_csv(uploaded_file)
        required_columns = {"ID", "Message"}
        if not required_columns.issubset(set(df_uploaded.columns)):
            st.sidebar.error(f"CSV must include columns: {', '.join(required_columns)}")
        else:
            valid_file = True
            st.sidebar.success("File uploaded and validated successfully.")
            st.sidebar.markdown("</div>", unsafe_allow_html=True)

            data_list = df_uploaded.values.tolist()
    except Exception as e:
        st.sidebar.error(f"An error occurred while processing the file: {e}")

st.sidebar.markdown('<div class="stMarkdown"><h4>Run</h4></div>', unsafe_allow_html=True)
if "flow_completed" not in st.session_state:
    st.session_state.flow_completed = True

start_button = st.sidebar.button(
    "Start",
    disabled=not (st.session_state.flow_completed and valid_file),
)

st.markdown('<div class="comparison-container">', unsafe_allow_html=True)

if df_uploaded is not None and valid_file:
    st.markdown("### Uploaded Data")
    dataset_exp = st.expander(uploaded_file.name, expanded=True)
    dataset_exp.dataframe(df_uploaded, height=200, use_container_width=True)

def display_category(data):
    if not isinstance(data, dict) or "categories" not in data:
        st.warning("No category data found in the report.")
        return

    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    for category in data.get("categories", []):
        with st.container():
            st.markdown(
                f'<div class="response-card finetuned"><div class="response-header">'
                f'<div class="model-name">{category.get("category_level_1", "Unknown")}</div>'
                f'</div><div class="response-content">',
                unsafe_allow_html=True,
            )
            st.write(category.get("summary", ""))

            col1, col2, col3 = st.columns(3)
            with col1:
                avg = category.get("average_sentiment_score", None)
                if avg is not None:
                    st.metric("Avg Sentiment Score", avg, delta=None)
                    st.progress(min(max(avg / 10, 0.0), 1.0))
            with col2:
                high = category.get("highest_sentiment_message", {})
                st.success(f"Highest Sentiment: {high.get('sentiment_score', 'N/A')}")
                st.write(f"“{high.get('summary', '')}”")
            with col3:
                low = category.get("lowest_sentiment_message", {})
                st.error(f"Lowest Sentiment: {low.get('sentiment_score', 'N/A')}")
                st.write(f"“{low.get('summary', '')}”")

            st.markdown("#### Key Insights")
            for insight in category.get("key_insights", []):
                st.info(f"• {insight}")

            st.markdown("#### Subcategories Breakdown")
            for subcategory in category.get("subcategories", []):
                with st.expander(
                    f"{subcategory.get('category_level_2','(Unknown)')} "
                    f"(Avg: {subcategory.get('average_sentiment_score','N/A')})"
                ):
                    st.write(subcategory.get("summary", ""))
            st.markdown("</div></div>", unsafe_allow_html=True)

def display_sentiment(df: pd.DataFrame):
    if df.empty:
        st.warning("No sentiment data to display.")
        return
    fig = px.bar(
        df,
        x="id",
        y="sentiment_score",
        color="sentiment_score",
        text="topic",
        labels={"id": "Id", "sentiment_score": "Sentiment Score (1-10)"},
        title="Sentiment Scores per Feedback Category",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        legend_title_text="Score",
    )
    fig.update_traces(textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

if start_button and st.session_state.flow_completed and valid_file:
    st.session_state.flow_completed = False

    agent = FeedbackAgentWrapper(data_list)
    steps, edges = agent.get_nodes_edges()
    steps = steps[1:-1]
    outputs = []
    current_step = steps[0] if steps else "summarize"

    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    total_steps = len(steps) if steps else 1
    step_counter = 0

    while current_step != "FINALIZED":
        status_placeholder.markdown(
            f'<div class="response-meta">Running step: <strong>{current_step}</strong> '
            f'({step_counter}/{total_steps})</div>',
            unsafe_allow_html=True,
        )
        next_step, output = agent.run_step_by_step()
        if not output:
            current_step = "FINALIZED"
        else:
            outputs.append(output)
            current_step = next_step
            step_counter += 1
            progress_bar.progress(min(step_counter / max(total_steps, 1), 1.0))

    progress_bar.progress(1.0)
    status_placeholder.markdown(
        f'<div class="response-meta">Completed {step_counter} of {total_steps} steps.</div>',
        unsafe_allow_html=True,
    )

    def find_report(objs):
        for o in objs:
            for v in o.values():
                if isinstance(v, dict) and "reports" in v:
                    return v["reports"]
        return None

    report_list = find_report(outputs) or []
    if report_list:
        try:
            categories = json.loads(report_list[0])
            st.markdown("### Report")
            display_category(categories)
        except json.JSONDecodeError:
            st.error("Report is not valid JSON.")

    def find_summaries(objs):
        for o in objs:
            if "summarize" in o and "messages_info" in o["summarize"]:
                return o["summarize"]["messages_info"]
        return []

    summaries = find_summaries(outputs)
    try:
        df = pd.DataFrame([s if isinstance(s, dict) else s.dict() for s in summaries])
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        st.markdown("### Sentiment Overview")
        display_sentiment(df)

    st.session_state.flow_completed = True

# Footer
st.markdown(
    """
    <div class="oracle-footer">
      © Oracle Corporation | Technology Engineering | OCI Generative AI Services
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
