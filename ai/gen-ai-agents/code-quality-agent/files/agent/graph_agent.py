"""
File name: graph_agent.py
Author: Luigi Saetta
Date last modified: 2026-01-12
Python Version: 3.11

License:
    MIT

Description:
    LangGraph agent that runs a pipeline over local Python files (read-only access),
    producing outputs elsewhere.

Usage:
    from agent.graph_agent import build_graph, run_agent

    graph = build_graph()
    result = await run_agent(graph, root_dir="...", out_dir="...", request="...")
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from fnmatch import fnmatch

from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from agent.fs_ro import ReadOnlySandboxFS
from agent.header_rules import check_header
from agent.secrets_scan import scan_for_secrets
from agent.docgen import generate_doc_for_file
from agent.docgen_utils import call_llm_normalized
from agent.oci_models import get_llm
from agent.docgen_prompt import REPORT_PROMPT
from agent.license_check import check_license
from agent.pii_scan import scan_for_pii
from agent.header_fix import generate_header_snippet
from agent.requirements_check import check_requirements_at_root
from agent.gitignore_utils import parse_gitignore, is_ignored

from agent.config import ACCEPTED_LICENSE_TYPES, EXCLUDED_PATHS

from agent.utils import get_console_logger

from agent.dep_license_check import check_dependency_licenses
from agent.config import (
    ACCEPTED_DEP_LICENSES,
    FAIL_ON_UNKNOWN_DEP_LICENSE,
    FAIL_ON_NOT_INSTALLED_DEP,
    LLM_MODEL_ID,
    ENABLE_DOC_GENERATION,
    ENABLE_HEADER_SNIPPET_GENERATION
)


logger = get_console_logger()


# ---- Helpers ----
def get_config_value(
    config: RunnableConfig | None,
    key: str,
    default: Any = None,
) -> Any:
    if not config:
        return default
    configurable = config.get("configurable")
    if not configurable:
        return default
    return configurable.get(key, default)


def _is_excluded(relpath: str) -> bool:
    """
    Check if a given repo-relative path matches any of the excluded patterns.
    """
    posix = relpath.replace("\\", "/")
    return any(fnmatch(posix, pat) for pat in EXCLUDED_PATHS)


# ---- State ----
@dataclass
class AgentState:
    request: str
    root_dir: str
    out_dir: str

    file_list: list[str] = field(default_factory=list)

    header_issues: dict[str, str] = field(default_factory=dict)  # relpath -> message
    secrets: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )  # relpath -> findings
    docs: dict[str, str] = field(default_factory=dict)  # relpath -> doc out path

    summary: str = ""

    license_ok: bool = True
    license_info: dict[str, Any] = field(default_factory=dict)  # details of check

    # PII
    # relpath -> findings
    pii_findings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    pii_failures: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )  # subset severity=fail
    pii_warnings: dict[str, list[dict[str, Any]]] = field(
        default_factory=dict
    )  # subset severity=warn

    header_fixes: dict[str, str] = field(
        default_factory=dict
    )  # relpath -> header snippet file path

    # to check library licenses
    requirements_ok: bool = True
    requirements_info: dict[str, Any] = field(default_factory=dict)

    dep_license_ok: bool = True
    dep_licenses: list[dict[str, Any]] = field(default_factory=list)
    dep_license_failures: list[dict[str, Any]] = field(default_factory=list)
    dep_license_warnings: list[dict[str, Any]] = field(default_factory=list)

    # .gitignore
    ignored_paths: set[str] = field(default_factory=set)  # repo-relative posix paths

    # Secrets split
    secrets_failures: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    secrets_warnings: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


# ---- Nodes ----


def node_discover_files(state: AgentState) -> AgentState:
    """
    Discover all source files under the root directory.

    Modified to use ReadOnlySandboxFS.
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))
    source_files = fs.list_source_files()

    # apply any exclusions
    files: list[str] = []
    for p in source_files:
        rel = str(fs.relpath(p))
        if _is_excluded(rel):
            continue
        files.append(rel)

    state.file_list = files

    logger.info("")
    logger.info("Discovered %d source files.", len(state.file_list))

    for f_name in state.file_list:
        logger.info(" - %s", f_name)

    logger.info("")

    return state


