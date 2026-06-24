# Managed Function Demo

This is the primary OKE demo. It uses `mode: Managed`, so the operator creates or updates the OCI Functions application/function and discovers the invoke endpoint into `Function.status.invokeEndpoint`.

OKE deployments should install the manager with Helm. The chart defaults to OCI mode with Workload Identity.

There is no global `OCI_FUNCTIONS_INVOKE_ENDPOINT` in managed mode.

## Prerequisites

- `kubectl` points at the target OKE cluster.
- Helm is available for installing the operator chart.
- The manager service account has IAM permissions to manage OCI Functions applications/functions, use the target network resources, and invoke functions in the target compartment.
- You have a Jeddah compartment OCID and subnet OCID for OCI Functions.
- If the Functions application uses Network Security Groups, you have an NSG OCID whose egress rules allow TCP 443 to Oracle Services Network/OCIR.
- You can push an operator image to a registry OKE can pull.
- You can push a function runtime image to Jeddah OCIR.

The operator controller image and function runtime image are different:

- Operator/controller image: runs the Kubernetes controller manager in OKE. It can be in GHCR, OCIR, or any registry OKE can pull.
- Function runtime image: runs in OCI Functions. It must be an OCI Functions-compatible Fn image in same-region OCIR, such as `jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:fn-v1` for Jeddah.

OCI Functions pulls the function image from OCIR during invocation. The Functions application subnet must route to Oracle Services Network/OCIR, usually through a Service Gateway. If an NSG is attached to the Functions application, that NSG must also allow egress TCP 443 to Oracle Services Network/OCIR. A public OCIR repository does not remove the need for this network egress.

## 1. Build And Push The Operator Image

If you are testing local code changes, build and push the operator/controller image first:

```sh
export OPERATOR_IMAGE="ghcr.io/ronsevet/oci-functions-operator/controller:mvp-events-functionevents-v1"

docker build -t "$OPERATOR_IMAGE" .
docker push "$OPERATOR_IMAGE"
```

Any registry OKE can pull is acceptable for the operator image.

## 2. Build And Push The Function Runtime Image

This repo includes a minimal Python FDK function under `examples/hello-function`.
Prefer the Fn CLI build path so the output image matches the Fn Project layout.

The function image must be pushed to Jeddah OCIR for this Jeddah demo:

```text
jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:fn-v1
```

Log in to OCIR with the container engine used by Fn CLI:

```sh
docker login jed.ocir.io
# or:
podman login jed.ocir.io
```

Build and push with Fn CLI:

```sh
cd examples/hello-function
fn build
fn push --registry jed.ocir.io/<TENANCY_NAMESPACE>
```

With the default `func.yaml` version, use this pushed image as `<FUNCTION_IMAGE>`:

```text
jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:0.0.1
```

Manual Podman builds are acceptable only when the Dockerfile keeps the Fn Python FDK layout and entrypoint:

```sh
export TENANCY_NAMESPACE="<TENANCY_NAMESPACE>"
export TAG="0.0.1"

podman build --platform linux/amd64 --format docker \
  -t "jed.ocir.io/${TENANCY_NAMESPACE}/hello-function:${TAG}" \
  examples/hello-function
podman push "jed.ocir.io/${TENANCY_NAMESPACE}/hello-function:${TAG}"
```

Use `linux/amd64` for a `GENERIC_X86` OCI Functions application. If you choose an ARM application shape, build an ARM64-compatible image instead.

## 3. Install The Operator With Helm

```sh
export OPERATOR_IMAGE_REPOSITORY="${OPERATOR_IMAGE_REPOSITORY:-ghcr.io/ronsevet/oci-functions-operator/controller}"
export OPERATOR_IMAGE_TAG="mvp-events-functionevents-v1"
export OCI_REGION="me-jeddah-1"

helm upgrade --install oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --create-namespace \
  --set image.repository="$OPERATOR_IMAGE_REPOSITORY" \
  --set image.tag="$OPERATOR_IMAGE_TAG" \
  --set oci.region="$OCI_REGION"

kubectl -n oci-functions-operator-system rollout status deployment/oci-functions-operator-controller-manager
```

OKE Workload Identity does not require a local OCI config file, PEM Secret, mounted developer credentials, or `OCI_RESOURCE_PRINCIPAL_*` environment variables.
Do not mix this Helm install with Kustomize resources from `config/` on the same cluster.

Helm fresh install installs CRDs, but Helm upgrade does not upgrade CRDs from the chart `crds/` directory. Before upgrading an existing release after API schema changes, run:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

## 4. Apply A Managed Function

Create a managed `Function` in Jeddah:

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: Function
metadata:
  name: managed-hello
  namespace: default
spec:
  mode: Managed
  config:
    region: me-jeddah-1
    compartmentId: <COMPARTMENT_OCID>
    applicationName: oke-functions-operator-demo
    subnetIds:
    - <SUBNET_OCID>
    # Optional. Omit nsgIds to leave existing application NSGs unmanaged.
    # Use nsgIds: [] to explicitly clear NSGs.
    # Any attached NSG must allow egress TCP 443 to Oracle Services Network/OCIR.
    # nsgIds:
    # - <NSG_OCID>
    displayName: managed-hello
    image: jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:fn-v1
    memoryInMBs: 256
    timeoutInSeconds: 120
    config:
      GREETING: "hello from oke functions operator"
