# Recommended OKE + OCI Karpenter Reference Architecture

## Goal

Use a **small fixed OKE node pool** to guarantee cluster survivability and host bootstrap-critical services, while using **OCI Karpenter-managed NodePools** for elastic application capacity.

## Recommended architecture

Use this default pattern for production OKE clusters:

- **Fixed baseline OKE node pool**
  - Always present
  - Non-preemptible
  - Small but highly available
  - Hosts bootstrap-critical components

- **General OCI Karpenter NodePool**
  - Broad shape choices
  - Elastic
  - Primary destination for application workloads

- **Optional specialized OCI Karpenter NodePools**
  - Preemptible or lower-cost workloads
  - GPU / ARM / memory-heavy workloads
  - Isolation only when clearly needed

## Placement model

The core placement rule is:

- **Fixed pool = survival**
- **Karpenter pools = elasticity**

Recommended workload placement:

- **Karpenter/KPO:** fixed pool only
- **CoreDNS:** simple recommended pattern below
- **Other add-ons:** case by case
- **Applications:** primarily Karpenter-managed pools

## CoreDNS simple recommended pattern

This is the **simple recommended pattern** for customers who want:

- a stable bias toward the fixed pool
- overflow to app/Karpenter pools when needed
- replicas spread across ADs, FDs, and nodes
- a practical setup without trying to hard-guarantee a minimum number of replicas on the fixed pool

### Design principles

Use:

- **toleration** so CoreDNS can run on the fixed pool
- **preferred node affinity** to bias CoreDNS toward the fixed pool
- **preferred pod anti-affinity** to keep replicas off the same node
- **preferred pod anti-affinity** to spread replicas across availability and fault domains

This gives a strong tendency toward keeping CoreDNS on the fixed pool when capacity is available, while still allowing overflow to the app/Karpenter pools.

### Fixed pool requirement

Taint the fixed pool for system use, for example:

```yaml
CriticalAddonsOnly=true:NoSchedule
```

Also label the fixed pool nodes so node affinity can prefer them:

```yaml
node-role/system: "true"
```

### Example CoreDNS configuration

```yaml
tolerations:
- key: "CriticalAddonsOnly"
  operator: "Exists"

affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        preference:
          matchExpressions:
            - key: node-role/system
              operator: In
              values:
                - "true"
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              k8s-app: kube-dns
          topologyKey: kubernetes.io/hostname
      - weight: 80
        podAffinityTerm:
          labelSelector:
            matchLabels:
              k8s-app: kube-dns
          topologyKey: topology.kubernetes.io/zone
      - weight: 50
        podAffinityTerm:
          labelSelector:
            matchLabels:
              k8s-app: kube-dns
          topologyKey: oci.oraclecloud.com/fault-domain

```

### How this behaves

This pattern gives the following behavior:

- CoreDNS is allowed onto the tainted fixed pool because of the toleration
- CoreDNS prefers the fixed pool because of node affinity
- CoreDNS can overflow to app/Karpenter nodes because the affinity is soft, not hard
- CoreDNS replicas tend not to stack on the same node because of hostname anti-affinity
- CoreDNS also tends to spread across availability and fault domains because of AD/FD anti-affinity


### Practical notes

- This is a **simple recommended pattern**, not a hard guarantee of a minimum fixed-pool baseline
- Do **not** use a `nodeSelector` to force CoreDNS only onto the fixed pool, or overflow will not be possible
- Use `minReplica` and `nodesPerReplica` based on cluster size and DNS load, but keep the scheduling model above as the default placement guidance
- The AD/FD anti-affinity only helps when the eligible nodes actually span multiple AD/FD

## Sample OCIClass for Karpenter-OCI

The following example shows a simple baseline configuration for a general-purpose Karpenter-OCI worker pool class for OCI_VCN_NATIVE CNI.

To facilitate subnet and NSG selection, the infrastructure script automatically add the freeform tags: `karpenter-oci/role: pod` and `karpenter-oci/role: worker` to the networking objects for pods and workers.

### Sample `OCIClass`

```yaml
apiVersion: oci.oraclecloud.com/v1beta1
kind: OCINodeClass
metadata:
  name: oci-nodeclass
spec:
  shapeConfigs:
    - ocpus: 2
      memoryInGbs: 8
    - ocpus: 4
      memoryInGbs: 16
  volumeConfig:
    bootVolumeConfig:
      sizeInGBs: 100
      imageConfig:
        imageType: OKEImage
        imageFilter:
          osFilter: "Oracle Linux"
          osVersionFilter: "8"
  networkConfig:
    primaryVnicConfig:
      subnetConfig:
        subnetFilter:
          compartmentId: ""   # Required if network compartment is different from cluster compartment
          freeformTags:
            karpenter-oci/role: worker
      networkSecurityGroupConfigs:
        - networkSecurityGroupFilter:
            compartmentId: ""   # Required if network compartment is different from cluster compartment
            freeformTags:
              karpenter-oci/role: worker
    secondaryVnicConfigs:
      - subnetConfig:
          subnetFilter:
            compartmentId: ""   # Required if network compartment is different from cluster compartment
            freeformTags:
              karpenter-oci/role: pod
        networkSecurityGroupConfigs:
          - networkSecurityGroupFilter:
              compartmentId: ""   # Required if network compartment is different from cluster compartment
              freeformTags:
                karpenter-oci/role: pod
        ipCount: 128
```

### Notes on Karpenter

- Use a broad worker `NodePool` for general workloads, and create additional specialized pools only when there is a real need.
- Keep the fixed baseline OKE node pool separate from Karpenter-managed worker capacity.
- Start with on-demand capacity for predictable production behavior, then introduce other capacity types only for workloads that can tolerate it.
- Keep the `requirements` broad enough for Karpenter to make efficient placement decisions.

