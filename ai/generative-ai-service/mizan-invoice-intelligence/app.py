"""Mizan Invoice Intelligence — evidence-led invoice extraction on OCI.

Author: Ali Ottoman

What this app does
- Extracts multilingual invoices with an imported DAC or an on-demand model.
- Checks required fields, page evidence, dates, identifiers, and invoice arithmetic.
- Gives reviewers clear typed editors before approval and audit-pack export.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import streamlit as st

import config
from src.documents import DocumentPages, load_document
from src.extractor import InvoiceExtractor
from src.models import ExtractionRun
from src.review import apply_batch_duplicate_checks
from src.review_ui import render_review
from src.sample_data import build_sample_run
from src.ui import (
    app_bar,
    footer,
    hero,
    inject_styles,
    model_card,
    section,
    workflow_rail,
)
from src.validators import DEFAULT_REQUIRED_FIELDS

st.set_page_config(
    page_title="Mizan · Invoice Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

settings = config.load_settings()
inject_styles()


REQUIRED_FIELD_LABELS = {
    "invoice.invoice_number": "Invoice number",
    "invoice.invoice_date": "Invoice date",
    "supplier.name": "Supplier",
    "customer.name": "Customer",
    "invoice.currency": "Currency",
    "totals.total_amount": "Total amount",
}
CUSTOM_FIELD_SUGGESTIONS = (
    "Cost centre",
    "Contract reference",
    "Delivery note",
    "Incoterms",
    "Letter of credit",
    "Port of loading",
)

supported_on_demand_ids = {item.id for item in config.ON_DEMAND_MODELS}
default_on_demand_id = (
    settings.on_demand_model_id
    if settings.on_demand_model_id in supported_on_demand_ids
    else config.ON_DEMAND_MODELS[0].id
)
DEFAULTS = {
    "runs": [],
    "documents": {},
    "run_errors": [],
    "setup_source_mode": "Sample invoice",
    "setup_live_sample": False,
    "setup_inference_choice": (
        "On-demand" if settings.inference_mode == "on_demand" else "Imported DAC"
    ),
    "setup_on_demand_model_id": default_on_demand_id,
    "setup_required_fields": list(DEFAULT_REQUIRED_FIELDS),
    "setup_custom_fields": [],
    "setup_verify_output": True,
    "setup_confidence_floor": float(settings.confidence_floor),
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def _clear_results() -> None:
    """Return to setup while preserving the user's choices."""

    st.session_state.runs = []
    st.session_state.documents = {}
    st.session_state.run_errors = []
    st.session_state.pop("review_run_index", None)
    st.session_state.pop("flash", None)


def _sync_setup_value(name: str) -> None:
    """Copy a widget value into state that survives hidden screens."""

    st.session_state[f"setup_{name}"] = st.session_state[f"{name}_widget"]


def _seed_setup_widget(name: str) -> str:
    """Refresh a widget from its durable value before rendering it."""

    widget_key = f"{name}_widget"
    st.session_state[widget_key] = st.session_state[f"setup_{name}"]
    return widget_key


def _set_flash(kind: str, message: str) -> None:
    """Keep one confirmation visible across Streamlit's next rerun."""

    st.session_state.flash = {"kind": kind, "message": message}


def _render_flash() -> None:
    flash = st.session_state.pop("flash", None)
    if not flash:
        return
    renderer = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
    }.get(flash["kind"], st.info)
    renderer(flash["message"])


def _active_settings(
    base: config.Settings,
) -> tuple[config.Settings, config.ModelOption | None]:
    """Resolve the visible route and exact on-demand model selection."""

    base = replace(
        base,
        confidence_floor=float(st.session_state.setup_confidence_floor),
    )
    if st.session_state.setup_inference_choice == "Imported DAC":
        return replace(base, inference_mode="dac"), None
    option = next(
        (
            item
            for item in config.ON_DEMAND_MODELS
            if item.id == st.session_state.setup_on_demand_model_id
        ),
        config.ON_DEMAND_MODELS[0],
    )
    return (
        replace(
            base,
            inference_mode="on_demand",
            on_demand_model_id=option.id,
            on_demand_model_label=option.label,
        ),
        option,
    )


def _unique_filename(filename: str, used: set[str]) -> str:
    path = Path(filename)
    candidate = filename
    sequence = 2
    while candidate in used:
        candidate = f"{path.stem} ({sequence}){path.suffix}"
        sequence += 1
    used.add(candidate)
    return candidate


def _load(name: str, data: bytes, active_settings: config.Settings) -> DocumentPages:
    return load_document(
        name,
        data,
        dpi=active_settings.pdf_dpi,
        max_pages=active_settings.max_pages,
        max_dimension=active_settings.max_image_dimension,
        quality=active_settings.jpeg_quality,
    )


