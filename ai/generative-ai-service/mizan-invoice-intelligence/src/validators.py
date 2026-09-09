"""Deterministic checks that decide what needs human review.

Author: Ali Ottoman
"""

from __future__ import annotations

import re
from calendar import month_abbr, month_name
from datetime import date
from decimal import Decimal, InvalidOperation

from .models import InvoiceExtraction, ValidationCheck, ValidationReport
from .paths import flatten_values

DEFAULT_REQUIRED_FIELDS = (
    "invoice.invoice_number",
    "invoice.invoice_date",
    "supplier.name",
    "customer.name",
    "invoice.currency",
    "totals.total_amount",
)


def _close(left: float, right: float, tolerance: float) -> bool:
    """Compare displayed amounts with an absolute currency-unit tolerance."""

    difference = abs(Decimal(str(left)) - Decimal(str(right)))
    return difference <= Decimal(str(tolerance))


def _add(
    checks: list[ValidationCheck],
    code: str,
    label: str,
    ok: bool,
    success: str,
    failure: str,
    fields: list[str],
    severity: str = "error",
) -> None:
    checks.append(
        ValidationCheck(
            code=code,
            label=label,
            severity="pass" if ok else severity,
            message=success if ok else failure,
            field_paths=fields,
        )
    )


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def evidence_is_grounded(quote: str, page_text: str) -> bool:
    """Match an evidence quote after normalizing whitespace and case."""

    return bool(
        quote and page_text and _normalize_text(quote) in _normalize_text(page_text)
    )


