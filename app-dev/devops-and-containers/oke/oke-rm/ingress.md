# Ingress guide and best practices in OKE

Configuring an Ingress is one of the first steps any engineer needs to understand when dealing with Kubernetes.

A full list of all the annotations both for Load Balancers and Network Load Balancers can be found [here](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingloadbalancer_topic-Summaryofannotations.htm).

There are some best practices and common tasks to perform, and as an example we will use Traefik OSS Helm chart, but you are free to use whatever ingress you like.

## Prerequisites: policies

Some policies are needed for the OKE cluster to interact with NSGs during this guide, so better have everything already in place!
```
ALLOW any-user to manage network-security-groups in compartment <network-compartment-name> where request.principal.type = 'cluster'
ALLOW any-user to manage vcns in compartment <network-compartment-name> where request.principal.type = 'cluster'
ALLOW any-user to manage virtual-network-family in compartment <network-compartment-name> where request.principal.type = 'cluster'
```
Note that these policies are necessary even if the network compartment and the cluster compartment are the same!

These policies can also be further restricted by specifying the OKE cluster id.

## Configuring the Service of type LoadBalancer

This OKE stack has created a NSG for all the Load Balancers called **oke-lb-nsg**. This is part of the infrastructure and should not be modified, as it contains the
security rules to connect the LB to the worker nodes.
  
To adopt a GitOps approach, the LB created by OKE is configured through annotations. The list of all valid annotations can be found [here](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingloadbalancer_topic-Summaryofannotations.htm).
  
As a starting point, I would suggest these annotations, to be configured directly in the Helm chart:
```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "None"
```
These annotations will create a flexible public Load Balancer and attach the right NSG. Note that we have put the security-rule management-mode to None, and we will come back to that one later.



### Private Load Balancer

If you have chosen to create the Load Balancer in a private subnet, you will need an additional annotation, or the creation will fail:
```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "None"
    service.beta.kubernetes.io/oci-load-balancer-internal: "true"	
```
**service.beta.kubernetes.io/oci-load-balancer-internal** is required to create a LB in a private subnet.

## Specifying externalTrafficPolicy to Local

By default, many Ingress controllers are exposed through a Service with externalTrafficPolicy set to Cluster by default.

This means that the Load Balancer may potentially send traffic to a node where no Ingress controller pod is scheduled. To avoid this, it is a best practice to set externalTrafficPolicy to Local:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "None"
  spec:
    externalTrafficPolicy: "Local"
```

NOTE: as a side effect, you will see in the OCI Load Balancer that not all the backend nodes report a successful health check. This is normal, as only nodes with an Ingress pod scheduled will actually receive traffic and respond to the health check.

## Assigning a Public Reserved IP to the Load Balancer

If you want to use a public reserved IP for the Load Balancer, you need to specify it in the Service spec:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "None"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"    # Your public reserved IP
```
NOTE: If the public reserved IP is in a different compartment that the OKE cluster, you will need an additional policy:
```text
ALLOW any-user to read public-ips in tenancy where request.principal.type = 'cluster'
ALLOW any-user to manage floating-ips in tenancy where request.principal.type = 'cluster'
```

## Configuring LB ingress access from OKE

The main idea here is to have a separate NSG managed by OKE in which the ingress security rules are defined.
We can accomplish this by specifying the NSG mode in **security-rule-management-mode** and by using **loadBalancerSourceRanges** in the Service specification:
```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```
OKE will create a **frontend** NSG and attach it directly to the Load Balancer. It will allow all traffic coming from the CIDR blocks specified in **loadBalancerSourceRanges** on the ports exposed by the Service.
You are now capable of controlling the Ingress CIDR block allow rules declaratively!

## Redirect HTTP traffic to HTTPS

Often, the Service used by Ingress controllers exposes both port 80 and 443. It is then common to configure redirection of HTTP traffic to HTTPS.
While this feature is something that is supported in the OCI Load Balancer, there is no annotation to configure it from OKE.

It is often preferable and easier to implement it at the Ingress level.
For example, for Traefik you just need to specify this in the Helm chart values:

