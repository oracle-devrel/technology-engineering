# Naming

- Cluster directory: `clusters/<stable-lowercase-name>`
- Shared profile: `profiles/<capability>`
- Dedicated profile: `profiles/<cluster>-specific`
- Profile Kustomization: `fleet-<profile>`
- ResourceSet: `fleet-<application-or-capability>`
- Component reconciliation: `fleet-<application>-<component>-<environment>`

Names identify ownership and are identical across clusters because every
cluster has an independent Kubernetes API. Standard application environments
remain exactly `dev`, `staging`, and `production`.
