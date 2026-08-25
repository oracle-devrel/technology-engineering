# Template catalog

Copy templates from `assets/`, rename files without `.tpl`, and replace every
`__TOKEN__`. Never copy over an existing application directory without first
reviewing its contents.

| Pattern | Asset path | Destination |
|---|---|---|
| Local namespaced Kustomize | `assets/platform-kustomize/` | `cluster-config/platform/applications/<app>/` |
| Local external Helm chart | `assets/platform-helm-repository/` | `cluster-config/platform/applications/<app>/` |
| Developer Kustomize component | `assets/application-kustomize/` | `apps-config/applications/<app>/kustomize/components/<component>/` |
| Developer umbrella Helm app | `assets/application-helm/` | `apps-config/applications/<app>/helm/` |
| Local logical application placement | `assets/logical-application-local/` | `cluster-config/platform/applications/<app>/` |
| Fleet cluster object | `assets/fleet-cluster/cluster.yaml.tpl` | `fleet-config/clusters/<cluster>/cluster.yaml` |
| Fleet namespaced Kustomize binding | `assets/fleet-kustomize/kustomize.application.yaml.tpl` | `fleet-config/clusters/<cluster>/applications/<binding>/` |

The umbrella Helm asset provides one complete component skeleton. Rename the
`charts/component` and `values/environment/component.yml` paths, duplicate the
environment values for all three environments, and add dependencies/subcharts
for additional components. The local logical-application asset contains the
Kustomize component ApplicationSet variant. For umbrella Helm, adapt the
complete `reference-helm-app/components.application-set.yml` already present in
the generated repository so the two ordered values paths remain exact.

After copying, search the new directory for `__` and fail the change if any
template token remains.
