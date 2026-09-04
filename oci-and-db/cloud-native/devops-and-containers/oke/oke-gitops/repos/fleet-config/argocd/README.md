# Operate an Argo CD fleet

This repository is the cluster administrator's source of truth for resources
delivered from one Argo CD hub to registered spoke clusters. Spokes do not run
a local GitOps controller.

## Start here

1. [Understand the architecture](docs/architecture.md).
2. [Register a cluster](docs/register-cluster.md).
3. [Choose a use case and review impacted files](docs/use-cases.md).
4. [Learn the cluster/profile model](docs/deployment-patterns.md).
5. [Use the naming conventions](docs/naming.md).
6. [Validate and operate changes](docs/operations.md).

## Repository layout

```text
clusters/
  <cluster>/
    cluster.yaml                  Identity and one clusterResourcesPath
    applications/
      <binding>/
        kustomize.application.yaml
        # OR helm-repository.application.yaml
        # OR helm-git.application.yaml
      <environment-aware-application>/
        application.yaml
        infrastructure/application.yml
        components.application-set.yml
profiles/
  <profile>/
    profile.yaml
    cluster-resources/           The profile's single cluster Kustomize root
      kustomization.yml
    applications/
      <application>/
        resources/               Reusable namespaced Kustomize resources
        values/                  Reusable ordered Helm values
        chart/                   Optional Git-hosted chart
examples/
  oke-example/                   Inactive complete cluster object
```

Each profile is an umbrella configuration set, not one application. It can
contain the cluster-resource root and any number of Kustomize or Helm
applications. Profiles select nothing by themselves. A cluster selects exactly
one cluster-resource root in `cluster.yaml`; its application descriptors then
bind the required profile applications.

A profile may be shared by many clusters or intentionally dedicated to one
cluster. A dedicated profile is useful whenever configuration belongs to one
cluster, from a complete configuration set to a small exception. Its
assignment is still explicit in that cluster's `cluster.yaml` and application
descriptors.

Cluster files below `clusters/*/cluster.yaml` and descriptors below
`clusters/*/applications/*/` are discovered. Environment-aware applications
use a parent descriptor and keep infrastructure and component activation in the
same folder. The inactive example and unbound profiles deploy nothing.

## Generated ApplicationSets

The hub `cluster-config/gitops/argocd/fleet.yml` contains:

- `fleet-cluster-resources`
- `fleet-kustomize`
- `fleet-helm-repository`
- `fleet-helm-git`
- `fleet-applications`

These mirror the single-cluster platform delivery forms. The first
ApplicationSet is an adapter implementation detail: it creates one Argo CD
reconciliation object per cluster, but there is no cluster-resource
application descriptor in Git. A cluster or descriptor's `cluster` value
selects an Argo CD cluster Secret labeled
`fleet.oke.oracle.com/cluster=<name>`.

`fleet-applications` creates a hub-side parent Application per logical
application and cluster. A wave `-10` child reconciles profile-owned namespace
infrastructure; the wave `0` component ApplicationSet creates one Application
per selected component/environment pair from `apps-config`. Reuse the folder
beneath several cluster objects to deploy the same selection to several clusters.

The seed includes both component Kustomize (`reference-app`) and Git-hosted
umbrella Helm (`reference-helm-app`) examples. The Helm example keeps all
subcharts disabled by default and activates frontend/dev and api/dev as two
independent Applications on the managed cluster.

## Create the first cluster object

```bash
cp -R profiles/example profiles/standard
cp -R examples/oke-example clusters/oke-2
```

Then replace `oke-example` in `cluster.yaml` and every application descriptor,
and replace `profiles/example` paths with `profiles/standard`. Remove bindings
that do not apply. Label the runtime cluster Secret as documented in
[registration](docs/register-cluster.md), render the changed resources,
commit, review, and merge.
