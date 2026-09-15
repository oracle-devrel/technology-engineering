# Architecture

The hub's Argo CD instance manages registered spoke clusters directly:

```text
cluster.yaml ─────── singleton cluster-resource Kustomization
profile application ─── namespaced/Helm binding descriptor
logical application ─── parent with infrastructure + component ApplicationSet
                         ↓
                ApplicationSet Git generator
                         +
                ApplicationSet cluster generator
                         ↓
                Application on spoke private API
```

Cluster credentials are runtime Argo CD Secrets and never Git content.
`fleet.oke.oracle.com/cluster=<name>` connects a Secret to `cluster.yaml` and
descriptors whose `cluster` field has the same value.

The Git repository deliberately separates three concerns:

- `profiles/<name>` owns one complete reusable configuration set, containing a
  cluster-resource root and any number of applications;
- `clusters/<name>` represents one cluster;
- `clusters/<name>/applications/<binding>` says which administrator-owned
  profile application content is delivered to that cluster;
- `clusters/<name>/applications/<application>` may converge profile-owned
  infrastructure and developer-owned component overlays beneath one
  logical parent.

The logical parent exists on the hub. Its child Applications target the
registered spoke by name. Infrastructure uses sync wave `-10`; the component
ApplicationSet uses wave `0` and has no ordering among generated Applications.
The hub's Application health customization makes the parent wait until
infrastructure is Healthy before advancing.

Cluster resources remain a singleton, like `platform/cluster-resources` in the
single-cluster repository. Argo CD still reconciles that path through one
generated Application per cluster because Application is its delivery unit;
the administrator does not model it as an application or create a descriptor.
Cluster-specific configuration lives in an intentionally dedicated profile.

No GitOps controller is installed on a spoke. Networking must permit the
hub's Argo CD workloads to reach every spoke's private Kubernetes API endpoint.
