# OKE policies

The stack creates IAM policies only when **Enable policies** is selected. Enable
**Policy dry-run** to review the generated statements without creating policy
resources.

## Policies managed by the stack

The stack generates only policies that can be derived from its configuration:

| Feature | When generated | Access granted |
| --- | --- | --- |
| Cross-compartment VCN-native networking | VCN-native CNI is selected and the OKE and network compartments differ | Worker instances in the OKE compartment, and private IPs and NSGs in the network compartment |
| Cluster encryption | A customer-managed cluster encryption key is selected | Use of the selected KMS key by an OKE cluster principal |
| Cluster Autoscaler | Cluster Autoscaler policies are selected for an enhanced cluster | Management of node pools and their required compute and network resources |
| Karpenter | Karpenter policies are selected for an enhanced cluster | Management of instances, volumes, volume attachments, and network resources; tenancy-level compartment inspection; and node registration for the target cluster |

Karpenter permissions for capacity reservations, compute clusters, cluster
placement groups, and defined tags are generated only when their corresponding
options are selected.

The `policy_statements` output provides one flat list. Use
`policy_statements_by_feature` to see why each statement was generated and
`policy_resources` to see which IAM policies the stack created.

In Karpenter dry-run output, replace `<karpenter-dynamic-group-ocid>` with the
OCID of a dynamic resource group that uses the displayed matching rule.

## Additional OKE policies

Cluster creation does not reveal every capability that applications will use later.
Create additional policies when workloads or node pools use any of these features:

- IPv6 with the VCN-native CNI
- Customer-managed keys for worker boot volumes, persistent block volumes, or
  file systems
- Cloud Controller Manager updates to load balancer or network load balancer NSGs
- Reserved public IP addresses for load balancers or network load balancers
- Load balancers, network load balancers, or attached NSGs in another compartment
- Statically provisioned volume snapshots in another compartment
- Dynamic file-system provisioning with the FSS CSI driver
- Defined tag namespaces in another compartment
- Worker-node replacement or reboot with a custom image
- OCI Certificates attached to load balancers
- Zero Trust Packet Routing security attributes
- Managed node pools using capacity reservations, host groups, or compute clusters

These policies are not created automatically because they depend on Kubernetes
annotations, storage classes, node-pool settings, or target resources that are not
inputs to this stack. Review the complete
[OKE policy collection](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/cloud-native/devops-and-containers/oke/oke-policies/policies.md)
and confirm current syntax in the linked OCI documentation before enabling a feature.
