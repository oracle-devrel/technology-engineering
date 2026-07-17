#!/usr/bin/env python3
"""OP04 identity and rendering contract backed by a protected v2 blueprint."""
from __future__ import annotations
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_RE = re.compile(r"^(?P<environment>[a-z][a-z0-9]{0,30})-(?P<project_name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$")
OCID_RE = re.compile(r"^ocid1\.(?P<kind>tenancy|compartment)\.oc1\.\.[A-Za-z0-9_-]+$")
REGION_RE = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
RUNTIME_CONTRACT_PATH = ".github/project-onboarding-contract.json"


class ContractError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectIdentity:
    slug: str
    environment: str
    project_name: str
    @property
    def compact(self) -> str: return self.project_name
    @property
    def title(self) -> str: return "Project " + self.project_name.replace("-", " ").title()


@dataclass(frozen=True)
class Baseline:
    tenancy_ocid: str
    region: str
    parent_compartment_id: str
    evidence_count: int
    normalized_manifest: str


def git_text(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", *args], cwd=repo, text=True, capture_output=True, timeout=15, check=False)
    if result.returncode: raise ContractError("Git contract inspection failed.")
    return result.stdout


def load_at(repo: Path, ref: str, path: str) -> Any:
    try: return json.loads(git_text(repo, "show", f"{ref}:{path}"))
    except (json.JSONDecodeError, ContractError) as error: raise ContractError("The onboarding contract is invalid.") from error


def validate_project(project: str) -> ProjectIdentity:
    match = PROJECT_RE.fullmatch(project)
    if match is None or len(match.group("project_name")) > 30: raise ContractError("The project must match <environment>-<dns-name>.")
    return ProjectIdentity(project, match.group("environment"), match.group("project_name"))


def validate_runtime_contract(repo: Path, ref: str, environment: str) -> dict[str, Any]:
    contract = load_at(repo, ref, RUNTIME_CONTRACT_PATH)
    required = {
        "contract_version", "project_slug_pattern", "project_name_max_length",
        "same_slug_repository", "allowed_environments", "environment_blueprints",
        "target_repository_prefixes", "repository_layouts",
        "handoff_path_template", "op04_template",
    }
    allowed = ["dev", "test", "uat", "prod"]
    prefixes = {"dev": "nonprod", "test": "nonprod", "uat": "nonprod", "prod": "prod"}
    layouts = {"dev": "shared-nonprod-v2", "test": "shared-nonprod-v2", "uat": "shared-nonprod-v2", "prod": "production-v1"}
    if (
        not isinstance(contract, dict)
        or set(contract) != required
        or contract.get("contract_version") != 2
        or contract.get("project_slug_pattern") != r"^(?:dev|test|uat|prod)-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
        or contract.get("project_name_max_length") != 30
        or contract.get("same_slug_repository") is not False
        or contract.get("allowed_environments") != allowed
        or set(contract.get("environment_blueprints", {})) != set(allowed)
        or contract.get("target_repository_prefixes") != prefixes
        or contract.get("repository_layouts") != layouts
        or contract.get("handoff_path_template") != "environments/{environment}/environment_information.md"
        or environment not in allowed
    ):
        raise ContractError(f"The landing-zone runtime does not support governed {environment} onboarding.")
    return contract


def derive_baseline(repo: Path, ref: str, environment: str) -> Baseline:
    contract = validate_runtime_contract(repo, ref, environment)
    blueprint = load_at(repo, ref, contract["environment_blueprints"][environment])
    template = load_at(repo, ref, contract["op04_template"])
    if blueprint.get("schema_version") != 2 or blueprint.get("environment") != environment or not REGION_RE.fullmatch(str(blueprint.get("region", ""))): raise ContractError("The protected environment blueprint is invalid.")
    tenancy, parent = blueprint.get("tenancy_ocid"), blueprint.get("parent_compartment_ocid")
    if not OCID_RE.fullmatch(str(tenancy)) or not OCID_RE.fullmatch(str(parent)): raise ContractError("The protected environment blueprint contains invalid identifiers.")
    return Baseline(tenancy, blueprint["region"], parent, 1, json.dumps(template, sort_keys=True, separators=(",", ":")))


def replace(value: Any, identity: ProjectIdentity) -> Any:
    mapping = {"__PROJECT_UPPER__": identity.compact.upper(), "__project_lower__": identity.compact, "__Project_Title__": identity.title, "__environment__": identity.environment, "__ENVIRONMENT_UPPER__": identity.environment.upper(), "__Environment_Title__": identity.environment.replace("-", " ").title()}
    if isinstance(value, str):
        for old, new in mapping.items(): value = value.replace(old, new)
        return value
    if isinstance(value, list): return [replace(item, identity) for item in value]
    if isinstance(value, dict): return {replace(key, identity): replace(item, identity) for key, item in value.items()}
    return value


def expected_credentials(baseline: Baseline) -> dict[str, str]: return {"tenancy_ocid": baseline.tenancy_ocid, "region": baseline.region}


def expected_manifest(project: str, baseline: Baseline) -> dict[str, Any]:
    value = replace(json.loads(baseline.normalized_manifest), validate_project(project))
    value["compartments_configuration"]["default_parent_id"] = baseline.parent_compartment_id
    return value


def expected_readme(project: str) -> str:
    identity = validate_project(project)
    return f"# OP04 Project Foundation: {identity.environment}/{identity.slug}\n\nPlatform-owned project foundation. Authentication uses the runner identity. State: `op04_manage_project/{identity.environment}/{identity.slug}/terraform.tfstate`.\n"


def expected_files(project: str, baseline: Baseline) -> dict[str, bytes]:
    identity = validate_project(project); root = f"op04_manage_project/{identity.environment}/{identity.slug}"
    return {f"{root}/README.md": expected_readme(project).encode(), f"{root}/oci-credentials.tfvars.json": (json.dumps(expected_credentials(baseline), indent=2)+"\n").encode(), f"{root}/oe_manage_project_{identity.environment}_{identity.slug}_iam.auto.tfvars.json": (json.dumps(expected_manifest(project, baseline), indent=2)+"\n").encode()}
