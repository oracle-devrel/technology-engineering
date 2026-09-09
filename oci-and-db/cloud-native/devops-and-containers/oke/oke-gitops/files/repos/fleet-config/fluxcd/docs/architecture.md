# Architecture

The Resource Manager stack installs Flux Operator only on its selected OKE
cluster through the private Kubernetes API endpoint. That primary cluster is
bootstrapped from `cluster-config`. Each additional member has a manually
created private OCI DevOps OKE environment and dedicated installation
pipeline, then uses a copied and completed manifest from
`fleet-config/bootstrap/member-template.yml`.

Each member then pulls the same repositories independently:

```text
Resource Manager pipeline -> install Flux Operator on oke-1
Manual oke-2 pipeline      -> install Flux Operator on oke-2

Flux on oke-1 -> fleet-config/clusters/oke-1 -> selected profiles
Flux on oke-2 -> fleet-config/clusters/oke-2 -> selected profiles
                         |
                         +-> apps-config component catalog
```

An unavailable cluster affects only its own reconciliation. Clusters do not
need network routes to each other's Kubernetes APIs and no member stores a
kubeconfig for another member.
