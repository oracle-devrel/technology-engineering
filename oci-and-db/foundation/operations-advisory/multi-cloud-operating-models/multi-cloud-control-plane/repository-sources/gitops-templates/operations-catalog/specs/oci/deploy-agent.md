# OCI Compute deploy-agent

Copy [`deploy-agent.json`](../../oci/deploy-agent.json) to the project
repository path:

```text
oci/<environment>/<region>/lifecycle_operations/deploy-agent.json
```

This operation connects by SSH to one or more Compute instances already
declared in Terraform state for the same environment and region.

| Field | What to provide | Allowed values or behavior |
| --- | --- | --- |
| `operation_type` | Operation identifier. | Always `deploy-agent`. |
| `agent_type` | Agent product or role name. | Non-empty text, such as `monitoring-agent`. |
| `agent_version` | Intended agent version. | Non-empty text, such as `1.2.3` or `latest`. |
| `targets` | Instances to operate. | One or more target objects. |
| `targets[].display_name` | Instance display name. | Exact, case-sensitive display name from Terraform state. |

The supplied playbook is a safe demonstration placeholder: it creates
`/opt/agents/<agent_type>.installed` with the requested type and version. It
does not download or install a real third-party agent. Replacing it with an
actual installer is a separate platform change.
