# Install Karpenter Provider for OCI on this OKE cluster

This guide adds Karpenter-managed application capacity to a cluster created by
the two Resource Manager stacks in this repository. The recommended design is:

- a small, fixed OKE node pool for Karpenter and bootstrap-critical services;
- a general Karpenter `NodePool` for elastic application capacity; and
- additional specialized `NodePool` resources only when workloads require them.

The fixed pool keeps Karpenter available when no Karpenter-managed nodes exist.
Karpenter must never depend on nodes that it manages itself.

For the complete KPO API and the latest compatibility information, see
[Using Karpenter Provider for OCI](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/conteng-kpo.htm)
and the
[Karpenter Provider for OCI releases](https://github.com/oracle/karpenter-provider-oci/releases).

## 1. Prepare the Resource Manager stacks

Apply the infrastructure stack before the OKE stack. Karpenter requires an
enhanced OKE cluster when using the workload identity policies created by this
project.

In the OKE stack, configure:

- **Cluster type:** Enhanced cluster
- **Enable policies:** selected
- **Create Karpenter policies:** selected
- **Karpenter namespace:** `karpenter`
- **Karpenter service account:** `karpenter`
- **Policy dry-run:** cleared for the final apply
- **Karpenter identity domain** and a tenancy-unique dynamic group name

Enable optional Karpenter policies only for the corresponding features used in
an `OCINodeClass`. The stack creates the basic compute, networking, storage,
compartment-inspection, and node-registration permissions.
See the [OKE policy guide](oke/POLICIES.md) for the exact
statements and optional-policy mapping.

### Create fixed worker capacity

In `oke/oke.tf`, enable `np-system` before applying the OKE stack:

```hcl
np-system = {
  # Keep the existing settings in the sample.
  size   = 2
  create = true
}
```

The example above shows only the values to change; retain the label, cloud-init
configuration, and other settings already present in `np-system`.

KPO's Helm chart runs two controller replicas with hostname anti-affinity. Use
at least two fixed nodes so both replicas can run. For production, distribute
fixed capacity across the availability or fault domains supported by the
region, and size it for KPO, CoreDNS, and other system workloads.

The system nodes use:

```yaml
node-role/system: "true"
```

and the following taint:

```text
CriticalAddonsOnly=true:NoSchedule
```

Optionally set `override_coredns = true` in
`oke/addons.tf` before the OKE apply to enable the CoreDNS
placement configuration described later in this guide.

Do not install KPO until the OKE apply has completed and both fixed nodes are
`Ready`:

```shell
kubectl get nodes -l node-role/system=true
```

## 2. Check KPO and networking prerequisites

Choose a KPO version compatible with the cluster's Kubernetes version. At the
time this guide was updated, the minimum versions were:

| Kubernetes version | Minimum KPO version |
| --- | --- |
| 1.31-1.34 | 1.0.0 |
| 1.35 | 1.1.0 |
| 1.36 | 1.3.0 |

Check the official compatibility table before every installation or upgrade.
The commands below use KPO `1.3.0`; Helm chart versions do not include the
leading `v` used by GitHub release tags.

This stack uses OCI VCN-Native Pod Networking. Confirm that the CNI image is
version 3.2.0 or newer:

```shell
kubectl --namespace kube-system get daemonset vcn-native-ip-cni \
  --output jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

KPO requires version 3.0.0 or newer, but version 3.2.0 or newer is recommended
and is required for more than 16 IP addresses on a secondary VNIC.

### Select the network resources

Record these values after the infrastructure stack has been applied:

- `worker_subnet_id`;
- `worker_nsg_id`;
- `pod_subnet_id`; and
- `pod_nsg_id`.

Use the infrastructure stack outputs when it creates those resources. In
existing-VCN mode, use the external subnet OCIDs selected for the OKE stack and
the NSG OCIDs created by the infrastructure stack.

The stack also adds `karpenter-oci/role` freeform tags to the network resources
it creates. Their values include the stack's persistent eight-character UUID
suffix and are
available in the `karpenter_worker_role_tag_value` and
`karpenter_pod_role_tag_value` outputs. This prevents selectors from matching
resources created by another copy of the stack. Exact OCIDs remain the default
in this guide because they also work for externally managed subnets, which this
stack cannot tag.

## 3. Install KPO

Add the official Helm repository and inspect the selected chart:

```shell
export KPO_VERSION=1.3.0

helm repo add karpenter-provider-oci \
  https://oracle.github.io/karpenter-provider-oci/charts
helm repo update karpenter-provider-oci
helm show values karpenter-provider-oci/karpenter \
  --version "${KPO_VERSION}"
```

Obtain the private Kubernetes API endpoint from the cluster details in OCI, or
with the OCI CLI:

```shell
oci ce cluster get \
  --cluster-id <cluster-ocid> \
  --query 'data.endpoints."private-endpoint"' \
  --raw-output | sed 's/:6443$//'
```

The Helm value requires the private endpoint IP without the `:6443` port.

Create `karpenter-values.yaml`:

```yaml
serviceAccount:
  name: karpenter

nodeSelector:
  kubernetes.io/os: linux
  node-role/system: "true"

tolerations:
  - key: CriticalAddonsOnly
    operator: Exists

settings:
  clusterCompartmentId: <oke-compartment-ocid>
  vcnCompartmentId: <network-compartment-ocid>
  apiserverEndpoint: <private-api-endpoint-ip>
  ociVcnIpNative: true
  ipFamilies:
    - IPv4
```

The namespace and service account must match the values used when the OKE stack
created the Karpenter workload identity policies.

Install and verify KPO:

```shell
helm upgrade --install karpenter karpenter-provider-oci/karpenter \
  --version "${KPO_VERSION}" \
  --namespace karpenter \
  --create-namespace \
  --values karpenter-values.yaml

kubectl --namespace karpenter rollout status deployment/karpenter \
  --timeout=180s
kubectl --namespace karpenter get pods
```

## 4. Create an OCINodeClass

Save the following as `oci-nodeclass.yaml`:

```yaml
apiVersion: oci.oraclecloud.com/v1beta1
kind: OCINodeClass
metadata:
  name: general
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
          osVersionFilter: "9"
  networkConfig:
    primaryVnicConfig:
      subnetConfig:
        subnetId: <worker-subnet-ocid>
      networkSecurityGroupConfigs:
        - networkSecurityGroupId: <worker-nsg-ocid>
    secondaryVnicConfigs:
      - subnetConfig:
          subnetId: <pod-subnet-ocid>
        networkSecurityGroupConfigs:
          - networkSecurityGroupId: <pod-nsg-ocid>
        ipCount: 32
```

If you intentionally replace an OCID with a selector, it must resolve to exactly
one resource. Do not add `compartmentId: ""`: omit the field to use
`settings.vcnCompartmentId`, or specify a real compartment OCID.

`ipCount: 32` works with VCN-Native CNI 3.2.0 or newer and this stack's default
single-CIDR IPv4 pod subnet. Use at most `16` with CNI versions older than 3.2.0.
Values above `32` require multiple pod-subnet CIDR blocks; they must be powers of
two, and the aggregate across all secondary VNICs cannot exceed `256`.

Apply the resource and wait for KPO to resolve its image and network selectors:

```shell
kubectl apply -f oci-nodeclass.yaml
kubectl wait --for=condition=Ready ocinodeclass/general --timeout=180s
kubectl describe ocinodeclass general
```

Do not continue until the `OCINodeClass` reports `Ready=True`.

## 5. Create a general NodePool

Save the following as `karpenter-nodepool.yaml`:

```yaml
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: general
spec:
  template:
    metadata:
      labels:
        workload-tier: karpenter
    spec:
      nodeClassRef:
        group: oci.oraclecloud.com
        kind: OCINodeClass
        name: general
      requirements:
        - key: karpenter.sh/capacity-type
          operator: In
          values:
            - on-demand
        - key: oci.oraclecloud.com/instance-shape
          operator: In
          values:
            - VM.Standard.E5.Flex
      expireAfter: Never
      terminationGracePeriod: 120m
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 10m
    budgets:
      - nodes: 5%
  limits:
    cpu: 64
    memory: 256Gi
```

Start with on-demand capacity. Add Spot, GPU, Arm, memory-heavy, capacity
reservation, or placement-specific pools only when workloads need them and the
required IAM policies are enabled.

Apply and validate the pool:

```shell
kubectl apply -f karpenter-nodepool.yaml
kubectl get nodepool general
kubectl describe nodepool general
```

## 6. Test node provisioning

This deployment can schedule only on the Karpenter pool because it selects the
label defined in the `NodePool`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inflate
spec:
  replicas: 1
  selector:
    matchLabels:
      app: inflate
  template:
    metadata:
      labels:
        app: inflate
    spec:
      nodeSelector:
        workload-tier: karpenter
      containers:
        - name: pause
          image: registry.k8s.io/pause:3.10
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
```

Save it as `inflate.yaml`, then run:

```shell
kubectl apply -f inflate.yaml
kubectl get nodeclaims,nodes,pods -o wide
kubectl wait --for=condition=Available deployment/inflate --timeout=15m
```

If provisioning fails, inspect:

```shell
kubectl describe ocinodeclass general
kubectl describe nodepool general
kubectl get nodeclaims
kubectl --namespace karpenter logs deployment/karpenter --all-containers
```

Typical causes are unmatched network selectors, incorrect workload identity
namespace or service account values, an incompatible KPO/CNI version, OCI
service limits, or unavailable shape capacity.

## 7. CoreDNS placement

When `override_coredns = true`, the stack configures CoreDNS to:

- tolerate the fixed pool's `CriticalAddonsOnly` taint;
- prefer nodes labeled `node-role/system=true`;
- overflow to other eligible nodes when fixed capacity is unavailable; and
- prefer spreading replicas across hosts, availability domains, and fault
  domains.

The preference is intentional. Do not use a `nodeSelector` that forces CoreDNS
onto the fixed pool, because that would prevent overflow. Domain spreading helps
only when eligible nodes actually span those domains.

Choose `minReplica` and `nodesPerReplica` values in `oke/addons.tf`
according to cluster size and DNS load.

## 8. Remove Karpenter safely

Delete application workloads and Karpenter `NodePool` resources while the KPO
controller is still running. This allows KPO to terminate the instances it
created:

```shell
kubectl delete -f inflate.yaml
kubectl delete -f karpenter-nodepool.yaml
kubectl wait --for=delete nodeclaim \
  --selector karpenter.sh/nodepool=general \
  --timeout=15m
```

Wait until no Karpenter `NodeClaim` resources remain, then remove the node class
and controller:

```shell
kubectl delete -f oci-nodeclass.yaml
helm uninstall karpenter --namespace karpenter
```

Complete these steps before deleting the OKE cluster to avoid leaving
Karpenter-created compute, VNIC, or boot-volume resources behind.
