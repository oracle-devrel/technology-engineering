# Naming and labels

- Registered cluster name: stable, DNS-safe, and recognizable; for example
  `payments-eu-milan-1-01`.
- Cluster identity label:
  `fleet.oke.oracle.com/cluster=<registered-cluster-name>`.
- Descriptor `application`: stable application identity; the generated name is
  `<application>-<cluster>`.
- Logical parent: `<application>-<cluster>`; children use
  `<application>-infrastructure-<cluster>` and
  `<application>-<environment>-<cluster>`.
- Tool namespace: normally the tool name, such as `keda`.
- Shared application boundary: use an intentional namespace such as
  `monitoring` when several components belong together.

Profile directory names describe one cohesive reusable configuration set, such
as `standard`, `restricted`, or `test`. A profile dedicated to one cluster may
use a clear name such as `oke-2-specific`. Application directories inside the
profile describe individual capabilities such as `monitoring` or `keda`.
Profiles must remain composable Git configuration, not an infrastructure
cluster type. Tools have no environment dimension; environment-aware applications use
exactly `dev`, `staging`, or `production`.
