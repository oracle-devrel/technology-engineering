# Standalone operator composition

This profile demonstrates one Application owning the KEDA Helm release, a
Deployment, and its dependent `ScaledObject`. It is an alternative to the
plain `keda` profile, not an add-on to it: do not bind both profiles to the
same cluster because KEDA installs cluster-scoped resources.

Create a `helm-repository.application.yaml` binding that points to this
profile's `resources/` and `values/` directories. The `oke-example` cluster
does not activate it, so copying that example remains safe.