def node_check_headers(state: AgentState) -> AgentState:
    fs = ReadOnlySandboxFS(Path(state.root_dir))
    issues: dict[str, str] = {}

    for rel in state.file_list:

        logger.info("Checking headers for: %s...", rel)

        src = fs.read_text(rel)
        res = check_header(src, path=fs._resolve_under_root(Path(rel)))
        if not res.ok:
            issues[rel] = res.message

    state.header_issues = issues
    return state


def node_scan_secrets(state: AgentState) -> AgentState:
    """
    Scan files for secrets using predefined patterns.
    Modified to use ReadOnlySandboxFS.
    It distinguishes between ignored files (warnings) and others (failures).
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))
    failures: dict[str, list[dict[str, Any]]] = {}
    warnings: dict[str, list[dict[str, Any]]] = {}

    ignored = getattr(state, "ignored_paths", set()) or set()

    for rel in state.file_list:
        logger.info("Scanning secrets for: %s...", rel)

        src = fs.read_text(rel)
        findings = scan_for_secrets(src)
        if not findings:
            continue

        payload = [
            {"kind": f.kind, "line": f.line, "excerpt": f.excerpt} for f in findings
        ]

        # DOWNGRADE: if file is ignored, treat as warning (still report)
        if rel.replace("\\", "/") in ignored:
            warnings[rel] = payload
        else:
            failures[rel] = payload

    # Keep legacy state.secrets if you want, but prefer split
    state.secrets_failures = failures
    state.secrets_warnings = warnings
    state.secrets = failures  # optional: keep old behavior for other code paths

    return state


def node_scan_pii(state: AgentState) -> AgentState:
    """
    Scan files for PII using predefined patterns.
    Modified to use ReadOnlySandboxFS.
    It distinguishes between ignored files (warnings) and others (failures).
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))

    all_findings: dict[str, list[dict[str, Any]]] = {}
    failures: dict[str, list[dict[str, Any]]] = {}
    warnings: dict[str, list[dict[str, Any]]] = {}

    ignored = getattr(state, "ignored_paths", set()) or set()

    for rel in state.file_list:
        logger.info("Scanning PII for: %s...", rel)
        src = fs.read_text(rel)

        found = scan_for_pii(src)
        if not found:
            continue

        payload = [
            {
                "kind": f.kind,
                "severity": f.severity,
                "line": f.line,
                "excerpt": f.excerpt,  # already masked
                "confidence": f.confidence,
            }
            for f in found
        ]
        all_findings[rel] = payload

        rel_posix = rel.replace("\\", "/")
        is_ign = rel_posix in ignored

        # DOWNGRADE: any "fail" in ignored files becomes "warn"
        for p in payload:
            sev = p["severity"]
            if is_ign and sev == "fail":
                p = dict(p)
                p["severity"] = "warn"
                p["confidence"] = "low"  # optional: signal downgraded severity
                warnings.setdefault(rel, []).append(p)
            elif sev == "fail":
                failures.setdefault(rel, []).append(p)
            else:
                warnings.setdefault(rel, []).append(p)

    state.pii_findings = all_findings
    state.pii_failures = failures
    state.pii_warnings = warnings
    return state


async def node_generate_docs(
    state: AgentState, *, config: RunnableConfig
) -> AgentState:
    if not ENABLE_DOC_GENERATION:
        # doc generation disabled
        logger.info("Document generation is disabled. Skipping this step.")
        return state

    fs = ReadOnlySandboxFS(Path(state.root_dir))

    # get model_id from config
    model_id = get_config_value(config, "model_id")

    llm = get_llm(model_id=model_id)
    out_dir = Path(state.out_dir).expanduser().resolve()

    docs: dict[str, str] = {}

    for rel in state.file_list:

        # added this try-except to avoid stopping the whole process if one file fails
        # one situation where it fails is where the file contains secret info
        # that the LLM refuses to process
        try:
            logger.info("Generating doc for: %s...", rel)

            src = fs.read_text(rel)
            res = await generate_doc_for_file(
                llm=llm,
                relpath=Path(rel),
                source=src,
                out_dir=out_dir,
                # ✅ NEW: now docgen uses the request
                request=state.request,
            )
            docs[rel] = str(res.out_path)
        except Exception as e:
            logger.error("Doc generation failed for %s: %s", rel, e)
            docs[rel] = ""

    state.docs = docs
    return state


