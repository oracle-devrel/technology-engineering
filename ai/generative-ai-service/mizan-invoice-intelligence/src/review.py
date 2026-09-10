"""Pure review and approval transitions for invoice extraction runs.

Author: Ali Ottoman

What this module does
- Records reviewer edits and invalidates superseded page evidence.
- Re-runs deterministic checks without depending on Streamlit state.
- Maintains duplicate checks, approval events, and the audit trail.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import config

from .documents import DocumentPages
from .models import ExtractionRun, InvoiceExtraction, PassRecord, ReviewChange
from .paths import flatten_values
from .validators import (
    validate_invoice,
    with_duplicate_check,
    with_verification_review,
)

_EVIDENCE_ROW_PATH = re.compile(r"^(?:custom_fields|line_items|tax_lines)\[\d+\]")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _audit_value(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _affects_evidence(changed_path: str, evidence_path: str) -> bool:
    """Match exact fields and edits elsewhere in the same repeated row."""

    if changed_path == evidence_path:
        return True
    match = _EVIDENCE_ROW_PATH.match(changed_path)
    return bool(match and evidence_path.startswith(f"{match.group()}."))


def review_changes(
    before: InvoiceExtraction,
    after: InvoiceExtraction,
) -> list[ReviewChange]:
    """Return field-level audit entries for a reviewer edit."""

    left = flatten_values(before.model_dump(mode="json"))
    right = flatten_values(after.model_dump(mode="json"))
    evidence_paths = {item.field_path for item in before.evidence}
    changed_at = _utc_timestamp()
    return [
        ReviewChange(
            field_path=path,
            before=_audit_value(left.get(path)),
            after=_audit_value(right.get(path)),
            changed_at=changed_at,
            evidence_disposition=(
                "source_quote_overridden"
                if any(_affects_evidence(path, item) for item in evidence_paths)
                else "not_linked"
            ),
        )
        for path in sorted(left.keys() | right.keys())
        if left.get(path) != right.get(path)
    ]


def verification_change_paths(run: ExtractionRun) -> list[str]:
    """Collect every field changed by an automatic verification pass."""

    return sorted(
        {path for item in run.passes if item.kind == "verify" for path in item.changes}
    )


def invalidate_approval(
    run: ExtractionRun,
    reason: str,
    changes: list[str] | None = None,
) -> ExtractionRun:
    """Reopen an approved run and append the reason to its audit history."""

    if run.approval_status != "approved":
        return run
    event = PassRecord(
        pass_number=len(run.passes) + 1,
        kind="invalidate",
        score=run.validation.score,
        issues=run.validation.errors + run.validation.reviews,
        changes=changes or [],
        note=reason,
        actor="system",
        recorded_at=_utc_timestamp(),
    )
    return run.model_copy(
        update={
            "approval_status": "pending",
            "approved_by": None,
            "approved_at": None,
            "passes": [*run.passes, event],
        }
    )


def apply_batch_duplicate_checks(runs: list[ExtractionRun]) -> list[ExtractionRun]:
    """Refresh duplicate-number checks across a batch without mutating it."""

    numbers = [
        (run.extraction.invoice.invoice_number or "").strip().casefold() for run in runs
    ]
    counts = Counter(number for number in numbers if number)
    checked: list[ExtractionRun] = []
    for run, number in zip(runs, numbers, strict=True):
        prior = next(
            (item for item in run.validation.checks if item.code == "batch_duplicate"),
            None,
        )
        duplicate = bool(number and counts[number] > 1)
        refreshed = run.model_copy(
            update={"validation": with_duplicate_check(run.validation, duplicate)}
        )
        duplicate_changed = (
            prior is not None and (prior.severity == "review") != duplicate
        )
        if duplicate_changed:
            refreshed = invalidate_approval(
                refreshed,
                "The duplicate-invoice result changed after approval.",
                ["invoice.invoice_number"],
            )
        checked.append(refreshed)
    return checked


def revalidate_review(
    run: ExtractionRun,
    extraction: InvoiceExtraction,
    document: DocumentPages,
    settings: config.Settings,
) -> tuple[ExtractionRun, list[str]]:
    """Apply reviewer edits, re-run checks, and return changed field paths."""

    audit_changes = review_changes(run.extraction, extraction)
    if not audit_changes:
        return run, []

    changed_paths = [item.field_path for item in audit_changes]
    extraction = extraction.model_copy(
        update={
            "evidence": [
                item
                for item in extraction.evidence
                if not any(
                    _affects_evidence(path, item.field_path) for path in changed_paths
                )
            ]
        }
    )
    report = validate_invoice(
        extraction,
        document.text_by_page,
        tolerance=settings.tolerance,
        confidence_floor=settings.confidence_floor,
        requested_custom_fields=run.requested_custom_fields,
        required_fields=run.required_field_paths,
    )
    report = with_verification_review(report, verification_change_paths(run))
    review_pass = PassRecord(
        pass_number=len(run.passes) + 1,
        kind="review",
        score=report.score,
        issues=report.errors + report.reviews,
        changes=changed_paths,
        actor="reviewer",
        recorded_at=_utc_timestamp(),
    )
    refreshed = run.model_copy(
        update={
            "extraction": extraction,
            "validation": report,
            "passes": [*run.passes, review_pass],
            "review_changes": [*run.review_changes, *audit_changes],
        }
    )
    return (
        invalidate_approval(
            refreshed,
            "Reviewer edits changed extracted values after approval.",
            changed_paths,
        ),
        changed_paths,
    )


def approve_run(run: ExtractionRun, reviewer: str) -> ExtractionRun:
    """Validate the reviewer identity and return an approved run."""

    if run.validation.errors:
        raise ValueError("Resolve the blocking checks before approval.")
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("Enter the reviewer name before approval.")

    approved_at = _utc_timestamp()
    approval_pass = PassRecord(
        pass_number=len(run.passes) + 1,
        kind="approve",
        score=run.validation.score,
        issues=run.validation.reviews,
        changes=[],
        note="Human approval recorded after review.",
        actor=reviewer,
        recorded_at=approved_at,
    )
    return run.model_copy(
        update={
            "approval_status": "approved",
            "approved_by": reviewer,
            "approved_at": approved_at,
            "passes": [*run.passes, approval_pass],
        }
    )
