# Native Argo CD fleet

The hub Argo CD manages spokes directly. Spokes run neither Argo CD nor Flux.
Hub pods must reach every spoke private Kubernetes API endpoint.

## Runtime registration

Never commit a populated cluster Secret. Create it in hub namespace `argocd`
with `argocd.argoproj.io/secret-type: cluster` and label:

```text
fleet.oke.oracle.com/cluster=<cluster-object-name>
```

Its server must be the spoke private API URL. Use reviewed least privilege for
the spoke credential.

## Repository model

```text
fleet-config/
  clusters/<cluster>/
    cluster.yaml
    applications/<binding>/<kind>.application.yaml
    applications/<logical-app>/
      application.yaml
      infrastructure/application.yml
      components.application-set.yml
  profiles/<profile>/
    profile.yaml
    cluster-resources/kustomization.yml
    applications/<application>/{resources,values,chart}/
```

`cluster.yaml` selects exactly one `clusterResourcesPath`. Cluster resources
have no application descriptor. Namespaced Kustomize and Helm use per-cluster
descriptors. Logical developer applications use the same parent/wave pattern
as local placement and read workloads from `apps-config`.

A profile may be shared or intentionally dedicated to one cluster. Put all
cluster-specific desired state in a clearly named dedicated profile; do not
invent a `clusters/<cluster>/local/` payload hierarchy.

Generated Application names append the cluster name. Application descriptors'
`cluster` value and runtime Secret label must match exactly.

## Before merge

Render every changed profile Kustomization and chart. Review cluster, namespace,
paths, chart version, ordered values, and pruning. After merge, verify on the
hub that the generated Application destination resolves to the private spoke
API, then verify workload health on the spoke.