def _show_workflow(slot: Any, active: int) -> None:
    with slot.container():
        workflow_rail(active)


def _process_documents(
    source_documents: list[tuple[str, bytes]],
    active_settings: config.Settings,
    *,
    guided_sample: bool,
    custom_fields: list[str],
    required_fields: list[str],
    verify_output: bool,
    workflow_slot: Any,
) -> None:
    completed: list[ExtractionRun] = []
    rendered: dict[str, DocumentPages] = {}
    errors: list[str] = []
    extractor: InvoiceExtractor | None = None

    if not guided_sample:
        extractor = InvoiceExtractor(active_settings)

    with st.status("Reading invoice pages…", expanded=True) as status:
        _show_workflow(workflow_slot, 2)
        for index, (name, data) in enumerate(source_documents, start=1):
            status.write(f"{index}/{len(source_documents)} · Reading {name}")
            try:
                document = _load(name, data, active_settings)
                _show_workflow(workflow_slot, 3)
                status.update(label="Checking extracted fields and totals…")
                if extractor is None:
                    run = build_sample_run(
                        document,
                        active_settings,
                        custom_fields,
                        required_fields,
                    )
                else:
                    run = extractor.extract(
                        document,
                        custom_fields=custom_fields,
                        required_fields=required_fields,
                        verify=verify_output,
                    )
                completed.append(run)
                rendered[name] = document
            except Exception as exc:  # noqa: BLE001 - isolate each file in a batch.
                errors.append(f"{name}: {exc}")

        if completed:
            status.update(
                label=f"Analysis complete · {len(completed)} invoice(s)",
                state="complete",
                expanded=False,
            )
        else:
            status.update(label="Analysis did not complete", state="error")

    st.session_state.runs = apply_batch_duplicate_checks(completed)
    st.session_state.documents = rendered
    st.session_state.run_errors = errors
    if completed:
        _set_flash("success", "Analysis complete. Review the extracted values below.")
        st.rerun()
    for message in errors:
        st.error(message)


