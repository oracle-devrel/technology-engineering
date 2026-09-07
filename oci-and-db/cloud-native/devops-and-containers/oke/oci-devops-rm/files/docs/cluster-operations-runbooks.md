# Cluster Operations Runbooks

These runbooks assume `enable_cluster_admin=true` and an initialized `cluster-admin` repository.

## Add A Tool

Adding a tool changes the administrator-owned repository and the topology consumed by both orchestrators; it does not create per-tool OCI stages.

1. Add the globally unique tool name, public Helm repository, upstream chart name, pinned version, namespace, and direct `depends_on` entries to the Resource Manager `cluster_administration.tools` list.
2. Apply the stack to create the tool stages in both `cluster-admin-noprod` and `cluster-admin-prod`.
3. Confirm the stack added the configured chart source to `catalog/tools.yaml`.
4. Review the seeded `tool.yaml` and `values.yaml` under both `clusters/noprod/tools/<tool>` and `clusters/prod/tools/<tool>`.
5. Configure noprod first. Keep prod values valid, but deploy the prod configuration only through a reviewed prod change and approval.
6. Add optional `resources/*.yaml` and `verify.sh` files.
7. Open a pull request and make `cluster-admin-pr` pass.
8. Merge to `main` and confirm the missing chart is mirrored before the selected deployment stages run.

The shared topology creates the tool stages for both clusters. The namespace defaults to the tool name; keep explicit namespaces synchronized between Resource Manager and both generated `tool.yaml` files.

## Define Tool Dependencies

1. Put only direct prerequisites in `depends_on`; transitive dependencies are derived.
2. Declare the same dependency topology in Resource Manager and each tool's `tool.yaml`.
3. Open a pull request and let validation reject unknown tools, self-dependencies, duplicates, or cycles.
4. After merge, confirm independent tools run in parallel and dependent tools start in later waves.

When a prerequisite changes, the dispatcher also selects downstream dependents.

## Change Cluster Values

1. Edit only `clusters/<cluster>/tools/<tool>/values.yaml`.
2. Open and merge a pull request.
3. Confirm `cluster-admin-build` publishes an immutable Generic Artifact with the full Git commit SHA as its version.
4. Confirm only the selected cluster/tool Helm stage runs, plus any required downstream dependents.
5. For prod, approve the production approval deployment before mutation begins.
6. Verify the Helm release in the tool namespace.

Noprod and prod values are independent even though the tool topology is shared.

## Add Supplemental Namespaced Resources

1. Add YAML under `clusters/<cluster>/tools/<tool>/resources`.
2. Set the resource namespace to the configured tool namespace, or omit it when the resource type and script safely default it.
3. Do not commit plain Kubernetes `Secret` objects. Use External Secrets or another reference to an external secret store.
4. Open and merge a pull request.
5. Confirm the tool Helm stage runs before the supplemental-resource stage when both are selected.

Validation rejects explicit cross-namespace resources.

## Add Cluster-Wide Resources

1. Add non-namespaced YAML under `clusters/<cluster>/baseline`.
2. Use this location for resources such as ClusterRoles, ClusterRoleBindings, StorageClasses, and custom resources that are not owned by a tool chart.
3. Open and merge a pull request.
4. Confirm the baseline stage validates that every object is cluster-scoped.
5. Confirm selected tool waves finish before the baseline stage, allowing baseline objects to use tool-installed CRDs.

## Promote A Tool Configuration To Prod

There is no automatic environment promotion. Prod is a separate physical-cluster configuration.

1. Copy or adapt the reviewed noprod values and resources into `clusters/prod/tools/<tool>`.
2. Review cluster-specific endpoints, storage classes, load balancer annotations, identities, and capacity.
3. Open and merge a pull request.
4. Confirm `cluster-admin-prod` starts and pauses at its approval stage.
5. Review the target summary and approve it.
6. Verify the production orchestrator deploys only the selected targets and applies baseline resources last.

When noprod and prod point to the same test cluster, avoid conflicting release names, namespaces, cluster-scoped objects, and external endpoints.

## Remove A Tool

Removal is explicit because deleting Git files does not prune live resources.

1. Keep the tool configuration on `main` so the removal pipeline can validate its supplemental resources.
2. Identify cluster-scoped objects not owned by the Helm release; the pipeline intentionally does not infer or delete those objects.
3. Run `cluster-admin-<cluster>-decommission` with `tool_name` and `tool_namespace`.
4. Approve the deployment when removing from prod.
5. Confirm supplemental resources are absent and the Helm release is uninstalled. The namespace is deliberately retained.
6. Verify the namespace contains no unrelated workloads before deleting it manually.
7. Remove dependent references, then remove the tool from Git and the Resource Manager topology.
8. Apply the stack only after live cleanup and dependency review are complete.

Neither cluster has per-tool Helm stages. Use the explicit decommission pipeline for removal.
