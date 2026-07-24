# Operations Catalog (Day 2)

Day 2 operations are post-provisioning actions executed by Ansible via the shared `ansible-shared.yaml` workflow. Each JSON file here is the manifest an operator edits and commits to trigger an operation.

The workflow picks up the file that changed in the PR diff, parses it, and runs the playbook tag that matches `operation_type`.

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

- `operation_type` — must match a tag defined in `platform-ci/ansible/playbooks/master.yml`.
- `targets[].display_name` — the display name of the resource as it appears in Terraform state for state-backed operations. The ExaCS patch operation resolves it from the platform-owned environment registry.
- `targets[].action` — optional. `adb-lifecycle` accepts only the exact lowercase values `start` or `stop`; `restart` and every other action are unsupported. Other operations may ignore it.

Extra top-level fields are operation-specific (e.g. `deploy-agent` adds `agent_type` and `agent_version`).

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
| `oci/exacs-database-out-of-place-patch.json` | `exacs-database-out-of-place-patch` | OCI | Move one regular ExaCS database to an approved patched Database Home through OCI APIs |
| `azure/adb-lifecycle.json` | `adb-lifecycle` | Azure | Template only — playbook not connected yet |

## Adding a new operation

1. Add the playbook and tag in `platform-ci/ansible/playbooks/master.yml` and the corresponding file under `platform-ci/ansible/playbooks/operations/`.
2. Create the JSON manifest here under the right provider directory.
3. Make sure `operation_type` matches the tag exactly.

## Directory layout

```text
operations-catalog/
  oci/
    adb-lifecycle.json
    deploy-agent.json
    exacs-database-out-of-place-patch.json
  azure/
    adb-lifecycle.json
```

## Warranty disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND.
