# Platform applications

Create one directory per application. The directory name should normally match
the application name and destination namespace. "Infrastructure" and "custom"
describe ownership, not two different Git directory types.

Choose exactly one descriptor:

- `kustomize.application.yaml`
- `helm-repository.application.yaml`
- `helm-git.application.yaml`

Environment-aware applications instead use `application.yaml` and
keep all deployment definitions together:

```text
reference-app/
  application.yaml
  kustomization.yml
  infrastructure/
    application.yml              # sync-wave: -10
    resources/
  components.application-set.yml # sync-wave: 0
```

The generated parent `Application/reference-app` waits for its infrastructure
child to become Healthy, then creates
`ApplicationSet/reference-app-components`. Its explicit list generator creates
one Application per selected component/environment pair. Components have no
ordering dependency. Add or remove list elements to change placement;
production overlays exist in the catalog but are intentionally inactive.

`reference-helm-app/` follows the same parent and sync-wave model for a
developer-owned umbrella Helm chart. Its ApplicationSet supplies two ordered
files from `apps-config`: global `helm/values.yaml`, then the selected
`helm/values/<environment>/<component>.yml`. It generates one release for each
selected component/environment pair. The local example activates frontend and
API in dev and staging; production remains renderable but inactive.

Terraform injects the real `cluster-config` and `apps-config` repository URLs
into the seeded reference child Applications. To add another application, copy
`reference-app/`, rename every resource and path, keep the infrastructure
source in `cluster-config`, point the component ApplicationSet to `apps-config`,
and list only the required component/environment combinations.

Argo CD ApplicationSets discover these descriptors and generate one Application
per directory. Helm applications keep one or more files under `values/`; the
descriptor's ordered `helm.valueFiles` list determines precedence. They also
include a `resources/` Kustomize source, even when it is initially empty. This
makes it possible to add related manifests later without changing the
Application.

`argocd/` is the bootstrap-created self-managed Argo CD application. Its
descriptor and `values/` files are administrator-owned after the first
repository seed.

`reference-app/` is the complete namespace-onboarding and workload-placement
example. Argo CD creates namespace `reference-app` through
`CreateNamespace=true`; `infrastructure/resources` owns the quota, limits, and
shared NetworkPolicies. There is deliberately no `namespace.yml`.

In the Helm reference chart, all vendored subcharts are disabled by default and
the component values file enables exactly one. Keep generated Applications
separate so an image update or rollback affects only one component/environment.

The Argo CD chart values include the `argoproj.io/Application` health
assessment required by parent/child sync waves. Keep an equivalent health
customization if the chart configuration is replaced.

See the repository root README for complete examples.
The copyable operator-readiness example is under
`examples/advanced/operator-and-custom-resources/`.
