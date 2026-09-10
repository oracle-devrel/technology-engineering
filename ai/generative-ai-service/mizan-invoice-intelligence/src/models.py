"""Validated contracts for invoice extraction and review.

Author: Ali Ottoman
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Reject fields outside the customer-facing contract."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, strict=True)


class Party(StrictModel):
    name: str | None
    address: str | None
    country: str | None
    tax_id: str | None
    registration_id: str | None


class InvoiceHeader(StrictModel):
    invoice_number: str | None
    invoice_date: str | None
    due_date: str | None
    purchase_order: str | None
    currency: str | None
    payment_terms: str | None
    contract_number: str | None


class PaymentDetails(StrictModel):
    bank_name: str | None
    iban: str | None
    swift_bic: str | None
    payment_reference: str | None


class LineItem(StrictModel):
    line_number: int | None = Field(ge=1)
    description_original: str | None
    description_english: str | None
    product_code: str | None
    quantity: float | None
    unit: str | None
    unit_price: float | None
    discount: float | None
    tax_rate: float | None = Field(description="Printed percentage points; 5% is 5.0.")
    amount: float | None
    source_page: int | None = Field(ge=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> object:
        if isinstance(value, (int, float)) and value > 1:
            return value / 100
        return value


class TaxLine(StrictModel):
    name: str | None
    rate: float | None = Field(description="Printed percentage points; 5% is 5.0.")
    taxable_amount: float | None
    tax_amount: float | None


class Totals(StrictModel):
    subtotal: float | None
    discount: float | None
    shipping: float | None
    other_charges: float | None
    total_tax: float | None
    total_amount: float | None
    amount_paid: float | None
    balance_due: float | None


class CustomField(StrictModel):
    name: str
    value_original: str | None
    value_english: str | None
    source_page: int | None = Field(ge=1)
    confidence: float = Field(ge=0, le=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> object:
        if isinstance(value, (int, float)) and value > 1:
            return value / 100
        return value


class Evidence(StrictModel):
    field_path: str = Field(
        description=(
            "Exact dotted path in this schema, for example "
            "invoice.invoice_number, supplier.name, customer.name, or totals.total_amount."
        )
    )
    source_page: int = Field(ge=1)
    quote: str = Field(
        min_length=1,
        description="Short verbatim source text that contains the extracted field value.",
    )
    confidence: float = Field(ge=0, le=1)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> object:
        if isinstance(value, (int, float)) and value > 1:
            return value / 100
        return value


DocumentType = Literal["invoice", "credit_note", "debit_note", "not_invoice", "unknown"]


class InvoiceExtraction(StrictModel):
    document_type: DocumentType
    source_languages: list[str]
    supplier: Party
    customer: Party
    invoice: InvoiceHeader
    payment: PaymentDetails
    line_items: list[LineItem]
    tax_lines: list[TaxLine]
    totals: Totals
    custom_fields: list[CustomField]
    notes: list[str]
    summary_english: str
    evidence: list[Evidence]
    overall_confidence: float = Field(ge=0, le=1)

    @field_validator("overall_confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: object) -> object:
        if isinstance(value, (int, float)) and value > 1:
            return value / 100
        return value


Severity = Literal["pass", "review", "error"]


class ValidationCheck(StrictModel):
    code: str
    label: str
    severity: Severity
    message: str
    field_paths: list[str] = Field(default_factory=list)


class ValidationReport(StrictModel):
    score: int
    passed: int
    reviews: int
    errors: int
    grounded_evidence: int
    total_evidence: int
    checks: list[ValidationCheck]


class PassRecord(StrictModel):
    pass_number: int
    kind: Literal["extract", "verify", "sample", "review", "approve", "invalidate"]
    score: int
    issues: int
    changes: list[str] = Field(default_factory=list)
    note: str | None = None
    actor: str | None = None
    recorded_at: str | None = None


class ReviewChange(StrictModel):
    field_path: str
    before: str
    after: str
    changed_at: str
    evidence_disposition: Literal["not_linked", "source_quote_overridden"]


class ExtractionRun(StrictModel):
    filename: str
    page_count: int
    mode: Literal["dac", "on_demand", "sample"]
    model_label: str
    elapsed_seconds: float | None
    input_tokens: int | None
    output_tokens: int | None
    requested_custom_fields: list[str] = Field(default_factory=list)
    required_field_paths: list[str] = Field(default_factory=list)
    extraction: InvoiceExtraction
    validation: ValidationReport
    passes: list[PassRecord]
    review_changes: list[ReviewChange] = Field(default_factory=list)
    approval_status: Literal["pending", "approved"] = "pending"
    approved_by: str | None = None
    approved_at: str | None = None
