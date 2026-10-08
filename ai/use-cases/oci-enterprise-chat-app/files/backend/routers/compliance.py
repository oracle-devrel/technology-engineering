"""Evidence-backed, industry-specific compliance checks for PDF documents."""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from models.document import ComplianceAssessment, ComplianceEvidence, ComplianceFinding
from routers.documents import StorageDep
from services.adapter_service import get_compliance_rules, list_domains, load_adapter
from services.storage import DocumentNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/compliance", tags=["compliance"])

_PAGE_MARKER = re.compile(r"^--- Page (\d+) ---\s*$", re.MULTILINE)
_FIELD_ALIASES: dict[str, list[str]] = {
    "document_title": ["document title", "title"],
    "document_number": ["document number", "document no", "reference", "ref"],
    "revision": ["revision", "rev", "version"],
    "document_date": ["document date", "date", "issued"],
    "document_type": ["document type", "type"],
    "document_status": ["document status", "status", "suitability"],
    "author": ["author", "prepared by", "prepared for"],
    "reviewer": ["reviewer", "reviewed by", "checked by", "checker"],
    "approver": ["approver", "approved by", "authorised by", "authorized by"],
    "organization": ["organization", "organisation", "issued by", "company"],
    "recipient": ["recipient", "to", "addressee"],
    "scope": ["scope", "purpose"],
    "summary": ["summary", "executive summary", "abstract"],
}


class ComplianceCheckRequest(BaseModel):
    document_ids: list[str] = Field(..., min_length=1)
    industry: str = Field(default="generic")


class DocumentComplianceResult(BaseModel):
    document_id: str
    filename: str
    industry: str
    total: int = 0
    passes: int = 0
    warnings: int = 0
    reviews: int = 0
    fails: int = 0
    pass_rate: int = 0
    findings: list[ComplianceFinding] = Field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    ruleset_version: str = ""
    document_sha256: str | None = None
    assessed_at: datetime | None = None
    assessment_status: str = "completed"
    error_message: str | None = None
    review_status: str = "pending"
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None


class ComplianceDocumentError(BaseModel):
    document_id: str
    message: str


class ComplianceReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=1, max_length=120)
    decision: Literal["approved", "changes_requested"]
    notes: str | None = Field(default=None, max_length=4000)


class ComplianceCheckResponse(BaseModel):
    results: list[DocumentComplianceResult] = Field(default_factory=list)
    industry: str = "generic"
    total_documents: int = 0
    errors: list[ComplianceDocumentError] = Field(default_factory=list)


def _ruleset_version(rules: list[dict[str, Any]]) -> str:
    """Produce a deterministic identifier for exactly the rules that were evaluated."""
    canonical = json.dumps(rules, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode()).hexdigest()[:16]}"


def _normalise_term(value: str) -> str:
    return " ".join(value.replace("_", " ").split())


def _term_pattern(term: str) -> re.Pattern[str]:
    """Match a configured term as words, allowing whitespace differences but not substrings."""
    words = [re.escape(word) for word in _normalise_term(term).split()]
    return re.compile(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)", re.IGNORECASE)


