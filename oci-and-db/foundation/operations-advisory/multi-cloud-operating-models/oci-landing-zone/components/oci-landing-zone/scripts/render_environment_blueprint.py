#!/usr/bin/env python3
"""Create protected project-onboarding evidence from foundation outputs."""

import argparse
import json
import re
from pathlib import Path


TENANCY_OCID = re.compile(r"^ocid1\.tenancy\.oc1\.\.[A-Za-z0-9_-]+$")
COMPARTMENT_OCID = re.compile(
    r"^ocid1\.compartment\.oc1\.\.[A-Za-z0-9_-]+$"
)
RESOURCE_OCID = re.compile(
    r"^ocid1\.(?P<kind>vcn|subnet)\.oc1\.[a-z0-9-]+\."
    r"[A-Za-z0-9_-]+$"
)
SHA = re.compile(r"^[0-9a-f]{40}$")
ENVIRONMENT = re.compile(r"^(dev|test|uat|prod)$")
REGION = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW = "oci-op02-terraform.yaml"
SUBNET_ROLES = {
    "web": "-WEB-KEY",
    "app": "-APP-KEY",
    "database": "-DB-KEY",
    "infrastructure": "-INFRA-KEY",
}
COMPARTMENT_ROLES = {
    "projects": "-PROJECTS-KEY",
    "network": "-NETWORK-KEY",
    "security": "-SECURITY-KEY",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def require_resource(resources, key, kind):
    value = resources.get(key)
    ocid = value.get("id") if isinstance(value, dict) else None
    match = RESOURCE_OCID.fullmatch(str(ocid))
    if match is None or match.group("kind") != kind:
        raise SystemExit(f"missing {kind} output for logical key {key}")
    return ocid


def find_environment_network(network_config, environment):
    categories = (
        network_config.get("network_configuration", {})
        .get("network_configuration_categories", {})
    )
    matches = [
        value
        for key, value in categories.items()
        if key == environment
        or re.fullmatch(rf"\d+-{re.escape(environment)}", key)
    ]
    if len(matches) != 1:
        raise SystemExit(
            f"expected one generated network category for {environment}"
        )
    vcns = matches[0].get("vcns", {})
    if not isinstance(vcns, dict) or len(vcns) != 1:
        raise SystemExit(
            f"expected one generated projects VCN for {environment}"
        )
    return next(iter(vcns.items()))


def main():
    parser = argparse.ArgumentParser()
    for name in (
        "environment",
        "region",
        "tenancy-ocid",
        "iam-output",
        "network-output",
        "network-config",
        "repository",
        "run-id",
        "commit-sha",
        "output",
    ):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()

    if not all(
        (
            TENANCY_OCID.fullmatch(args.tenancy_ocid),
            SHA.fullmatch(args.commit_sha),
            ENVIRONMENT.fullmatch(args.environment),
            REGION.fullmatch(args.region),
            REPOSITORY.fullmatch(args.repository),
            args.run_id.isdigit(),
        )
    ):
        raise SystemExit("invalid foundation provenance or identifiers")

    iam = load_json(args.iam_output)
    network = load_json(args.network_output)
    network_config = load_json(args.network_config)
    compartments = iam.get("compartments", {})
    state_vcns = network.get("vcns", {})
    state_subnets = network.get("subnets", {})
    environment_token = args.environment.upper()
    environment_compartments = {}
    for role, suffix in COMPARTMENT_ROLES.items():
        key = f"CMP-LZ-{environment_token}{suffix}"
        value = compartments.get(key, {})
        ocid = value.get("id") if isinstance(value, dict) else None
        if COMPARTMENT_OCID.fullmatch(str(ocid)) is None:
            raise SystemExit(
                f"missing {role} compartment output for logical key {key}"
            )
        environment_compartments[role] = {"key": key, "ocid": ocid}

    parent = environment_compartments["projects"]

    vcn_key, vcn_config = find_environment_network(
        network_config,
        args.environment,
    )
    vcn_cidrs = vcn_config.get("cidr_blocks")
    if (
        not isinstance(vcn_cidrs, list)
        or len(vcn_cidrs) != 1
        or not isinstance(vcn_cidrs[0], str)
    ):
        raise SystemExit(f"invalid generated CIDR for {vcn_key}")
    vcn = {
        "key": vcn_key,
        "name": vcn_config.get("display_name"),
        "cidr": vcn_cidrs[0],
        "ocid": require_resource(state_vcns, vcn_key, "vcn"),
    }

    configured_subnets = vcn_config.get("subnets", {})
    subnets = {}
    for role, suffix in SUBNET_ROLES.items():
        candidates = [
            (key, value)
            for key, value in configured_subnets.items()
            if key.endswith(suffix)
        ]
        if len(candidates) != 1:
            raise SystemExit(
                f"expected one {role} subnet for {args.environment}"
            )
        key, value = candidates[0]
        subnets[role] = {
            "key": key,
            "name": value.get("display_name"),
            "cidr": value.get("cidr_block"),
            "ocid": require_resource(state_subnets, key, "subnet"),
        }

    artifact = {
        "schema_version": 2,
        "environment": args.environment,
        "region": args.region,
        "tenancy_ocid": args.tenancy_ocid,
        "parent_compartment_key": parent["key"],
        "parent_compartment_ocid": parent["ocid"],
        "compartments": environment_compartments,
        "network": {"vcn": vcn, "subnets": subnets},
        "op02_state_key":
          f"op02_manage_environment/{args.environment}/terraform.tfstate",
        "source": {
            "repository": args.repository,
            "workflow": WORKFLOW,
            "run_id": args.run_id,
            "commit_sha": args.commit_sha,
        },
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
