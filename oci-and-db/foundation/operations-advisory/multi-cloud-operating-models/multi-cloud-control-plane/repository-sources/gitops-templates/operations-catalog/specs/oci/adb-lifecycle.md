# OCI Autonomous Database lifecycle

Copy [`adb-lifecycle.json`](../../oci/adb-lifecycle.json) to the project
repository path:

```text
oci/<environment>/<region>/lifecycle_operations/adb-lifecycle.json
```

This operation starts or stops one or more OCI Autonomous Databases already
declared in Terraform state for the same environment and region.

After the workflow has completed and the result is verified, delete the request
file in a focused pull request. Deleting it records cleanup of the completed
request; it does not reverse the lifecycle operation.

| Field | What to provide | Allowed values or behavior |
| --- | --- | --- |
| `operation_type` | Operation identifier. | Always `adb-lifecycle`. |
| `database_compartment_id` | Database child-compartment OCID from the approved project handoff. | Required; it must exactly match the handed-off Database compartment. |
| `targets` | Databases to operate. | One or more target objects. All targets run in the same workflow execution. |
| `targets[].display_name` | ADB display name. | Exact, case-sensitive display name from Terraform state. |
| `targets[].action` | Desired state. | Lowercase `start` or `stop` only; restart is not supported. |

The pull request checks the request against state. After merge, the playbook
reads the current lifecycle state and changes only databases not already in the
requested state, so repeating the same request is safe. The workflow waits up
to 30 minutes for the requested state. A target may override that with
`timeout_minutes`, or disable waiting with `wait_for_state: false`; no other
field is accepted.

```json
{
  "operation_type": "adb-lifecycle",
  "database_compartment_id": "ocid1.compartment.oc1..database",
  "targets": [
    {
      "display_name": "orders-adb-dev",
      "action": "stop"
    }
  ]
}
```
