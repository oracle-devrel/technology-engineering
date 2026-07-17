#!/usr/bin/env python3
"""Create the protected OP02 environment artifact from exact apply outputs."""
import argparse
import json
import re
from pathlib import Path

TENANCY_OCID = re.compile(r"^ocid1\.tenancy\.oc1\.\.[A-Za-z0-9_-]+$")
COMPARTMENT_OCID = re.compile(r"^ocid1\.compartment\.oc1\.\.[A-Za-z0-9_-]+$")
SHA = re.compile(r"^[0-9a-f]{40}$")
ENVIRONMENT = re.compile(r"^[a-z][a-z0-9]{0,30}$")
REGION = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW = re.compile(r"^oci-op02-[a-z0-9]+-terraform\.yaml$")


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("environment", "region", "tenancy-ocid", "environment-config", "network-output", "repository", "workflow", "run-id", "commit-sha", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.environment_config).read_text(encoding="utf-8"))
    network = json.loads(Path(args.network_output).read_text(encoding="utf-8"))
    parent = config.get("compartments_configuration", {}).get("default_parent_id")
    if not all((
        TENANCY_OCID.fullmatch(args.tenancy_ocid),
        COMPARTMENT_OCID.fullmatch(str(parent)),
        SHA.fullmatch(args.commit_sha),
        ENVIRONMENT.fullmatch(args.environment),
        REGION.fullmatch(args.region),
        REPOSITORY.fullmatch(args.repository),
        WORKFLOW.fullmatch(args.workflow),
        args.run_id.isdigit(),
        isinstance(network, dict),
    )):
        raise SystemExit("invalid OP02 environment provenance or identifiers")
    artifact = {
        "schema_version": 2,
        "environment": args.environment,
        "region": args.region,
        "tenancy_ocid": args.tenancy_ocid,
        "parent_compartment_ocid": parent,
        "network": network,
        "source": {"repository": args.repository, "workflow": args.workflow, "run_id": args.run_id, "commit_sha": args.commit_sha},
    }
    Path(args.output).write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
