"""Mizan visual system and safe Streamlit render helpers.

Author: Ali Ottoman
"""

from __future__ import annotations

import html

import streamlit as st

from .models import ExtractionRun, ValidationCheck

CSS = r"""
<style>
:root {
  --paper: #f7f4ef;
  --paper-lift: #fcfaf6;
  --surface: #ede9e1;
  --ink: #211f1d;
  --ink-2: #5e5a54;
  --ink-3: #7b7789;
  --line: #dfdacf;
  --line-hover: #c6b8d6;
  --purple: #c29ce0;
  --purple-edge: #e0c8ea;
  --forest: #39594d;
  --forest-deep: #2f4a40;
  --coral: #ff7759;
  --lav-surface: #f0dff3;
  --lav-ink: #773d92;
  --mint-surface: #e5f4ef;
  --mint-edge: #c6e3d6;
  --green-ink: #00754e;
  --warn-surface: #fbecc7;
  --warn-ink: #856121;
  --danger-surface: #ffe6de;
  --danger-edge: #ffad9b;
  --danger-ink: #cf4023;
  --shadow-float: 0 24px 60px -28px rgba(60, 30, 80, .45);
  --shadow-band: 0 22px 48px -30px rgba(60, 30, 80, .55);
  --r-pill: 999px;
  --r-field: 12px;
  --r-card: 14px;
  --r-band: 20px;
  --ease: cubic-bezier(.4, 0, .2, 1);
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", system-ui, sans-serif;
  --font-display: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", system-ui, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], .stApp {
  color: var(--ink);
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}

.stApp {
  min-height: 100vh;
  background: var(--paper);
}

.block-container {
  max-width: 1160px;
  padding: 2rem clamp(1.25rem, 4vw, 3rem) 5rem;
}

[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], #MainMenu, footer,
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {
  display: none !important;
}

header[data-testid="stHeader"] { height: 0; background: transparent; }

h1, h2, h3, h4, p, label { font-family: var(--font-sans) !important; }
h1, h2, h3, h4 {
  color: var(--ink) !important;
  font-family: var(--font-display) !important;
  font-weight: 400 !important;
}
h1 { letter-spacing: -.034em !important; }
h2 { letter-spacing: -.022em !important; }
h3, h4 { letter-spacing: -.016em !important; }

::selection { background: var(--lav-surface); }

button:focus-visible, input:focus-visible, textarea:focus-visible,
[role="tab"]:focus-visible,
[role="checkbox"]:focus-visible, [role="slider"]:focus-visible {
  outline: 2px solid var(--purple) !important;
  outline-offset: 2px !important;
}

/* Top bar */
.mizan-topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--line);
}
.mizan-wordmark {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 400;
  letter-spacing: -.03em;
  line-height: 1;
}
.mizan-wordmark span { color: var(--coral); }
.mizan-edition {
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .02em;
  text-transform: uppercase;
}
.mizan-topbar-spacer { flex: 1; }
.mizan-topbar-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }

.mizan-pill, .state-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 26px;
  padding: 0 11px;
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  background: var(--paper-lift);
  color: var(--ink-2);
  font-family: var(--font-mono);
  font-size: 10px;
  line-height: 1;
  white-space: nowrap;
}
.mizan-dot { width: 6px; height: 6px; flex: none; border-radius: 50%; background: var(--coral); }
.mizan-pill.live { border-color: var(--mint-edge); background: var(--mint-surface); color: var(--green-ink); }
.mizan-pill.live .mizan-dot { background: var(--green-ink); }

/* One signature field per view */
.mizan-hero {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  margin: 20px 0 22px;
  padding: 28px 30px 30px;
  border-radius: var(--r-band);
  background: var(--purple);
  color: var(--ink);
  box-shadow: var(--shadow-band);
}
.mizan-hero::before {
  content: "";
  position: absolute;
  inset: -45% -8% auto auto;
  z-index: -2;
  width: 500px;
  height: 350px;
  transform: rotate(19deg);
  background: conic-gradient(from 210deg, #ff7759, #7be3d8, #d18ee2, #ffe08a, #ff7759);
  filter: blur(26px);
  opacity: .5;
  mask-image: radial-gradient(closest-side, #000, transparent);
  -webkit-mask-image: radial-gradient(closest-side, #000, transparent);
}
.mizan-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(100deg, var(--purple) 34%, rgba(194,156,224,.62) 100%);
}
.mizan-hero-copy { max-width: 720px; }
.mizan-eyebrow, .section-kicker {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .02em;
  text-transform: uppercase;
}
.mizan-eyebrow { color: rgba(33,31,29,.72); }
.mizan-hero h1 {
  max-width: 760px;
  margin: 8px 0 0 !important;
  color: var(--ink) !important;
  font-size: clamp(2rem, 4.2vw, 3.25rem) !important;
  line-height: 1.03 !important;
  letter-spacing: -.04em !important;
  font-weight: 400 !important;
}
.mizan-hero p {
  max-width: 66ch;
  margin: 11px 0 0;
  color: rgba(33,31,29,.84);
  font-size: 14.5px;
  line-height: 1.58;
}
.mizan-hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }
.mizan-hero .mizan-pill { border-color: rgba(33,31,29,.2); background: rgba(252,250,246,.3); color: var(--ink); }

/* Quiet four-stage workflow */
.workflow-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin: 22px 0 30px;
}
.workflow-step {
  position: relative;
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  color: var(--ink-3);
  font-size: 12px;
}
.workflow-step:not(:last-child)::after {
  content: "";
  height: 1px;
  flex: 1;
  min-width: 16px;
  margin: 0 14px;
  background: var(--line);
}
.workflow-index {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  flex: none;
  border: 1px solid var(--line);
  border-radius: 50%;
  background: var(--paper-lift);
  font-family: var(--font-mono);
  font-size: 9px;
}
.workflow-step.active { color: var(--lav-ink); font-weight: 650; }
.workflow-step.active .workflow-index { border-color: var(--purple-edge); background: var(--lav-surface); }
.workflow-step.done { color: var(--green-ink); }
.workflow-step.done .workflow-index { border-color: var(--mint-edge); background: var(--mint-surface); }

/* Section hierarchy */
.section-heading { margin: 30px 0 14px; }
.section-kicker { color: var(--ink-3); }
.section-heading h2 { margin: 5px 0 0 !important; font-size: 22px !important; line-height: 1.18 !important; }
.section-description { max-width: 68ch; margin: 7px 0 0; color: var(--ink-2); font-size: 13.5px; }

/* Flat content surfaces */
.model-card, .result-card, .score-card, .audit-item {
  border: 1px solid var(--line);
  border-radius: var(--r-card);
  background: var(--surface);
  box-shadow: none;
}
.model-card { padding: 18px 20px; }
.model-top, .result-head, .audit-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}
.model-name, .result-name, .audit-name { color: var(--ink); font-size: 14px; font-weight: 650; }
.model-id, .model-boundary, .result-meta {
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 10.5px;
}
.model-id { margin-top: 4px; overflow-wrap: anywhere; }
.model-note { max-width: 72ch; margin-top: 12px; color: var(--ink-2); font-size: 13px; line-height: 1.55; }
.model-boundary { margin-top: 10px; }

.state-chip { text-transform: uppercase; letter-spacing: .03em; }
.state-chip.ready, .state-chip.pass { border-color: var(--mint-edge); background: var(--mint-surface); color: var(--green-ink); }
.state-chip.review { border-color: transparent; background: var(--warn-surface); color: var(--warn-ink); }
.state-chip.error { border-color: var(--danger-edge); background: var(--danger-surface); color: var(--danger-ink); }

.result-card { overflow: hidden; }
.result-head { padding: 18px 20px; }
.result-meta { margin-top: 5px; }
.result-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  border-top: 1px solid var(--line);
  background: var(--line);
}
.result-stat { min-width: 0; padding: 14px 18px; background: var(--paper-lift); }
.result-stat-value {
  overflow: hidden;
  color: var(--ink);
  font-family: var(--font-display);
  font-size: 20px;
  font-variant-numeric: tabular-nums;
  letter-spacing: -.022em;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result-stat-label {
  margin-top: 4px;
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 9.5px;
  letter-spacing: .05em;
  text-transform: uppercase;
}

.score-card { display: grid; grid-template-columns: 124px minmax(0, 1fr); gap: 22px; padding: 20px 22px; }
.score-value { font-family: var(--font-display); font-size: 42px; font-variant-numeric: tabular-nums; letter-spacing: -.04em; line-height: 1; }
.score-value span { color: var(--ink-3); font-size: 18px; }
.score-label { margin-top: 7px; color: var(--ink-3); font-family: var(--font-mono); font-size: 9.5px; text-transform: uppercase; }
.score-copy { align-self: center; }
.score-title { font-size: 15px; font-weight: 650; }
.score-description { margin-top: 6px; color: var(--ink-2); font-size: 13px; line-height: 1.52; }
.score-track { height: 5px; margin-top: 13px; overflow: hidden; border-radius: var(--r-pill); background: var(--paper-lift); }
.score-fill { height: 100%; border-radius: inherit; background: var(--forest); }
.score-counts { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 12px; }

.audit-item { padding: 14px 16px; margin-bottom: 8px; }
.audit-message { margin-top: 7px; color: var(--ink-2); font-size: 12.5px; line-height: 1.5; }
.audit-paths { margin-top: 8px; color: var(--ink-3); font-family: var(--font-mono); font-size: 9.5px; overflow-wrap: anywhere; }

/* Streamlit buttons */
.stButton > button, .stDownloadButton > button,
.stFormSubmitButton > button {
  min-height: 42px;
  padding-inline: 17px !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-pill) !important;
  background: var(--paper-lift) !important;
  box-shadow: none !important;
  color: var(--ink) !important;
  font-family: var(--font-sans) !important;
  font-size: 11.5px !important;
  font-weight: 680 !important;
  transition: background-color .22s var(--ease), border-color .22s var(--ease), color .22s var(--ease) !important;
}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover {
  border-color: var(--line-hover) !important;
  color: var(--ink) !important;
  transform: none !important;
}
.stButton > button:active, .stDownloadButton > button:active,
.stFormSubmitButton > button:active { transform: scale(.985) !important; }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {
  border-color: var(--forest) !important;
  background: var(--forest) !important;
  color: #f4f7f5 !important;
}
.stButton > button[kind="primary"] *, .stDownloadButton > button[kind="primary"] *,
.stFormSubmitButton > button[kind="primary"] * { color: #f4f7f5 !important; }
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {
  border-color: var(--forest-deep) !important;
  background: var(--forest-deep) !important;
}
.stButton > button:disabled, .stDownloadButton > button:disabled,
.stFormSubmitButton > button:disabled { opacity: .45 !important; cursor: not-allowed !important; }

/* Inputs and text areas */
[data-baseweb="input"] > div, [data-baseweb="textarea"] > div,
.stTextInput input, .stNumberInput input, .stTextArea textarea {
  min-height: 42px;
  border-color: var(--line) !important;
  border-radius: var(--r-field) !important;
  background: var(--paper-lift) !important;
  box-shadow: none !important;
  color: var(--ink) !important;
  font-family: var(--font-sans) !important;
  font-size: 13.5px !important;
}
.stTextArea textarea { min-height: 96px; line-height: 1.55; }
[data-baseweb="input"]:focus-within > div, [data-baseweb="textarea"]:focus-within > div,
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {
  border-color: var(--line-hover) !important;
  box-shadow: 0 0 0 3px rgba(194,156,224,.2) !important;
  outline: none !important;
}
input::placeholder, textarea::placeholder { color: var(--ink-3) !important; opacity: 1; }

/* Closed select trigger */
[data-baseweb="select"] > div {
  min-height: 42px !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-field) !important;
  background: var(--paper-lift) !important;
  box-shadow: none !important;
  color: var(--ink) !important;
  font-family: var(--font-sans) !important;
  font-size: 13.5px !important;
  transition: border-color .22s var(--ease), box-shadow .22s var(--ease) !important;
}
[data-baseweb="select"] > div:hover { border-color: var(--line-hover) !important; }
[data-baseweb="select"] > div:focus-within {
  border-color: var(--line-hover) !important;
  box-shadow: 0 0 0 3px rgba(194,156,224,.2) !important;
}
[data-baseweb="select"] svg { fill: var(--ink-3) !important; }
[data-baseweb="tag"] {
  border: 1px solid var(--purple-edge) !important;
  border-radius: var(--r-pill) !important;
  background: var(--lav-surface) !important;
  color: var(--lav-ink) !important;
}
[data-baseweb="tag"] span { color: var(--lav-ink) !important; }

/* Select portal menu, listbox and options */
[data-baseweb="popover"]:has([role="listbox"]) > div {
  overflow: hidden;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-card) !important;
  background: var(--paper-lift) !important;
  box-shadow: var(--shadow-float) !important;
}
[data-baseweb="popover"] [role="listbox"] { padding: 6px !important; background: var(--paper-lift) !important; }
[data-baseweb="popover"] [role="option"] {
  min-height: 36px !important;
  margin: 2px 0 !important;
  border-radius: 9px !important;
  color: var(--ink-2) !important;
  font-family: var(--font-sans) !important;
  font-size: 13px !important;
}
[data-baseweb="popover"] [role="option"]:hover { background: var(--surface) !important; color: var(--ink) !important; }
[data-baseweb="popover"] [role="option"][aria-selected="true"] { background: var(--lav-surface) !important; color: var(--lav-ink) !important; }

/* Labels and editable affordances */
[data-testid="stWidgetLabel"] p, .stTextInput label p, .stNumberInput label p,
.stTextArea label p, .stSelectbox label p, .stMultiSelect label p,
.stCheckbox label p, .stToggle label p {
  color: var(--ink-3) !important;
  font-family: var(--font-mono) !important;
  font-size: 10px !important;
  font-weight: 500 !important;
  letter-spacing: .06em !important;
  text-transform: uppercase !important;
}

/* Segmented controls and pills */
[data-testid="stSegmentedControl"] > div {
  gap: 4px !important;
  width: fit-content;
  padding: 4px !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-pill) !important;
  background: var(--surface) !important;
}
button[kind="segmented_control"], button[kind="segmented_controlActive"],
[data-testid="stSegmentedControl"] button {
  min-height: 34px !important;
  padding: 0 14px !important;
  border: 1px solid transparent !important;
  border-radius: var(--r-pill) !important;
  background: transparent !important;
  box-shadow: none !important;
  color: var(--ink-2) !important;
  font-size: 11.5px !important;
}
button[kind="segmented_controlActive"],
[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
  border-color: var(--purple-edge) !important;
  background: var(--lav-surface) !important;
  color: var(--lav-ink) !important;
}
[data-testid="stPills"] button {
  min-height: 32px !important;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-pill) !important;
  background: var(--paper-lift) !important;
  color: var(--ink-2) !important;
}
[data-testid="stPills"] button[aria-selected="true"],
[data-testid="stPills"] button[aria-pressed="true"],
button[kind="pillsActive"],
[data-testid="stBaseButton-pillsActive"] {
  border-color: var(--purple-edge) !important;
  background: var(--lav-surface) !important;
  color: var(--lav-ink) !important;
}
button[kind="pillsActive"] *,
[data-testid="stBaseButton-pillsActive"] * {
  color: var(--lav-ink) !important;
}

/* Toggles, checks and sliders */
[data-baseweb="checkbox"] span { border-color: var(--line) !important; }
[data-baseweb="checkbox"] input:checked + div, [data-baseweb="checkbox"] input:checked ~ div { background-color: var(--forest) !important; }
.stSlider [role="slider"] { background: var(--forest) !important; box-shadow: none !important; }
.stSlider [data-baseweb="slider"] > div > div { background: var(--line) !important; }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 4px;
  width: fit-content;
  margin-bottom: 16px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: var(--r-pill);
  background: var(--surface);
}
[data-testid="stTabs"] button[role="tab"] {
  min-height: 34px;
  padding: 0 14px;
  border-radius: var(--r-pill);
  color: var(--ink-2);
  font-size: 11.5px;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { background: var(--paper-lift); color: var(--ink); }
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] { display: none; }

/* Upload, forms, expanders and data */
[data-testid="stFileUploader"], [data-testid="stForm"],
[data-testid="stExpander"], [data-testid="stStatus"] {
  border: 1px solid var(--line) !important;
  border-radius: var(--r-card) !important;
  background: var(--surface) !important;
  box-shadow: none !important;
}
[data-testid="stFileUploader"] { padding: 10px 12px; }
[data-testid="stFileUploaderDropzone"] {
  min-height: 174px;
  border: 1px dashed var(--line) !important;
  border-radius: var(--r-band) !important;
  background: transparent !important;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--line-hover) !important; }
[data-testid="stForm"] { padding: 18px 20px; }
[data-testid="stExpander"] details, [data-testid="stStatus"] details { border: 0 !important; }
[data-testid="stDataFrame"], [data-testid="stDataEditor"] {
  overflow: hidden;
  border: 1px solid var(--line) !important;
  border-radius: var(--r-card) !important;
  background: var(--paper-lift) !important;
  box-shadow: none !important;
}
[data-testid="stImage"] img { border: 1px solid var(--line); border-radius: var(--r-card); background: var(--paper-lift); }

/* Keep only the source column containing the keyed preview in view. */
[data-testid="stColumn"]:has(.st-key-mizan_source_preview) {
  position: sticky;
  top: 20px;
  align-self: flex-start;
  max-height: calc(100vh - 40px);
  overflow: auto;
}

/* Native alerts */
[data-testid="stAlert"] {
  border: 1px solid var(--line) !important;
  border-left-width: 3px !important;
  border-radius: var(--r-field) !important;
  box-shadow: none !important;
}

.mizan-footer {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  margin-top: 46px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  color: var(--ink-3);
  font-family: var(--font-mono);
  font-size: 10px;
}

@media (max-width: 760px) {
  .block-container { padding: 1.2rem 1rem 4rem; }
  .mizan-topbar { align-items: flex-start; flex-wrap: wrap; }
  .mizan-topbar-meta { width: 100%; justify-content: flex-start; }
  .mizan-hero { padding: 23px 20px 25px; }
  .workflow-rail { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 0; }
  .workflow-step:nth-child(2)::after { display: none; }
  .workflow-step:not(:last-child)::after { margin: 0 7px; }
  .workflow-label { font-size: 10.5px; }
  .result-stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .score-card { grid-template-columns: 1fr; gap: 14px; }
  .mizan-footer { flex-direction: column; gap: 5px; }
  [data-testid="stTabs"] [data-baseweb="tab-list"] { width: 100%; overflow-x: auto; }
  [data-testid="stColumn"]:has(.st-key-mizan_source_preview) {
    position: static;
    max-height: none;
    overflow: visible;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
  }
}
</style>
"""


