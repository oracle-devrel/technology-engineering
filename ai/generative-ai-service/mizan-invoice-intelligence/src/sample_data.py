"""Deterministic output for the bundled synthetic invoice preview.

Author: Ali Ottoman
"""

from __future__ import annotations

from copy import deepcopy

import config

from .documents import DocumentPages
from .models import ExtractionRun, InvoiceExtraction, PassRecord
from .validators import (
    DEFAULT_REQUIRED_FIELDS,
    validate_invoice,
    with_verification_review,
)

SAMPLE_PAYLOAD = {
    "document_type": "invoice",
    "source_languages": ["English"],
    "supplier": {
        "name": "DEMO NORTHSTAR COMPONENTS LLC",
        "address": "100 Demo Avenue, Example City, United Arab Emirates",
        "country": "United Arab Emirates",
        "tax_id": "100000000000001",
        "registration_id": None,
    },
    "customer": {
        "name": "EXAMPLE HORIZON INDUSTRIES",
        "address": "200 Sample Road, Test District, Cairo, Egypt",
        "country": "Egypt",
        "tax_id": "000000000000002",
        "registration_id": None,
    },
    "invoice": {
        "invoice_number": "DEMO-INV-2026-001",
        "invoice_date": "2026-09-01",
        "due_date": "2026-10-01",
        "purchase_order": "DEMO-PO-1001",
        "currency": "USD",
        "payment_terms": "30 days",
        "contract_number": "DEMO-CONTRACT-01",
    },
    "payment": {
        "bank_name": "Fictional Demo Bank",
        "iban": None,
        "swift_bic": "DEMOXXXX",
        "payment_reference": "DEMO-PAY-001",
    },
    "line_items": [
        {
            "line_number": 1,
            "description_original": "Demo pressure sensor, 0-10 bar",
            "description_english": "Demo pressure sensor, 0-10 bar",
            "product_code": "DEMO-SEN-01",
            "quantity": 10,
            "unit": "pcs",
            "unit_price": 125,
            "discount": 0,
            "tax_rate": 0,
            "amount": 1250,
            "source_page": 1,
            "confidence": 0.99,
        },
        {
            "line_number": 2,
            "description_original": "Demo calibration service",
            "description_english": "Demo calibration service",
            "product_code": "DEMO-SVC-02",
            "quantity": 2,
            "unit": "svc",
            "unit_price": 350,
            "discount": 0,
            "tax_rate": 0,
            "amount": 700,
            "source_page": 1,
            "confidence": 0.99,
        },
        {
            "line_number": 3,
            "description_original": "Demo protective transport case",
            "description_english": "Demo protective transport case",
            "product_code": "DEMO-CASE-03",
            "quantity": 5,
            "unit": "pcs",
            "unit_price": 80,
            "discount": 0,
            "tax_rate": 0,
            "amount": 400,
            "source_page": 1,
            "confidence": 0.98,
        },
        {
            "line_number": 4,
            "description_original": "Demo documentation pack",
            "description_english": "Demo documentation pack",
            "product_code": "DEMO-DOC-04",
            "quantity": 1,
            "unit": "pack",
            "unit_price": 150,
            "discount": 0,
            "tax_rate": 0,
            "amount": 150,
            "source_page": 1,
            "confidence": 0.98,
        },
    ],
    "tax_lines": [
        {
            "name": "VAT - synthetic export",
            "rate": 0,
            "taxable_amount": 2500,
            "tax_amount": 0,
        }
    ],
    "totals": {
        "subtotal": 2500,
        "discount": -50,
        "shipping": 120,
        "other_charges": 30,
        "total_tax": 0,
        "total_amount": 2600,
        "amount_paid": 0,
        "balance_due": 2600,
    },
    "custom_fields": [],
    "notes": [
        "Synthetic demonstration document. No goods, services, or payment are due.",
        "All parties, identifiers, and banking details are fictional.",
    ],
    "summary_english": "A synthetic USD 2,600 demo invoice for sample industrial equipment.",
    "evidence": [
        {
            "field_path": "invoice.invoice_number",
            "source_page": 1,
            "quote": "DEMO-INV-2026-001",
            "confidence": 0.99,
        },
        {
            "field_path": "invoice.invoice_date",
            "source_page": 1,
            "quote": "1 September 2026",
            "confidence": 0.99,
        },
        {
            "field_path": "invoice.currency",
            "source_page": 1,
            "quote": "Currency\nUSD",
            "confidence": 0.99,
        },
        {
            "field_path": "invoice.purchase_order",
            "source_page": 1,
            "quote": "DEMO-PO-1001",
            "confidence": 0.99,
        },
        {
            "field_path": "supplier.name",
            "source_page": 1,
            "quote": "DEMO NORTHSTAR COMPONENTS LLC",
            "confidence": 0.99,
        },
        {
            "field_path": "customer.name",
            "source_page": 1,
            "quote": "EXAMPLE HORIZON INDUSTRIES",
            "confidence": 0.99,
        },
        {
            "field_path": "totals.total_amount",
            "source_page": 1,
            "quote": "2,600.00",
            "confidence": 0.99,
        },
    ],
    "overall_confidence": 0.99,
}


