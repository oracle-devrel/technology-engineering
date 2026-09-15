"""Streamlit review workspace for Mizan Invoice Intelligence.

Author: Ali Ottoman

What this module does
- Renders editable invoice fields, line items, checks, and audit evidence.
- Connects reviewer actions to pure review-domain transitions.
- Records approval and provides customer-ready audit exports.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, get_args

import pandas as pd
import streamlit as st

import config

from .documents import DocumentPages
from .exporters import runs_to_csv, runs_to_json, runs_to_xlsx
from .models import (
    CustomField,
    DocumentType,
    ExtractionRun,
    InvoiceExtraction,
    LineItem,
    TaxLine,
)
from .review import apply_batch_duplicate_checks, approve_run, revalidate_review
from .ui import audit_item, result_summary, score_card, section
from .validators import evidence_is_grounded

DOCUMENT_TYPES = get_args(DocumentType)


def _set_flash(kind: str, message: str) -> None:
    st.session_state.flash = {"kind": kind, "message": message}


def _clean_text(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None


def _restore_optional_int(value: Any) -> int | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    numeric = float(value)
    if not numeric.is_integer():
        raise ValueError(f"'{value}' must be a whole number.")
    return int(numeric)


def _frame_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    clean = frame.astype(object).where(pd.notna(frame), None)
    return clean.to_dict("records")


def _refresh_run(
    run_index: int,
    extraction: InvoiceExtraction,
    active_settings: config.Settings,
) -> None:
    """Persist one reviewer edit and refresh its batch-level checks."""

    runs: list[ExtractionRun] = list(st.session_state.runs)
    run = runs[run_index]
    document: DocumentPages = st.session_state.documents[run.filename]
    refreshed, changed_paths = revalidate_review(
        run,
        extraction,
        document,
        active_settings,
    )
    if not changed_paths:
        _set_flash("info", "No changes to save.")
        return

    runs[run_index] = refreshed
    st.session_state.runs = apply_batch_duplicate_checks(runs)
    _set_flash(
        "success",
        f"Saved {len(changed_paths)} change(s) and ran every check again.",
    )


def _approve_selected_run(run_index: int, reviewer: str) -> None:
    runs: list[ExtractionRun] = list(st.session_state.runs)
    runs[run_index] = approve_run(runs[run_index], reviewer)
    st.session_state.runs = runs
    _set_flash("success", f"Invoice approved by {reviewer.strip()}.")


def _field_form_payload(
    run: ExtractionRun,
    run_index: int,
) -> tuple[dict[str, Any], bool]:
    """Render the complete typed field form and return its edited payload."""

    extraction = run.extraction
    payload = extraction.model_dump(mode="python")
    form_version = len(run.passes)
    with st.form(f"fields_form_{run_index}_{form_version}"):
        document_left, document_right = st.columns(2)
        with document_left:
            document_type = st.selectbox(
                "Document type",
                DOCUMENT_TYPES,
                index=DOCUMENT_TYPES.index(extraction.document_type),
                format_func=lambda value: value.replace("_", " ").title(),
            )
        with document_right:
            language_options = list(
                dict.fromkeys(
                    [*extraction.source_languages, "English", "Arabic", "French"]
                )
            )
            source_languages = st.multiselect(
                "Source languages",
                language_options,
                default=extraction.source_languages,
                accept_new_options=True,
            )

        st.markdown("#### Parties")
        supplier_col, customer_col = st.columns(2, gap="large")
        with supplier_col:
            st.caption("SUPPLIER")
            supplier_name = st.text_input(
                "Supplier name", value=extraction.supplier.name or ""
            )
            supplier_address = st.text_area(
                "Supplier address", value=extraction.supplier.address or "", height=90
            )
            supplier_country = st.text_input(
                "Supplier country", value=extraction.supplier.country or ""
            )
            supplier_tax_id = st.text_input(
                "Supplier tax ID", value=extraction.supplier.tax_id or ""
            )
            supplier_registration_id = st.text_input(
                "Supplier registration ID",
                value=extraction.supplier.registration_id or "",
            )
        with customer_col:
            st.caption("CUSTOMER")
            customer_name = st.text_input(
                "Customer name", value=extraction.customer.name or ""
            )
            customer_address = st.text_area(
                "Customer address", value=extraction.customer.address or "", height=90
            )
            customer_country = st.text_input(
                "Customer country", value=extraction.customer.country or ""
            )
            customer_tax_id = st.text_input(
                "Customer tax ID", value=extraction.customer.tax_id or ""
            )
            customer_registration_id = st.text_input(
                "Customer registration ID",
                value=extraction.customer.registration_id or "",
            )

        st.markdown("#### Invoice")
        invoice_left, invoice_right = st.columns(2, gap="large")
        with invoice_left:
            invoice_number = st.text_input(
                "Invoice number", value=extraction.invoice.invoice_number or ""
            )
            invoice_date = st.text_input(
                "Invoice date",
                value=extraction.invoice.invoice_date or "",
                placeholder="YYYY-MM-DD",
            )
            due_date = st.text_input(
                "Due date",
                value=extraction.invoice.due_date or "",
                placeholder="YYYY-MM-DD",
            )
            purchase_order = st.text_input(
                "Purchase order", value=extraction.invoice.purchase_order or ""
            )
        with invoice_right:
            currency = st.text_input(
                "Currency",
                value=extraction.invoice.currency or "",
                max_chars=3,
                placeholder="USD",
            )
            payment_terms = st.text_input(
                "Payment terms", value=extraction.invoice.payment_terms or ""
            )
            contract_number = st.text_input(
                "Contract number", value=extraction.invoice.contract_number or ""
            )

        st.markdown("#### Payment")
        payment_left, payment_right = st.columns(2, gap="large")
        with payment_left:
            bank_name = st.text_input(
                "Bank name", value=extraction.payment.bank_name or ""
            )
            iban = st.text_input("IBAN", value=extraction.payment.iban or "")
        with payment_right:
            swift_bic = st.text_input(
                "SWIFT / BIC", value=extraction.payment.swift_bic or ""
            )
            payment_reference = st.text_input(
                "Payment reference",
                value=extraction.payment.payment_reference or "",
            )

        st.markdown("#### Totals")
        totals_left, totals_right = st.columns(2, gap="large")
        with totals_left:
            subtotal = st.number_input(
                "Subtotal", value=extraction.totals.subtotal, format="%.2f"
            )
            discount = st.number_input(
                "Discount", value=extraction.totals.discount, format="%.2f"
            )
            shipping = st.number_input(
                "Shipping", value=extraction.totals.shipping, format="%.2f"
            )
            other_charges = st.number_input(
                "Other charges",
                value=extraction.totals.other_charges,
                format="%.2f",
            )
        with totals_right:
            total_tax = st.number_input(
                "Total tax", value=extraction.totals.total_tax, format="%.2f"
            )
            total_amount = st.number_input(
                "Total amount", value=extraction.totals.total_amount, format="%.2f"
            )
            amount_paid = st.number_input(
                "Amount paid", value=extraction.totals.amount_paid, format="%.2f"
            )
            balance_due = st.number_input(
                "Balance due", value=extraction.totals.balance_due, format="%.2f"
            )

        st.markdown("#### Summary")
        summary = st.text_area(
            "English summary", value=extraction.summary_english, height=90
        )
        notes = st.text_area(
            "Notes",
            value="\n".join(extraction.notes),
            height=90,
            help="One note per line.",
        )

        edited_custom: pd.DataFrame | None = None
        if run.requested_custom_fields or extraction.custom_fields:
            st.markdown("#### Custom fields")
            st.caption(
                "Click a value to edit it. Add a row only when the contract needs it."
            )
            custom_df = pd.DataFrame(
                [item.model_dump(mode="python") for item in extraction.custom_fields],
                columns=list(CustomField.model_fields),
            )
            edited_custom = st.data_editor(
                custom_df,
                hide_index=True,
                width="stretch",
                num_rows="dynamic",
                disabled=["confidence"],
                column_config={
                    "name": st.column_config.TextColumn("Field"),
                    "value_original": st.column_config.TextColumn("Source value"),
                    "value_english": st.column_config.TextColumn("English value"),
                    "source_page": st.column_config.NumberColumn(
                        "Page", min_value=1, step=1, format="%d"
                    ),
                    "confidence": st.column_config.ProgressColumn(
                        "Confidence", min_value=0.0, max_value=1.0, format="percent"
                    ),
                },
                key=f"custom_editor_{run_index}_{form_version}",
            )

        save = st.form_submit_button(
            "Save changes & re-check",
            type="primary",
            width="stretch",
        )

    payload.update(
        {
            "document_type": document_type,
            "source_languages": list(source_languages),
            "supplier": {
                "name": _clean_text(supplier_name),
                "address": _clean_text(supplier_address),
                "country": _clean_text(supplier_country),
                "tax_id": _clean_text(supplier_tax_id),
                "registration_id": _clean_text(supplier_registration_id),
            },
            "customer": {
                "name": _clean_text(customer_name),
                "address": _clean_text(customer_address),
                "country": _clean_text(customer_country),
                "tax_id": _clean_text(customer_tax_id),
                "registration_id": _clean_text(customer_registration_id),
            },
            "invoice": {
                "invoice_number": _clean_text(invoice_number),
                "invoice_date": _clean_text(invoice_date),
                "due_date": _clean_text(due_date),
                "purchase_order": _clean_text(purchase_order),
                "currency": _clean_text(currency.upper()),
                "payment_terms": _clean_text(payment_terms),
                "contract_number": _clean_text(contract_number),
            },
            "payment": {
                "bank_name": _clean_text(bank_name),
                "iban": _clean_text(iban),
                "swift_bic": _clean_text(swift_bic),
                "payment_reference": _clean_text(payment_reference),
            },
            "totals": {
                "subtotal": subtotal,
                "discount": discount,
                "shipping": shipping,
                "other_charges": other_charges,
                "total_tax": total_tax,
                "total_amount": total_amount,
                "amount_paid": amount_paid,
                "balance_due": balance_due,
            },
            "summary_english": summary.strip(),
            "notes": [line.strip() for line in notes.splitlines() if line.strip()],
        }
    )
    if edited_custom is not None:
        fields: list[CustomField] = []
        for row in _frame_records(edited_custom):
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            row["name"] = name
            row["source_page"] = _restore_optional_int(row.get("source_page"))
            row["confidence"] = float(row.get("confidence") or 0.0)
            fields.append(CustomField.model_validate(row))
        payload["custom_fields"] = [item.model_dump(mode="python") for item in fields]
    return payload, save


def _render_fields_tab(
    run: ExtractionRun,
    run_index: int,
    active_settings: config.Settings,
) -> None:
    st.caption(
        "Every business value below is editable. Evidence and confidence stay locked "
        "to preserve provenance. Saving records the edit and runs every check again."
    )
    try:
        payload, save = _field_form_payload(run, run_index)
        if save:
            extraction = InvoiceExtraction.model_validate(payload)
            _refresh_run(run_index, extraction, active_settings)
            st.rerun()
    except Exception as exc:  # noqa: BLE001 - leave reviewer input available.
        st.error(f"Could not save these field changes: {exc}")


def _render_line_items_tab(
    run: ExtractionRun,
    run_index: int,
    active_settings: config.Settings,
) -> None:
    st.caption(
        "Edit any business or page cell. Confidence stays locked to preserve model "
        "provenance. Save once when the table is ready."
    )
    form_version = len(run.passes)
    line_df = pd.DataFrame(
        [item.model_dump(mode="python") for item in run.extraction.line_items],
        columns=list(LineItem.model_fields),
    )
    tax_df = pd.DataFrame(
        [item.model_dump(mode="python") for item in run.extraction.tax_lines],
        columns=list(TaxLine.model_fields),
    )
    with st.form(f"lines_form_{run_index}_{form_version}"):
        edited_lines = st.data_editor(
            line_df,
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            disabled=["confidence"],
            column_config={
                "line_number": st.column_config.NumberColumn(
                    "Line", min_value=1, step=1, format="%d"
                ),
                "description_original": st.column_config.TextColumn(
                    "Source description", width="large"
                ),
                "description_english": st.column_config.TextColumn(
                    "English description", width="large"
                ),
                "product_code": st.column_config.TextColumn("Product code"),
                "quantity": st.column_config.NumberColumn("Quantity", format="%.3f"),
                "unit": st.column_config.TextColumn("Unit"),
                "unit_price": st.column_config.NumberColumn(
                    "Unit price", format="%.2f"
                ),
                "discount": st.column_config.NumberColumn("Discount", format="%.2f"),
                "tax_rate": st.column_config.NumberColumn("Tax %", format="%.2f"),
                "amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                "source_page": st.column_config.NumberColumn(
                    "Page", min_value=1, step=1, format="%d"
                ),
                "confidence": st.column_config.ProgressColumn(
                    "Confidence", min_value=0.0, max_value=1.0, format="percent"
                ),
            },
            key=f"line_editor_{run_index}_{form_version}",
        )
        st.markdown("#### Tax breakdown")
        edited_tax = st.data_editor(
            tax_df,
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            column_config={
                "name": st.column_config.TextColumn("Tax"),
                "rate": st.column_config.NumberColumn("Rate %", format="%.3f"),
                "taxable_amount": st.column_config.NumberColumn(
                    "Taxable amount", format="%.2f"
                ),
                "tax_amount": st.column_config.NumberColumn(
                    "Tax amount", format="%.2f"
                ),
            },
            key=f"tax_editor_{run_index}_{form_version}",
        )
        save = st.form_submit_button(
            "Save line items & tax",
            type="primary",
            width="stretch",
        )

    if not save:
        return
    try:
        line_items: list[LineItem] = []
        for row in _frame_records(edited_lines):
            row["line_number"] = _restore_optional_int(row.get("line_number"))
            row["source_page"] = _restore_optional_int(row.get("source_page"))
            for field in (
                "quantity",
                "unit_price",
                "discount",
                "tax_rate",
                "amount",
                "confidence",
            ):
                row[field] = float(row[field]) if row.get(field) is not None else None
            row["confidence"] = row["confidence"] or 0.0
            line_items.append(LineItem.model_validate(row))

        tax_lines: list[TaxLine] = []
        for row in _frame_records(edited_tax):
            for field in ("rate", "taxable_amount", "tax_amount"):
                row[field] = float(row[field]) if row.get(field) is not None else None
            tax_lines.append(TaxLine.model_validate(row))

        payload = run.extraction.model_dump(mode="python")
        payload["line_items"] = [item.model_dump(mode="python") for item in line_items]
        payload["tax_lines"] = [item.model_dump(mode="python") for item in tax_lines]
        _refresh_run(
            run_index,
            InvoiceExtraction.model_validate(payload),
            active_settings,
        )
        st.rerun()
    except Exception as exc:  # noqa: BLE001 - leave the table available for repair.
        st.error(f"Could not save the line-item changes: {exc}")


def _render_checks_tab(run: ExtractionRun) -> None:
    score_card(run)
    actionable = [item for item in run.validation.checks if item.severity != "pass"]
    passed = [item for item in run.validation.checks if item.severity == "pass"]
    if actionable:
        st.markdown("#### Needs attention")
        for check in actionable:
            audit_item(check)
    else:
        st.success("Every automated check passed. Human approval is the final step.")
    with st.expander(f"Passed checks ({len(passed)})"):
        for check in passed:
            audit_item(check)


def _render_audit_tab(run: ExtractionRun, document: DocumentPages) -> None:
    with st.expander("Page-level evidence"):
        rows = []
        for item in run.extraction.evidence:
            page_text = (
                document.text_by_page[item.source_page - 1]
                if 0 < item.source_page <= len(document.text_by_page)
                else ""
            )
            if page_text:
                state = (
                    "Matched to PDF text"
                    if evidence_is_grounded(item.quote, page_text)
                    else "Quote mismatch"
                )
            else:
                state = "Visual-only evidence"
            rows.append(
                {
                    "Field": item.field_path,
                    "Page": item.source_page,
                    "Source quote": item.quote,
                    "Confidence": item.confidence,
                    "Status": state,
                }
            )
        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
            column_config={
                "Confidence": st.column_config.ProgressColumn(
                    min_value=0.0, max_value=1.0, format="percent"
                )
            },
        )

    with st.expander("Pass history"):
        st.dataframe(
            [
                {
                    "Pass": item.pass_number,
                    "Type": item.kind.title(),
                    "Score": f"{item.score}%",
                    "Issues": item.issues,
                    "Changed fields": ", ".join(item.changes) or "—",
                    "Note": item.note or "—",
                    "Actor": item.actor or "—",
                    "Recorded at": item.recorded_at or "—",
                }
                for item in run.passes
            ],
            hide_index=True,
            width="stretch",
        )

    if run.review_changes:
        with st.expander("Reviewer changes"):
            st.dataframe(
                [
                    {
                        "Field": item.field_path,
                        "Before": item.before,
                        "After": item.after,
                        "Changed at": item.changed_at,
                        "Evidence": item.evidence_disposition.replace("_", " ").title(),
                    }
                    for item in run.review_changes
                ],
                hide_index=True,
                width="stretch",
            )

    with st.expander("Raw structured record"):
        st.json(run.extraction.model_dump(mode="json"), expanded=1)


def _selector_label(runs: list[ExtractionRun], index: int) -> str:
    run = runs[index]
    status = (
        "Approved"
        if run.approval_status == "approved"
        else "Blocked"
        if run.validation.errors
        else "Needs review"
        if run.validation.reviews
        else "Ready"
    )
    identity = run.extraction.invoice.invoice_number or run.filename
    return (
        f"{identity} · {run.extraction.supplier.name or 'Unknown supplier'} · {status}"
    )


def _render_decision_and_exports(run: ExtractionRun, run_index: int) -> None:
    runs: list[ExtractionRun] = st.session_state.runs
    section(
        "Decision & export",
        "Finish the review",
        "Approval records the reviewer and timestamp. Any later edit reopens the invoice.",
    )
    if run.approval_status == "approved":
        st.success(f"Approved by {run.approved_by} at {run.approved_at}.")
    else:
        if run.validation.errors:
            st.error(
                f"{run.validation.errors} blocking check(s) remain. "
                "Correct the values in Fields or Line items, then save and re-check."
            )
        with st.form(f"approval_form_{run_index}_{len(run.passes)}"):
            reviewer = st.text_input(
                "Reviewer name", placeholder="Name recorded in the audit pack"
            )
            acknowledged = True
            if run.validation.reviews:
                acknowledged = st.checkbox(
                    f"I reviewed all {run.validation.reviews} flagged item(s)"
                )
            approve = st.form_submit_button(
                "Approve invoice",
                type="primary",
                width="stretch",
                disabled=bool(run.validation.errors),
            )
        if approve:
            if not acknowledged:
                st.error("Confirm that every flagged item was reviewed.")
            else:
                try:
                    _approve_selected_run(run_index, reviewer)
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    all_approved = all(item.approval_status == "approved" for item in runs)
    pack_state = "approved audit" if all_approved else "pending review"
    st.caption(f"Exports contain the complete batch and are marked: {pack_state}.")
    export_columns = st.columns(3)
    with export_columns[0]:
        st.download_button(
            "JSON record",
            data=runs_to_json(runs),
            file_name=f"mizan-invoice-{'audit' if all_approved else 'review'}.json",
            mime="application/json",
            width="stretch",
        )
    with export_columns[1]:
        st.download_button(
            "Line items CSV",
            data=runs_to_csv(runs),
            file_name="mizan-invoice-line-items.csv",
            mime="text/csv",
            width="stretch",
        )
    with export_columns[2]:
        st.download_button(
            "Excel audit pack",
            data=runs_to_xlsx(runs),
            file_name=f"mizan-invoice-{'audit' if all_approved else 'review'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width="stretch",
        )


def render_review(
    active_settings: config.Settings,
    on_new_extraction: Callable[[], None],
) -> None:
    """Render the complete source-to-approval review workspace."""

    runs: list[ExtractionRun] = st.session_state.runs
    section(
        "04 · Review",
        "Check the source, correct the record, then approve",
        "Only exceptions are highlighted. Business values are editable; evidence and "
        "confidence remain protected.",
    )
    selection_col, new_col = st.columns([4, 1])
    with selection_col:
        if len(runs) > 1:
            if st.session_state.get("review_run_index", 0) >= len(runs):
                st.session_state.review_run_index = 0
            run_index = st.selectbox(
                "Invoice",
                list(range(len(runs))),
                format_func=lambda index: _selector_label(runs, index),
                key="review_run_index",
            )
        else:
            run_index = 0
            st.caption(f"Reviewing · {_selector_label(runs, run_index)}")
    with new_col:
        st.button(
            "New extraction",
            width="stretch",
            on_click=on_new_extraction,
        )

    run = runs[run_index]
    document: DocumentPages = st.session_state.documents[run.filename]
    result_summary(run)

    source_col, review_col = st.columns([0.78, 1.42], gap="large")
    with source_col, st.container(key="mizan_source_preview"):
        st.markdown("#### Source document")
        if document.page_count > 1:
            page_number = st.selectbox(
                "Page",
                list(range(1, document.page_count + 1)),
                format_func=lambda page: f"Page {page} of {document.page_count}",
                key=f"source_page_{run_index}_{run.filename}",
            )
        else:
            page_number = 1
            st.caption("Page 1 of 1")
        st.image(
            document.images[page_number - 1],
            caption=f"Page {page_number} of {document.page_count}",
            width="stretch",
        )

    with review_col:
        fields_tab, lines_tab, checks_tab, audit_tab = st.tabs(
            ["Fields", "Line items", "Checks", "Audit details"]
        )
        with fields_tab:
            _render_fields_tab(run, run_index, active_settings)
        with lines_tab:
            _render_line_items_tab(run, run_index, active_settings)
        with checks_tab:
            _render_checks_tab(run)
        with audit_tab:
            _render_audit_tab(run, document)

    _render_decision_and_exports(run, run_index)
