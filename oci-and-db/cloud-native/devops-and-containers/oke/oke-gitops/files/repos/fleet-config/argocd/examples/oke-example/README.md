# Example cluster object

Copy `profiles/example` to the desired profile name, then copy this directory
to `clusters/<registered-cluster-name>`. Rename the cluster directory, set the
same value in `cluster.yaml` and every descriptor's `cluster` field, update all
profile paths, then label the runtime Argo CD cluster Secret:

```text
fleet.oke.oracle.com/cluster=<registered-cluster-name>
```

`cluster.yaml` demonstrates the singleton cluster-resource Kustomization. The
active bindings demonstrate the other three delivery forms, an umbrella
profile, advanced composition, a shared namespace, and one cluster-specific
configuration through a dedicated profile. Remove bindings the cluster does
not need. The standalone
`reference-app/` demonstrates the logical-parent convention: infrastructure and
the active dev environment share one folder and reconcile in sync-wave order.
Terraform writes the generated OCI repository URLs into its child Applications
when the seed is created. `profiles/example/applications/queue-worker` operator composition is deliberately not bound because
it is an alternative to the example's plain KEDA installation.

`reference-helm-app/` applies the same model to a developer-owned umbrella
chart. It activates frontend/dev and api/dev, with namespace infrastructure in
the selected profile and one generated Application per enabled subchart.
