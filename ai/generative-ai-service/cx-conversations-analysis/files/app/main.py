import copy
import json
import os

import config
import pandas as pd
import streamlit as st
from backend import ai_tools, prompts
from frontend import display_widgets, navbar

# ---------- Page config ----------
st.set_page_config(
    page_title="Audio Call Analyzer",
    page_icon="🎧",
    layout="wide",
)

# --- Session state initialization ---
if "results" not in st.session_state:
    st.session_state["results"] = None
if "processed" not in st.session_state:
    st.session_state["processed"] = False
if "selected_model" not in st.session_state:
    st.session_state["selected_model"] = None


def load_css():
    """
    Load global CSS from styles.css and inject into the app.
    Adjust paths here if your file lives elsewhere.
    """
    css_paths = [
        os.path.join(os.path.dirname(__file__), "styles.css"),
        os.path.join(os.path.dirname(__file__), "frontend", "styles.css"),
        "styles.css",
        "frontend/styles.css",
    ]

    for path in css_paths:
        try:
            with open(path) as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            return
        except OSError:
            continue
    # If not found, do nothing (app still works, just without custom CSS)


# ---------- Helpers ----------
def upload_audio(uploaded_file):
    """
    Save a single uploaded file to disk and return its path.
    """
    uploaded_file.seek(0)
    if not os.path.exists(config.UPLOAD_PATH):
        os.mkdir(config.UPLOAD_PATH)

    audio_file = os.path.join(config.UPLOAD_PATH, uploaded_file.name)
    with open(audio_file, "wb") as f:
        f.write(uploaded_file.read())
    return audio_file


