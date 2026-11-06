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

## Mirror Container Images

Enable `mirror_images` per tool in the Resource Manager/Terraform cluster-tool
configuration; it defaults to `false`. Use `additional_images` for operator-created
workloads or images not present in rendered standard Pod specifications. Terraform
updates these stack-managed catalog fields and triggers affected builds without
overwriting customer-owned target values. Removing an entry does not delete its
previously mirrored OCIR content.

Mirroring runs in `cluster-admin-build` after chart mirroring, not in deployment
shell stages. It renders install and upgrade workloads, including hooks, with
each selected target's values, namespace and release name from the selected Git
commit. Different targets can discover different images; shared copies are
deduplicated. Local rendering cannot discover live `lookup` results or arbitrary
image references inside custom resources; declare those with `additional_images`.

The build runner needs upstream registry access. Images are copied to private
OCIR with all platforms preserved and source/destination manifest digests checked:

```text
<registry>/<tenancy-namespace>/<project>/images/cluster-tools/<source-registry>/<source-repository>:sha256-<digest>
```

Each target/tool publishes `cluster-admin/<cluster>/tools/<tool>/images.json` in
the Generic Artifact repository, versioned by the full configuration commit.
Inspect its source-to-destination mappings, chart version and values hash;
destination tags are digest-derived, not the upstream version tags. Images already
in the target OCIR tenancy namespace are reported without recursive copying.

For an air-gapped target:

1. Build the intended per-target values and explicit additional images, then
   inspect the immutable mapping reports before approving deployment.
2. Set the chart's registry, repository and tag or digest values to the reported
   OCIR references. Configure private OCIR pull authentication separately.
3. Commit those values and verify the resulting build and normal deployment
   pipelines. Mirroring does not rewrite values or manifests, install pull secrets,
   enforce registry use, or bypass production approval.
4. Verify every running container and init container uses the intended OCIR image
   and digest, including conditionally enabled hooks or operator workloads. Check
   workload readiness and required Oracle Service Network connectivity; a successful
   mirror build alone does not prove the cluster can pull or run the images.

Keep upstream credentials out of catalogs, values and reports. If private source
registries require authentication, use the build runner's private
`REGISTRY_AUTH_FILE`; do not disable registry TLS verification.

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
