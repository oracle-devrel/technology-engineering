#!/usr/bin/env python3
"""Render the credential-free OP04 handoff from protected evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PROJECT_PATTERN = re.compile(
    r"^(?P<environment>dev|test|uat|prod)-"
    r"(?P<project_name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$"
)
REGION_PATTERN = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
OCID_PATTERN = re.compile(
    r"^ocid1\.(?P<kind>compartment|vcn|subnet)\.oc1"
    r"\.(?:[a-z0-9-]+)?\.[A-Za-z0-9_-]+$"
)


class HandoffError(ValueError):
    """Raised when state and protected evidence do not match."""


def load_json(path):
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HandoffError(f"cannot read valid JSON from {path}") from exc
    if isinstance(value, dict) and value and all(
        isinstance(item, dict) and "value" in item for item in value.values()
    ):
        return {key: item["value"] for key, item in value.items()}
    return value


def require_mapping(value, label):
    if not isinstance(value, dict):
        raise HandoffError(f"{label} must be a JSON object")
    return value


def validate_project(project):
    match = PROJECT_PATTERN.fullmatch(project)
    if match is None or len(match.group("project_name")) > 30:
        raise HandoffError(f"invalid project input: {project!r}")
    return match.group("environment"), match.group("project_name")


def require_ocid(mapping, key, kind, label):
    value = mapping.get(key)
    ocid = value.get("id") if isinstance(value, dict) else None
    match = OCID_PATTERN.fullmatch(str(ocid))
    if match is None or match.group("kind") != kind:
        raise HandoffError(f"missing {label} output for logical key {key}")
    return ocid


def find_project_config(project_directory):
    candidates = []
    for path in sorted(Path(project_directory).glob("generated/*.json")):
        value = load_json(path)
        if isinstance(value, dict) and "compartments_configuration" in value:
            candidates.append(value)
    if len(candidates) != 1:
        raise HandoffError(
            "expected one generated OP04 project configuration"
        )
    return candidates[0]


def build_handoff_data(project, project_config, op04_output, blueprint):
    environment, project_name = validate_project(project)
    if (
        blueprint.get("schema_version") != 2
        or blueprint.get("environment") != environment
        or REGION_PATTERN.fullmatch(str(blueprint.get("region", ""))) is None
    ):
        raise HandoffError("protected environment blueprint is invalid")
    parent_key = f"CMP-LZ-{environment.upper()}-{project_name.upper()}-KEY"
    compartments_config = require_mapping(
        project_config.get("compartments_configuration"),
        "compartments_configuration",
    )
    parents = require_mapping(
        compartments_config.get("compartments"),
        "compartments_configuration.compartments",
    )
    if set(parents) != {parent_key}:
        raise HandoffError("generated OP04 parent compartment is invalid")
    iam_resources = require_mapping(
        op04_output.get("iam_resources"),
        "iam_resources",
    )
    state_compartments = require_mapping(
        iam_resources.get("compartments"),
        "iam_resources.compartments",
    )
    project_ocid = require_ocid(
        state_compartments,
        parent_key,
        "compartment",
        "project compartment",
    )
    compartments = {
        role: {
            "key": parent_key,
            "ocid": project_ocid,
        }
        for role in ("app", "database", "infrastructure")
    }
    network = require_mapping(blueprint.get("network"), "blueprint network")
    vcn = require_mapping(network.get("vcn"), "blueprint VCN")
    subnets = require_mapping(network.get("subnets"), "blueprint subnets")
    if set(subnets) != {"web", "app", "database", "infrastructure"}:
        raise HandoffError("protected subnet evidence is incomplete")
    return {
        "project": project,
        "environment": environment,
        "region": blueprint["region"],
        "compartments": compartments,
        "vcn": vcn,
        "subnets": subnets,
    }


def render_markdown(data):
    _, project_name = validate_project(data["project"])
    project_compartment = data["compartments"]["app"]
    subnet_labels = {
        "web": "Web subnet",
        "app": "App subnet",
        "database": "DB subnet",
        "infrastructure": "Infra subnet",
    }
    subnet_rows = "\n".join(
        f"| {subnet_labels[role]} | {value['key']} | {value['name']} | "
        f"{value['cidr']} | {value['ocid']} |"
        for role, value in data["subnets"].items()
    )
    vcn = data["vcn"]
    return f"""# Project Environment Information