```yaml
ports:
  web:
    redirections:
      to: websecure
      scheme: https
  websecure:
    asDefault: true
```

## Ensure High Availability for ingress pods

Ensuring that ingress pods are replicated and spread across different nodes is critical to ensure high availability. This is because ingress pods will handle all the ingress traffic
to the cluster.

Be sure to have at least 3 ingress pods and to configure a **HorizontalPodAutoscaler** to dynamically scale replicas.

To ensure distribution of ingress pods across AD/FD and nodes, it's better to define **TopologySpreadConstrain** and **pod anti-affinity**:
```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: "topology.kubernetes.io/zone"        # Distribute pods across ADs, put "oci.oraclecloud.com/fault-domain" if you have a region with only 1 AD, so that pods are distributed across FDs
    whenUnsatisfiable: "ScheduleAnyway"       # Soft rule        
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: '{{ template "traefik.name" . }}'

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:      # Soft rule
      - podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: '{{ template "traefik.name" . }}'
          topologyKey: "kubernetes.io/hostname"         # Try to distribute pods in different nodes. Better keep this rule as soft, otherwise max number of pods == number of current nodes
        weight: 100
```

## Use proxy protocol v2 to keep caller IP address

Often, the security team will require the Kubernetes administrator to keep the source IP address of the caller in the X-Forwarded-For header, so that it is logged in the
Ingress Controller access logs.

The cloud native environment is also full of reverse proxy, and so it is difficult to keep the original source IP. Thankfully, Proxy Protocol solves this, but it has to
be enabled both at the Load Balancer level and at the Ingress pod level:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

Although we have enabled Proxy Protocol v2 at the Load Balancer level, the same must be done for the Ingress.

For Traefik, proxy protocol is enabled by default, but Traefik implements a mechanism that requires the administrator to trust the IP ranges of the incoming requests, that is,
no X-Forwarded-For header will be populated unless the sender proxy IP is not explicitly trusted.
Let's then trust all the IP addresses of the VCN where the cluster is installed:
```yaml
ports:
  web:
    redirections:
      to: websecure
      scheme: https
  websecure:
    asDefault: true
    forwardedHeaders:
      trustedIPs:
        - "10.0.0.0/16"
    proxyProtocol:
      trustedIPs:
        - "10.0.0.0/16"
```
Where 10.0.0.0/16 is the CIDR block of the VCN where the OKE cluster has been provisioned and where the Load Balancer is located.

## Select only the necessary worker nodes to be included in the Load Balancer

By default, OKE will include all the worker nodes in a cluster as backend set of the Load Balancer. If nodes increase a lot, having many nodes in the backend set
may slow down the Load Balancer.
We can restrict the nodes to be included in the backend set by using labels and the annotation **oci.oraclecloud.com/node-label-selector**:
```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```
See the [documentation](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer_topic-Selecting_worker_nodes_to_include_in_backend_sets) for more examples.

## Change the default Load Balancer policy if needed