```

Or edit and apply the sample:

```sh
kubectl apply -f config/samples/functions_v1alpha1_function_managed.yaml
kubectl get functions -w
```

In another terminal:

```sh
kubectl describe function managed-hello
kubectl get events --field-selector involvedObject.kind=Function,involvedObject.name=managed-hello --sort-by=.lastTimestamp
```

Expected success indicators:

- `Function` shows `Ready=True`.
- `status.applicationId` is populated.
- `status.functionId` is populated.
- `status.invokeEndpoint` is populated.
- `status.phase=Ready`.

## 5. Submit A FunctionJob

The managed sample job references `managed-hello`:

```yaml
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionJob
metadata:
  name: managed-hello-job
  namespace: default
spec:
  functionRef:
    name: managed-hello
  payloads:
  - name: Ron
    index: 0
  - name: Ron
    index: 1
  parallelism: 1
  retryLimit: 1
```

Apply and watch:

```sh
kubectl apply -f config/samples/functions_v1alpha1_functionjob_managed.yaml
kubectl get functionjobs -w
```

Inspect status and events:

```sh
kubectl describe functionjob managed-hello-job
kubectl get functionjob managed-hello-job -o yaml
kubectl get events --field-selector involvedObject.kind=FunctionJob,involvedObject.name=managed-hello-job --sort-by=.lastTimestamp
```

Expected success indicators:

- `FunctionJob.status.phase=Succeeded`.
- `Complete=True`.
- `status.succeeded` equals the payload count.
- per-payload `invocationStatuses[*].phase=Succeeded`.
- per-payload `invocationId` and/or `ociRequestId` are populated after OCI invocation.

## Troubleshooting

### Workload Identity Or IAM Permission Failure

Symptoms:

- Manager logs mention Workload Identity, stale Resource Principal env var expectations, `401`, or `403`.
- `Function.status.phase=Error`.
- `FunctionJob.status.lastError` contains an OCI auth error.

Checks:

- Confirm the Helm release uses `oci.invokerMode=oci` and `oci.authMode=workload`.
- Confirm `OCI_REGION=me-jeddah-1` is set when an explicit Workload Identity region is needed.
- Confirm `OCI_RESOURCE_PRINCIPAL_*` variables are not required by the deployed operator image.
- Confirm IAM policy matches the OKE cluster OCID, namespace, and service account.
- Confirm the workload can manage Functions applications/functions and use the target network resources.

### Wrong Compartment

Symptoms:

- The operator cannot list or create applications.
- Status mentions `list OCI Functions applications` or `create OCI Functions application`.

Checks:

- Replace `<COMPARTMENT_OCID>` with the real Functions compartment OCID.
- Confirm the compartment is in the tenancy used by Workload Identity.
- Confirm IAM policy is scoped to that compartment or an ancestor compartment.

### Wrong Subnet Or NSG

Symptoms:

- Application creation/update fails.
- Status or manager logs mention subnet, VCN, NSG, network, or authorization errors.

Checks:

- Replace `<SUBNET_OCID>` with a subnet in `me-jeddah-1`.
- Confirm OCI Functions is allowed to use the subnet.
- If `spec.config.nsgIds` is set, confirm each NSG OCID is valid and can be attached to the Functions application.
- Confirm IAM policy allows network use if the subnet or NSG is in a different compartment.

### Image Pull Or Access Failure

Symptoms:

- The `Function` becomes Ready, but invocation fails.
- OCI reports `FunctionInvokeImageNotAvailable`.
- Error text includes `FunctionInvokeImageNotAvailable: Failed to pull function image`.

Checks:

- Confirm the function image is in same-region OCIR. For Jeddah use `jed.ocir.io/...`, not GHCR and not `me-jeddah-1.ocir.io`.
- Confirm the image path and tag exist.
- Confirm the image is an OCI Functions-compatible Fn image, not a generic application container.
- Confirm the image architecture matches the OCI Functions application shape, such as `linux/amd64` for `GENERIC_X86`.
- For private OCIR repositories, add repository read permission for the Functions application principal as required by your tenancy policy model.
- Public OCIR repository visibility can avoid normal repo-read IAM for public pulls, but it does not solve network egress.
- Confirm the Functions application subnet has a route to Oracle Services Network/OCIR, such as a Service Gateway route.
- If `spec.config.nsgIds` is set, confirm each attached NSG allows egress TCP 443 to Oracle Services Network/OCIR.

### Stale CRDs

Symptoms:

- `kubectl apply` reports unknown fields such as `status.functionId` or rejects current `spec.config` fields.

Checks:

- Apply the chart CRDs deliberately after API schema changes:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

### Function Not Ready So FunctionJob Refuses To Run

Symptoms:

- `FunctionJob.status.phase=Failed`.
- The job status says the referenced Function is not Ready.
- No payload invocation occurs.

Checks:

- Run `kubectl describe function managed-hello`.
- Confirm `Ready=True`.
- Confirm `status.applicationId`, `status.functionId`, and `status.invokeEndpoint` are populated.
- Recreate the `FunctionJob` after the `Function` is Ready.