This credential-free document is the human-readable representation of the
validated `project-foundation-handoff.json` artifact.

| Reference | Value |
|---|---|
| Project | {project_name} |
| Environment | {data['environment']} |
| OCI region | {data['region']} |

## OP04 project compartment

| Role | Logical key | OCID |
|---|---|---|
| App compartment | {project_compartment['key']} | {project_compartment['ocid']} |
| DB compartment | {project_compartment['key']} | {project_compartment['ocid']} |
| Infra compartment | {project_compartment['key']} | {project_compartment['ocid']} |

The machine handoff's application, database, and infrastructure compartment
fields are compatibility aliases for this same OE `v3.1.0` project
compartment.

## OP02 network

| Role | Logical key | Name | CIDR | OCID |
|---|---|---|---|---|
| Projects VCN | {vcn['key']} | {vcn['name']} | {vcn['cidr']} | {vcn['ocid']} |
{subnet_rows}

## Manifest locations

| Change type | Path |
|---|---|
| Project NSGs | `oci/{data['environment']}/{data['region']}/network/project-nsgs.json` |
| OCI databases | `oci/{data['environment']}/{data['region']}/database/database.json` |
| OCI compute | `oci/{data['environment']}/{data['region']}/compute/compute.json` |
| Day 2 | `oci/{data['environment']}/{data['region']}/lifecycle_operations/` |
"""


def build_machine_handoff(
    data,
    source,
    op02_state_key,
    op04_state_key,
    target_repository,
    handoff_path,
):
    required_source = {"repository", "workflow", "run", "commit"}
    if set(source) != required_source or not all(source.values()):
        raise HandoffError("handoff provenance is incomplete")
    environment, project_name = validate_project(data["project"])
    expected_repository = (
        f"prod-{project_name}"
        if environment == "prod"
        else f"nonprod-{project_name}"
    )
    expected_path = f"environments/{environment}/environment_information.md"
    if (
        target_repository != expected_repository
        or handoff_path != expected_path
        or not re.fullmatch(r"[0-9a-f]{40}", source["commit"])
        or not str(source["run"]).isdigit()
    ):
        raise HandoffError("handoff routing or provenance is invalid")
    return {
        "schema_version": 2,
        "cloud": "oci",
        "project_slug": target_repository,
        "environment": environment,
        "region": data["region"],
        "app_compartment": data["compartments"]["app"]["ocid"],
        "database_compartment": data["compartments"]["database"]["ocid"],
        "infrastructure_compartment":
            data["compartments"]["infrastructure"]["ocid"],
        "vcn": data["vcn"]["ocid"],
        "subnets": {
            role: value["ocid"] for role, value in data["subnets"].items()
        },
        "source_repository": source["repository"],
        "source_workflow": source["workflow"],
        "source_run": str(source["run"]),
        "source_commit": source["commit"],
        "op02_state_key": op02_state_key,
        "op04_state_key": op04_state_key,
        "repository_layout":
            "production-v1"
            if environment == "prod"
            else "shared-nonprod-v2",
        "target_repository": target_repository,
        "handoff_path": handoff_path,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-directory", required=True, type=Path)
    parser.add_argument("--op04-output", required=True, type=Path)
    parser.add_argument("--environment-blueprint", required=True, type=Path)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-workflow", required=True)
    parser.add_argument("--source-run", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--op02-state-key", required=True)
    parser.add_argument("--op04-state-key", required=True)
    parser.add_argument("--target-repository", required=True)
    parser.add_argument("--handoff-path", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--handoff-output", required=True, type=Path)
    args = parser.parse_args()
    try:
        data = build_handoff_data(
            args.project,
            find_project_config(args.project_directory),
            load_json(args.op04_output),
            load_json(args.environment_blueprint),
        )
        document = render_markdown(data)
        handoff = build_machine_handoff(
            data,
            {
                "repository": args.source_repository,
                "workflow": args.source_workflow,
                "run": args.source_run,
                "commit": args.source_commit,
            },
            args.op02_state_key,
            args.op04_state_key,
            args.target_repository,
            args.handoff_path,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
        args.handoff_output.write_text(
            json.dumps(handoff, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (HandoffError, OSError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
