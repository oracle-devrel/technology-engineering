# Solution Map

## Delivery Modes

- `oci_devops`: OCI DevOps owns component CI, application charts, development,
  staging, approval, production promotion, and releases.
- `build_only`: OCI DevOps owns PR validation and immutable component image
  builds. Another delivery system owns application deployment.
- `enable_cluster_admin=true`: adds an independent operations workflow for
  cluster tools and cluster-wide or supplemental namespaced resources.

These choices are independent. In hybrid deployments, define ownership per
Kubernetes object, not merely per namespace.

## Generated Resources

The shared pipeline repository defaults to `devops-pipelines`. Each component
has a source repository, PR pipeline, and build pipeline. Full delivery also
adds one chart repository and baseline lifecycle per application, plus dev and
release pipelines per component.

Cluster administration adds the `cluster-admin` repository, chart mirroring,
immutable values artifacts, and pre-production and production orchestrators.

Resource Manager outputs expose the actual repository URLs, pipeline OCIDs,
environment OCIDs, artifact paths, and suggested next actions. Prefer those
outputs over deriving OCIDs manually.

## Naming

- Image: `<project>/<application>/<component>:<sha7-or-release>`
- Umbrella chart: `<project>/charts/<application>`
- Component chart: `<project>/charts/<application>/<component>`
- Component dev Helm release: `<component>-dev`
- Component staging Helm release: `<component>-staging`
- Component production Helm release: `<component>`
- Application pre-production baseline: `<application>-noprod`
- Application production baseline: `<application>`

Application names are unique. Component names are globally unique.

## Template Ownership

Terraform creates stable wiring and starter content. Release-mode lifecycle
rules preserve later pipeline customization, and repository seeding adds only
missing paths. Do not assume a later stack apply refreshes customer-edited
repository files or pipeline internals.