def _render_setup(active_settings: config.Settings, workflow_slot: Any) -> None:
    section(
        "02 · Invoice & policy",
        "Choose the document and the fields that matter",
        "The guided sample needs no OCI connection. Uploads always use the selected live model.",
    )
    st.segmented_control(
        "Document source",
        ["Sample invoice", "Upload invoices"],
        key=_seed_setup_widget("source_mode"),
        on_change=_sync_setup_value,
        args=("source_mode",),
        width="stretch",
    )
    source_mode = st.session_state.setup_source_mode

    source_documents: list[tuple[str, bytes]] = []
    if source_mode == "Sample invoice":
        if config.SAMPLE_INVOICE.exists():
            source_documents = [
                (config.SAMPLE_INVOICE.name, config.SAMPLE_INVOICE.read_bytes())
            ]
        with st.container(border=True):
            st.markdown("**Northstar synthetic demo invoice**")
            st.caption(
                "Clearly marked synthetic invoice · one page · four line items · "
                "recorded two-pass extraction"
            )
            if active_settings.is_live_ready:
                st.checkbox(
                    "Analyze the sample live with the selected model",
                    key=_seed_setup_widget("live_sample"),
                    on_change=_sync_setup_value,
                    args=("live_sample",),
                    help="Off uses the guided extraction. On makes a real OCI inference call.",
                )
            else:
                st.session_state.setup_live_sample = False
                st.session_state.live_sample_widget = False
                st.caption(
                    "Guided mode is selected because the live route is not configured."
                )
    else:
        uploads = st.file_uploader(
            "Upload PDF or image invoices",
            type=["pdf", "png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            max_upload_size=20,
            help="Up to 10 files. Each file is treated as a separate invoice.",
        )
        used_names: set[str] = set()
        for uploaded in (uploads or [])[:10]:
            name = _unique_filename(uploaded.name, used_names)
            source_documents.append((name, uploaded.getvalue()))
        if source_documents:
            st.caption(
                f"{len(source_documents)} file(s) ready · PDF, PNG, JPG, and WEBP supported"
            )
        elif not active_settings.is_live_ready:
            st.info(active_settings.configuration_hint)

    setup_left, setup_right = st.columns([1.15, 1], gap="large")
    with setup_left:
        st.markdown("#### Required fields")
        st.pills(
            "Required fields",
            list(REQUIRED_FIELD_LABELS),
            format_func=lambda path: REQUIRED_FIELD_LABELS[path],
            selection_mode="multi",
            key=_seed_setup_widget("required_fields"),
            on_change=_sync_setup_value,
            args=("required_fields",),
            label_visibility="collapsed",
            help="Missing selected fields become blocking checks.",
        )
        required_fields = list(st.session_state.setup_required_fields or [])
        st.caption("Click a field to make it required or optional.")

    with setup_right:
        st.markdown("#### Additional fields")
        st.multiselect(
            "Additional fields",
            options=list(CUSTOM_FIELD_SUGGESTIONS),
            key=_seed_setup_widget("custom_fields"),
            on_change=_sync_setup_value,
            args=("custom_fields",),
            accept_new_options=True,
            max_selections=12,
            label_visibility="collapsed",
            placeholder="Choose or type a field, then press Enter",
            help="Add customer-specific fields such as a cost centre or contract reference.",
        )
        st.caption("Choose a suggestion or type any field name and press Enter.")

    with st.expander("Advanced verification settings"):
        st.toggle(
            "Targeted verification pass",
            key=_seed_setup_widget("verify_output"),
            on_change=_sync_setup_value,
            args=("verify_output",),
            help="Re-read only fields that fail deterministic checks.",
        )
        st.slider(
            "Confidence review threshold",
            min_value=0.50,
            max_value=0.99,
            step=0.01,
            key=_seed_setup_widget("confidence_floor"),
            on_change=_sync_setup_value,
            args=("confidence_floor",),
            help="Values below this confidence are flagged for human review.",
        )

    needs_live_model = (
        source_mode == "Upload invoices" or st.session_state.setup_live_sample
    )
    live_route_blocked = needs_live_model and not active_settings.is_live_ready
    if source_documents and live_route_blocked:
        st.warning(active_settings.configuration_hint)

    analyze = st.button(
        "Analyze invoice",
        type="primary",
        width="stretch",
        disabled=not source_documents or live_route_blocked,
    )
    if not analyze:
        return

    try:
        _process_documents(
            source_documents,
            active_settings,
            guided_sample=not needs_live_model,
            custom_fields=list(st.session_state.setup_custom_fields),
            required_fields=required_fields,
            verify_output=bool(st.session_state.setup_verify_output),
            workflow_slot=workflow_slot,
        )
    except Exception as exc:  # noqa: BLE001 - keep configuration failures readable.
        message = f"Could not start analysis: {exc}"
        st.session_state.run_errors = [message]
        st.error(message)


# Resolve the current route before drawing the header.
active_settings, selected_on_demand = _active_settings(settings)
app_bar(
    active_settings.route_location,
    active_settings.is_live_ready,
    active_settings.serving_label,
    active_settings.active_model_label,
)
_render_flash()

has_results = bool(st.session_state.runs)
if not has_results:
    hero()

    section(
        "01 · Model",
        "Choose how Mizan reads the invoice",
        "Use the imported endpoint for dedicated OCI hosting, or compare two on-demand models.",
    )
    route_col, model_col = st.columns([1, 1], gap="large")
    with route_col:
        st.segmented_control(
            "Inference path",
            ["Imported DAC", "On-demand"],
            key=_seed_setup_widget("inference_choice"),
            on_change=_sync_setup_value,
            args=("inference_choice",),
            width="stretch",
            help="Dedicated imported endpoint or pay-as-you-go OCI model access.",
        )
    with model_col:
        if st.session_state.setup_inference_choice == "On-demand":
            st.selectbox(
                "On-demand model",
                [item.id for item in config.ON_DEMAND_MODELS],
                format_func=lambda model_id: next(
                    item.label
                    for item in config.ON_DEMAND_MODELS
                    if item.id == model_id
                ),
                key=_seed_setup_widget("on_demand_model_id"),
                on_change=_sync_setup_value,
                args=("on_demand_model_id",),
                help="Gemini is recommended for document extraction; Grok is the challenger.",
            )
        else:
            st.caption("IMPORTED MODEL")
            st.markdown(f"**{active_settings.active_model_label}**")
            st.caption("The deployed endpoint selects the runtime model.")

    model_note = (
        selected_on_demand.note
        if selected_on_demand is not None
        else "Private imported endpoint · predictable dedicated capacity"
    )
    model_card(
        active_settings.active_model_label,
        active_settings.active_model_id,
        model_note,
        active_settings.processing_boundary,
        active_settings.is_live_ready,
    )

workflow_slot = st.empty()
_show_workflow(workflow_slot, 4 if has_results else 1)

if st.session_state.run_errors:
    st.warning("Some files did not complete. Successful invoices remain available.")
    with st.expander("Processing details"):
        for message in st.session_state.run_errors:
            st.write(f"- {message}")

if has_results:
    render_review(active_settings, _clear_results)
else:
    _render_setup(active_settings, workflow_slot)

footer()
