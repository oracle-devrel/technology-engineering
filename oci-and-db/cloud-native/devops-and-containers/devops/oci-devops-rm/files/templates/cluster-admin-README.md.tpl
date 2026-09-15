# Cluster Administration

This repository owns cluster-wide Kubernetes objects and cluster-specific tool configuration for the OKE clusters connected to the `${project_name}` OCI DevOps project.

## Layout

- `catalog/tools.yaml`: stack-managed pinned public Helm charts mirrored into OCIR.
- `clusters/<cluster>/baseline`: non-namespaced Kubernetes objects applied with `kubectl apply --server-side`.
- `clusters/<cluster>/tools/<tool>/values.yaml`: values for that tool on that physical cluster.
- `clusters/<cluster>/tools/<tool>/tool.yaml`: tool name, namespace, and `depends_on` metadata generated when the target is added.
- `clusters/<cluster>/tools/<tool>/resources`: supplemental namespaced objects applied after Helm.
- `clusters/<cluster>/tools/<tool>/verify.sh`: optional post-deployment verification script.

Changes must reach `main` through a pull request. The PR pipeline validates configuration and dependency cycles without touching a cluster. After merge, only changed stages are dispatched. Independent tools run in parallel dependency waves, supplemental resources follow their tool's Helm stage, and selected cluster-wide baseline resources run last so they can use CRDs installed by the charts.

Before mirroring charts, requesting approval, or mutating a cluster, `cluster-admin-build` prints an execution plan containing the configuration commit, selected cluster, dependency waves, actions, namespaces, chart versions, values versions, and final baseline work. The production deployment includes a compact target summary in its display name and tags.

Both cluster pipelines use the same shell orchestrator and immutable commit-versioned deployment plan. `cluster-admin-noprod` starts its orchestrator immediately; `cluster-admin-prod` requires approval first. Each orchestrator deploys only selected targets in dependency waves and applies baseline resources last. Cluster-specific values and supplemental resources remain under their respective `clusters/<cluster>` directories.

Cluster pipelines expose only `config_commit`, `cluster_id`, and `cluster_name`. The dispatcher supplies chart/value versions and tool identity as generic stage-level overrides, so adding tools does not expand the pipeline parameter list.

Resource Manager regenerates only `catalog/tools.yaml` and adds missing cluster/tool directories when its cluster administration JSON changes. Other existing repository files are never replaced. Every JSON tool entry must include the public Helm repository, upstream chart name, and pinned version; edit those coordinates through Resource Manager rather than directly in the generated catalog.

The repository field accepts either an HTTPS Helm repository or an OCI repository base path. OCI charts are resolved as `<repository>/<chart>`. Public OCI sources work without additional authentication; private sources require Helm credentials for the source registry.

Removing a manifest does not delete the live object, and out-of-band drift is not continuously reconciled. Plain Kubernetes `Secret` resources are rejected; use External Secrets Operator resources instead.

The orchestrators retain Helm releases unless the explicit decommission pipeline is run. Removing a file from `resources/` still does not prune the live object.

Use `cluster-admin-<cluster>-decommission` before removing a tool from Git or Resource Manager. Supply the tool name and namespace, then type `DELETE <cluster>/<tool>` exactly. The pipeline validates and deletes supplemental resources, uninstalls the Helm release, and retains the namespace for review. Production requires approval before removal.

OCI resources created for this workflow carry freeform tags for `owner=cluster-administrators`, `purpose=cluster-administration`, and `scope=operations`, plus `cluster`, `tool`, and `role` where applicable.
