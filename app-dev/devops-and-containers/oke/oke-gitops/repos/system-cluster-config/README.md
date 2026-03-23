# System Cluster Configuration Repository

This Git repository serves as a centralized configuration hub for managing Kubernetes clusters using ArgoCD, a declarative, GitOps continuous delivery tool for Kubernetes.


## First access to ArgoCD

ArgoCD has been installed in the argocd namespace of the cluster.
For the first access, you can get the admin password directly from the secret by running this command:

`kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

Then, you can initially access the argocd interface by performing a port-forwarding:

`kubectl port-forward svc/argo-cd-argocd-server -n argocd 8080:443`

After running the command, you should be able to access ArgoCD UI from `localhost:8080`, enter with username **admin** and the admin password.

NOTE: If you have deployed the Helm Chart on a private OKE cluster, you will need to perform some networking setup to be able to connect through kubectl.

## Connecting to the OCI Code Repository

Under `Settings --> Repositories` click on **CONNECT REPO** and select to connect to a repository **VIA HTTPS**.
Fill the form with the following values:
1. `Repository type`: "git"
2. `Repository URL`: <oke-cluster-config clone URL>
3. `Project`. "None" (leave blank)
4. `Username`: \<OCI username of a user with access to the git repository>
5. `Password`: \<Auth Token of the user>

The repository we want to connect to is the system-cluster-config repository in OCI DevOps, already created by the Resource Manager Stack.
It's better to go into the OCI DevOps, find the repository, and find the right HTTPS clone URL.

NOTE: The username to connect to the OCI DevOps Code Repository should be `<tenancy_name>/<user_domain>/<user_name>`

## Clone the OCI Code Repository locally

It is always better to clone the Git repository locally and have an appropriate IDE where we can work. A lot of YAMLs are involved when managing a cluster,
so it's important to correctly indent the code.
Once you have cloned the **system-cluster-config**, it's time to perform the following actions:
1. Deploy the cluster secret by running `kubectl apply -f in-cluster.yml`
2. Substitute `#RepoURL` in `hub.yml` with the repository https URL from OCI DevOps
3. Substitute `#RepoURL` in `appsets/hub/ci-cd/argocd.yml` and `appsets/hub/infra.yml` with the repository https URL from OCI DevOps
3. Push the code to the remote Git repository
4. Run `kubectl apply -f hub.yml`
5. You will lose the port-forwarding session if still active, but don't worry, it's something expected
6. Access to the ArgoCD UI, and be sure that `hub-apps` application is synchronized

After having performed these steps, you will have an installation of ArgoCD configured with the apps-of-apps pattern.

## Overview

ArgoCD is a tool that automates the deployment of applications to Kubernetes clusters by keeping the cluster state in sync with configurations stored in Git repositories. It provides a web UI for visualizing applications, their statuses, and allowing manual or automated syncing.

This repository organizes configurations to install tools and configure clusters through ArgoCD ApplicationSets. ApplicationSets are templates that generate multiple ArgoCD Applications based on defined criteria, allowing scalable deployment across multiple clusters.

## Key Concepts

- **Clusters**: Kubernetes clusters managed by ArgoCD. Each cluster is registered as a Secret in the ArgoCD namespace with labels indicating its type (e.g., "hub" for the main ArgoCD server cluster, "workload" for application clusters), region, provider, and environment.

- **Applications**: Individual deployments managed by ArgoCD, pointing to Helm charts, Kustomize manifests, or plain YAMLs.

- **ApplicationSets**: Templates that generate Applications dynamically. They use generators to define where (clusters) and what (applications) to deploy.

## Repository Structure

```
system-cluster-config/
├── hub.yml                 # ArgoCD Application to deploy ApplicationSets to the hub cluster
├── in-cluster.yml          # Secret defining the hub cluster itself
├── apps/                   # Application definitions, organized by category
│   ├── ci-cd/              # Category for CI/CD tools
│   │   └── argocd/         # ArgoCD application
│   │       ├── config/     # Configuration JSON for cluster profiles
│   │       ├── helm/       # Helm values for profiles
│   │       └── kustomize/  # Kustomize overlays for profiles
│   └── app-category/       # Category for example applications
│       └── example-app/    # Example application
│           ├── config/     # Profile-specific configs
│           ├── helm/       # Helm values per profile
│           └── kustomize/  # Kustomize overlays per profile
├── appsets/                # ApplicationSet definitions
│   └── hub/                # Profile-specific ApplicationSets (hub profile)
│       ├── ci-cd/
│       │   └── argocd.yml  # ApplicationSet for deploying ArgoCD
│       └── infra.yml       # ApplicationSet for infrastructure apps
└── infra/                  # Cluster-level infrastructure resources
    ├── base/               # Base kustomize resources (quotas, namespaces, etc.)
    └── overlays/           # Profile-specific overlays
        └── hub/            # Hub cluster infrastructure
            ├── common/     # Resources common to all namespaces (RBAC, configmaps)
            ├── namespaces/ # Namespace-specific resources
            │   └── dev-team/  # Example namespace (dev-team)
            └── kustomization.yaml  # Main overlay combining all resources
```

