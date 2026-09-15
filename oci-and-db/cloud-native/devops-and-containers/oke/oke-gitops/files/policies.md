# OCI IAM policy reference

This page is the stack-author reference for DevOps resource-principal and
runtime-reader policies. Cluster administrators should follow the navigable
bootstrap guide generated into `cluster-config`:

- [Argo CD IAM guide](repos/argocd/cluster-config/docs/iam.md)
- [Flux CD IAM guide](repos/fluxcd/cluster-config/docs/iam.md)

## Dynamic group

Dynamic group needed:

```
DevOpsDynamicGroup
NOTE: CompartmentOCID == compartment id where the OCI DevOps is located

ALL {resource.type = 'devopsdeploypipeline', resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsrepository', resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsbuildpipeline',resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsconnection',resource.compartment.id = 'compartmentOCID'}

```

## DevOps resource-principal policies

Policies needed:
```
NOTE1: CompartmentOCID == compartment id where the OCI DevOps is located
NOTE2: CompartmentOCIDNetwork == compartment id where the network for the OKE cluster has been provisioned
NOTE3: CompartmentOCIDOKE == compartment id where the OKE cluster is provisioned
NOTE4: CompartmentOCIDVault == compartment containing the separate Git reader and OCIR reader credential secrets

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage repos in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage devops-family in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use ons-topics in compartment id compartmentOCID

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use subnets in compartment id compartmentOCIDNetwork
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use vnics in compartment id compartmentOCIDNetwork
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use dhcp-options in compartment id compartmentOCIDNetwork
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use network-security-groups in compartment id compartmentOCIDNetwork

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to read all-artifacts in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage compute-container-family in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage cluster in compartment id compartmentOCIDOKE
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to read secret-bundles in compartment id compartmentOCIDVault
```

## Runtime reader policies

The runtime identities are deliberately outside the DevOps dynamic group.
Place each non-human identity in a separate group and grant only its read
operation:

```text
Allow group <domain-name>/<gitops-reader-group> to read devops-repositories in compartment id compartmentOCID
Allow group <domain-name>/<ocir-reader-group> to read repos in compartment id compartmentOCID
```

The GitOps reader must not receive `manage devops-repositories`; the OCIR
reader must not receive `manage repos`. The Resource Manager user's token is
used only for initial repository seeding and is not stored in the cluster.
