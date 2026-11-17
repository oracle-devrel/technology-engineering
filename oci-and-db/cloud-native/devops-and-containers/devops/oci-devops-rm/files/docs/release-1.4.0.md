# OKE DevOps Starter 1.4.0

## Cluster Tool Image Mirroring

Cluster tools can now mirror container images to private OCIR repositories during
their build. Enable `mirror_images` per tool; it is disabled by default.

Discovery renders each target's committed Helm values, including conditional
workloads, hooks and init containers. Non-production and production can discover
different images from the same chart. Use `additional_images` for operator-created
workloads and images that are not visible in locally rendered manifests.

Copies preserve multi-platform manifests and verify source and destination
digests. Immutable per-target `images.json` reports map upstream references to
digest-derived OCIR references. Terraform changes to mirroring settings and
additional images update the tool catalog and select affected builds; values-only
changes also trigger preparation.

Mirroring supports air-gapped OKE deployments without changing administrator-owned
Helm values. Administrators explicitly configure destination image references and
private OCIR pull authentication. Deployment stages do not download upstream
images or run mirroring tools, and production approvals remain unchanged.

## Agent Skill

The portable `oke-devops-starter` skill now covers mirroring settings, per-target
image reports, discovery limits and air-gapped workload verification.

## Release Assets

- `stack.zip`: Resource Manager configuration in release mode.
- `stack.zip.sha256`: SHA-256 checksum for the stack archive.
- `oke-devops-starter.zip`: updated portable agent skill.
