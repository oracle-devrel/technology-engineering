import streamlit as st

def get_scrollable_box(text: str) -> str:
    """
    Simple scrollable box for non-diarized transcripts.
    Returns HTML string to be rendered with st.markdown(..., unsafe_allow_html=True).
    """
    html_text = f"""
        <div style="
            border-radius: 0.8rem;
            border: 1px solid #e5e7eb;
            background-color: #f9fafb;
            padding: 0.9rem 1rem;
            max-height: 260px;
            overflow-y: auto;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 0.9rem;
            line-height: 1.5;
        ">
            {text}
        </div>
    """
    return html_text


def display_transcription(speakers_list):
    """
    Render diarized transcript as a chat-like interface with *inline* styles only.
    `speakers_list` is a list of dicts like:
        [{ "speaker_id": 0, "speaker_text": "..." }, ...]
    Returns HTML string to be rendered with st.markdown(..., unsafe_allow_html=True).
    """

    # Soft, professional colors per speaker
    colors = {
        0: "#dbeafe",  # Speaker A
        1: "#fee2e2",  # Speaker B
    }
    labels = {
        0: "Speaker A",
        1: "Speaker B",
    }

    container_style = (
        "max-height: 260px; "
        "overflow-y: auto; "
        "padding: 0.75rem; "
        "border: 1px solid #e5e7eb; "
        "border-radius: 0.9rem; "
        "background-color: #f9fafb; "
        "font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; "
        "font-size: 0.9rem;"
    )

    bubble_base_style = (
        "padding: 0.55rem 0.7rem; "
        "border-radius: 0.75rem; "
        "max-width: 75%; "
        "box-shadow: 0 4px 10px rgba(15,23,42,0.08); "
        "line-height: 1.45;"
    )

    label_style = (
        "font-size: 0.7rem; "
        "font-weight: 600; "
        "opacity: 0.75; "
        "margin-bottom: 0.15rem; "
        "text-transform: uppercase; "
        "letter-spacing: 0.06em;"
    )

    rows_html = []

    for msg in speakers_list:
        speaker = msg.get("speaker_id", 0)
        raw_text = msg.get("speaker_text", "")
        # preserve newlines
        raw_text = raw_text.replace("\n", "<br>")

        color = colors.get(speaker, "#e5e7eb")
        label = labels.get(speaker, f"Speaker {speaker}")

        # left/right alignment per speaker
        if speaker == 0:
            row_style = "display:flex; justify-content:flex-start; margin-bottom:0.35rem;"
        else:
            row_style = "display:flex; justify-content:flex-end; margin-bottom:0.35rem;"

        bubble_style = bubble_base_style + f" background-color: {color};"

        bubble_html = f"""<div style="{row_style}">
                <div style="{bubble_style}">
                    <div style="{label_style}">{label}</div>
                    <div>{raw_text}</div>
                </div>
            </div>
        """

        rows_html.append(bubble_html)

    html = f"""
        <div style="{container_style}">
            {''.join(rows_html)}
        </div>
    """
    return html