def node_check_license(state: AgentState) -> AgentState:
    """
    Check that a license file exists and the license type is accepted.
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))

    # We want a list of all repo files (not just python source files).
    # If your ReadOnlySandboxFS doesn't expose this, see note below.
    def _list_all_files() -> list[str]:
        return [str(fs.relpath(p)).replace("\\", "/") for p in fs.list_all_files()]

    res = check_license(
        list_files=_list_all_files,
        read_text=fs.read_text,
        accepted_types=ACCEPTED_LICENSE_TYPES,
    )

    state.license_ok = res.ok
    state.license_info = {
        "ok": res.ok,
        "found_file": res.found_file,
        "detected_type": res.detected_type,
        "message": res.message,
    }

    if res.ok:
        logger.info("License check OK: %s", res.message)
    else:
        logger.warning("License check FAILED: %s", res.message)

    return state


async def node_generate_header_fixes(
    state: AgentState, *, config: RunnableConfig
) -> AgentState:
    if not state.header_issues:
        return state

    if not ENABLE_HEADER_SNIPPET_GENERATION:
        logger.info("Header snippet generation disabled. Skipping this step.")
        return state
    
    fs = ReadOnlySandboxFS(Path(state.root_dir))

    model_id = get_config_value(config, "model_id")
    llm = get_llm(model_id=model_id)

    out_dir = Path(state.out_dir).expanduser().resolve()
    fixes_dir = out_dir / "header_fixes"
    fixes_dir.mkdir(parents=True, exist_ok=True)

    fixes: dict[str, str] = {}

    for rel in state.header_issues.keys():
        logger.info("Generating header snippet for: %s...", rel)

        try:
            detected_license = (getattr(state, "license_info", {}) or {}).get(
                "detected_type"
            ) or "Unknown"

            src = fs.read_text(rel)

            header = await generate_header_snippet(
                llm=llm,
                relpath=Path(rel),
                source=src,
                author="Unknown",
                license_hint=detected_license,
                pyver="3.11",
            )

            # Create a mirrored directory structure under header_fixes
            target = fixes_dir / (Path(rel).as_posix() + ".header.py")
            target.parent.mkdir(parents=True, exist_ok=True)

            # File contains ONLY the header docstring
            target.write_text(header, encoding="utf-8")

            fixes[rel] = str(target)

        except Exception as e:
            logger.error("Header snippet generation failed for %s: %s", rel, e)
            fixes[rel] = ""

    state.header_fixes = fixes
    return state


def node_check_requirements(state: AgentState) -> AgentState:
    """
    Check whether requirements.txt exists at repo root.
    Modified to use ReadOnlySandboxFS.
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))
    repo_root = Path(state.root_dir).expanduser().resolve()

    res = check_requirements_at_root(repo_root=repo_root, fs=fs)

    state.requirements_ok = res.ok
    state.requirements_info = {
        "ok": res.ok,
        "relpath": res.relpath,
        "message": res.message,
        "preview": res.preview,
    }

    if res.ok:
        logger.info("Requirements check OK: %s", res.message)
    else:
        logger.warning("Requirements check FAILED: %s", res.message)

    return state


