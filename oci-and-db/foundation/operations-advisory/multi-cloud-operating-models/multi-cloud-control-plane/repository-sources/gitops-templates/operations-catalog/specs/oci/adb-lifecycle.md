# OCI Autonomous Database lifecycle

Use this operation to start or stop one or more existing OCI Autonomous Databases. Copy [`adb-lifecycle.json`](../../oci/adb-lifecycle.json) to the project repository path below.

```text
oci/<environment>/<region>/lifecycle_operations/adb-lifecycle.json
```

Each target must already appear in Terraform state for the same environment and region. Platform CI uses it to build [temporary inventory](https://github.com/__CUSTOMER_ORG__/platform-ci/blob/main/README.md#terraform-state-as-dynamic-inventory).

| Field | What to provide | Allowed values or behavior |
| --- | --- | --- |
| `operation_type` | Operation identifier. | Always `adb-lifecycle`. |
| `database_compartment_id` | Database child-compartment OCID from the approved project handoff. | Required; it must exactly match the handed-off Database compartment. |
| `targets` | Databases to operate. | One or more target objects. All targets run in the same workflow execution. |
| `targets[].display_name` | ADB display name. | Exact, case-sensitive display name from Terraform state. |
| `targets[].action` | Desired state. | Use lowercase `start` or `stop`. A restart is not supported. |
| `targets[].wait_for_state` | Whether to wait for the requested state. | Defaults to `true`. Set `false` to submit the action without waiting. |
| `targets[].timeout_minutes` | How long to wait. | Defaults to 30 minutes. |

The pull request checks the targets against state. After merge, Platform CI verifies that the request is still current on `main`, including for queued jobs and reruns. It stops if a later change replaced or cleared the request or superseded it for a target in the same region. The playbook changes only targets that need the requested action.

Verify the matching execution and database state. Then remove the operation file in a focused pull request. The database stays in its current state when the request is cleared.

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
