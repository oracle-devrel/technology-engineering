# OCI Mode Validation Notes

Use this template to record results from a real OCI-mode demo run.

## Environment

- Date/time:
- Operator commit:
- Kubernetes context:
- Kubernetes version:
- Namespace:
- Operator/controller image:
- `INVOKER_MODE`:
- `OCI_AUTH_MODE`:
- `OCI_CONFIG_FILE`:
- `OCI_CONFIG_PROFILE`:
- `OCI_REGION`:
- OCI region:
- OCI tenancy/profile notes:
- Workload Identity policy used:

## Function Details

- OCI Function display name:
- Function mode (`Existing` or `Managed`):
- Function OCID:
- Application OCID:
- Spec invoke endpoint, if existing mode:
- Status invoke endpoint:
- Function runtime image:
- Function compartment:
- OCIR repo compartment:
- Managed config region:
- Managed config subnet IDs:
- Subnet route table status for Oracle Services Network/OCIR:
- Managed config NSG IDs:
- NSG egress rules for Oracle Services Network/OCIR:
- Application shape:
- Expected payload shape:
- Expected response:
- IAM/policy notes:
- Functions application route/NSG egress notes for OCIR image pulls:

## FunctionJob Spec

```yaml
# Paste the FunctionJob manifest used for validation.
```

- Referenced `Function` name:
- Payload count:
- `parallelism`:
- `retryLimit`:

## Observed Status

```yaml
# Paste: kubectl get functionjob <name> -o yaml
```

- Final phase:
- `status.succeeded`:
- `status.failed`:
- `status.active`:
- `status.retries`:
- `status.lastError`:
- `status.lastOciRequestId`:
- Per-payload invocation IDs:
- Per-payload OCI request IDs:
- Per-payload status summary:

## Errors

- Did any invocation fail?
- Error classification observed:
- Did OCI report `FunctionInvokeImageNotAvailable: Failed to pull function image`?
- Was the error actionable from `kubectl get` or `kubectl describe`?
- Was any response body truncated appropriately?
- Related manager log excerpt:

## Latency

- Time from `kubectl apply` to first status update:
- Time from `kubectl apply` to terminal phase:
- Approximate OCI invocation latency:
- Any retries observed:
- Any timeout behavior observed:

## UX Notes

- Was setup clear?
- Were required environment variables obvious?
- Was existing-mode `spec.functionId` and `spec.invokeEndpoint` validation clear?
- Was managed-mode status discovery (`applicationId`, `functionId`, `invokeEndpoint`) clear?
- Were status fields easy to find?
- Were events useful?
- What should change before the next demo?