def _quote_supports_value(quote: str, value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        expected = Decimal(str(value))
        numeric_tokens = re.findall(
            r"[-+]?(?:\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.\d+)?",
            quote,
        )
        for token in numeric_tokens:
            normalized = token.replace(",", "").replace(" ", "")
            try:
                if Decimal(normalized) == expected:
                    return True
            except InvalidOperation:
                continue
        return False
    if isinstance(value, str) and _is_iso_date(value):
        parsed = date.fromisoformat(value)
        variants = {
            value,
            f"{parsed.year}/{parsed.month:02d}/{parsed.day:02d}",
            f"{parsed.day:02d}/{parsed.month:02d}/{parsed.year}",
            f"{parsed.day:02d}-{parsed.month:02d}-{parsed.year}",
            f"{parsed.day} {month_name[parsed.month]} {parsed.year}",
            f"{parsed.day} {month_abbr[parsed.month]} {parsed.year}",
        }
        normalized_quote = _normalize_text(quote)
        return any(
            _normalize_text(candidate) in normalized_quote for candidate in variants
        )
    normalized_quote = _normalize_text(quote)
    normalized_value = _normalize_text(str(value))
    if not normalized_value:
        return False
    return bool(
        re.search(
            rf"(?<!\w){re.escape(normalized_value)}(?!\w)",
            normalized_quote,
        )
    )


def _evidence_label_conflicts(field_path: str, quote: str) -> bool:
    """Reject invoice-number evidence that is clearly labelled as a PO."""

    if field_path != "invoice.invoice_number":
        return False
    normalized = _normalize_text(quote)
    invoice_label = bool(
        re.search(r"\binvoice\b|\binv\s*(?:no\.?|number|#)", normalized)
        or "رقم الفاتورة" in normalized
    )
    purchase_order_label = bool(
        re.search(
            r"\bpurchase\s+order\b|\bp\.?\s*o\.?\s*(?:no\.?|number|#)",
            normalized,
        )
        or "رقم أمر الشراء" in normalized
        or "رقم امر الشراء" in normalized
    )
    return purchase_order_label and not invoice_label


def validate_invoice(
    data: InvoiceExtraction,
    text_by_page: list[str],
    *,
    tolerance: float,
    confidence_floor: float,
    requested_custom_fields: list[str] | None = None,
    required_fields: list[str] | None = None,
) -> ValidationReport:
    """Run business, format, and evidence checks without changing source values."""

    checks: list[ValidationCheck] = []
    accepted_types = {"invoice", "credit_note", "debit_note"}
    document_ok = data.document_type in accepted_types
    _add(
        checks,
        (
            "document_type_non_invoice"
            if data.document_type == "not_invoice"
            else "document_type"
        ),
        "Invoice document class",
        document_ok,
        f"Document classified as {data.document_type.replace('_', ' ')}.",
        (
            "This file is not classified as an invoice, credit note, or debit note; "
            "do not post it to accounts payable."
        ),
        ["document_type"],
    )

    critical = {
        "invoice.invoice_number": data.invoice.invoice_number,
        "invoice.invoice_date": data.invoice.invoice_date,
        "supplier.name": data.supplier.name,
        "customer.name": data.customer.name,
        "invoice.currency": data.invoice.currency,
        "totals.total_amount": data.totals.total_amount,
    }
    required = set(
        DEFAULT_REQUIRED_FIELDS if required_fields is None else required_fields
    )
    missing = [
        path
        for path, value in critical.items()
        if path in required
        and (value is None or (isinstance(value, str) and not value.strip()))
    ]
    _add(
        checks,
        "critical_fields",
        "Core fields present",
        not missing,
        (
            f"All {len(required & critical.keys())} configured required field(s) "
            "were captured."
        ),
        f"Missing: {', '.join(missing)}.",
        missing,
    )

    requested_names = {
        _normalize_text(name)
        for name in (requested_custom_fields or [])
        if name.strip()
    }
    returned_list = [
        _normalize_text(item.name) for item in data.custom_fields if item.name.strip()
    ]
    returned_names = set(returned_list)
    missing_custom = sorted(requested_names - returned_names)
    unexpected_custom = sorted(returned_names - requested_names)
    duplicate_custom = sorted(
        name for name in returned_names if returned_list.count(name) > 1
    )
    custom_contract_ok = not (missing_custom or unexpected_custom or duplicate_custom)
    custom_issues = []
    if missing_custom:
        custom_issues.append(f"missing: {', '.join(missing_custom)}")
    if unexpected_custom:
        custom_issues.append(f"unexpected: {', '.join(unexpected_custom)}")
    if duplicate_custom:
        custom_issues.append(f"duplicated: {', '.join(duplicate_custom)}")
    _add(
        checks,
        "custom_field_contract",
        "Requested custom fields returned",
        custom_contract_ok,
        "Every requested custom field has a response object.",
        f"Custom-field contract mismatch ({'; '.join(custom_issues)}).",
        ["custom_fields"],
    )

    currency = data.invoice.currency or ""
    valid_currency = not currency or bool(re.fullmatch(r"[A-Z]{3}", currency))
    _add(
        checks,
        "currency_format",
        "Currency format",
        valid_currency,
        "Currency uses an ISO-style three-letter code.",
        f"'{currency}' is not a three-letter currency code.",
        ["invoice.currency"],
        "review",
    )

    dated = [data.invoice.invoice_date, data.invoice.due_date]
    valid_dates = all(value is None or _is_iso_date(value) for value in dated)
    _add(
        checks,
        "date_format",
        "Date normalization",
        valid_dates,
        "Captured dates use YYYY-MM-DD.",
        "One or more captured dates are not valid YYYY-MM-DD values.",
        ["invoice.invoice_date", "invoice.due_date"],
        "review",
    )

    chronology_ok = _chronology_ok(data.invoice.invoice_date, data.invoice.due_date)
    _add(
        checks,
        "date_order",
        "Due-date chronology",
        chronology_ok,
        "The due date is not earlier than the invoice date.",
        "The due date is earlier than the invoice date.",
        ["invoice.invoice_date", "invoice.due_date"],
        "review",
    )

    invoice_number = _normalize_text(data.invoice.invoice_number or "")
    identifiers = {
        "invoice.purchase_order": data.invoice.purchase_order,
        "invoice.contract_number": data.invoice.contract_number,
        "payment.payment_reference": data.payment.payment_reference,
    }
    collisions = [
        path
        for path, value in identifiers.items()
        if invoice_number and _normalize_text(value or "") == invoice_number
    ]
    _add(
        checks,
        "identifier_collision",
        "Invoice identifier distinct",
        not collisions,
        "The invoice number is distinct from other captured references.",
        (
            "The invoice number duplicates another reference; confirm its printed "
            f"label ({', '.join(collisions)})."
        ),
        ["invoice.invoice_number", *collisions],
        "review",
    )

    page_count = len(text_by_page)
    invalid_source_pages = [
        f"line_items[{index}].source_page"
        for index, item in enumerate(data.line_items)
        if item.source_page is None or not 1 <= item.source_page <= page_count
    ]
    invalid_source_pages.extend(
        f"custom_fields[{index}].source_page"
        for index, item in enumerate(data.custom_fields)
        if (
            item.value_original not in (None, "")
            or item.value_english not in (None, "")
        )
        and (item.source_page is None or not 1 <= item.source_page <= page_count)
    )
    _add(
        checks,
        "source_pages",
        "Source pages valid",
        not invalid_source_pages,
        "Line items and populated custom fields point to valid pages.",
        f"Invalid source page on: {', '.join(invalid_source_pages)}.",
        invalid_source_pages,
        "review",
    )

    missing_descriptions = [
        f"line_items[{index}].description_original"
        for index, item in enumerate(data.line_items)
        if not (item.description_original or "").strip()
        and not (item.description_english or "").strip()
    ]
    _add(
        checks,
        "line_descriptions",
        "Line descriptions present",
        bool(data.line_items) and not missing_descriptions,
        "Every line item has a source or English description.",
        "One or more line items has no usable description.",
        missing_descriptions or (["line_items"] if not data.line_items else []),
    )

    line_numbers = [item.line_number for item in data.line_items]
    numbered = [value for value in line_numbers if value is not None]
    line_ids_ok = len(numbered) == len(line_numbers) and len(set(numbered)) == len(
        numbered
    )
    line_number_paths = [
        f"line_items[{index}].line_number" for index in range(len(data.line_items))
    ]
    _add(
        checks,
        "line_identifiers",
        "Line identifiers distinct",
        line_ids_ok,
        "Line numbers are present and distinct.",
        "One or more line numbers is missing or duplicated; confirm the row sequence.",
        line_number_paths or ["line_items"],
        "review",
    )

    amounts = [item.amount for item in data.line_items if item.amount is not None]
    subtotal = data.totals.subtotal
    complete_amounts = len(amounts) == len(data.line_items)
    if data.line_items and complete_amounts and subtotal is not None:
        line_sum = sum(amounts)
        lines_ok = _close(line_sum, subtotal, tolerance)
        line_message = (
            f"Line items sum to {line_sum:,.2f}; subtotal is {subtotal:,.2f}."
        )
    else:
        lines_ok = False
        line_message = (
            "Line items, every line amount, and the subtotal are required to reconcile."
        )
    _add(
        checks,
        "line_sum",
        "Line items reconcile",
        lines_ok,
        line_message,
        line_message,
        [
            *(f"line_items[{index}].amount" for index in range(len(data.line_items))),
            "totals.subtotal",
        ],
    )

    missing_line_amounts = [
        f"line_items[{index}].amount"
        for index, item in enumerate(data.line_items)
        if item.amount is None
    ]
    _add(
        checks,
        "line_amounts",
        "Line amounts present",
        bool(data.line_items) and not missing_line_amounts,
        "Every captured line has a printed amount.",
        "One or more line amounts are missing.",
        missing_line_amounts or (["line_items"] if not data.line_items else []),
    )

    line_math_failures: list[int] = []
    incomplete_operands: list[int] = []
    for index, item in enumerate(data.line_items):
        if (item.quantity is None) != (item.unit_price is None):
            incomplete_operands.append(index)
            continue
        if item.quantity is None or item.amount is None:
            continue
        expected = (item.quantity or 0) * (item.unit_price or 0) + (item.discount or 0)
        if not _close(expected, item.amount or 0, tolerance):
            line_math_failures.append(index)
    math_indexes = [*line_math_failures, *incomplete_operands]
    math_rows = [f"line_items[{index}]" for index in math_indexes]
    math_fields = [
        f"line_items[{index}].{field}"
        for index in math_indexes
        for field in ("quantity", "unit_price", "discount", "amount")
    ]
    if line_math_failures:
        math_message = f"Quantity × price differs on {', '.join(math_rows)}."
    elif incomplete_operands:
        math_message = (
            "Quantity or unit price is missing on "
            f"{', '.join(math_rows)}; confirm visually."
        )
    else:
        math_message = "Every applicable line recomputes within tolerance."
    _add(
        checks,
        "line_math",
        "Quantity × price",
        not math_fields,
        math_message,
        math_message,
        math_fields,
        "error" if line_math_failures else "review",
    )

    totals = data.totals
    total_inputs = (
        totals.subtotal,
        totals.discount,
        totals.shipping,
        totals.other_charges,
        totals.total_tax,
        totals.total_amount,
    )
    if totals.subtotal is not None and totals.total_amount is not None:
        computed = totals.subtotal + sum(value or 0 for value in total_inputs[1:5])
        total_ok = _close(computed, totals.total_amount, tolerance)
        total_message = (
            f"Components calculate to {computed:,.2f}; printed total is "
            f"{totals.total_amount:,.2f}."
        )
    else:
        total_ok = False
        total_message = "Subtotal or total amount is missing."
    _add(
        checks,
        "grand_total",
        "Grand total reconciles",
        total_ok,
        total_message,
        total_message,
        [
            "totals.subtotal",
            "totals.discount",
            "totals.shipping",
            "totals.other_charges",
            "totals.total_tax",
            "totals.total_amount",
        ],
    )

    if totals.total_amount is not None and totals.balance_due is not None:
        expected_due = totals.total_amount - (totals.amount_paid or 0)
        balance_ok = _close(expected_due, totals.balance_due, tolerance)
        balance_message = (
            f"Expected balance is {expected_due:,.2f}; captured balance is "
            f"{totals.balance_due:,.2f}."
        )
    elif totals.amount_paid not in (None, 0) or totals.balance_due is not None:
        balance_ok = False
        balance_message = "A paid amount or balance was captured without enough values to reconcile it."
    else:
        balance_ok = True
        balance_message = "No separate balance calculation was required."
    tax_sum_fields = (
        [
            *(f"tax_lines[{index}].tax_amount" for index in range(len(data.tax_lines))),
            "totals.total_tax",
        ]
        if data.tax_lines
        else ["tax_lines", "totals.total_tax"]
    )
    _add(
        checks,
        "balance_due",
        "Balance due reconciles",
        balance_ok,
        balance_message,
        balance_message,
        ["totals.amount_paid", "totals.balance_due"],
    )

    tax_amounts = [line.tax_amount for line in data.tax_lines]
    complete_tax_rows = bool(data.tax_lines) and all(
        value is not None for value in tax_amounts
    )
    if complete_tax_rows and totals.total_tax is not None:
        tax_sum = sum(value or 0 for value in tax_amounts)
        tax_ok = _close(tax_sum, totals.total_tax, tolerance)
        tax_message = (
            f"Tax rows sum to {tax_sum:,.2f}; captured tax is {totals.total_tax:,.2f}."
        )
    elif data.tax_lines:
        tax_ok = False
        tax_message = "Every tax row and the total tax need an amount to reconcile."
    elif totals.total_tax not in (None, 0):
        tax_ok = False
        tax_message = "The invoice has tax, but no tax-breakdown rows were captured."
    else:
        tax_ok = True
        tax_message = "No separate tax-breakdown calculation was required."
    _add(
        checks,
        "tax_sum",
        "Tax breakdown reconciles",
        tax_ok,
        tax_message,
        tax_message,
        tax_sum_fields,
    )

    tax_math_failures: list[int] = []
    incomplete_tax_math: list[int] = []
    for index, line in enumerate(data.tax_lines):
        values = (line.rate, line.taxable_amount, line.tax_amount)
        if any(value is None for value in values):
            incomplete_tax_math.append(index)
            continue
        expected_tax = (line.taxable_amount or 0) * (line.rate or 0) / 100
        if not _close(expected_tax, line.tax_amount or 0, tolerance):
            tax_math_failures.append(index)
    tax_math_indexes = [*tax_math_failures, *incomplete_tax_math]
    tax_math_rows = [f"tax_lines[{index}]" for index in tax_math_indexes]
    tax_math_fields = [
        f"tax_lines[{index}].{field}"
        for index in tax_math_indexes
        for field in ("rate", "taxable_amount", "tax_amount")
    ]
    if tax_math_failures:
        tax_math_message = (
            f"Taxable amount × percentage differs on {', '.join(tax_math_rows)}."
        )
    elif incomplete_tax_math:
        tax_math_message = (
            "Tax rate, taxable amount, or tax amount is missing on "
            f"{', '.join(tax_math_rows)}."
        )
    else:
        tax_math_message = "Every complete tax row recomputes within tolerance."
    _add(
        checks,
        "tax_math",
        "Tax percentages reconcile",
        not tax_math_fields,
        tax_math_message,
        tax_math_message,
        tax_math_fields,
        "error" if tax_math_failures else "review",
    )

    supplier = _normalize_text(data.supplier.name or "")
    customer = _normalize_text(data.customer.name or "")
    parties_ok = not supplier or not customer or supplier != customer
    _add(
        checks,
        "party_collision",
        "Supplier and customer differ",
        parties_ok,
        "Supplier and customer were distinguished.",
        "Supplier and customer names are identical; check a side-by-side layout.",
        ["supplier.name", "customer.name"],
        "review",
    )

    iban = re.sub(r"\s+", "", data.payment.iban or "").upper()
    iban_ok = not iban or _valid_iban(iban)
    _add(
        checks,
        "iban",
        "IBAN checksum",
        iban_ok,
        "IBAN is absent or passes its checksum.",
        "The captured IBAN fails its checksum.",
        ["payment.iban"],
        "review",
    )

    swift = re.sub(r"\s+", "", data.payment.swift_bic or "").upper()
    swift_ok = not swift or bool(
        re.fullmatch(r"[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?", swift)
    )
    _add(
        checks,
        "swift",
        "SWIFT/BIC format",
        swift_ok,
        "SWIFT/BIC is absent or has a valid structure.",
        "The captured SWIFT/BIC has an invalid structure.",
        ["payment.swift_bic"],
        "review",
    )

    low_confidence = [
        item.field_path for item in data.evidence if item.confidence < confidence_floor
    ]
    low_confidence.extend(
        f"line_items[{index}].confidence"
        for index, item in enumerate(data.line_items)
        if item.confidence < confidence_floor
    )
    low_confidence.extend(
        f"custom_fields[{index}].confidence"
        for index, item in enumerate(data.custom_fields)
        if item.confidence < confidence_floor
    )
    if data.overall_confidence < confidence_floor:
        low_confidence.append("overall_confidence")
    low_confidence = sorted(set(low_confidence))
    _add(
        checks,
        "confidence",
        "Confidence threshold",
        not low_confidence,
        f"All reported confidence values meet {confidence_floor:.0%}.",
        f"{len(low_confidence)} field(s) fall below {confidence_floor:.0%}.",
        low_confidence,
        "review",
    )

    traceable_fields = {
        "invoice.invoice_number",
        "invoice.invoice_date",
        "invoice.currency",
        "supplier.name",
        "customer.name",
        "totals.total_amount",
    }
    source_values = flatten_values(data.model_dump(mode="json", exclude={"evidence"}))
    grounded = 0
    valid_evidence = 0
    supported_paths: set[str] = set()
    label_conflicts: set[str] = set()
    for evidence in data.evidence:
        index = evidence.source_page - 1
        valid_reference = (
            bool(evidence.quote.strip())
            and 0 <= index < len(text_by_page)
            and evidence.field_path in source_values
        )
        literal_support = valid_reference and _quote_supports_value(
            evidence.quote, source_values[evidence.field_path]
        )
        label_conflict = literal_support and _evidence_label_conflicts(
            evidence.field_path, evidence.quote
        )
        supports_value = literal_support and not label_conflict
        if label_conflict:
            label_conflicts.add(evidence.field_path)
        if valid_reference:
            valid_evidence += 1
        if supports_value:
            supported_paths.add(evidence.field_path)
        if supports_value and evidence_is_grounded(evidence.quote, text_by_page[index]):
            grounded += 1
    has_embedded_text = any(text_by_page)
    missing_traceability = sorted(traceable_fields - supported_paths)
    all_references_valid = valid_evidence == len(data.evidence)
    all_quotes_support_values = len(supported_paths) == len(
        {item.field_path for item in data.evidence}
    )
    enough_evidence = not missing_traceability
    evidence_ok = (
        enough_evidence
        and all_references_valid
        and all_quotes_support_values
        and has_embedded_text
        and grounded == len(data.evidence)
    )
    evidence_success = (
        f"{grounded}/{len(data.evidence)} evidence quotes match embedded PDF text."
    )
    if not enough_evidence:
        evidence_failure = (
            f"Missing value-supporting evidence for: {', '.join(missing_traceability)}."
        )
    elif label_conflicts:
        evidence_failure = (
            "Evidence label conflicts with the target field for: "
            f"{', '.join(sorted(label_conflicts))}."
        )
    elif not all_references_valid or not all_quotes_support_values:
        evidence_failure = (
            "One or more evidence entries has an invalid field/page or does not "
            "contain the extracted value."
        )
    elif not has_embedded_text:
        evidence_failure = (
            f"{valid_evidence} visual evidence quote(s) need reviewer confirmation "
            "because this source has no embedded text."
        )
    else:
        evidence_failure = (
            f"{grounded}/{len(data.evidence)} evidence quotes match embedded PDF text; "
            "review the rest visually."
        )
    _add(
        checks,
        "evidence",
        "Evidence grounding",
        evidence_ok,
        evidence_success,
        evidence_failure,
        ["evidence", *missing_traceability],
        "review",
    )

    passed = sum(item.severity == "pass" for item in checks)
    reviews = sum(item.severity == "review" for item in checks)
    errors = sum(item.severity == "error" for item in checks)
    score = round(100 * passed / len(checks)) if checks else 100
    return ValidationReport(
        score=score,
        passed=passed,
        reviews=reviews,
        errors=errors,
        grounded_evidence=grounded,
        total_evidence=len(data.evidence),
        checks=checks,
    )


def actionable_checks(
    report: ValidationReport,
    *,
    has_embedded_text: bool,
) -> list[ValidationCheck]:
    """Return failures worth a targeted visual re-read."""

    return [
        item
        for item in report.checks
        if item.severity != "pass"
        and item.code != "document_type_non_invoice"
        and not (item.code == "evidence" and not has_embedded_text)
    ]


def with_duplicate_check(report: ValidationReport, duplicate: bool) -> ValidationReport:
    """Add the batch-level invoice-number check and recalculate the score."""

    checks = [item for item in report.checks if item.code != "batch_duplicate"]
    checks.append(
        ValidationCheck(
            code="batch_duplicate",
            label="Duplicate invoice",
            severity="review" if duplicate else "pass",
            message=(
                "This invoice number appears more than once in the current batch."
                if duplicate
                else "No duplicate invoice number was found in the current batch."
            ),
            field_paths=["invoice.invoice_number"],
        )
    )
    passed = sum(item.severity == "pass" for item in checks)
    reviews = sum(item.severity == "review" for item in checks)
    errors = sum(item.severity == "error" for item in checks)
    return report.model_copy(
        update={
            "score": round(100 * passed / len(checks)) if checks else 100,
            "passed": passed,
            "reviews": reviews,
            "errors": errors,
            "checks": checks,
        }
    )


def with_verification_review(
    report: ValidationReport,
    changed_paths: list[str],
) -> ValidationReport:
    """Require human review whenever the model revises its first-pass output."""

    paths = sorted(set(changed_paths))
    checks = [item for item in report.checks if item.code != "verification_changes"]
    if paths:
        checks.append(
            ValidationCheck(
                code="verification_changes",
                label="Automatic verification changes",
                severity="review",
                message=(
                    f"The targeted re-read changed {len(paths)} field(s). Compare the "
                    "revised values and page evidence with the source before approval."
                ),
                field_paths=paths,
            )
        )
    passed = sum(item.severity == "pass" for item in checks)
    reviews = sum(item.severity == "review" for item in checks)
    errors = sum(item.severity == "error" for item in checks)
    return report.model_copy(
        update={
            "score": round(100 * passed / len(checks)) if checks else 100,
            "passed": passed,
            "reviews": reviews,
            "errors": errors,
            "checks": checks,
        }
    )


def _is_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
    except ValueError:
        return False


def _chronology_ok(invoice_date: str | None, due_date: str | None) -> bool:
    if not invoice_date or not due_date:
        return True
    if not (_is_iso_date(invoice_date) and _is_iso_date(due_date)):
        return True
    return date.fromisoformat(due_date) >= date.fromisoformat(invoice_date)


def _valid_iban(value: str) -> bool:
    if not 15 <= len(value) <= 34 or not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", value):
        return False
    rearranged = value[4:] + value[:4]
    digits = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in rearranged
    )
    return int(digits) % 97 == 1
