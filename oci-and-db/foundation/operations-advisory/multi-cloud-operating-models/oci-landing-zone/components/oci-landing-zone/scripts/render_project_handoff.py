import argparse
import json
import re
from pathlib import Path


REGION = "eu-frankfurt-1"
VCN_KEY = "VCN-FRA-LZP-P-PROJECTS-KEY"
SUBNET_KEYS = {
    "web": "SSN-FRA-LZP-P-WEB-KEY",
    "app": "SSN-FRA-LZP-P-APP-KEY",
    "database": "SSN-FRA-LZP-P-DB-KEY",
    "infrastructure": "SSN-FRA-LZP-P-INFRA",
}
PROJECT_PATTERN = re.compile(
    r"^(?P<environment>dev|test|uat|prod)-"
    r"(?P<project_name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)$"
)
PLACEHOLDER_PATTERN = re.compile(r"<[^<>\r\n]+>")


class HandoffError(ValueError):
    pass


def load_json(path):
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        # `terraform output -json` wraps every output in metadata. Accept that
        # local state representation while keeping the renderer's contract flat.
        if isinstance(value, dict) and value and all(
            isinstance(item, dict) and "value" in item for item in value.values()
        ):
            return {key: item["value"] for key, item in value.items()}
        return value
    except OSError as exc:
        raise HandoffError(f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise HandoffError(f"invalid JSON in {path}: {exc}") from exc


def require_mapping(value, label):
    if not isinstance(value, dict):
        raise HandoffError(f"{label} must be a JSON object")
    return value


def validate_project(project):
    match = PROJECT_PATTERN.fullmatch(project)
    if match is None:
        raise HandoffError(f"invalid project input: {project!r}")
    project_name = match.group("project_name")
    if len(project_name) > 30:
        raise HandoffError(f"invalid project input: {project!r}")
    return match.group("environment"), project_name


def find_project_config(project_directory):
    candidates = []
    for path in sorted(Path(project_directory).glob("*.auto.tfvars.json")):
        data = require_mapping(
            load_json(path),
            f"OP04 project configuration {path}",
        )
        if "compartments_configuration" in data:
            candidates.append((path, data))
    if len(candidates) != 1:
        raise HandoffError(
            "expected exactly one active OP04 *.auto.tfvars.json file "
            f"containing compartments_configuration; found {len(candidates)}"
        )
    return candidates[0][1]


def require_ocid(mapping, key, prefix, label):
    item = mapping.get(key)
    if not isinstance(item, dict):
        raise HandoffError(f"missing {label} logical key {key}")
    ocid = item.get("id")
    if not isinstance(ocid, str) or not ocid.startswith(prefix):
        raise HandoffError(
            f"{label} {key} does not contain an OCID starting with {prefix}"
        )
    return ocid


def require_text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise HandoffError(f"missing {label}")
    if PLACEHOLDER_PATTERN.fullmatch(value.strip()):
        raise HandoffError(f"{label} must not be a placeholder token")
    return value


def build_handoff_data(
    project,
    project_config,
    op04_output,
    op02_output,
    network_config,
):
    environment, project_name = validate_project(project)
    project_token = project_name.upper()
    project_config = require_mapping(
        project_config,
        "OP04 project configuration",
    )
    op04_output = require_mapping(op04_output, "OP04 output")
    op02_output = require_mapping(op02_output, "OP02 output")
    network_config = require_mapping(
        network_config,
        "network configuration",
    )

    compartment_config = require_mapping(
        project_config.get("compartments_configuration"),
        "compartments_configuration",
    )
    parents = require_mapping(
        compartment_config.get("compartments"),
        "compartments_configuration.compartments",
    )
    if len(parents) != 1:
        raise HandoffError(
            f"expected exactly one project parent compartment; found {len(parents)}"
        )
    parent_key, parent = next(iter(parents.items()))
    if f"-{project_token}-" not in parent_key:
        raise HandoffError(
            f"project parent key {parent_key} does not contain {project_token}"
        )
    if not parent_key.endswith("-KEY"):
        raise HandoffError(
            f"project parent key {parent_key} must end in -KEY"
        )
    children = require_mapping(
        require_mapping(parent, f"project parent {parent_key}").get("children"),
        f"children for {parent_key}",
    )
    child_prefix = parent_key[:-len("-KEY")]
    expected_roles = {
        "app": ("application", f"{child_prefix}-APP-KEY"),
        "database": ("database", f"{child_prefix}-DB-KEY"),
        "infrastructure": (
            "infrastructure",
            f"{child_prefix}-INFRA-KEY",
        ),
    }
    role_keys = {}
    for role, (label, key) in expected_roles.items():
        if key not in children:
            raise HandoffError(
                f"missing {label} compartment logical key {key}"
            )
        role_keys[role] = key

    state_compartments = require_mapping(
        require_mapping(op04_output, "iam_resources").get("compartments"),
        "iam_resources.compartments",
    )
    compartments = {
        role: {
            "key": key,
            "ocid": require_ocid(
                state_compartments,
                key,
                "ocid1.compartment.",
                f"{role} compartment",
            ),
        }
        for role, key in role_keys.items()
    }

    state_network = require_mapping(op02_output, "network_resources")
    state_vcns = require_mapping(state_network.get("vcns"), "network_resources.vcns")
    state_subnets = require_mapping(
        state_network.get("subnets"),
        "network_resources.subnets",
    )

    network_root = require_mapping(
        network_config.get("network_configuration"),
        "network_configuration",
    )
    categories = require_mapping(
        network_root.get("network_configuration_categories"),
        "network_configuration_categories",
    )
    environment_category = require_mapping(
        categories.get(environment), f"{environment} network category"
    )
    configured_vcns = require_mapping(environment_category.get("vcns"), f"{environment}.vcns")
    configured_vcn = require_mapping(
        configured_vcns.get(VCN_KEY),
        f"configured VCN {VCN_KEY}",
    )
    configured_subnets = require_mapping(
        configured_vcn.get("subnets"),
        f"subnets for {VCN_KEY}",
    )

    cidr_blocks = configured_vcn.get("cidr_blocks")
    if (
        not isinstance(cidr_blocks, list)
        or len(cidr_blocks) != 1
        or not isinstance(cidr_blocks[0], str)
        or not cidr_blocks[0].strip()
    ):
        raise HandoffError(f"{VCN_KEY} must contain exactly one CIDR block")
    vcn_cidr = require_text(cidr_blocks[0], f"{VCN_KEY} CIDR")
    vcn = {
        "key": VCN_KEY,
        "name": require_text(
            configured_vcn.get("display_name"),
            f"{VCN_KEY} name",
        ),
        "cidr": vcn_cidr,
        "ocid": require_ocid(
            state_vcns,
            VCN_KEY,
            "ocid1.vcn.",
            "projects VCN",
        ),
    }

    subnets = {}
    for role, key in SUBNET_KEYS.items():
        configured_subnet = require_mapping(
            configured_subnets.get(key),
            f"configured subnet {key}",
        )
        subnets[role] = {
            "key": key,
            "name": require_text(
                configured_subnet.get("display_name"),
                f"{key} name",
            ),
            "cidr": require_text(
                configured_subnet.get("cidr_block"),
                f"{key} CIDR",
            ),
            "ocid": require_ocid(
                state_subnets,
                key,
                "ocid1.subnet.",
                f"{role} subnet",
            ),
        }

    return {
        "project": project,
        "environment": environment,
        "region": REGION,
        "compartments": compartments,
        "vcn": vcn,
        "subnets": subnets,
    }


def render_markdown(data):
    compartments = data["compartments"]
    vcn = data["vcn"]
    subnets = data["subnets"]
    compartment_rows = "\n".join(
        (
            (
                f"| App compartment | {compartments['app']['key']} | "
                f"{compartments['app']['ocid']} |"
            ),
            (
                f"| DB compartment | {compartments['database']['key']} | "
                f"{compartments['database']['ocid']} |"
            ),
            (
                "| Infra compartment | "
                f"{compartments['infrastructure']['key']} | "
                f"{compartments['infrastructure']['ocid']} |"
            ),
        )
    )
    subnet_rows = "\n".join(
        (
            (
                f"| Web subnet | {subnets['web']['key']} | "
                f"{subnets['web']['name']} | {subnets['web']['cidr']} | "
                f"{subnets['web']['ocid']} |"
            ),
            (
                f"| App subnet | {subnets['app']['key']} | "
                f"{subnets['app']['name']} | {subnets['app']['cidr']} | "
                f"{subnets['app']['ocid']} |"
            ),
            (
                f"| DB subnet | {subnets['database']['key']} | "
                f"{subnets['database']['name']} | "
                f"{subnets['database']['cidr']} | "
                f"{subnets['database']['ocid']} |"
            ),
            (
                "| Infra subnet | "
                f"{subnets['infrastructure']['key']} | "
                f"{subnets['infrastructure']['name']} | "
                f"{subnets['infrastructure']['cidr']} | "
                f"{subnets['infrastructure']['ocid']} |"
            ),
        )
    )
    return f"""# Project Environment Information

This file is the human-readable representation of the validated
`project-foundation-handoff.json` artifact. Deployment workflows do not parse
it; executable intent remains in JSON under `oci/{data['region']}/`.

Do not store secrets, passwords, private keys, or user credentials here.

## Handoff Status

| Reference | Value |
|-----------|-------|
| Project | {data['project']} |
| Environment | {data['environment']} |
| OCI region | {data['region']} |

## OP04 Project Foundation

| Reference | Logical key | OCID |
|-----------|-------------|------|
{compartment_rows}

## Landing-Zone Network

| Reference | Logical key | Name | CIDR | OCID |
|-----------|-------------|------|------|------|
| Projects VCN | {vcn['key']} | {vcn['name']} | {vcn['cidr']} | {vcn['ocid']} |
{subnet_rows}

## Manifest Locations

| Change type | Manifest path |
|-------------|---------------|
| Project NSGs | `oci/{data['environment']}/{data['region']}/network/project-nsgs.json` |
| OCI ADB | `oci/{data['environment']}/{data['region']}/database/database.json` |
| OCI compute | `oci/{data['environment']}/{data['region']}/compute/compute.json` |
| Day 2 operations | `oci/{data['environment']}/{data['region']}/lifecycle_operations/` |
"""


def generate_document(
    project,
    project_directory,
    op04_output_path,
    op02_output_path,
    network_config_path,
):
    validate_project(project)
    project_directory = Path(project_directory)
    if not project_directory.is_dir():
        raise HandoffError(
            f"project directory {project_directory} is missing or not a directory"
        )
    if project_directory.name != project:
        raise HandoffError(
            f"project directory {project_directory} does not match "
            f"requested project {project!r} ({project.upper()})"
        )
    project_config = find_project_config(project_directory)
    data = build_handoff_data(
        project=project,
        project_config=project_config,
        op04_output=load_json(op04_output_path),
        op02_output=load_json(op02_output_path),
        network_config=load_json(network_config_path),
    )
    return data, render_markdown(data)


def build_machine_handoff(data, source, op02_state_key, op04_state_key, target_repository, handoff_path):
    """Return the credential-free shared-nonprod-v2 handoff contract."""
    required_source = {"repository", "workflow", "run", "commit"}
    if set(source) != required_source or not all(isinstance(value, str) and value for value in source.values()):
        raise HandoffError("handoff provenance is incomplete")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repository"]):
        raise HandoffError("source repository is invalid")
    if not source["run"].isdigit() or not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
        raise HandoffError("source run or commit is invalid")
    if not all(isinstance(value, str) and value.endswith("terraform.tfstate") for value in (op02_state_key, op04_state_key)):
        raise HandoffError("handoff state keys are invalid")
    if data["environment"] not in {"dev", "test", "uat"}:
        raise HandoffError("shared non-production handoff environment is invalid")
    expected_repository = (
        rf"nonprod-[a-z][a-z0-9-]*" if data["environment"] != "prod"
        else rf"prod-[a-z][a-z0-9-]*"
    )
    if not re.fullmatch(expected_repository, target_repository):
        raise HandoffError("target repository does not match the foundation environment")
    expected_path = f"environments/{data['environment']}/environment_information.md"
    if handoff_path != expected_path:
        raise HandoffError("shared non-production handoff path is invalid")
    return {
        "schema_version": 2,
        "cloud": "oci",
        "project_slug": target_repository,
        "environment": data["environment"],
        "region": data["region"],
        "app_compartment": data["compartments"]["app"]["ocid"],
        "database_compartment": data["compartments"]["database"]["ocid"],
        "infrastructure_compartment": data["compartments"]["infrastructure"]["ocid"],
        "vcn": data["vcn"]["ocid"],
        "subnets": {role: value["ocid"] for role, value in data["subnets"].items()},
        "source_repository": source["repository"],
        "source_workflow": source["workflow"],
        "source_run": source["run"],
        "source_commit": source["commit"],
        "op02_state_key": op02_state_key,
        "op04_state_key": op04_state_key,
        "repository_layout": "production-v1" if data["environment"] == "prod" else "shared-nonprod-v2",
        "target_repository": target_repository,
        "handoff_path": handoff_path,
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Render a validated OCI project handoff document."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-directory", required=True, type=Path)
    parser.add_argument("--op04-output", required=True, type=Path)
    parser.add_argument("--op02-output", required=True, type=Path)
    parser.add_argument("--network-config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--handoff-output", type=Path)
    parser.add_argument("--source-repository")
    parser.add_argument("--source-workflow")
    parser.add_argument("--source-run")
    parser.add_argument("--source-commit")
    parser.add_argument("--op02-state-key")
    parser.add_argument("--op04-state-key")
    parser.add_argument("--target-repository")
    parser.add_argument("--handoff-path")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        data, document = generate_document(
            project=args.project,
            project_directory=args.project_directory,
            op04_output_path=args.op04_output,
            op02_output_path=args.op02_output,
            network_config_path=args.network_config,
        )
    except HandoffError as exc:
        parser.error(str(exc))
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(document, encoding="utf-8")
        if args.handoff_output:
            machine_args = (
                args.source_repository, args.source_workflow, args.source_run,
                args.source_commit, args.op02_state_key, args.op04_state_key,
                args.target_repository, args.handoff_path,
            )
            if not all(machine_args):
                raise HandoffError("machine handoff requires complete provenance and state keys")
            handoff = build_machine_handoff(
                data,
                {"repository": args.source_repository, "workflow": args.source_workflow,
                 "run": args.source_run, "commit": args.source_commit},
                args.op02_state_key, args.op04_state_key,
                args.target_repository, args.handoff_path,
            )
            args.handoff_output.parent.mkdir(parents=True, exist_ok=True)
            args.handoff_output.write_text(
                json.dumps(handoff, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    except (OSError, HandoffError) as exc:
        parser.error(f"cannot write {args.output}: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