class _EvidenceLocator:
    """Map matches in extracted PDF text to pages, sections, and bounded quotes."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.page_markers = [
            (match.start(), int(match.group(1))) for match in _PAGE_MARKER.finditer(text)
        ]

    def evidence(self, match: re.Match[str], matched_text: str) -> ComplianceEvidence:
        page = None
        for marker_position, marker_page in self.page_markers:
            if marker_position > match.start():
                break
            page = marker_page

        quote_start = max(0, match.start() - 90)
        quote_end = min(len(self.text), match.end() + 150)
        quote = " ".join(self.text[quote_start:quote_end].split())

        section = None
        for line in reversed(self.text[: match.start()].splitlines()):
            candidate = " ".join(line.split())
            if not candidate or _PAGE_MARKER.match(candidate):
                continue
            if candidate.endswith(":") or (len(candidate) <= 100 and candidate.isupper()):
                section = candidate.rstrip(":")
                break

        return ComplianceEvidence(
            page=page,
            section=section,
            quote=quote,
            matched_text=matched_text,
            start_char=match.start(),
            end_char=match.end(),
        )

    def find_term(self, terms: list[str]) -> tuple[re.Match[str], str] | None:
        for term in terms:
            if not term:
                continue
            match = _term_pattern(term).search(self.text)
            if match:
                return match, term
        return None

    def find_labelled_value(self, terms: list[str]) -> tuple[re.Match[str], str, str] | None:
        """Find a configured field label followed by a non-empty value on the same line."""
        for term in terms:
            if not term:
                continue
            label = _term_pattern(term).pattern
            pattern = re.compile(
                label + r"(?:\s*[:\-]\s*|\s{2,})(?P<value>[^\n|]{1,160})",
                re.IGNORECASE,
            )
            match = pattern.search(self.text)
            if match:
                value = " ".join(match.group("value").split()).strip(" .;,")
                if value:
                    return match, term, value
        return None


def _field_terms(rule: dict[str, Any], adapter: dict[str, Any]) -> list[str]:
    field_name = str(rule.get("field_name", ""))
    schema_fields = adapter.get("schema", {}).get("fields", [])
    schema_label = next(
        (str(field.get("label", "")) for field in schema_fields if field.get("name") == field_name),
        "",
    )
    candidates = [field_name, schema_label, *_FIELD_ALIASES.get(field_name, [])]
    candidates.extend(str(alias) for alias in rule.get("aliases", []) if isinstance(alias, str))

    unique: list[str] = []
    for candidate in candidates:
        candidate = _normalise_term(candidate)
        if candidate and candidate.lower() not in {term.lower() for term in unique}:
            unique.append(candidate)
    return unique


def _configured_terms(rule: dict[str, Any], primary_key: str) -> list[str]:
    candidates = [str(rule.get(primary_key, ""))]
    candidates.extend(str(alias) for alias in rule.get("aliases", []) if isinstance(alias, str))
    return [term for term in (_normalise_term(candidate) for candidate in candidates) if term]


def _finding_for_rule(
    rule: dict[str, Any], locator: _EvidenceLocator, adapter: dict[str, Any]
) -> ComplianceFinding | None:
    check_type = rule.get("type", "keyword_present")
    severity = rule.get("severity", "medium")
    base = {
        "rule_id": rule.get("id", ""),
        "category": rule.get("category", ""),
        "severity": severity if severity in {"low", "medium", "high", "critical"} else "medium",
    }

    if check_type == "required_field":
        terms = _field_terms(rule, adapter)
        value_match = locator.find_labelled_value(terms)
        if value_match:
            match, term, value = value_match
            return ComplianceFinding(
                **base,
                status="pass",
                message=rule.get("pass_message", "Required field extracted"),
                extracted_value=value,
                evidence=[locator.evidence(match, term)],
                confidence=0.95,
                requires_human_review=severity in {"high", "critical"},
            )

        label_match = locator.find_term(terms)
        if label_match:
            match, term = label_match
            return ComplianceFinding(
                **base,
                status="review",
                message="Field label found, but no value could be extracted. " + rule.get(
                    "fail_message", "Human review required"
                ),
                evidence=[locator.evidence(match, term)],
                confidence=0.5,
                requires_human_review=True,
            )

        return ComplianceFinding(
            **base,
            status=rule.get("missing_status", "fail"),
            message=rule.get("fail_message", "Required field was not found"),
            confidence=0.0,
            requires_human_review=True,
        )

    if check_type in {"keyword_present", "standard_reference"}:
        primary_key = "keyword" if check_type == "keyword_present" else "standard"
        match_result = locator.find_term(_configured_terms(rule, primary_key))
        if match_result:
            match, term = match_result
            return ComplianceFinding(
                **base,
                status="pass",
                message=rule.get("pass_message", "Configured term found"),
                extracted_value=match.group(0),
                evidence=[locator.evidence(match, term)],
                confidence=1.0,
                requires_human_review=severity in {"high", "critical"},
            )

        return ComplianceFinding(
            **base,
            status=rule.get("missing_status", "warning"),
            message=rule.get("fail_message", "Configured term was not found"),
            confidence=0.0,
            requires_human_review=True,
        )

    logger.warning("Skipping unsupported compliance rule type %r", check_type)
    return None


def run_compliance_checks(text: str, industry: str) -> list[ComplianceFinding]:
    """Evaluate the selected ruleset and attach page-level evidence to each finding."""
    domain = industry if industry in list_domains() else "generic"
    adapter = load_adapter(domain)
    locator = _EvidenceLocator(text)
    findings = [_finding_for_rule(rule, locator, adapter) for rule in get_compliance_rules(domain)]
    return [finding for finding in findings if finding is not None]


def _result_from_assessment(
    document_id: str, filename: str, assessment: ComplianceAssessment
) -> DocumentComplianceResult:
    findings = assessment.findings
    passes = sum(finding.status == "pass" for finding in findings)
    warnings = sum(finding.status == "warning" for finding in findings)
    reviews = sum(finding.status == "review" for finding in findings)
    fails = sum(finding.status == "fail" for finding in findings)
    total = len(findings)
    return DocumentComplianceResult(
        document_id=document_id,
        filename=filename,
        industry=assessment.industry,
        total=total,
        passes=passes,
        warnings=warnings,
        reviews=reviews,
        fails=fails,
        pass_rate=round((passes / total) * 100) if total else 0,
        findings=findings,
        critical_count=sum(
            finding.severity == "critical" and finding.status in {"warning", "review", "fail"}
            for finding in findings
        ),
        high_count=sum(
            finding.severity == "high" and finding.status in {"warning", "review", "fail"}
            for finding in findings
        ),
        ruleset_version=assessment.ruleset_version,
        document_sha256=assessment.document_sha256,
        assessed_at=assessment.assessed_at,
        assessment_status=assessment.assessment_status,
        error_message=assessment.error_message,
        review_status=assessment.review_status,
        reviewed_by=assessment.reviewed_by,
        reviewed_at=assessment.reviewed_at,
        review_notes=assessment.review_notes,
    )


@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(req: ComplianceCheckRequest, storage: StorageDep):
    """Run and persist evidence-backed compliance checks on selected documents."""
    industry = req.industry if req.industry in list_domains() else "generic"
    rules = get_compliance_rules(industry)
    ruleset_version = _ruleset_version(rules)
    results: list[DocumentComplianceResult] = []
    errors: list[ComplianceDocumentError] = []

    for doc_id in req.document_ids:
        try:
            document = await storage.get_document(doc_id)
            text = storage.extract_text_from_pdf(doc_id)
            document_sha256 = None
            if hasattr(storage, "get_document_sha256"):
                document_sha256 = storage.get_document_sha256(doc_id)

            if not text.strip():
                assessment = ComplianceAssessment(
                    industry=industry,
                    ruleset_version=ruleset_version,
                    document_sha256=document_sha256,
                    assessment_status="not_assessable",
                    error_message=(
                        "No text could be extracted from the PDF. OCR or a readable text layer is required."
                    ),
                )
            else:
                assessment = ComplianceAssessment(
                    industry=industry,
                    ruleset_version=ruleset_version,
                    document_sha256=document_sha256,
                    findings=run_compliance_checks(text, industry),
                )

            if hasattr(storage, "update_compliance_assessment"):
                await storage.update_compliance_assessment(doc_id, assessment)
            results.append(
                _result_from_assessment(doc_id, document.metadata.filename, assessment)
            )
        except DocumentNotFoundError:
            errors.append(
                ComplianceDocumentError(document_id=doc_id, message="Document was not found")
            )
        except Exception as exc:
            logger.warning("Failed to check compliance for %s: %s", doc_id, exc)
            errors.append(ComplianceDocumentError(document_id=doc_id, message=str(exc)))

    results.sort(key=lambda result: result.pass_rate)
    return ComplianceCheckResponse(
        results=results,
        industry=industry,
        total_documents=len(results),
        errors=errors,
    )


@router.put("/{document_id}/review", response_model=DocumentComplianceResult)
async def review_compliance_assessment(
    document_id: str, review: ComplianceReviewRequest, storage: StorageDep
):
    """Persist a human approval or requested-change decision for an assessment."""
    if not hasattr(storage, "review_compliance_assessment"):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="The configured storage service cannot record compliance reviews",
        )
    try:
        document = await storage.review_compliance_assessment(
            document_id,
            review.decision,
            review.reviewer.strip(),
            review.notes.strip() if review.notes else None,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document was not found") from exc
    except Exception as exc:
        logger.warning("Failed to record compliance review for %s: %s", document_id, exc)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    assessment = (
        document.extraction_result.compliance_assessment if document.extraction_result else None
    )
    if assessment is None:
        raise HTTPException(
            status_code=409, detail="No compliance assessment exists for this document"
        )
    return _result_from_assessment(document_id, document.metadata.filename, assessment)


@router.get("/industries")
async def list_industries():
    """List available industries for compliance checking (from adapter configs)."""
    industries = []
    for domain in list_domains():
        try:
            adapter = load_adapter(domain)
            schema_info = adapter.get("schema", {})
            rules = adapter.get("rules", {}).get("checks", [])
            industries.append(
                {
                    "id": domain,
                    "name": schema_info.get("name", domain.replace("-", " ").title()),
                    "description": schema_info.get("description", ""),
                    "rules_count": len(rules),
                }
            )
        except Exception:
            industries.append(
                {
                    "id": domain,
                    "name": domain.replace("-", " ").title(),
                    "description": "",
                    "rules_count": 0,
                }
            )
    return {"industries": industries}
