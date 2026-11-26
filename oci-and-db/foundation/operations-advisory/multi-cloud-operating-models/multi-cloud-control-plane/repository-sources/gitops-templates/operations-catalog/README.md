# Lifecycle operations catalog

Choose an operation for an existing OCI resource. Start or stop a database with `adb-lifecycle`, or use `deploy-agent` to demonstrate the approved SSH execution path.

Submit one operation file per pull request. The project workflow validates its path and sends it to `ansible-shared.yaml`. Platform CI selects the approved playbook from `operation_type`.

## Manifest shape

```json
{
  "operation_type": "adb-lifecycle",
  "database_compartment_id": "__DATABASE_COMPARTMENT_OCID__",
  "targets": [
    {
      "display_name": "resource-display-name-in-tfstate",
      "action": "stop"
    }
  ]
}
```

- `operation_type` — must be an operation explicitly supported by Platform CI: `adb-lifecycle` or `deploy-agent`.
- `database_compartment_id` — required for `adb-lifecycle`; it must be the Database child-compartment OCID from the approved project handoff.
- `targets[].display_name` — must match the resource in Terraform state.
- `targets[].action` is required for `adb-lifecycle`. Use lowercase `start` or `stop`.

The JSON example is an ADB lifecycle request. Additional top-level fields are operation-specific: `deploy-agent` instead requires `agent_type` and `agent_version`, and does not use `database_compartment_id`.

## Field reference

See the fields, defaults and execution behavior for each operation.

- [OCI ADB lifecycle](specs/oci/adb-lifecycle.md)
- [OCI Compute deploy-agent](specs/oci/deploy-agent.md)

## Multiple ADB targets

Add one entry to `targets` for each database. Each distinct display name must match Terraform state for the selected OCI environment and region. One workflow run processes the targets.

## Current operations

| File | operation_type | Cloud | Notes |
| --- | --- | --- | --- |
| `oci/adb-lifecycle.json` | `adb-lifecycle` | OCI | Start or stop an Autonomous Database |
| `oci/deploy-agent.json` | `deploy-agent` | OCI | Hardened SSH marker operation on a Compute instance; it does not install third-party software |

## Extension boundary

To enable a new operation, Cloud Operations must update the catalog, its allowed manifest fields in Platform CI `scripts_python/validate_operation_manifest.py`, target inventory, approved playbook, permissions and documentation. Follow the canonical [extension model](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/architecture.md#extension-model) before publishing it to Project Teams.

## Directory layout

```text
operations-catalog/
  oci/
    adb-lifecycle.json
    deploy-agent.json
```

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal Permissive License, Version 1.0. See [LICENSE](../LICENSE).