The default Load Balancer policy is ROUND_ROBIN. If your applications require long connection times, better change the policy to LEAST_CONNECTIONS:
```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
    oci.oraclecloud.com/loadbalancer-policy: "LEAST_CONNECTIONS"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

## Change the default Connection Idle timeout

By default, the Load Balancer TCP listener will keep a session alive even if there are no request/response interactions for 5 minutes.
Depending on your requirements, you have the possibility to reduce this idle time. Here, I am setting it to last 60 seconds:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
    service.beta.kubernetes.io/oci-load-balancer-connection-idle-timeout: "60"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

## Change the default health check parameters

By default, health check on nodes will be performed by the Load Balancer every 10 seconds. Although Kubernetes will still forward traffic to different pods on different nodes in case of disruption,
it is safer to set it to a lower level:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
    service.beta.kubernetes.io/oci-load-balancer-connection-idle-timeout: "60"
    service.beta.kubernetes.io/oci-load-balancer-health-check-interval: "3000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-timeout: "2000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-retries: "3"
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

## Restrict HTTP header size

As a security measure, it is better to restrict the HTTP header size. Here, I am restricting it to 16 KB:

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
    service.beta.kubernetes.io/oci-load-balancer-connection-idle-timeout: "60"
    service.beta.kubernetes.io/oci-load-balancer-health-check-interval: "3000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-timeout: "2000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-retries: "3"
    oci.oraclecloud.com/oci-load-balancer-rule-sets: |
      {
        "header_size": {
          "items": [
            {
              "action": "HTTP_HEADER",
              "httpLargeHeaderSizeInKB": 16
            }
          ]
        }
      }
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

## Provision the Load Balancer in a different subnet

You can specify a different subnet where to provision the OCI Load Balancer. This is very useful for hub/spoke architectures.

```yaml
service:
  type: LoadBalancer
  annotations:
    oci.oraclecloud.com/load-balancer-type: "lb"
    service.beta.kubernetes.io/oci-load-balancer-shape: "flexible"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-min: "10"
    service.beta.kubernetes.io/oci-load-balancer-shape-flex-max: "100"
    oci.oraclecloud.com/oci-network-security-groups: "ocid1.networksecuritygroup.oc1...." # It is the oke-lb-nsg OCID
    oci.oraclecloud.com/security-rule-management-mode: "NSG"
    service.beta.kubernetes.io/oci-load-balancer-backend-protocol: "TCP"  # Proxy Protocol only works with a TCP listener
    service.beta.kubernetes.io/oci-load-balancer-connection-proxy-protocol-version: "2" # Enable Proxy Protocol v2
    oci.oraclecloud.com/node-label-selector: "env=test"
    service.beta.kubernetes.io/oci-load-balancer-connection-idle-timeout: "60"
    service.beta.kubernetes.io/oci-load-balancer-health-check-interval: "3000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-timeout: "2000"
    service.beta.kubernetes.io/oci-load-balancer-health-check-retries: "3"
    oci.oraclecloud.com/oci-load-balancer-rule-sets: |
      {
        "header_size": {
          "items": [
            {
              "action": "HTTP_HEADER",
              "httpLargeHeaderSizeInKB": 16
            }
          ]
        }
      }
    service.beta.kubernetes.io/oci-load-balancer-subnet1: "ocid1.subnet.oc1...."
  spec:
    externalTrafficPolicy: "Local"
    loadBalancerIP: "121.127.6.12"
    loadBalancerSourceRanges:
      - "10.1.0.0/16"
```

## Additional best practices

If you expect to have multiple environments in the same OKE cluster, it's better to create multiple IngressClasses for every environment, each with its own ingress controller and Load Balancer.

To better manage costs, do not forget to add cost-tracking tags to the Load Balancer! See [here](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengtaggingclusterresources_tagging-oke-resources_load-balancer-tags.htm#contengtaggingclusterresources_tagging_oke_resources_load_balancer_tags) for more information.

NOTE: Remember that to apply tags additional policies may be needed, see [here](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengtaggingclusterresources_iam-tag-namespace-policy.htm#contengtaggingclusterresources_iam-tag-namespace-policy).

This guide shows how to configure an ingress controller with a Load Balancer configured with TLS passthrough. SSL/TLS termination will happen at the Ingress level.

Usually, this is preferable as the Ingress controller is directly integrated with cert-manager and is capable to handle multiple certificates.

If you only have one certificate, you can also terminate TLS at the Load Balancer level and there are some additional [annotations](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengcreatingloadbalancers-subtopic.htm#creatinglbhttps).

## Enable API Gateway features (requires an enterprise license)

Generally speaking, all the major Ingress controllers (Nginx, Traefik, Kong) are open source, but many useful features require an enterprise license.

If you are serious about developing in Kubernetes, it is suggested to have one to better manage and secure APIs.

For example, with an enterprise license it is possible to integrate OIDC with the Ingress, so that developers do not need to deal with security in their applications.
It is also possible to establish some rate limiting for APIs and some controllers even offer the possibility to create developer portals!

One of such example for OKE is Traefik, as it is nicely [integrated with OCI](https://traefik.io/solutions/oracle-and-traefik/).