SAMPLE_CUSTOM_FIELDS = {
    "incoterms": "DAP Example City (demo)",
    "letter of credit": "DEMO-LC-0001",
    "port of loading": "Example Port Alpha",
    "port of discharge": "Example Port Beta",
    "vessel/voyage": "MV Sample Star / V.001",
    "country of origin": "Fictional Demo Origin",
    "gross weight": "500 kg",
}


def build_sample_run(
    document: DocumentPages,
    settings: config.Settings,
    custom_fields: list[str] | None = None,
    required_fields: list[str] | None = None,
) -> ExtractionRun:
    """Replay an honest two-pass sample through the live validation rules."""

    requested = custom_fields or []
    required = required_fields
    final_payload = deepcopy(SAMPLE_PAYLOAD)
    final_payload["custom_fields"] = [
        {
            "name": name,
            "value_original": SAMPLE_CUSTOM_FIELDS.get(name.casefold()),
            "value_english": SAMPLE_CUSTOM_FIELDS.get(name.casefold()),
            "source_page": 1 if name.casefold() in SAMPLE_CUSTOM_FIELDS else None,
            "confidence": 0.99 if name.casefold() in SAMPLE_CUSTOM_FIELDS else 0.0,
        }
        for name in requested
    ]
    first_payload = deepcopy(final_payload)
    first_payload["line_items"][0]["amount"] = 1_200
    first = InvoiceExtraction.model_validate(first_payload)
    first_report = validate_invoice(
        first,
        document.text_by_page,
        tolerance=settings.tolerance,
        confidence_floor=settings.confidence_floor,
        requested_custom_fields=requested,
        required_fields=required,
    )
    extraction = InvoiceExtraction.model_validate(final_payload)
    report = validate_invoice(
        extraction,
        document.text_by_page,
        tolerance=settings.tolerance,
        confidence_floor=settings.confidence_floor,
        requested_custom_fields=requested,
        required_fields=required,
    )
    report = with_verification_review(report, ["line_items[0].amount"])
    return ExtractionRun(
        filename=document.filename,
        page_count=document.page_count,
        mode="sample",
        model_label="Recorded two-pass extraction",
        elapsed_seconds=None,
        input_tokens=None,
        output_tokens=None,
        requested_custom_fields=requested,
        required_field_paths=(
            list(required) if required is not None else list(DEFAULT_REQUIRED_FIELDS)
        ),
        extraction=extraction,
        validation=report,
        passes=[
            PassRecord(
                pass_number=1,
                kind="sample",
                score=first_report.score,
                issues=first_report.reviews + first_report.errors,
                note="Recorded first pass contains one plausible line-amount digit error.",
            ),
            PassRecord(
                pass_number=2,
                kind="verify",
                score=report.score,
                issues=report.reviews + report.errors,
                changes=["line_items[0].amount"],
                note="Recorded targeted re-read restored the printed amount.",
            ),
        ],
    )
