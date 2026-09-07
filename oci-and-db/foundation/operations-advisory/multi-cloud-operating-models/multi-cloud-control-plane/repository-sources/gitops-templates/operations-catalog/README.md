# Lifecycle operations catalog

Lifecycle operations are post-provisioning actions executed by Ansible through
the shared `ansible-shared.yaml` workflow. Each JSON file is an approved
manifest template for one operation.

The protected project caller validates exactly one changed operation file and
passes its path explicitly to the shared workflow. Platform CI parses
`operation_type` and selects one explicitly allow-listed operation playbook;
project input never selects a playbook path or Ansible tag.

## JSON schema

```json
{
  "operation_type": "adb-lifecycle",
  "database_compartment_id": "__DATABASE_COMPARTMENT_OCID__",
  "targets": [
    {
      "display_name": "resource-display-name-in-tfstate",
      "action": "optional-per-target-action"
    }
  ]
}
```

- `operation_type` — must be an operation explicitly supported by Platform CI:
  `adb-lifecycle` or `deploy-agent`.
- `database_compartment_id` — required for `adb-lifecycle`; it must be the
  Database child-compartment OCID from the approved project handoff.
- `targets[].display_name` — must match the resource in Terraform state.
- `targets[].action` — is operation-specific. `adb-lifecycle` accepts only
  lowercase `start` or `stop`; `restart` and every other value are unsupported.

The JSON example is an ADB lifecycle request. Additional top-level fields are
operation-specific: `deploy-agent` instead requires `agent_type` and
`agent_version`, and does not use `database_compartment_id`.

## Field reference

The following guides explain supported operations in plain language,
including required fields, allowed values, runtime defaults, and observed
behavior:

- [OCI ADB lifecycle](specs/oci/adb-lifecycle.md)
- [OCI Compute deploy-agent](specs/oci/deploy-agent.md)

They are reference-only. They do not change JSON manifests, shared workflows,
or Ansible playbooks.

## Multiple ADB targets

`adb-lifecycle` supports one or more entries in `targets`. All targets in a
manifest are processed by the same workflow run and must resolve to exact ADB
display names in Terraform state for that OCI region. Add another object to the
`targets` array for each additional database.

## Current operations

| File | operation_type | Cloud | Notes |
| --- | --- | --- | --- |
| `oci/adb-lifecycle.json` | `adb-lifecycle` | OCI | Start or stop an Autonomous Database |
| `oci/deploy-agent.json` | `deploy-agent` | OCI | Worked SSH example: records an installation marker on a compute instance |

## Extension boundary

Adding a JSON template here does not enable an operation. A supported extension
also requires its allowed manifest fields in Platform CI
`scripts_python/validate_operation_manifest.py`, inventory extraction, an
explicitly allow-listed Platform CI playbook, permissions, documentation, and
qualification evidence. Follow the canonical
[extension model](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/architecture.md#extension-model)
before publishing it to Project Teams.

## Directory layout

```text
operations-catalog/
  oci/
    adb-lifecycle.json
    deploy-agent.json
```

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](../LICENSE).