def render_header():
    """
    Use the .main-header / .header-content / .oracle-logo styles
    from styles.css.
    """
    st.markdown(
        """
        <header class="main-header">
            <div class="header-content">
                <h1>Audio Call Analyzer</h1>
                <p>
                    Upload one or more calls, generate diarized transcripts and LLM-powered
                    summaries, and explore batch-level insights.
                </p>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def parse_llm_json(raw_summary: str):
    """
    Parse JSON coming from the LLM.
    Makes a best-effort attempt, including stripping ```json fences if present.
    Returns a dict with the expected keys, with safe defaults on failure.
    """
    cleaned = raw_summary.strip()

    # Handle possible code fences, just in case
    if cleaned.startswith("```"):
        # Remove first line (``` or ```json) and last ```
        parts = cleaned.split("```")
        if len(parts) >= 3:
            cleaned = parts[1].strip()

    try:
        summary_json = json.loads(cleaned)
    except json.JSONDecodeError:
        summary_json = {
            "call_reason": "",
            "issue_solved": "",
            "info_asked": "",
            "summary": cleaned,
            "sentiment_score": None,
        }

    # Ensure all expected keys exist
    summary_json.setdefault("call_reason", "")
    summary_json.setdefault("issue_solved", "")
    summary_json.setdefault("info_asked", "")
    summary_json.setdefault("summary", "")
    summary_json.setdefault("sentiment_score", None)

    return summary_json


def process_batch(uploaded_files, selected_model):
    """
    Run the speech + LLM pipeline on a batch of uploaded files.
    Stores structured results in st.session_state.
    """
    speech_pipeline = ai_tools.SpeechPipeline(config)
    genai_pipeline = ai_tools.GenAIPipeline(config)

    do_diarization = True
    results = []

    progress = st.progress(0.0)
    status_box = st.empty()

    total_files = len(uploaded_files)

    for idx, uploaded_file in enumerate(uploaded_files):
        status_box.info(
            f"Processing **{uploaded_file.name}** "
            f"({idx + 1}/{total_files}) - transcribing & summarizing..."
        )

        # 1. Save audio
        audio_path = upload_audio(uploaded_file)

        # 2. Transcription
        whisper_trans = speech_pipeline.get_transcription(
            audio_path,
            model_type="Oracle",  # or "Whisper"
            whisper_prompt=None,
            diarization=do_diarization,
            number_of_speakers=2,
        )
        processed_trans, speakers_list = ai_tools.post_process_trans(
            whisper_trans,
            diarization=do_diarization,
        )

        # 3. LLM JSON summary
        prompt = prompts.SUMMARIZE_SYSTEM_PROMPT.format(format=prompts.SUMMARY_FORMAT)
        summary_json = genai_pipeline.get_chat_response(
            prompt,
            prompts.SUMMARIZE_PROMPT.format(conversation=processed_trans),
            model_id=config.GENAI_MODELS[selected_model],
        )

        # summary_json = parse_llm_json(raw_summary)

        results.append(
            {
                "name": uploaded_file.name,
                "audio_path": audio_path,
                "transcription": processed_trans,
                "speakers_list": speakers_list,
                # "summary_raw": raw_summary,
                "summary_json": summary_json,
            }
        )

        progress.progress((idx + 1) / total_files)

    status_box.success("All files processed successfully ✅")

    # Save to session_state
    st.session_state["results"] = results
    st.session_state["processed"] = True
    st.session_state["selected_model"] = selected_model


# ---------- Page renderers ----------
def render_per_call_view(results, selected_model):
    do_diarization = True

    # KPIs
    if results:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Calls in batch", len(results))
        with col2:
            st.metric("LLM model", selected_model)
        with col3:
            st.metric("Diarization", "On")

    if not results:
        st.markdown(
            """
            <div class="upload-placeholder">
                <div class="upload-placeholder-title">
                    Start by uploading audio files in the sidebar.
                </div>
                <div class="upload-placeholder-subtitle">
                    Select one or more files, choose a model, and click <b>Run</b>.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Tabs per file
    tab_labels = [f"{i + 1}. {r['name']}" for i, r in enumerate(results)]
    per_call_tabs = st.tabs(tab_labels)

    for tab, res in zip(per_call_tabs, results):
        with tab:
            st.markdown(
                f"""
                <div class="file-header">
                    <div class="file-name">{res["name"]}</div>
                    <div>
                        <span class="pill">Model: {selected_model}</span>
                        <span class="pill">Diarization: On</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Audio player
            audio_col, _ = st.columns([2, 1])
            with audio_col:
                st.audio(res["audio_path"])

            st.write("")  # spacer

            # 2-column layout: Transcript | Summary
            transcript_col, summary_col = st.columns([1.4, 1.0])

            # LEFT: Transcript
            with transcript_col:
                st.markdown(
                    '<div class="section-title">Transcript</div>',
                    unsafe_allow_html=True,
                )
                if do_diarization and res["speakers_list"]:
                    transcription_display = display_widgets.display_transcription(
                        res["speakers_list"]
                    )
                else:
                    transcription_display = display_widgets.get_scrollable_box(
                        text=res["transcription"]
                    )
                st.markdown(transcription_display, unsafe_allow_html=True)

            # RIGHT: JSON summary visualization
            with summary_col:
                data = res.get("summary_json") or {}
                call_reason = data.get("call_reason", "") or "—"
                issue_solved = data.get("issue_solved", "") or "—"
                info_asked = data.get("info_asked", "")
                short_summary = data.get("summary", "") or "—"
                sentiment_score = data.get("sentiment_score", None)

                # Normalize info_asked to a list
                if isinstance(info_asked, list):
                    info_items = info_asked
                elif isinstance(info_asked, str) and info_asked.strip():
                    info_items = [info_asked.strip()]
                else:
                    info_items = []

                # Sentiment class based on score
                if isinstance(sentiment_score, int):
                    if sentiment_score <= 3:
                        sentiment_class = "sentiment-badge--low"
                    elif sentiment_score <= 7:
                        sentiment_class = "sentiment-badge--mid"
                    else:
                        sentiment_class = "sentiment-badge--high"
                    sentiment_label = f"{sentiment_score}/10"
                else:
                    sentiment_class = ""
                    sentiment_label = "—"

                st.markdown(
                    f"""<div class="summary-json-card">
                        <div class="summary-json-header">
                            <div class="summary-json-title">Call summary</div>
                            <span class="sentiment-badge {sentiment_class}">
                                Sentiment&nbsp;{sentiment_label}
                            </span>
                        </div>
                        <div class="summary-json-grid">
                            <div class="summary-json-item">
                                <div class="summary-json-label">Call reason</div>
                                <div class="summary-json-value">{call_reason}</div>
                            </div>
                            <div class="summary-json-item">
                                <div class="summary-json-label">Issue solved</div>
                                <div class="summary-json-value">{issue_solved}</div>
                            </div>
                        </div>
                        <div class="summary-json-item" style="margin-top:0.6rem;">
                            <div class="summary-json-label">Info requested by agent</div>
                            <div class="summary-json-tags">
                                {"".join(f'<span class="summary-tag">{item}</span>' for item in info_items) if info_items else '<span class="summary-json-value">—</span>'}
                            </div>
                        </div>
                        <div class="summary-json-item" style="margin-top:0.8rem;">
                            <div class="summary-json-label">1-2 sentence summary</div>
                            <div class="summary-json-value">{short_summary}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_batch_overview(results, selected_model):
    if not results:
        st.info(
            "Batch overview is disabled until you process at least one batch of audio. "
            "Go to *Per-call view*, upload files, and click **Run** first."
        )
        st.stop()

    # ---------- BASIC STATS ----------
    st.markdown(
        '<div class="section-title">Batch statistics</div>',
        unsafe_allow_html=True,
    )

    rows = []
    for res in results:
        trans = res["transcription"] or ""
        total_words = len(trans.split())

        summary_json = res.get("summary_json") or {}
        sentiment = summary_json.get("sentiment_score", None)
        issue_solved = summary_json.get("issue_solved", "")

        rows.append(
            {
                "File": res["name"],
                "Total words (approx.)": total_words,
                "Sentiment score": sentiment,
                "Issue solved": issue_solved,
            }
        )

    stats_df = pd.DataFrame(rows)

    total_calls = len(stats_df)
    issues_solved = (stats_df["Issue solved"] == "Yes").sum()

    # Average sentiment (ignore None)
    if "Sentiment score" in stats_df.columns:
        valid_sentiments = stats_df["Sentiment score"].dropna()
        avg_sentiment = valid_sentiments.mean() if not valid_sentiments.empty else None
    else:
        avg_sentiment = None

    c1, c2, c3 = st.columns(3)
    c1.metric("Calls Processed", total_calls)
    c2.metric("First-Call Resolution Rate", f"{issues_solved:,}/{total_calls}")
    if avg_sentiment is not None:
        c3.metric("Customer Satisfaction", f"{avg_sentiment:.1f}/10")
    else:
        c3.metric("Avg. Sentiment", "—")

    # ---------- GENAI-GENERATED CATEGORIZATION & REPORT ----------
    st.write("")
    st.markdown(
        '<div class="section-title">GenAI-generated overview</div>',
        unsafe_allow_html=True,
    )

    genai_pipeline = ai_tools.GenAIPipeline(config)

    with st.expander(
        "Show categorization and insights across all calls", expanded=True
    ):
        # 1) Prepare a lightweight version of the messages for the prompts
        messages_info = copy.deepcopy(results)
        for item in messages_info:
            item.pop("audio_path", None)

        # 2) Categorization
        try:
            prompt = prompts.CATEGORIZATION_SYSTEM.format(
                format=prompts.CATEGORIZATION_FORMAT
            )
            categ_json = genai_pipeline.get_chat_response(
                prompt,
                prompts.CATEGORIZATION.format(MESSAGE_BATCH=messages_info),
                model_id=config.GENAI_MODELS[selected_model],
            )
        except Exception as e:
            st.warning(f"Could not generate categorization: {e}")
            categ_json = []

        # Build lookup: file name -> category
        category_lookup = {}
        if isinstance(categ_json, list):
            for item in categ_json:
                name = item.get("name")
                category = item.get("category")
                if name is not None:
                    category_lookup[name] = category

        # Attach categories back to messages_info and results
        for item, elem in zip(messages_info, results):
            categ = category_lookup.get(item.get("name"), None)
            item["category"] = categ
            elem["category"] = categ  # so per-call view can reuse it

        # Update stats_df with category information
        stats_df["Category"] = [res.get("category", "") for res in results]

        # 3) Report generation
        try:
            prompt = prompts.REPORT_GEN_SYSTEM.format(format=prompts.REPORT_GEN_FORMAT)
            report_obj = genai_pipeline.get_chat_response(
                prompt,
                prompts.REPORT_GEN.format(MESSAGE_BATCH=messages_info),
                model_id=config.GENAI_MODELS[selected_model],
            )
        except Exception as e:
            st.warning(f"Could not generate report: {e}")
            report_obj = None

        # ---------- VISUALIZATION OF CATEGORIES & REPORT ----------
        if report_obj and isinstance(report_obj, dict) and report_obj.get("categories"):
            st.markdown(
                '<div class="section-title">Category insights</div>',
                unsafe_allow_html=True,
            )

            for cat in report_obj["categories"]:
                cat_name = cat.get("category", "Uncategorized")
                cat_summary = cat.get("summary", "")
                avg_cat_sentiment = cat.get("average_sentiment_score", None)
                highest = cat.get("highest_sentiment_message", {}) or {}
                lowest = cat.get("lowest_sentiment_message", {}) or {}
                key_insights = cat.get("key_insights", []) or []
                issues_rate = cat.get("issue_resolution_rate", []) or []

                # How many calls in this category (from updated stats_df)
                cat_calls = stats_df[stats_df["Category"] == cat_name]
                cat_call_count = len(cat_calls)

                if isinstance(avg_cat_sentiment, (int, float)):
                    if avg_cat_sentiment <= 3:
                        avg_bg = "#fef2f2"
                        avg_border = "#fecaca"
                        avg_color = "#b91c1c"
                    elif avg_cat_sentiment <= 6:
                        avg_bg = "#fefce8"
                        avg_border = "#fef9c3"
                        avg_color = "#a16207"
                    elif avg_cat_sentiment <= 8:
                        avg_bg = "#eff6ff"
                        avg_border = "#bfdbfe"
                        avg_color = "#1d4ed8"
                    else:
                        avg_bg = "#ecfdf5"
                        avg_border = "#bbf7d0"
                        avg_color = "#047857"
                else:
                    avg_bg = "#f3f4f6"
                    avg_border = "#e5e7eb"
                    avg_color = "#6b7280"

                avg_cat_label = (
                    f"{avg_cat_sentiment:.1f}/10"
                    if isinstance(avg_cat_sentiment, (int, float))
                    else "—"
                )

                issues_rate_label = (
                    f"{issues_rate * 100:.1f}"
                    if isinstance(issues_rate, (int, float))
                    else "—"
                )

                highest_summary = highest.get("summary", "—")
                highest_score = highest.get("sentiment_score", None)
                highest_label = (
                    f"{highest_score}/10"
                    if isinstance(highest_score, (int, float))
                    else "—"
                )

                lowest_summary = lowest.get("summary", "—")
                lowest_score = lowest.get("sentiment_score", None)
                lowest_label = (
                    f"{lowest_score}/10"
                    if isinstance(lowest_score, (int, float))
                    else "—"
                )

                key_insights_html = "".join(
                    f"<li>{insight}</li>" for insight in key_insights
                )

                # Category card
                st.markdown(
                    f"""
                    <div style="
                        border-radius: 1rem;
                        border: 1px solid #e5e7eb;
                        padding: 1rem 1.1rem;
                        margin-bottom: 1rem;
                        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 48%, #f3f4f6 100%);
                        box-shadow: 0 14px 30px rgba(15,23,42,0.08);
                    ">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.75rem;">
                            <div>
                                <div style="font-weight:600;font-size:0.95rem;color:#111827;">
                                    {cat_name}
                                </div>
                                <div style="font-size:0.85rem;color:#4b5563;margin-top:0.25rem;">
                                    {cat_summary}
                                </div>
                            </div>
                                <div style="
                                        display:inline-flex;
                                        align-items:center;
                                        padding:0.18rem 0.7rem;
                                        border-radius:999px;
                                        font-size:0.8rem;
                                        font-weight:600;
                                        background:{avg_bg};
                                        color:{avg_color};
                                        border:1px solid {avg_border};
                                    ">
                                        Avg sentiment:&nbsp;{avg_cat_label}
                                    </div>
                                    <div style="
                                        display:inline-flex;
                                        align-items:center;
                                        padding:0.18rem 0.7rem;
                                        border-radius:999px;
                                        font-size:0.8rem;
                                        font-weight:600;
                                        background:#eff6ff;
                                        color:#1d4ed8;
                                        border:1px solid #bfdbfe;
                                    ">
                                        Resolution&nbsp;rate:&nbsp;{issues_rate_label} %
                                    </div>
                                <div style="
                                        display:inline-flex;
                                        align-items:center;
                                        padding:0.18rem 0.7rem;
                                        border-radius:999px;
                                        font-size:0.8rem;
                                        font-weight:600;
                                        background:#eff6ff;
                                        color:#1d4ed8;
                                        border:1px solid #bfdbfe;">
                                    Number&nbsp;of&nbsp;calls:&nbsp;{cat_call_count}
                                </div>
                            </div>
                            <div style="display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0.75rem;margin-top:0.85rem;">
                                <div style="
                                    border-radius:0.75rem;
                                    padding:0.7rem;
                                    background:#ecfdf3;
                                    border:1px solid #bbf7d0;
                                    font-size:0.85rem;
                                ">
                                    <div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#166534;margin-bottom:0.15rem;">
                                        Highest sentiment
                                    </div>
                                    <div style="font-size:0.8rem;color:#166534;font-weight:600;margin-bottom:0.1rem;">
                                        {highest_label}
                                    </div>
                                    <div style="color:#065f46;">
                                        {highest_summary}
                                    </div>
                                </div>
                                <div style="
                                    border-radius:0.75rem;
                                    padding:0.7rem;
                                    background:#fef2f2;
                                    border:1px solid #fecaca;
                                    font-size:0.85rem;
                                ">
                                    <div style="font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#b91c1c;margin-bottom:0.15rem;">
                                        Lowest sentiment
                                    </div>
                                    <div style="font-size:0.8rem;color:#b91c1c;font-weight:600;margin-bottom:0.1rem;">
                                        {lowest_label}
                                    </div>
                                    <div style="color:#7f1d1d;">
                                        {lowest_summary}
                                    </div>
                                </div>
                            </div>
                            <div style="margin-top:0.85rem;">
                                <div style="font-size:0.8rem;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;color:#6b7280;margin-bottom:0.2rem;">
                                    Key insights
                                </div>
                                <ul style="padding-left:1.1rem;margin:0;font-size:0.86rem;color:#374151;">
                                    {key_insights_html}
                                </ul>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown("---")

        else:
            st.info(
                "No structured report available yet. Check the configuration of REPORT_GEN / CATEGORIZATION prompts."
            )


def render_footer():
    st.markdown(
        """
        <footer class="oracle-footer">
            Oracle &copy; Audio Call Analyzer – Internal demo UI
        </footer>
        """,
        unsafe_allow_html=True,
    )


# ---------- Main ----------
def main():
    load_css()
    render_header()

    # --- Sidebar controls & page selection ---
    uploaded_files, run_button, selected_model, page = navbar.make_sidebar(config)

    # Ensure list type for multi-file support
    if uploaded_files and not isinstance(uploaded_files, list):
        uploaded_files = [uploaded_files]

    # --- Run processing when button clicked ---
    if uploaded_files and run_button:
        process_batch(uploaded_files, selected_model)

    # Get last processed batch from session_state
    results = st.session_state.get("results")
    processed = st.session_state.get("processed", False)
    selected_model_state = st.session_state.get("selected_model") or selected_model

    # --- Route to the selected "page" ---
    if page == "Per-call view":
        render_per_call_view(results if processed else None, selected_model_state)
    elif page == "Batch overview":
        if not processed:
            st.info(
                "Batch overview is disabled until audio has been processed.\n\n"
                "Go to **Per-call view**, upload files, and click **Run** first."
            )
            st.stop()
        render_batch_overview(results, selected_model_state)

    render_footer()


if __name__ == "__main__":
    main()