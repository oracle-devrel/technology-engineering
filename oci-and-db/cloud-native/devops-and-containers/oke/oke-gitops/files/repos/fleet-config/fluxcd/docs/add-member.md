# Add a decentralized Flux member

Resource Manager deliberately provisions OCI DevOps connectivity and the
installation pipeline for one OKE cluster only. Adding another cluster is an
explicit administrator operation. The additional cluster still runs local
Flux controllers and never receives another cluster's kubeconfig.

## 1. Prepare Git activation

Choose a stable lowercase name such as `oke-2`.

1. Copy `bootstrap/member-template.yml` to `bootstrap/oke-2.yml`.
2. Replace every `CHANGE_ME` with `oke-2`.
3. Create `clusters/oke-2/kustomization.yml`:

   ```yaml
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   resources:
     - flux-operator.yml
     - common.yml
     - development.yml
   ```

4. Create `clusters/oke-2/flux-operator.yml`:

   ```yaml
   apiVersion: kustomize.toolkit.fluxcd.io/v1
   kind: Kustomization
   metadata:
     name: fleet-flux-operator
     namespace: flux-system
   spec:
     interval: 5m
     sourceRef:
       kind: GitRepository
       name: fleet-config
     path: ./profiles/flux-operator
     prune: true
     wait: true
     timeout: 5m
   ```

5. Create `common.yml` with the same structure, using name `fleet-common`, path
   `./profiles/common`, and `dependsOn: [{name: fleet-flux-operator}]`.
6. If required, create `development.yml` using name `fleet-development`, path
   `./profiles/development`, and `dependsOn: [{name: fleet-common}]`.
7. Render `clusters/oke-2`, commit, review, and push. Do not apply its bootstrap
   manifest until the Flux installation pipeline has succeeded.

Profiles are optional placement. A production cluster might activate only
`flux-operator` and `common`; a profile may also be dedicated to one cluster.

## 2. Create the private OKE environment

In the same OCI DevOps project, create an **OKE Cluster** deployment
environment for the additional cluster:

- select the additional OKE cluster;
- use a **Private Endpoint Channel**;
- select a subnet that can resolve and reach that cluster's private API
  endpoint and OCI services;
- attach an NSG when required by the cluster's network policy.

Do not select the public endpoint. The subnet and NSG are intentionally not
Resource Manager variables because they belong to this independently onboarded
cluster.

## 3. Create the installation pipeline

Create a dedicated deployment pipeline named `install-flux-oke-2`. Resource
Manager must not manage this pipeline. Define these parameters:

| Parameter | Value |
|---|---|
| `target_cluster_id` | Additional OKE cluster OCID |
| `chart_version` | Exact Flux Operator chart version already mirrored to OCIR |
| `chart_name` | `flux-operator` |
| `namespace` | `flux-system` |
| `region_key` | OCIR region key, for example `lin` |
| `tenancy_namespace` | Object Storage tenancy namespace used by OCIR |
| `repo_prefix` | The same OCIR repository prefix configured in the Resource Manager stack |
| `deployment_nonce` | A unique value for every installation run, for example the deployment timestamp or change ticket |
| `git_read_credentials_secret_ocid` | Vault JSON secret for the read-only Git identity |
| `registry_pull_secret_ocid` | Vault JSON secret for the read-only OCIR identity |
| `auth_token_secret_ocid` | `CHANGE_ME`; deprecated fallback only |

Add two stages in this order:

1. A Shell stage using the existing `gitops-bootstrap-prepare` command-spec
   artifact. Use a Container Instance network channel with connectivity to the
   additional cluster's private API. The reusable command artifact selects the
   cluster through `target_cluster_id` and creates only `flux-system`,
   `git-token-auth`, and `ocirsecret`.
2. An **OKE Helm Chart Deployment** stage targeting the additional cluster's
   environment. Use the existing `flux-operator-chart` and
   `flux-operator-chart-values` artifacts, execute a Helm upgrade, and make it
   depend on the Shell stage. Enable **Force Helm**, then add the string value
   `bootstrapNonce=${deployment_nonce}`. The Flux Operator chart safely ignores
   this unknown value; changing it prevents OCI DevOps from treating a deleted
   same-version release as an already completed deployment.

The three OCIR parameters are required because the shared values artifact uses
them to construct the mirrored controller image names. A literal
`${region_key}` or `${tenancy_namespace}` in a rendered Deployment means the
manual pipeline omitted these parameters.

Run `mirror-gitops-agent` first if the requested exact chart version is not
already present in OCIR. Then run the member installation pipeline with both
Vault secret OCIDs and a new `deployment_nonce`. Reuse the same chart version
when reinstalling, but never reuse the nonce. Do not use `LATEST` in the
deployment pipeline: resolve and mirror an exact version first.

## 4. Hand off to GitOps

Configure `kubectl` for the additional cluster's private endpoint and run:

```bash
kubectl apply -f bootstrap/oke-2.yml
kubectl -n flux-system get fluxinstance,resourceset
kubectl -n flux-system get gitrepository,kustomization,helmrelease
```

Expected sources are `fleet-config` and `apps-config`; an additional member
does not reconcile `cluster-config`. Its root Kustomization must be
`fleet-oke-2` and its path must be exactly `./clusters/oke-2`.

Once healthy, normal operation is Git-only. The manually created environment
and pipeline remain administrator-owned OCI DevOps resources and must be
updated or deleted manually when the member is upgraded or removed.
