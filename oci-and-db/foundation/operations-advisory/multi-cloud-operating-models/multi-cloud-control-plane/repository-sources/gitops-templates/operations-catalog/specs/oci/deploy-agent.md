# OCI Compute deploy-agent

Use this example to see how an approved operation reaches a Compute instance over SSH. Copy [`deploy-agent.json`](../../oci/deploy-agent.json) to the project repository path below.

```text
oci/<environment>/<region>/lifecycle_operations/deploy-agent.json
```

This operation connects by SSH to one or more Compute instances already declared in Terraform state for the same environment and region.

| Field | What to provide | Allowed values or behavior |
| --- | --- | --- |
| `operation_type` | Operation identifier. | Always `deploy-agent`. |
| `agent_type` | Platform-owned agent product or role identifier. | 1–63 characters. Start with a lowercase letter and use lowercase letters, digits or hyphens, as in `monitoring-agent`. |
| `agent_version` | Intended agent version identifier. | 1–64 characters. Start with a letter or digit, then use letters, digits, dots, underscores, pluses or hyphens. Examples are `1.2.3` and `latest`. |
| `targets` | Instances to operate. | One or more target objects. |
| `targets[].display_name` | Instance display name. | Exact, case-sensitive display name from Terraform state. |

The supplied playbook is a safe demonstration placeholder. It writes `/opt/agents/<agent_type>.installed` with the requested type and version. A real installation requires a separate reviewed platform change. Map the validated `agent_type` to a platform-owned implementation from an allowlist. The platform fixes the command, URL, playbook and paths.

## Terraform state as Ansible inventory

For the shared pattern used by ADB and Compute operations, see [Terraform state as dynamic inventory](https://github.com/__CUSTOMER_ORG__/platform-ci/blob/main/README.md#terraform-state-as-dynamic-inventory).

Platform CI derives the state key from the project repository and the manifest path: `<bucket>/<owner>/<project>/oci/<environment>/<region>/terraform.tfstate`. It downloads that object read-only, indexes `oci_core_instance` entries by their exact `display_name`, and keeps only the instances named in `targets`.

The generated `$WORK_TEMP/inventory.json` places those instances in the `compute_instances` group. Terraform provides `ansible_host` from the private IP, plus `oci_ocid` and `oci_state`; the runner provides the SSH user and private-key path; the validated manifest provides `agent_type` and `agent_version`. The operation stops before Ansible if a target is missing from state or has no private IP.

`ansible/playbooks/operations/deploy-agent.yml` requires an explicit execution mode and imports the common `precheck`, `apply`, and `verify` task files. To use a real installer, replace the marker task in `common/oci/deploy-agent/apply.yml` with a platform-owned role or task import. In the same reviewed change, update `verify.yml` in that directory to check the installed agent. The supplied verification only checks the marker. Keep the wrapper and its three phases.
