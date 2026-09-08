# Template catalog

Copy from `assets/`, rename files without `.tpl`, replace every `__TOKEN__`,
and adapt source names and paths. Never overwrite an existing application
directory without inspecting it.

| Pattern | Asset path | Destination |
|---|---|---|
| Namespaced Kustomize tool | `assets/platform-kustomize/` | `cluster-config/platform/applications/<app>/` |
| External Helm tool | `assets/platform-helm-repository/` | `cluster-config/platform/applications/<app>/` |
| Developer Kustomize component | `assets/application-kustomize/` | `apps-config/applications/<app>/kustomize/components/<component>/` |
| Developer umbrella Helm app | `assets/application-helm/` | `apps-config/applications/<app>/helm/` |
| Fleet profile activation | `assets/fleet-profile-activation/` | `fleet-config/clusters/<cluster>/` |

The umbrella Helm asset contains one component. Rename `charts/component` and
`values/environment/component.yml`, create all three environments, and add one
disabled dependency per component. For full ResourceSet selection, adapt the
working `reference-app` or `reference-helm-app` and retain source, dependency,
and ordered-value contracts. Search copied output for `__`; no token may remain.