def inject_styles() -> None:
    """Apply the shared Mizan visual system to native Streamlit controls."""

    st.markdown(CSS, unsafe_allow_html=True)


def app_bar(
    region: str,
    live_ready: bool,
    serving_label: str,
    model_label: str,
) -> None:
    """Render the compact product identity and selected inference state."""

    state_class = "live" if live_ready else ""
    state = "Ready" if live_ready else "Preview"
    st.markdown(
        f"""
        <div class="mizan-topbar">
          <div class="mizan-wordmark">mizan<span>.</span></div>
          <div class="mizan-edition">Invoice intelligence</div>
          <div class="mizan-topbar-spacer"></div>
          <div class="mizan-topbar-meta">
            <span class="mizan-pill">OCI · {html.escape(region)}</span>
            <span class="mizan-pill">{html.escape(model_label)}</span>
            <span class="mizan-pill {state_class}"><span class="mizan-dot"></span>{html.escape(serving_label)} · {state}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    """Render the application header band for the start view."""

    st.markdown(
        """
        <div class="mizan-hero">
          <div class="mizan-hero-copy">
            <div class="mizan-eyebrow">OCI Generative AI · Invoice extraction</div>
            <h1>From invoice to verified record.</h1>
            <p>Upload a document, review fields beside their source page, and approve a finance-checked record. The model reads; deterministic rules decide what needs attention.</p>
            <div class="mizan-hero-meta">
              <span class="mizan-pill">Page-level evidence</span>
              <span class="mizan-pill">Deterministic checks</span>
              <span class="mizan-pill">Human approval</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_rail(active: int) -> None:
    """Show the four customer-facing stages without exposing backend noise."""

    labels = ("Set up", "Read", "Check", "Review")
    safe_active = min(max(active, 1), len(labels))
    cells = []
    for index, label in enumerate(labels, start=1):
        state = (
            "done" if index < safe_active else "active" if index == safe_active else ""
        )
        current = ' aria-current="step"' if state == "active" else ""
        cells.append(
            f'<div class="workflow-step {state}"{current}>'
            f'<span class="workflow-index">0{index}</span>'
            f'<span class="workflow-label">{html.escape(label)}</span></div>'
        )
    st.markdown(
        f'<div class="workflow-rail">{"".join(cells)}</div>',
        unsafe_allow_html=True,
    )


def section(kicker: str, title: str, description: str | None = None) -> None:
    """Render one restrained section heading with optional guidance."""

    detail = (
        f'<p class="section-description">{html.escape(description)}</p>'
        if description
        else ""
    )
    st.markdown(
        f'<div class="section-heading"><div class="section-kicker">{html.escape(kicker)}</div>'
        f"<h2>{html.escape(title)}</h2>{detail}</div>",
        unsafe_allow_html=True,
    )


def model_card(
    model_label: str,
    model_id: str,
    note: str,
    boundary: str,
    ready: bool,
) -> None:
    """Summarize the selected model lane and its configuration state."""

    state_class = "ready" if ready else "review"
    state = "Configured" if ready else "Setup needed"
    st.markdown(
        f"""
        <div class="model-card">
          <div class="model-top">
            <div>
              <div class="model-name">{html.escape(model_label)}</div>
              <div class="model-id">{html.escape(model_id)}</div>
            </div>
            <span class="state-chip {state_class}">{state}</span>
          </div>
          <div class="model-note">{html.escape(note)}</div>
          <div class="model-boundary">Processing boundary · {html.escape(boundary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def result_summary(run: ExtractionRun) -> None:
    """Summarize one run before the reviewer enters field-level detail."""

    if run.approval_status == "approved":
        state_class, state = "ready", "Approved"
    elif run.validation.errors:
        state_class, state = "error", "Blocked"
    elif run.validation.reviews:
        state_class, state = "review", "Review needed"
    else:
        state_class, state = "ready", "Ready to approve"

    mode = {
        "dac": "Imported DAC",
        "on_demand": "On-demand",
        "sample": "Guided sample",
    }[run.mode]
    elapsed = f"{run.elapsed_seconds:.1f}s" if run.elapsed_seconds is not None else "—"
    evidence = f"{run.validation.grounded_evidence}/{run.validation.total_evidence}"
    stats = (
        (str(run.page_count), "Pages"),
        (str(len(run.extraction.line_items)), "Line items"),
        (f"{run.validation.score}%", "Checks"),
        (evidence, "Grounded evidence"),
    )
    cells = "".join(
        f'<div class="result-stat"><div class="result-stat-value">{html.escape(value)}</div>'
        f'<div class="result-stat-label">{html.escape(label)}</div></div>'
        for value, label in stats
    )
    st.markdown(
        f"""
        <div class="result-card">
          <div class="result-head">
            <div>
              <div class="result-name">{html.escape(run.filename)}</div>
              <div class="result-meta">{html.escape(mode)} · {html.escape(run.model_label)} · {elapsed}</div>
            </div>
            <span class="state-chip {state_class}">{state}</span>
          </div>
          <div class="result-stats">{cells}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_card(run: ExtractionRun) -> None:
    """Explain deterministic readiness with one score and three counts."""

    report = run.validation
    title = (
        "Blocking checks remain"
        if report.errors
        else "Human review needed"
        if report.reviews
        else "Automated checks passed"
    )
    st.markdown(
        f"""
        <div class="score-card">
          <div>
            <div class="score-value">{report.score}<span>%</span></div>
            <div class="score-label">Review readiness</div>
          </div>
          <div class="score-copy">
            <div class="score-title">{title}</div>
            <div class="score-description">Rules, arithmetic, confidence, and page evidence determine readiness. Model confidence never overrides a failed check.</div>
            <div class="score-track"><div class="score-fill" style="width:{min(max(report.score, 0), 100)}%"></div></div>
            <div class="score-counts">
              <span class="state-chip pass">{report.passed} passed</span>
              <span class="state-chip review">{report.reviews} review</span>
              <span class="state-chip error">{report.errors} blocked</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def audit_item(check: ValidationCheck) -> None:
    """Render one validation finding with a consistent semantic state."""

    paths = " · ".join(check.field_paths)
    path_markup = (
        f'<div class="audit-paths">{html.escape(paths)}</div>' if paths else ""
    )
    st.markdown(
        f"""
        <div class="audit-item">
          <div class="audit-head">
            <div class="audit-name">{html.escape(check.label)}</div>
            <span class="state-chip {html.escape(check.severity)}">{html.escape(check.severity)}</span>
          </div>
          <div class="audit-message">{html.escape(check.message)}</div>
          {path_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )


def footer() -> None:
    """Close the experience with the asset and platform context."""

    st.markdown(
        '<div class="mizan-footer"><span>Reusable OCI Generative AI reference asset</span>'
        "<span>OCI Generative AI · Mizan Invoice Intelligence</span></div>",
        unsafe_allow_html=True,
    )
