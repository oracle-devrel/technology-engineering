# OCI Compute deploy-agent

Copy [`deploy-agent.json`](../../oci/deploy-agent.json) to the project repository path:

```text
oci/<environment>/<region>/lifecycle_operations/deploy-agent.json
```

This operation connects by SSH to one or more Compute instances already declared in Terraform state for the same environment and region.

| Field | What to provide | Allowed values or behavior |
| --- | --- | --- |
| `operation_type` | Operation identifier. | Always `deploy-agent`. |
| `agent_type` | Platform-owned agent product or role identifier. | 1–63 lowercase characters: letters, digits, and hyphens; for example `monitoring-agent`. It cannot select a command, URL, playbook, or filesystem path. |
| `agent_version` | Intended agent version identifier. | 1–64 characters: letters, digits, dots, underscores, pluses, and hyphens; for example `1.2.3` or `latest`. |
| `targets` | Instances to operate. | One or more target objects. |
| `targets[].display_name` | Instance display name. | Exact, case-sensitive display name from Terraform state. |

The supplied playbook is a safe demonstration placeholder: it creates `/opt/agents/<agent_type>.installed` with the requested type and version. It does not download or install a real third-party agent. Replacing it with an actual installer is a separate platform change. A future installer must map the validated `agent_type` to a platform-owned, allow-listed implementation; project input must never select a command, URL, playbook, or filesystem path.

## Terraform state as Ansible inventory

For the shared pattern used by ADB and Compute operations, see [Terraform state as dynamic inventory](../../../../platform-ci/README.md#terraform-state-as-dynamic-inventory).

Platform CI derives the state key from the project repository and the manifest path: `<bucket>/<owner>/<project>/oci/<environment>/<region>/terraform.tfstate`. It downloads that object read-only, indexes `oci_core_instance` entries by their exact `display_name`, and keeps only the instances named in `targets`.

The generated `$WORK_TEMP/inventory.json` places those instances in the `compute_instances` group. Terraform provides `ansible_host` from the private IP, plus `oci_ocid` and `oci_state`; the runner provides the SSH user and private-key path; the validated manifest provides `agent_type` and `agent_version`. The operation stops before Ansible if a target is missing from state or has no private IP.

`ansible/playbooks/operations/deploy-agent.yml` follows the same pattern as `adb-lifecycle.yml`: it requires an explicit execution mode and imports the common `precheck`, `apply`, and `verify` task files. To turn the reference marker into a customer implementation, replace the marked extension point in `common/oci/deploy-agent/apply.yml` with a platform-owned role or task import and keep the wrapper and common phases unchanged.