def node_check_dep_licenses(state: AgentState) -> AgentState:
    """
    Check licenses of direct dependencies from requirements.txt.
    Requires that dependencies are installed in the runtime environment to be accurate.
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))

    # If requirements missing, we cannot proceed reliably
    req_info = getattr(state, "requirements_info", {}) or {}
    if not req_info.get("ok", True):
        state.dep_license_ok = (
            True  # don't fail the run, but warn in report via requirements_info
        )
        state.dep_licenses = []
        state.dep_license_failures = []
        state.dep_license_warnings = []
        return state

    req_text = fs.read_text("requirements.txt")

    res = check_dependency_licenses(
        requirements_text=req_text,
        accepted_licenses=set(ACCEPTED_DEP_LICENSES),
        fail_on_unknown=bool(FAIL_ON_UNKNOWN_DEP_LICENSE),
        fail_on_not_installed=bool(FAIL_ON_NOT_INSTALLED_DEP),
    )

    # Store as JSON-serializable dicts
    state.dep_license_ok = res.ok
    state.dep_licenses = [
        {
            "requirement": d.requirement,
            "distribution": d.distribution,
            "version": d.version,
            "license": d.license,
            "source": d.source,
        }
        for d in res.deps
    ]
    state.dep_license_failures = [
        {
            "requirement": d.requirement,
            "distribution": d.distribution,
            "version": d.version,
            "license": d.license,
            "source": d.source,
        }
        for d in res.failures
    ]
    state.dep_license_warnings = [
        {
            "requirement": d.requirement,
            "distribution": d.distribution,
            "version": d.version,
            "license": d.license,
            "source": d.source,
        }
        for d in res.warnings
    ]

    if res.ok:
        logger.info("Dependency license check OK. %s", res.message)
    else:
        logger.warning("Dependency license check FAILED. %s", res.message)

    return state


def node_load_gitignore(state: AgentState) -> AgentState:
    """
    Load and parse .gitignore from repo root, determine ignored paths.
    Modified to use ReadOnlySandboxFS.
    """
    fs = ReadOnlySandboxFS(Path(state.root_dir))

    try:
        gi = fs.read_text(".gitignore")
    except FileNotFoundError:
        state.ignored_paths = set()
        logger.info("No .gitignore found at repo root.")
        return state

    rules = parse_gitignore(gi)

    # Use list_all_files to know which repo paths exist
    all_files = [str(fs.relpath(p)).replace("\\", "/") for p in fs.list_all_files()]

    ignored = {p for p in all_files if is_ignored(p, rules)}
    state.ignored_paths = ignored

    logger.info("Loaded .gitignore: %d ignored files.", len(ignored))
    for p in ignored:
        logger.info(" - %s", p)

    return state


async def node_finalize(state: AgentState, *, config: RunnableConfig) -> AgentState:
    """
    Finalize run:
    - compute deterministic PASS/WARN/FAIL outcome
    - generate LLM report (markdown) using REPORT_PROMPT
    - write report to out_dir/report_<YYYY-MM-DD>.md

    Notes:
    - Secrets/PII found in .gitignore files are downgraded to WARN (if you implemented that logic
      in the scanning nodes and stored them into secrets_warnings / pii_warnings accordingly).
    """

    # ---- Helper accessors (avoid None surprises) ----
    header_issues = getattr(state, "header_issues", {}) or {}

    secrets_failures = getattr(state, "secrets_failures", {}) or {}
    secrets_warnings = getattr(state, "secrets_warnings", {}) or {}

    pii_failures = getattr(state, "pii_failures", {}) or {}
    pii_warnings = getattr(state, "pii_warnings", {}) or {}

    license_ok = getattr(state, "license_ok", True)
    license_info = getattr(state, "license_info", {}) or {}

    requirements_ok = getattr(state, "requirements_ok", True)
    requirements_info = getattr(state, "requirements_info", {}) or {}
    req_status = "OK" if requirements_ok else "MISSING"

    dep_failures = getattr(state, "dep_license_failures", []) or []
    dep_warnings = getattr(state, "dep_license_warnings", []) or []

    docs = getattr(state, "docs", {}) or {}

    # ---- Counts ----
    hard_pii_count = sum(len(v) for v in pii_failures.values())
    warn_pii_count = sum(len(v) for v in pii_warnings.values())

    secrets_fail_files = len(secrets_failures)
    secrets_warn_files = len(secrets_warnings)

    # ---- Determine deterministic outcome ----
    fail_reasons: list[str] = []
    warn_reasons: list[str] = []

    # FAIL conditions
    if secrets_fail_files > 0:
        fail_reasons.append("Secrets detected (non-ignored files)")

    if hard_pii_count > 0:
        fail_reasons.append("PII hard failures detected (non-ignored files)")

    if not license_ok:
        fail_reasons.append("Repository license check failed")

    if len(dep_failures) > 0:
        fail_reasons.append("Dependency license failures")

    # WARN conditions (only if not FAIL)
    if secrets_warn_files > 0:
        warn_reasons.append("Secrets detected in .gitignore files (downgraded to WARN)")

    if warn_pii_count > 0:
        warn_reasons.append(
            "PII warnings (includes downgraded findings from .gitignore files)"
        )

    if not requirements_ok:
        warn_reasons.append(
            "requirements.txt missing at repository root (dependency checks incomplete)"
        )

    if len(dep_warnings) > 0:
        warn_reasons.append(
            "Dependency license warnings (UNKNOWN/NOT_INSTALLED/ambiguous)"
        )

    if fail_reasons:
        overall = "FAIL"
    elif warn_reasons:
        overall = "WARN"
    else:
        overall = "PASS"

    # ---- Summary string (human readable) ----
    state.summary = (
        f"Outcome: {overall}\n"
        f"Processed {len(state.file_list)} files.\n"
        f"Repository license: {'OK' if license_ok else 'FAILED'}\n"
        f"requirements.txt at root: {req_status}\n"
        f"Dependency licenses: failures={len(dep_failures)}, warnings={len(dep_warnings)}\n"
        f"Header issues: {len(header_issues)} files.\n"
        f"Secrets: FAIL files={secrets_fail_files}, WARN files={secrets_warn_files}\n"
        f"PII hard failures: {hard_pii_count} findings in {len(pii_failures)} files.\n"
        f"PII warnings: {warn_pii_count} findings in {len(pii_warnings)} files.\n"
        f"Docs generated: {len(docs)} files.\n"
        f"Output dir: {state.out_dir}\n"
    )
    if fail_reasons:
        state.summary += "Fail reasons: " + "; ".join(fail_reasons) + "\n"
    elif warn_reasons:
        state.summary += "Warn reasons: " + "; ".join(warn_reasons) + "\n"

    # ---- Generate report via LLM ----
    model_id = get_config_value(config, "model_id")
    llm = get_llm(model_id=model_id)

    now_iso = datetime.now(timezone.utc).isoformat(timespec="minutes")

    # For REPORT_PROMPT: keep backward compatibility with your existing placeholder name `secret_issues`
    # by passing only the FAIL set there (policy-critical), and optionally include warnings in requirements_check.
    prompt = REPORT_PROMPT.format(
        root_dir=state.root_dir,
        now_datetime=now_iso,
        num_files=len(state.file_list),
        header_issues=header_issues,
        secret_issues=secrets_failures,  # only non-ignored failures
        license_check=license_info,
        dep_license_failures=dep_failures,
        dep_license_warnings=dep_warnings,
        pii_hard_failures=pii_failures,
        pii_warnings=pii_warnings,
        requirements_check={
            **requirements_info,
            # include extra detail for the report without changing your state model
            "requirements_status": req_status,
            "secrets_warnings_ignored_files": secrets_warnings,
        },
    )

    text, _ = await call_llm_normalized(llm, prompt)

    logger.info("")
    logger.info("Final report: %s", text)

    # ---- Save to file ----
    current_day = now_iso[:10]
    out_dir = Path(state.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"report_{current_day}.md"
    out_path.write_text(text.rstrip() + "\n", encoding="utf-8")

    return state


# ---- Graph ----


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("discover_files", node_discover_files)

    # sequentially here we process all the files discovered
    g.add_node("load_gitignore", node_load_gitignore)
    g.add_node("check_headers", node_check_headers)
    g.add_node("scan_secrets", node_scan_secrets)
    g.add_node("check_license", node_check_license)
    g.add_node("scan_pii", node_scan_pii)
    g.add_node("check_requirements", node_check_requirements)
    g.add_node("check_dep_licenses", node_check_dep_licenses)
    g.add_node("generate_header_fixes", node_generate_header_fixes)
    g.add_node("generate_docs", node_generate_docs)
    g.add_node("finalize", node_finalize)

    g.set_entry_point("discover_files")
    g.add_edge("discover_files", "load_gitignore")
    g.add_edge("load_gitignore", "check_requirements")
    g.add_edge("check_requirements", "check_license")
    g.add_edge("check_license", "check_dep_licenses")
    g.add_edge("check_dep_licenses", "check_headers")
    g.add_edge("check_headers", "generate_header_fixes")
    g.add_edge("generate_header_fixes", "scan_secrets")
    g.add_edge("scan_secrets", "scan_pii")
    g.add_edge("scan_pii", "generate_docs")
    g.add_edge("generate_docs", "finalize")
    g.add_edge("finalize", END)

    return g.compile()


async def run_agent(graph, *, root_dir: str, out_dir: str, request: str) -> AgentState:
    # here we define the initial state
    state = AgentState(request=request, root_dir=root_dir, out_dir=out_dir)

    # here we define the config for the run of the agent
    cfg = {"configurable": {"model_id": LLM_MODEL_ID}}

    logger.info("")
    logger.info("Running agent with config: %s...", cfg)
    logger.info("")

    # LangGraph returns the final state
    final_state = await graph.ainvoke(state, config=cfg)

    return final_state