### Infrastructure Folder

The `infra/` folder manages cluster-level infrastructure resources using a **3-tier hierarchical structure** deployed via Kustomize. This approach provides clear separation of concerns and promotes reusability across namespaces.

#### 3-Tier Structure Explained

**1. Base Layer (`infra/base/`)**
- Contains **global cluster resources** that apply to the entire cluster
- Examples: ResourceQuotas, PersistentVolumeClaims, ValidatingAdmissionPolicies, cluster-wide ConfigMaps
- These resources are shared across all namespaces and profiles

**2. Common Layer (`infra/overlays/hub/common/`)**
- Contains **cross-namespace resources** shared by multiple namespaces
- Examples: RBAC roles/cluster roles, shared ConfigMaps, NetworkPolicies that apply to multiple namespaces
- These resources are applied to all namespaces within a profile (e.g., hub)

**3. Namespace Layer (`infra/overlays/hub/namespaces/dev-team/`)**
- Contains **namespace-specific resources**
- Examples: Namespace definitions, namespace-scoped RBAC, namespace-specific quotas
- Each namespace gets its own folder following the pattern `namespaces/<namespace-name>/`

#### How It Works

The main overlay (`infra/overlays/hub/kustomization.yaml`) combines all layers:
1. **First**: Imports base resources (global scope)
2. **Then**: Includes namespace-specific configurations, which automatically include common resources

This hierarchical approach ensures:
- **DRY Principle**: Common resources aren't duplicated
- **Scalability**: Easy to add new namespaces following the same pattern
- **Maintainability**: Clear organization makes it easy to find and modify resources
- **Consistency**: Base and common resources are applied uniformly across the cluster

#### Example Workflow

When deploying infrastructure to a hub cluster:
1. Base resources (quotas, PVCs) are applied cluster-wide
2. Common resources (shared RBAC, configmaps) are applied to all namespaces
3. Namespace-specific resources (namespace definition, local RBAC) are applied to each namespace

This structure provides a solid foundation for managing complex multi-tenant Kubernetes clusters.

### Workflow

1. **Define Clusters**: Create Secrets in ArgoCD for each cluster, labeled appropriately (e.g., `type: hub`).

2. **Bootstrap Hub**: Apply `hub.yml` to deploy ApplicationSets to the hub cluster. This creates ApplicationSets that will generate Applications for matching clusters.

3. **ApplicationSets Generate Applications**: Each ApplicationSet uses generators to:
   - Select clusters based on labels (e.g., `type: hub`).
   - Pull configuration from `apps/*/config/config-*.json` to define what to deploy.

4. **Deploy Applications**: Generated Applications deploy using sources like Helm charts with values, Kustomize overlays, etc., tailored to the cluster type.

## Profiles and Overlays

Cluster profiles are defined by labels on cluster Secrets (e.g., `type: hub`, `type: workload`). These profiles determine which clusters an application deploys to and how it's configured.

- **Profiles**: Hub profile targets clusters with ArgoCD installed. Other profiles (e.g., workload) target application clusters.
- **Kustomize Overlays**: In `apps/category/app/kustomize/overlays/`, provide profile-specific customizations (e.g., `overlays/hub/` for hub clusters).
- **Helm Values**: In `apps/category/app/helm/values/`, YAML files tailored to profiles (e.g., `values-hub.yml`, `values-workload.yml`).

Applications are organized into category folders (e.g., `ci-cd/`, `app-category/`) to maintain order and scalability.

## Summary

1. Set up ArgoCD on your hub cluster.
2. Register clusters as Secrets (apply `in-cluster.yml` for the hub).
3. Customize `hub.yml` with the repo URL and apply it.
4. ApplicationSets will automatically generate and deploy applications to matching clusters.

For detailed ArgoCD documentation, visit [argo-cd.readthedocs.io](https://argo-cd.readthedocs.io).
