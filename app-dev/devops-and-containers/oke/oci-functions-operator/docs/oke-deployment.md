# Deploy The OCI Functions Operator On OKE

Helm is the supported OKE installation path. See [Helm install](helm-install.md) for full chart values, upgrades, CRD notes, and rendering checks.

Kustomize manifests under `config/` are retained for Kubebuilder-generated resources and local controller development only. Do not mix Helm and Kustomize resources for the same cluster install.

## What Gets Installed

- CRDs for `Function`, `FunctionJob`, `FunctionEventTrigger`, and `FunctionEvent`.
- A controller manager Deployment in `oci-functions-operator-system`.
- RBAC for watching `Function`, `FunctionJob`, `FunctionEventTrigger`, and `FunctionEvent` resources and writing status/events.
- OCI mode configured for OKE Workload Identity.

## Prerequisites

- `kubectl` points at the target OKE cluster.
- The operator image `ghcr.io/ronsevet/oci-functions-operator/controller:mvp-events-functionevents-v1` is reachable by OKE.
- OKE Workload Identity is enabled/available for the cluster and service account. Use an OKE cluster type/version that supports Workload Identity in your tenancy.
- OCI IAM policy allows this Kubernetes workload to manage OCI Functions resources, manage OCI Events rules, and invoke functions.
- For managed mode: a compartment OCID, subnet OCIDs, optional NSG OCIDs, and a same-region OCIR function image OCI Functions can pull.
- For existing mode: an existing function OCID and that function's invoke endpoint.

## Install With Helm

Set the operator image tag you want OKE to run:

```sh
export OPERATOR_IMAGE_REPOSITORY="ghcr.io/ronsevet/oci-functions-operator/controller"
export OPERATOR_IMAGE_TAG="mvp-events-functionevents-v1"
export OCI_REGION="me-jeddah-1"
```

Install or upgrade the operator:

```sh
helm upgrade --install oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --create-namespace \
  --set image.repository="$OPERATOR_IMAGE_REPOSITORY" \
  --set image.tag="$OPERATOR_IMAGE_TAG" \
  --set oci.region="$OCI_REGION"
```

Helm fresh install installs CRDs, but Helm upgrade does not upgrade CRDs from the chart `crds/` directory. Before upgrading an existing release after API schema changes, run:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

Confirm the deployment and CRDs:

```sh
kubectl -n oci-functions-operator-system rollout status deployment/oci-functions-operator-controller-manager
kubectl get crd functions.functions.oci.oracle.com functionjobs.functions.oci.oracle.com functioneventtriggers.functions.oci.oracle.com functionevents.functions.oci.oracle.com
```

## OKE Workload Identity Auth

For OKE, the Helm chart configures OCI mode with the OCI Go SDK OKE Workload Identity provider. The chart defaults are:

```yaml
oci:
  invokerMode: oci
  authMode: workload
```

Set `oci.region=<cluster-or-workload-region>`, for example `me-jeddah-1`, when the SDK needs an explicit region for OKE Workload Identity.

There is no manager-level `OCI_FUNCTIONS_INVOKE_ENDPOINT`. Existing Functions put the endpoint in `Function.spec.invokeEndpoint`; managed Functions discover it into `Function.status.invokeEndpoint`.

The SDK also uses the pod service account token, Kubernetes service account CA, and `KUBERNETES_SERVICE_HOST` provided by Kubernetes/OKE.

Workload mode must not require `OCI_RESOURCE_PRINCIPAL_*` environment variables. Resource Principal auth is a different OCI auth path and is not the intended OKE deployment mode for this operator.

## IAM Policy

Scope policies as tightly as your tenancy model allows. The workload principal conditions should match the namespace, service account, and OKE cluster OCID used by this deployment.

For managed mode, the operator needs to ensure OCI Functions applications/functions and invoke the resolved function. You can grant broad `manage functions-family` permissions, or use narrower permissions for `fn-app`, `fn-function`, and invocation according to your tenancy policy model.

