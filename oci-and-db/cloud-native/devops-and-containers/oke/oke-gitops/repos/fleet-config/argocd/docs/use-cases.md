# Native Argo CD fleet use cases

All fleet operations are initiated from the hub. Spokes run no GitOps agent and
Argo CD connects only to their private Kubernetes API endpoints.

| Fleet task | Create | Modify |
|---|---|---|
| Register a spoke | Runtime Argo CD cluster Secret and `clusters/<cluster>/cluster.yaml` | Label the Secret `fleet.oke.oracle.com/cluster=<cluster>` |
| Add cluster-wide resources | `profiles/<profile>/cluster-resources/kustomization.yml` and manifests | The cluster object's `clusterResourcesPath` |
| Add namespaced Kustomize | Profile application resources plus `clusters/<cluster>/applications/<binding>/kustomize.application.yaml` | — |
| Add repository Helm | Profile values/resources plus `helm-repository.application.yaml` binding | Its explicit ordered `helm.valueFiles` list |
| Add Git-hosted Helm | Profile chart/values/resources plus `helm-git.application.yaml` binding | Its explicit ordered `helm.valueFiles` list |
| Combine Helm and Kustomize | Resources below the bound profile application | Its `resources/kustomization.yml` |
| Operator plus custom resources | Operator binding and custom resources | Dependent-resource sync-wave annotations |
| Several independent tools in one namespace | One binding per tool | Use one shared `namespace`; ensure unique object ownership |
| Place a Kustomize developer application | Parent, infrastructure, and component ApplicationSet below the cluster application directory | Selected component/environment list |
| Place an umbrella Helm developer application | Equivalent parent folder | Selected component/environment list; global values load before the component file |
| Share configuration | One reusable profile | Point multiple cluster objects/bindings at it |
| Keep a cluster-specific exception | One `profiles/<cluster>-specific/` profile | Point only that cluster at it |
| Withdraw a workload | — | Remove the binding or component selection; review pruning first |
| Roll back | Git revert commit | — |

Use [deployment patterns](deployment-patterns.md) for descriptor examples,
[registration](register-cluster.md) for the runtime credential, and
[operations](operations.md) for validation and diagnosis.
