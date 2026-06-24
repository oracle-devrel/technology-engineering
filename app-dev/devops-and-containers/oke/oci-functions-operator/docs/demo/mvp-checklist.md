# MVP Demo Checklist

Secondary checklist. Use [MVP demo flow](mvp-demo-flow.md) as the primary guide.

## Repo

- [ ] Final image tag is visible in README and Helm docs: `ghcr.io/ronsevet/oci-functions-operator/controller:mvp-events-functionevents-v1`.
- [ ] `make test` passes.
- [ ] `helm lint charts/oci-functions-operator` passes.
- [ ] `helm template oci-functions-operator charts/oci-functions-operator --namespace oci-functions-operator-system --set oci.region=me-jeddah-1 --include-crds` renders the final image tag.
- [ ] `git diff --check` passes.

## Cluster

- [ ] `kubectl config current-context` points at the demo OKE cluster.
- [ ] `kubectl apply -f charts/oci-functions-operator/crds/` succeeds.
- [ ] Operator Deployment rolls out in `oci-functions-operator-system`.
- [ ] CRDs exist for `Function`, `FunctionJob`, `FunctionEventTrigger`, and `FunctionEvent`.

## OCI

- [ ] Workload Identity IAM matches namespace `oci-functions-operator-system`.
- [ ] Workload Identity IAM matches service account `oci-functions-operator-controller-manager`.
- [ ] Workload can inspect compartments, manage `functions-family`, use network resources, and manage `cloudevents-rules`.
- [ ] `eventrule` principal can use `fn-invocation` in the Function compartment.
- [ ] Function runtime image exists in Jeddah OCIR and is Fn-compatible.
- [ ] Function subnet and NSG allow egress TCP 443 to Oracle Services Network/OCIR.
- [ ] Object Storage bucket events are enabled if showing the OCI Events use case.

## Expected Demo States

- [ ] `managed-hello` reaches `Ready=True`.
- [ ] `managed-hello-job` reaches `Succeeded`.
- [ ] `object-created-trigger` reaches `Ready` with an OCI Events Rule OCID.
- [ ] `order-created-trigger` reaches `Ready` without an OCI Events Rule OCID.
- [ ] `order-created-abc123` reaches `Processed`.
- [ ] OCI Console metrics/logs show at least one real Function invocation.