Example with narrower resource families:

```text
Allow any-user to manage fn-app in compartment <functions-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage fn-function in compartment <functions-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

For `FunctionEventTrigger`, the same workload principal also needs permission to inspect compartments, manage OCI Events rules, and access the Function action target. Oracle documents `CreateRule` as `EVENTRULE_CREATE` under `manage cloudevents-rules`; for rules with Functions actions, Oracle's Events IAM guidance also lists Functions and virtual-network access for action resources. In OKE Workload Identity testing, `manage cloudevents-rules` was not enough by itself: OCI Events `CreateRule` failed until the workload principal also had `inspect compartments in tenancy`.

Use `functions-family` with the trailing `s`. `function-family` is incorrect.

```text
Allow any-user to inspect compartments in tenancy where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage cloudevents-rules in compartment <events-rule-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage functions-family in compartment <function-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to use virtual-network-family in compartment <function-network-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

If the trigger rule uses defined tags, also grant `use tag-namespaces` for those tag namespaces.

OCI Events also needs permission for the Events rule principal to invoke the target Function:

```text
Allow any-user to use fn-invocation in compartment <functions-compartment> where all {request.principal.type = 'eventrule'}
```

If a rule is created but matching events do not invoke the function, check this Events-rule-to-Functions invoke policy in the target function compartment.

Object Storage event conditions do not require `object-family` permissions for rule creation. The bucket still must have object events enabled.

Use `manage all-resources` only as a short-lived diagnostic policy while proving an IAM gap, then replace it with the least-privilege policy set above.

If the application subnets live in a different compartment, grant network use there:

```text
Allow any-user to use virtual-network-family in compartment <network-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

If the function image is in a private OCIR repository, add the appropriate repository read policy for the Functions application principal in your registry compartment/tenancy. Public OCIR repositories usually avoid normal repo-read IAM for public pulls, but network egress is still required.

For existing-mode invocation only, you may be able to narrow policy to `use fn-function` for the target compartment instead of `manage`.

## Network For Managed Functions

Managed mode creates or updates an OCI Functions application. OCI Functions pulls the function image from OCIR during invocation, so the application network must allow that pull path:

- The Functions application subnet must have a route to Oracle Services Network/OCIR, usually through a Service Gateway.
- Subnet security lists must allow the required HTTPS egress.
- If `spec.config.nsgIds` attaches NSGs to the Functions application, those NSGs must allow egress TCP 443 to Oracle Services Network/OCIR.

Missing NSG egress can surface only at invocation time as:

```text
FunctionInvokeImageNotAvailable: Failed to pull function image
```

A public OCIR repository or otherwise accessible repository does not avoid the need for network egress from the Functions application.

Confirm no local OCI credential Secret is mounted:

```sh
kubectl -n oci-functions-operator-system get deployment oci-functions-operator-controller-manager -o yaml
```

## Managed Function Mode

Create a managed `Function`. This example targets Jeddah with region identifier `me-jeddah-1`:

```sh
export COMPARTMENT_OCID="ocid1.compartment.oc1..exampleuniqueid"
export SUBNET_OCID="ocid1.subnet.oc1.me-jeddah-1.exampleuniqueid"
export NSG_OCID="ocid1.networksecuritygroup.oc1.me-jeddah-1.exampleuniqueid"
export FUNCTION_IMAGE="jed.ocir.io/<TENANCY_NAMESPACE>/hello-function:fn-v1"

cat <<EOF | kubectl apply -f -
apiVersion: functions.oci.oracle.com/v1alpha1
kind: Function
metadata:
  name: oci-managed-hello
spec:
  mode: Managed
  config:
    region: me-jeddah-1
    compartmentId: ${COMPARTMENT_OCID}
    applicationName: oci-functions-operator-demo
    subnetIds:
    - ${SUBNET_OCID}
    # Optional: uncomment when the Functions application should use NSGs.
    # The NSG must allow egress TCP 443 to Oracle Services Network/OCIR.
    # nsgIds:
    # - ${NSG_OCID}
    displayName: oci-managed-hello
    image: ${FUNCTION_IMAGE}
    memoryInMBs: 128
    timeoutInSeconds: 30
    config:
      LOG_LEVEL: info
