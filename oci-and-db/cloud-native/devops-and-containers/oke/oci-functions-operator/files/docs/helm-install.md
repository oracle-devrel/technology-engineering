# Helm Install

Helm is the recommended OKE deployment path for the OCI Functions Operator. The chart packages CRDs, RBAC, service account, deployment settings, metrics service, image values, and OCI Workload Identity environment defaults in one place. The packaged CRDs are `FunctionApplication`, `Function`, `FunctionJob`, `FunctionEventTrigger`, and `FunctionEvent`.

Use Helm for supported OKE installs and upgrades. Kustomize manifests under `config/` are retained for operator development only. Do not mix Helm and Kustomize resources for the same cluster install.

The chart lives at:

```sh
charts/oci-functions-operator
```

The current published image tag is:

```text
ghcr.io/ronsevetoci/oci-functions-operator/controller:v0.1.7
```

## Defaults

The default values target OKE with Workload Identity:

```yaml
oci:
  invokerMode: oci
  authMode: workload
  region: ""

serviceAccount:
  create: true
  name: oci-functions-operator-controller-manager
```

The chart does not mount OCI config files, PEM keys, developer credentials, or a global invoke endpoint. Function invoke endpoints come from each `Function` resource.

Set `oci.region` when the OKE Workload Identity provider needs an explicit OCI region, for example `me-jeddah-1`. Workload mode must not require `OCI_RESOURCE_PRINCIPAL_*` environment variables; Resource Principal auth is not the intended OKE path for this operator.

The Helm chart is the supported path for configuring `INVOKER_MODE=oci` and `OCI_AUTH_MODE=workload` on OKE.

## CRD Upgrade Rule

Fresh Helm installs install chart CRDs from `charts/oci-functions-operator/crds/`. Existing Helm upgrades do not add or update CRDs from the chart `crds/` directory.

Before installing or upgrading after API changes, apply the chart CRDs first:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

Then run `helm upgrade --install`.

## Install

Apply CRDs before the Helm command:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

```sh
helm upgrade --install oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --create-namespace \
  --set image.repository=ghcr.io/ronsevetoci/oci-functions-operator/controller \
  --set image.tag=v0.1.7
```

If needed, include the OKE region:

```sh
helm upgrade --install oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --create-namespace \
  --set image.repository=ghcr.io/ronsevetoci/oci-functions-operator/controller \
  --set image.tag=v0.1.7 \
  --set oci.region=me-jeddah-1
```

## Upgrade

Apply CRDs before the Helm command:

```sh
kubectl apply -f charts/oci-functions-operator/crds/
```

```sh
helm upgrade --install oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system \
  --set image.tag=v0.1.7
```

This explicit `kubectl apply` is required for API additions such as `FunctionApplication`; Helm upgrade will not install that CRD for an existing release by itself.

## Uninstall

```sh
helm uninstall oci-functions-operator \
  --namespace oci-functions-operator-system
```

Helm uninstall removes namespaced chart resources, ClusterRoles, and bindings, but CRDs installed from `crds/` are intentionally left behind by Helm. Remove CRDs manually only after deleting custom resources you care about.

Managed `Function` custom resources default to `spec.deletionPolicy: Retain`, so deleting them leaves OCI resources untouched. Set `Function.spec.deletionPolicy: Delete` only when Kubernetes deletion should also delete the managed OCI Function. `FunctionApplication.spec.deletionPolicy` separately controls OCI Application cleanup; Delete is honored only for managed applications and only when no functions remain. Existing-mode resources never delete OCI resources.

## Image Values

```yaml
image:
  repository: ghcr.io/ronsevetoci/oci-functions-operator/controller
  tag: v0.1.7
  pullPolicy: IfNotPresent
```

If you override `image.tag` to an empty string, the chart uses `Chart.appVersion`, currently `v0.1.7`.

## Service Account And Workload Identity

The default service account is:

```text
oci-functions-operator-controller-manager
```

Your OCI IAM Workload Identity policy must match the deployed namespace and service account. With the install command above, that means:

```text
namespace = oci-functions-operator-system
service_account = oci-functions-operator-controller-manager
```

Add service account annotations if your environment needs them:

```yaml
serviceAccount:
  annotations:
    example.com/key: value
```

## FunctionEventTrigger IAM

`FunctionEventTrigger` needs two OCI IAM paths:

- The operator workload identity must be able to inspect compartments, manage OCI Events rules, and access the Function action target.
- The OCI Events rule principal must be able to invoke the target Function in the function compartment.

Oracle documents `CreateRule` as requiring `EVENTRULE_CREATE`, which is included in `manage cloudevents-rules`. For Events rules with Functions actions, Oracle's Events IAM guidance also lists Functions and virtual-network access for action resources. In OKE Workload Identity testing, `manage cloudevents-rules` was not enough by itself: OCI Events `CreateRule` failed until the workload principal also had `inspect compartments in tenancy`.

Use the Functions aggregate resource type `functions-family` with the trailing `s`. `function-family` is incorrect.

Operator workload policy:

```text
Allow any-user to inspect compartments in tenancy where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage cloudevents-rules in compartment <events-rule-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to manage functions-family in compartment <function-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
Allow any-user to use virtual-network-family in compartment <function-network-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

For `FunctionApplication.spec.logging.invocationLogs`, OCI service-log enablement needs both log group permission and access to the logged resource. The `manage functions-family` policy above covers the Functions application side. Add Logging Management permission in the compartment that contains the referenced log group:

```text
Allow any-user to manage log-groups in compartment <logging-compartment> where all {request.principal.type = 'workload', request.principal.namespace = 'oci-functions-operator-system', request.principal.service_account = 'oci-functions-operator-controller-manager', request.principal.cluster_id = '<oke-cluster-ocid>'}
```

Use the exact Logging resource type `log-groups`. `logging-groups` is not a valid OCI IAM resource type. The aggregate diagnostic resource type is `logging-family`.

`404 NotAuthorizedOrNotFound` from Logging Management `ListLogs` means the `logGroupId` is wrong, the log group is in a different region, or the workload principal lacks `manage log-groups` in the log group's compartment. As a short diagnostic, temporarily test `manage logging-family in tenancy` for the same workload principal; if that works, narrow back to `manage log-groups` on the exact logging compartment or `target.loggroup.id`.

Events rule invocation policy:

```text
Allow any-user to use fn-invocation in compartment <function-compartment> where all {request.principal.type = 'eventrule'}
```

Scope these policies to the compartments and conditions your tenancy supports. If the rule uses defined tags, also grant `use tag-namespaces` for those tag namespaces. A missing workload policy can surface as `404 NotAuthorizedOrNotFound` from `CreateRule`; a missing function invocation policy can allow the rule to exist but prevent matching events from invoking the Function.

Object Storage event conditions do not require `object-family` permissions for rule creation. The bucket still must have object events enabled.

Use `manage all-resources` only as a short-lived diagnostic policy while proving an IAM gap, then replace it with the least-privilege policy set above.

## Extra Environment

Use `extraEnv` for additional literal values or Kubernetes `valueFrom` entries:

```yaml
extraEnv:
- name: OCI_REGION
  value: me-jeddah-1
```

Do not define the same environment variable twice. The chart's built-in OCI env vars use `value`, not `valueFrom`, so the rendered defaults avoid Kubernetes errors such as:

```text
env[0].valueFrom may not be specified when value is not empty
```

## Validate Rendering

```sh
helm lint charts/oci-functions-operator

helm template oci-functions-operator charts/oci-functions-operator \
  --namespace oci-functions-operator-system
```

Development helpers:

```sh
make helm-chart
make helm-crds-check
make helm-template
```

`make helm-chart` refreshes chart CRDs from `config/crd/bases`. `make helm-crds-check` fails if any generated CRD is missing from the chart or if a chart CRD is stale.

Check installed permissions after deployment:

```sh
kubectl auth can-i get functions.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i get functionapplications.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i update functionapplications.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i update functionapplications.functions.oci.oracle.com/status \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i update functions.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i patch functions.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i update functions.functions.oci.oracle.com/status \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i get functionjobs.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i get functioneventtriggers.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager

kubectl auth can-i get functionevents.functions.oci.oracle.com \
  --as=system:serviceaccount:oci-functions-operator-system:oci-functions-operator-controller-manager
```

## Troubleshooting

ImagePullBackOff:

- Confirm `image.repository` and `image.tag`.
- Confirm OKE nodes can pull from the image registry.
- Set `imagePullSecrets` if the operator image is private.

Missing CRDs:

- Confirm Helm installed the CRDs:
  `kubectl get crd functionapplications.functions.oci.oracle.com functions.functions.oci.oracle.com functionjobs.functions.oci.oracle.com functioneventtriggers.functions.oci.oracle.com functionevents.functions.oci.oracle.com`
- If CRDs were skipped or removed, apply:
  `kubectl apply -f charts/oci-functions-operator/crds/`

Stale CRDs after API changes:

- Helm does not upgrade `crds/` entries during normal upgrades.
- Apply the chart CRDs with `kubectl apply -f charts/oci-functions-operator/crds/`, then run `helm upgrade --install`.

Missing RBAC:

- Confirm `helm template` contains the ClusterRole rules for `functionapplications`, `functions`, `functionjobs`, `functioneventtriggers`, `functionevents`, their `status` and needed `finalizers`, and core `events`.
- Re-run the Helm upgrade if the ClusterRole drifted.
- Do not repair a Helm-managed install with `kubectl apply -k config/rbac`; keep ownership with Helm.

Wrong service account in IAM policy:

- Compare `kubectl -n oci-functions-operator-system get deploy oci-functions-operator-controller-manager -o jsonpath='{.spec.template.spec.serviceAccountName}'` with the IAM policy condition.
- The namespace and service account in OCI IAM must match the chart release.

`OCI_AUTH_MODE` accidentally set to `config` in OKE:

- OKE should normally use `oci.authMode=workload`.
- Check rendered env:
  `kubectl -n oci-functions-operator-system get deploy oci-functions-operator-controller-manager -o yaml`
- Do not mount local OCI config files or PEM keys into the OKE deployment.

Resource Principal env vars in OKE:

- Do not set `OCI_RESOURCE_PRINCIPAL_VERSION`, `OCI_RESOURCE_PRINCIPAL_REGION`, or other `OCI_RESOURCE_PRINCIPAL_*` variables for the Helm deployment.
- Use `oci.authMode=workload` and, when needed, `oci.region=<region>`.
- If manager logs mention missing `OCI_RESOURCE_PRINCIPAL_REGION`, confirm the chart and operator image include the Workload Identity auth fix.
