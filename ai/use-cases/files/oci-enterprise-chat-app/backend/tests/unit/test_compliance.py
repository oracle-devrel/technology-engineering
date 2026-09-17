"""Tests for evidence-backed compliance assessment."""

import io

import pytest

from models.document import DocumentStatus
from routers.compliance import (
    ComplianceCheckRequest,
    ComplianceReviewRequest,
    check_compliance,
    review_compliance_assessment,
    run_compliance_checks,
)


def _findings_by_id(text: str) -> dict[str, object]:
    return {finding.rule_id: finding for finding in run_compliance_checks(text, "generic")}


def test_required_fields_extract_values_and_page_evidence() -> None:
    text = """--- Page 1 ---
DOCUMENT CONTROL
Document Title: Site Safety Plan
Reference: PRJ-042
Revision: R3
Scope: Temporary works for the east wing
Approved by: Jordan Smith
This document is confidential.
"""

    findings = _findings_by_id(text)
    title = findings["G001"]
    reference = findings["G002"]
    approver = findings["G012"]
    confidentiality = findings["G060"]

    assert title.status == "pass"
    assert title.extracted_value == "Site Safety Plan"
    assert title.evidence[0].page == 1
    assert title.evidence[0].section == "DOCUMENT CONTROL"
    assert reference.status == "pass"
    assert reference.extracted_value == "PRJ-042"
    assert approver.status == "pass"
    assert approver.extracted_value == "Jordan Smith"
    assert confidentiality.status == "pass"
    assert confidentiality.evidence[0].quote


def test_keywords_use_word_boundaries_and_missing_required_fields_fail() -> None:
    findings = _findings_by_id("--- Page 1 ---\nThe confidentiality statement is retained.\n")

    assert findings["G060"].status == "warning"
    assert findings["G012"].status == "fail"
    assert findings["G012"].requires_human_review is True


@pytest.mark.asyncio
async def test_check_persists_assessment_with_document_hash(
    storage_service,
    sample_pdf_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = await storage_service.save_file(
        file=io.BytesIO(sample_pdf_bytes),
        filename="controlled-document.pdf",
        content_type="application/pdf",
    )
    await storage_service.update_document_status(document.id, DocumentStatus.COMPLETED)
    monkeypatch.setattr(
        storage_service,
        "extract_text_from_pdf",
        lambda _document_id: (
            "--- Page 1 ---\nDocument Title: Controlled Procedure\nScope: Validation\n"
        ),
    )

    response = await check_compliance(
        ComplianceCheckRequest(document_ids=[document.id], industry="generic"), storage_service
    )
    persisted = await storage_service.get_document(document.id)

    assert response.total_documents == 1
    assert response.errors == []
    assert response.results[0].ruleset_version.startswith("sha256:")
    assert (
        response.results[0].findings[0].evidence
        or response.results[0].findings[0].status == "fail"
    )
    assert persisted.extraction_result is not None
    assert persisted.extraction_result.compliance_assessment is not None
    assert persisted.extraction_result.compliance_assessment.document_sha256
    assert len(persisted.extraction_result.compliance_assessment.document_sha256) == 64
    assert persisted.compliance_audit_log[-1].event_type == "assessment_created"

    reviewed = await review_compliance_assessment(
        document.id,
        ComplianceReviewRequest(
            reviewer="Compliance Reviewer",
            decision="approved",
            notes="Evidence verified against source PDF.",
        ),
        storage_service,
    )
    assert reviewed.review_status == "approved"
    assert reviewed.reviewed_by == "Compliance Reviewer"
    assert reviewed.reviewed_at is not None
    persisted_review = await storage_service.get_document(document.id)
    assert persisted_review.compliance_audit_log[-1].event_type == "review_recorded"
    assert persisted_review.compliance_audit_log[-1].actor == "Compliance Reviewer"


@pytest.mark.asyncio
async def test_empty_document_is_returned_as_not_assessable(
    storage_service,
    sample_pdf_bytes: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = await storage_service.save_file(
        file=io.BytesIO(sample_pdf_bytes),
        filename="scanned-document.pdf",
        content_type="application/pdf",
    )
    monkeypatch.setattr(storage_service, "extract_text_from_pdf", lambda _document_id: "")

    response = await check_compliance(
        ComplianceCheckRequest(document_ids=[document.id], industry="generic"), storage_service
    )

    assert response.total_documents == 1
    assert response.results[0].assessment_status == "not_assessable"
    assert "OCR" in (response.results[0].error_message or "")