EOF
```

Watch status until `Ready=True` and these fields are populated:

```sh
kubectl get function oci-managed-hello -o yaml
```

- `status.applicationId`
- `status.functionId`
- `status.invokeEndpoint`

## Existing Function Mode

Create a `Function` that references an existing OCI Function:

```sh
export FUNCTION_OCID="ocid1.fnfunc.oc1.iad.exampleuniqueid"
export FUNCTION_INVOKE_ENDPOINT="https://functions.us-ashburn-1.oci.oraclecloud.com"

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

The operator copies the OCID and endpoint into status and marks the `Function` Ready.

## Submit A FunctionJob

Set the function resource name you want to invoke:

```sh
export FUNCTION_RESOURCE_NAME="oci-managed-hello"
# or:
# export FUNCTION_RESOURCE_NAME="oci-existing-hello"
```

Create a `FunctionJob`:

```sh
cat <<EOF | kubectl apply -f -
apiVersion: functions.oci.oracle.com/v1alpha1
kind: FunctionJob
metadata:
  name: oci-hello-job
spec:
  functionRef:
    name: ${FUNCTION_RESOURCE_NAME}
  payload:
    message: hello from OKE
    requestId: oke-demo-001
  parallelism: 1
  retryLimit: 1
EOF
```

Inspect status and events:

```sh
kubectl get functions,functionjobs
kubectl get events --field-selector involvedObject.kind=Function,involvedObject.name=${FUNCTION_RESOURCE_NAME} --sort-by=.lastTimestamp
kubectl get functionjob oci-hello-job -o yaml
kubectl describe functionjob oci-hello-job
kubectl get events --field-selector involvedObject.kind=FunctionJob,involvedObject.name=oci-hello-job --sort-by=.lastTimestamp
```

## Troubleshooting

### Workload Identity Auth Errors

Symptoms:

- Manager fails startup with `configure OCI Workload Identity auth provider`.
- `Function` status or `FunctionJob` status contains `oci auth error`.
- Manager logs mention `401`, `403`, `Workload Identity`, service account token, or stale `OCI_RESOURCE_PRINCIPAL_*` expectations.

Checks:

- Confirm the Helm release uses `oci.authMode=workload`.
- Confirm `OCI_REGION=<region>` is set when your deployment needs an explicit Workload Identity region.
- Confirm `OCI_RESOURCE_PRINCIPAL_VERSION`, `OCI_RESOURCE_PRINCIPAL_REGION`, and other `OCI_RESOURCE_PRINCIPAL_*` variables are not part of the intended OKE deployment config.
- Confirm the pod uses service account `oci-functions-operator-controller-manager`.
- Confirm the service account token is mounted in the pod.
- Confirm the OKE cluster supports Workload Identity for the workload.
- Confirm the IAM policy matches the namespace, service account, cluster OCID, and target compartments.
- If logs still say `OCI_RESOURCE_PRINCIPAL_REGION` is missing, confirm the deployed operator image includes the Workload Identity auth fix.

### Managed Function Reconcile Errors

Symptoms:

- `Function.status.phase=Error`.
- `Function.status.message` mentions listing, creating, getting, or updating OCI Functions applications/functions.

Checks:

- Confirm `spec.config.region` is a valid OCI region identifier such as `me-jeddah-1`.
- Confirm `spec.config.compartmentId` is the Functions compartment.
- Confirm `spec.config.subnetIds` are valid and usable by OCI Functions.
- If `spec.config.nsgIds` is set, confirm the NSG OCIDs are valid and can be attached to the Functions application.
- Confirm IAM policy allows managing `fn-app` and `fn-function`.
- Confirm the function image is in same-region OCIR and OCI Functions can pull it.

