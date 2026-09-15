# Cluster objects

Create one directory per registered cluster by copying
`../examples/oke-example`. The directory name, `cluster.yaml`'s `cluster`
value, and every descriptor's `cluster` value must equal the
`fleet.oke.oracle.com/cluster` label on that cluster's Argo CD Secret.

`cluster.yaml` points to exactly one cluster-resource Kustomization. It is not
an application descriptor. Each binding below `applications/` references an
application payload from a shared profile or a profile dedicated to this
cluster. Keep the cluster object declarative and put all payloads in profiles.

An environment-aware application is one binding directory containing an
`application.yaml`, its infrastructure child, and its active
component ApplicationSet. Payloads remain in the selected profile and
`apps-config`; the cluster directory owns placement and component/environment
selection.
