# Operations Catalog (Day 2)

Day 2 operations are post-provisioning actions executed by Ansible through the
shared `ansible-shared.yaml` workflow. Each JSON file is an approved manifest
template for one operation.

The protected project caller validates exactly one changed operation file and
passes its path explicitly to the shared workflow. The workflow parses that
file and runs the playbook tag matching `operation_type`.

## JSON schema

```json
{
  "operation_type": "tag-name-in-master.yml",
  "targets": [
    {
      "display_name": "resource-display-name-in-tfstate",
      "action": "optional-per-target-action"
    }
  ]
}
```

- `operation_type` — must match a tag defined in
  `platform-ci/ansible/playbooks/master.yml`.
- `targets[].display_name` — must match the resource in Terraform state.
- `targets[].action` — is operation-specific. `adb-lifecycle` accepts only
  lowercase `start` or `stop`; `restart` and every other value are unsupported.

Additional top-level fields are operation-specific. For example,
`deploy-agent` adds `agent_type` and `agent_version`.

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
| `oci/deploy-agent.json` | `deploy-agent` | OCI | Deploy an agent to a compute instance via SSH |

## Adding a new operation

1. Add the playbook and tag in `platform-ci/ansible/playbooks/master.yml` and the corresponding file under `platform-ci/ansible/playbooks/operations/`.
2. Create the JSON manifest here under the right provider directory.
3. Make sure `operation_type` matches the tag exactly.

These steps are only the catalog portion of an extension. Complete every
control and qualification requirement in the
[extension model](https://github.com/oracle-devrel/technology-engineering/blob/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/architecture.md#extension-model) before making
the operation available to Project Teams.

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
