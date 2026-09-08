# Cluster Administration

## Add Or Change A Tool

1. Edit the tool catalog and cluster-specific values in the generated
   `cluster-admin` repository.
2. Pin the chart repository, chart name, and exact version.
3. Express dependencies with `depends_on`; keep the graph acyclic.
4. Put supplemental namespaced objects only in the configured tool namespace.
5. Open a PR and confirm validation succeeds before merging.
6. After merge, verify that only affected cluster targets are selected.
7. Confirm missing charts are mirrored and immutable values artifacts use the
   full configuration commit.
8. Observe tool deployment in dependency waves. Independent tools may run in
   parallel; dependent tools wait for their prerequisites.
9. Confirm selected cluster-wide baseline resources are applied last because
   they may depend on tool-provided CRDs.

Pre-production begins without approval. Production requires approval before
mutation. Values and resources may differ by physical cluster; there is no
application-style environment promotion model for tools.

## Decommission

Use the explicit tool decommission pipeline for the selected cluster. Confirm
the exact Helm release, namespace, and supplemental resources before running
it. Removing a file or tool from Git does not automatically prune the live
object.

## Verify

Correlate the configuration commit, mirror run, immutable values version,
orchestrator run, Helm release revision, Kubernetes workload health, and any
supplemental resources. When two logical targets point to one physical cluster,
account for namespace and release-name collisions before deployment.
