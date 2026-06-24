# Local Existing Function Demo

This demo runs the manager locally with OCI config-file auth and invokes an OCI Function that already exists.

Use this when you want to test OCI invocation from your workstation. OKE users should use [managed-function-demo.md](managed-function-demo.md) and [oke-deployment.md](oke-deployment.md) for the primary managed-mode path.

Existing mode does not create or update OCI Functions applications/functions. It requires the existing function OCID and invoke endpoint in the `Function` spec.

Use `spec.functionId` for new manifests. `spec.existingFunctionOcid` remains as a deprecated compatibility alias.

## Prerequisites

- A Kubernetes cluster reachable by your current `kubectl` context.
- CRDs installed with `kubectl apply -k config/crd`.
- An OCI config file/profile for local development.
- Permission for that OCI principal to invoke the target OCI Function.
- An existing OCI Function OCID and its invoke endpoint.

There is no global `OCI_FUNCTIONS_INVOKE_ENDPOINT`. Existing-mode `Function` resources set `spec.invokeEndpoint`; managed-mode `Function` resources discover `status.invokeEndpoint`.

## 1. Find The Existing Function

```sh
export COMPARTMENT_OCID="ocid1.compartment.oc1..exampleuniqueid"

oci fn application list \
  --compartment-id "$COMPARTMENT_OCID" \
  --query 'data[].{name:"display-name",id:id}' \
  --output table
```

Choose the application, then list functions:

```sh
export APPLICATION_OCID="ocid1.fnapp.oc1.iad.exampleuniqueid"

oci fn function list \
  --application-id "$APPLICATION_OCID" \
  --query 'data[].{name:"display-name",id:id}' \
  --output table
```

Set the function OCID and invoke endpoint:

```sh
export FUNCTION_OCID="ocid1.fnfunc.oc1.iad.exampleuniqueid"
export FUNCTION_INVOKE_ENDPOINT="$(
  oci fn function get \
    --function-id "$FUNCTION_OCID" \
    --query 'data."invoke-endpoint"' \
    --raw-output
)"
```

The endpoint must be an HTTPS base URL and must not include `/20181201` or another API path.

## 2. Run The Manager Locally

```sh
export INVOKER_MODE=oci
export OCI_AUTH_MODE=config
export OCI_CONFIG_FILE="${OCI_CONFIG_FILE:-$HOME/.oci/config}"
export OCI_CONFIG_PROFILE="${OCI_CONFIG_PROFILE:-DEFAULT}"
```

Validate the OCI CLI can reach the target compartment/profile:

```sh
oci iam compartment get --compartment-id "$COMPARTMENT_OCID"
```

Install or refresh CRDs:

```sh
make generate
make manifests
kubectl apply -k config/crd
```

Run the manager:

```sh
INVOKER_MODE=oci \
OCI_AUTH_MODE=config \
OCI_CONFIG_FILE="$OCI_CONFIG_FILE" \
OCI_CONFIG_PROFILE="$OCI_CONFIG_PROFILE" \
go run ./cmd
```

## 3. Apply Existing Function

```sh
cat <<EOF | kubectl apply -f -
apiVersion: functions.oci.oracle.com/v1alpha1
kind: Function
metadata:
  name: oci-existing-hello
spec:
  mode: Existing
  functionId: ${FUNCTION_OCID}
  invokeEndpoint: ${FUNCTION_INVOKE_ENDPOINT}
EOF
```

Check readiness:

```sh
kubectl get function oci-existing-hello
kubectl describe function oci-existing-hello
```

Expected indicators:

- `status.phase=Ready`
- `status.functionId` is populated
- `status.invokeEndpoint` is populated
- `Ready=True`

## 4. Submit A FunctionJob

```sh
cat <<EOF | kubectl apply -f -
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionJob
metadata:
  name: oci-hello-job
spec:
  functionRef:
    name: oci-existing-hello
  payloads:
  - message: hello from local oci mode
    requestId: demo-001
  parallelism: 1
  retryLimit: 1
EOF
```

Watch and inspect:

```sh
kubectl get functions,functionjobs
kubectl get functionjob oci-hello-job -o yaml
kubectl describe functionjob oci-hello-job
kubectl get events --field-selector involvedObject.kind=FunctionJob,involvedObject.name=oci-hello-job --sort-by=.lastTimestamp
```

Expected success indicators:

- `FunctionJob.status.phase=Succeeded`
- `status.succeeded` equals the payload count
- per-payload `invocationStatuses[*].phase=Succeeded`
- `invocationId` and/or `ociRequestId` are populated after OCI invocation

## Notes

- `OCI_AUTH_MODE=config` is local-development-only.
- OKE deployments should not mount developer OCI config files or PEM keys; use Workload Identity instead.
- Managed mode is documented in [managed-function-demo.md](managed-function-demo.md).
- Fake mode is documented in the repository [README](../README.md).
