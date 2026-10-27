"""Provider-neutral extract → validate → targeted re-read workflow.

Author: Ali Ottoman
"""

from __future__ import annotations

import copy
import re
import time
from typing import Any

import config

from .documents import DocumentPages
from .models import ExtractionRun, InvoiceExtraction, PassRecord, ValidationCheck
from .paths import flatten_values
from .prompts import extraction_prompt, verification_prompt
from .providers import build_provider
from .validators import actionable_checks, validate_invoice, with_verification_review


class InvoiceExtractor:
    """Run the same controlled workflow against either OCI inference path."""

    def __init__(self, settings: config.Settings):
        if not settings.is_live_ready:
            raise RuntimeError(settings.configuration_hint)
        self.settings = settings
        self.provider = build_provider(settings)

    def extract(
        self,
        document: DocumentPages,
        *,
        custom_fields: list[str],
        required_fields: list[str],
        verify: bool,
    ) -> ExtractionRun:
        started = time.perf_counter()
        total_input = 0
        total_output = 0

        result, usage = self.provider.invoke(
            extraction_prompt(document.text_by_page, custom_fields), document.images
        )
        total_input += usage[0]
        total_output += usage[1]
        report = self._validate(result, document, custom_fields, required_fields)
        passes = [
            PassRecord(
                pass_number=1,
                kind="extract",
                score=report.score,
                issues=report.reviews + report.errors,
            )
        ]

        failures = actionable_checks(
            report,
            has_embedded_text=any(document.text_by_page),
        )
        if verify and failures:
            try:
                revised, usage = self.provider.invoke(
                    verification_prompt(result, failures, document.text_by_page),
                    document.images,
                )
                total_input += usage[0]
                total_output += usage[1]
                revised = _restrict_verification(
                    result,
                    revised,
                    failures,
                    requested_custom_fields=custom_fields,
                )
                changes = _changed_fields(result, revised)
                result = revised
                report = self._validate(
                    result,
                    document,
                    custom_fields,
                    required_fields,
                )
                report = with_verification_review(report, changes)
                passes.append(
                    PassRecord(
                        pass_number=2,
                        kind="verify",
                        score=report.score,
                        issues=report.reviews + report.errors,
                        changes=changes,
                    )
                )
            except Exception:  # noqa: BLE001 - verification is optional; retain pass one.
                passes.append(
                    PassRecord(
                        pass_number=2,
                        kind="verify",
                        score=report.score,
                        issues=report.reviews + report.errors,
                        note=(
                            "Targeted re-read was unavailable; retained the validated "
                            "first-pass values for review."
                        ),
                    )
                )

        return ExtractionRun(
            filename=document.filename,
            page_count=document.page_count,
            mode=self.settings.inference_mode,
            model_label=self.settings.active_model_label,
            elapsed_seconds=round(time.perf_counter() - started, 2),
            input_tokens=total_input or None,
            output_tokens=total_output or None,
            requested_custom_fields=custom_fields,
            required_field_paths=required_fields,
            extraction=result,
            validation=report,
            passes=passes,
        )

    def _validate(
        self,
        result: InvoiceExtraction,
        document: DocumentPages,
        custom_fields: list[str],
        required_fields: list[str],
    ):
        return validate_invoice(
            result,
            document.text_by_page,
            tolerance=self.settings.tolerance,
            confidence_floor=self.settings.confidence_floor,
            requested_custom_fields=custom_fields,
            required_fields=required_fields,
        )


def _changed_fields(before: InvoiceExtraction, after: InvoiceExtraction) -> list[str]:
    left = flatten_values(before.model_dump(mode="json"))
    right = flatten_values(after.model_dump(mode="json"))
    return sorted(
        path for path in left.keys() | right.keys() if left.get(path) != right.get(path)
    )


def _restrict_verification(
    before: InvoiceExtraction,
    candidate: InvoiceExtraction,
    failures: list[ValidationCheck],
    *,
    requested_custom_fields: list[str] | None = None,
) -> InvoiceExtraction:
    """Accept only values and evidence implicated by failed checks."""

    allowed_paths = {
        path
        for failure in failures
        if failure.code != "evidence"
        for path in failure.field_paths
    }
    evidence_recheck = any(failure.code == "evidence" for failure in failures)
    custom_contract_recheck = any(
        failure.code == "custom_field_contract" for failure in failures
    )
    allowed_paths.discard("evidence")
    allowed_paths.discard("custom_fields")
    payload = before.model_dump(mode="python")
    revised = candidate.model_dump(mode="python")
    for path in sorted(allowed_paths):
        _copy_path(revised, payload, path)

    if custom_contract_recheck:
        payload["custom_fields"] = _merge_custom_fields(
            payload["custom_fields"],
            revised["custom_fields"],
            requested_custom_fields or [],
        )

    if evidence_recheck:
        payload["evidence"] = copy.deepcopy(revised["evidence"])
    else:
        targeted = {
            item.field_path
            for item in [*before.evidence, *candidate.evidence]
            if _evidence_path_allowed(item.field_path, allowed_paths)
        }
        preserved = [
            item.model_dump(mode="python")
            for item in before.evidence
            if item.field_path not in targeted
        ]
        refreshed = [
            item.model_dump(mode="python")
            for item in candidate.evidence
            if item.field_path in targeted
        ]
        payload["evidence"] = [*preserved, *refreshed]
    return InvoiceExtraction.model_validate(payload)


def _merge_custom_fields(
    current: list[dict],
    candidate: list[dict],
    requested: list[str],
) -> list[dict]:
    """Repair the requested field set without rewriting valid existing values."""

    def grouped(items: list[dict]) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {}
        for item in items:
            key = str(item.get("name", "")).strip().casefold()
            if key:
                groups.setdefault(key, []).append(item)
        return groups

    current_by_name = grouped(current)
    candidate_by_name = grouped(candidate)
    merged: list[dict] = []
    for name in requested:
        key = name.strip().casefold()
        existing = current_by_name.get(key, [])
        proposed = candidate_by_name.get(key, [])
        if len(existing) == 1:
            merged.append(copy.deepcopy(existing[0]))
        elif proposed:
            merged.append(copy.deepcopy(proposed[0]))
        elif existing:
            merged.append(copy.deepcopy(existing[0]))
    return merged


def _evidence_path_allowed(field_path: str, allowed_paths: set[str]) -> bool:
    """Match an evidence field to an exact or intentionally broad repair path."""

    return any(
        field_path == path or field_path.startswith((f"{path}.", f"{path}["))
        for path in allowed_paths
    )


def _path_tokens(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    for name, index in re.findall(r"([^.\[\]]+)|\[(\d+)\]", path):
        tokens.append(int(index) if index else name)
    return tokens


def _copy_path(source: Any, target: Any, path: str) -> None:
    """Copy one dotted/list path if it exists in both complete payloads."""

    tokens = _path_tokens(path)
    if not tokens:
        return
    source_cursor = source
    target_cursor = target
    try:
        for token in tokens[:-1]:
            source_cursor = source_cursor[token]
            target_cursor = target_cursor[token]
        final = tokens[-1]
        target_cursor[final] = copy.deepcopy(source_cursor[final])
    except (KeyError, IndexError, TypeError):
        return