### Function Image Pull Failures

Symptoms:

- Managed `Function` becomes Ready, but `FunctionJob` invocation fails.
- OCI returns `FunctionInvokeImageNotAvailable: Failed to pull function image`.

Checks:

- Confirm the function image is an OCI Functions-compatible Fn image.
- Confirm the image is in the expected same-region registry, such as Jeddah OCIR `jed.ocir.io`.
- Confirm the Functions application subnet route table sends Oracle Services Network/OCIR traffic through a Service Gateway.
- Confirm subnet security lists allow HTTPS egress.
- If the Functions application has NSGs from `spec.config.nsgIds`, confirm those NSGs allow egress TCP 443 to Oracle Services Network/OCIR.
- Remember that public OCIR repository visibility does not bypass network egress requirements.

### Placeholder Controller Image

Symptoms:

- The manager pod cannot pull the configured operator image.
- The deployment stays in `ImagePullBackOff`.

Checks:

- Build and push the operator/controller image to a registry OKE can pull.
- Upgrade the Helm release with the reachable image:

```sh
helm upgrade oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --set image.repository="$OPERATOR_IMAGE_REPOSITORY" \
  --set image.tag="$OPERATOR_IMAGE_TAG"
```

- If you override `image.tag` to an empty string, the chart uses `Chart.appVersion`, currently `mvp-events-functionevents-v1`.

### Invoke Endpoint Errors

Symptoms:

- Existing-mode `Function` is not Ready because `spec.invokeEndpoint` is empty.
- Managed-mode `Function` remains Pending because OCI has not returned an invoke endpoint yet.
- `FunctionJob.status.lastError` contains `oci endpoint error`.

Checks:

- Existing mode: confirm `spec.invokeEndpoint` comes from the function `invokeEndpoint`.
- Do not include `/20181201` or another API path.
- Managed mode: inspect `Function.status.invokeEndpoint`.
- Confirm the endpoint region matches the function region.
- Confirm the OKE cluster can reach the endpoint.
- Confirm DNS and egress rules for worker nodes.

### Bad Function OCID

Symptoms:

- Existing-mode `Function` is not Ready if `spec.functionId` is missing.
- `FunctionJob` fails clearly if the referenced `Function` is not Ready.
- `status.lastError` contains `oci function OCID error` or a 404 from OCI.

Checks:

- Existing mode: use `spec.functionId` and `spec.invokeEndpoint`.
- Managed mode: use `status.functionId` populated by the `Function` controller.
- Confirm the OCID starts with `ocid1.fnfunc`.
- Confirm the function exists in the same region as the invoke endpoint.
- Confirm the workload identity policy allows invoking that function.

### Missing Kubernetes RBAC

Symptoms:

- Manager logs include `forbidden`.
- `Function` or `FunctionJob` status does not update.
- Events are missing.

Checks:

- Confirm `helm template` contains the ClusterRole rules for `functions`, `functionjobs`, `functioneventtriggers`, `functionevents`, status/finalizers, and core `events`.
- Re-run `helm upgrade` if the ClusterRole drifted.
- Confirm the deployment uses service account `oci-functions-operator-controller-manager`.
- Do not patch a Helm-managed install with `kubectl apply -k config/rbac`; keep ownership with Helm.

## Local Config Auth

`OCI_AUTH_MODE=config` is for local development runs, not the OKE deployment path. See [oci-mode-demo.md](oci-mode-demo.md) for the local `go run` workflow that uses `OCI_CONFIG_FILE` and `OCI_CONFIG_PROFILE`.

## Current MVP Boundary

This deployment supports existing Function references, managed application/function reconciliation, `FunctionJob` invocation, OCI Events rule triggers through `FunctionEventTrigger`, and Kubernetes-native `FunctionEvent` routing for `functionevent.*` event types. Image build/push workflows, Function deletion, schedules, Kubernetes watch triggers, workflows, and Function deployment packaging remain out of scope.
