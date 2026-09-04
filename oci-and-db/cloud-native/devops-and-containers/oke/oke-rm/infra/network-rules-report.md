# OKE Network Rules Report

This report documents the ingress and egress rules defined in Terraform for OKE core components:
- Control Plane (`cp`)
- Worker Nodes (`worker`)
- Pods (`pod`)
- Load Balancers (`lb`)

Scope of sources:
- `modules/network/cp-nsg.tf`
- `modules/network/worker-nsg.tf`
- `modules/network/pod-nsg.tf`
- `modules/network/lb-nsg.tf`
- `modules/network/lb-nsg-frontend.tf`
- `modules/network/security-list.tf`

## How to read this report

- Most component rules are implemented with **NSGs** (`oci_core_network_security_group_security_rule`).
- Each subnet also has a **Security List** (`oci_core_security_list`) with baseline ICMP rules.
- In this design, the ICMP rules in Security Lists are required to support VCN connectivity through a DRG (including ICMP behavior needed for MTU/error signaling across routed paths).
- Many rules are conditional (`count = ...`) and are only created when feature flags are enabled.

## 1) Control Plane (`cp`)

### 1.1 NSG Rules (`cp_nsg`)

| Flow | Peer / CIDR | Protocol / Port(s) | Condition | Why this exists |
|---|---|---|---|---|
| Ingress + Egress pair | `worker_nsg` | TCP 12250 | Always | Worker-to-control-plane kubelet channel. |
| Ingress + Egress pair | `cp_nsg` (self) | TCP 6443 | Always | Control-plane internal API communication. |
| Ingress + Egress pair | `bastion_subnet_cidr` | TCP 6443 | `create_bastion_subnet` | Bastion access to Kubernetes API server. |
| Ingress + Egress pair | `pod_nsg` | TCP 12250 | `local.is_npn` | Explicit pod-network kubelet channel from the CP point of view; intentionally coexists with broader CP↔Pod webhook-safe policy. |
| Ingress + Egress pair | `pod_nsg` | TCP 6443 | `local.is_npn` | Explicit Kubernetes API server path to/from pods; intentionally coexists with broader CP↔Pod webhook-safe policy. |
| Ingress + Egress pair | `worker_nsg` | TCP 6443 | Always | Worker access/response path to Kubernetes API server. |
| Ingress + Egress pair | `var.cp_allowed_source_cidr` | TCP 6443 | Always | Explicit stateless API-server external path; intentionally overlaps broader stateful external egress so stateless handling is preferred for this flow. |
| Ingress + Egress pair | `worker_nsg` | TCP 10250 | Always | Kubelet health check channel between CP and workers. |
| Ingress + Egress pair | `pod_nsg` | TCP (all ports) | `local.is_npn` | Broad CP↔Pod safety-net for webhook and controller traffic variability (kept by design). |
| Ingress + Egress pair | OCI Services CIDR (`SERVICE_CIDR_BLOCK`) | TCP (all ports) | Always | Private access path to OCI regional services. |
| Egress only | `var.cp_egress_cidr` | TCP (all ports) | `local.create_cp_external_traffic_rule` | Broad stateful external outbound path; kept stateful by design to avoid insecure stateless Internet-wide return exposure. |

### 1.2 Control Plane Subnet Security List (`cp_sl`)

| Direction | Source/Destination | Protocol | Purpose |
|---|---|---|---|
| Ingress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery from non-OCI communication. |
| Egress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery responses. |
| Ingress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP within VCN. |
| Egress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP responses within VCN. |

### 1.3 Control Plane Explanation

The control plane is reachable by workers and (for VCN-native CNI) pods on Kubernetes ports (`6443`, `12250`, `10250`). Optional rules allow API access from bastion and from `cp_allowed_source_cidr`. OCI service connectivity is explicitly permitted through service CIDR rules. Subnet security list is ICMP baseline only.

### 1.4 Important design note about CP-to-Pod webhook reliability

Some CP↔Pod rules may look overlapping because both broad and explicit port rules exist.
This is intentional and should be kept.

Reason:
- From the control-plane perspective, Kubernetes API server may need to reach webhook backends running in pods (for CRD admission/conversion flows).
- Webhook/controller implementations can evolve and not always stay within a single narrow expected path.
- Keeping broad CP↔Pod allowances reduces outage risk, while explicit `12250`/`6443` rules retain clear documentation of canonical traffic.

### 1.5 Important design note about stateless vs stateful overlap

Some CP external egress rules can look overlapping, but this is intentional behavior control:
- `oke_cp_nsg_external_apiserver_egress` is stateless and specific (`TCP 6443` to `cp_allowed_source_cidr`).
- `oke_cp_nsg_external_egress` is stateful and broader (`TCP` to `cp_egress_cidr`).

In OCI networking, when a stateless and stateful rule overlap, stateless handling is preferred.  
This pattern is used intentionally in this module.

Operational rationale:
- Most rules are designed as stateless to reduce dependency on connection tracking table capacity under high concurrency.
- Stateful tracking has a practical upper bound (commonly cited around ~200,000 concurrent tracked connections), after which packet drops can occur.

Security rationale for Internet egress:
- Broad Internet egress is intentionally kept stateful where needed.
- Making that broad Internet rule stateless would require correspondingly broad ingress allowance for return traffic, which is a significant security risk.

## 2) Worker Nodes (`worker`)

### 2.1 NSG Rules (`worker_nsg`)

| Flow | Peer / CIDR | Protocol / Port(s) | Condition | Why this exists |
|---|---|---|---|---|
| Ingress + Egress pair | `cp_nsg` | ALL | Always | Broad CP↔worker webhook reliability safety-net; intentionally coexists with explicit CP worker-port rules. |
| Ingress + Egress pair | `pod_nsg` | ALL | `local.is_npn` | Pod↔worker communication in VCN-native mode. |
| Ingress + Egress pair | `worker_nsg` (self) | ALL | Always | Worker-to-worker cluster traffic. |
| Ingress + Egress pair | `oke_lb_nsg` | TCP 10256 | Always | LB health checks to node services. |
| Ingress + Egress pair | `oke_lb_nsg` | TCP 30000-32767 | Always | NodePort service traffic (TCP). |
| Ingress + Egress pair | `oke_lb_nsg` | UDP 30000-32767 | Always | NodePort service traffic (UDP). |
| Ingress + Egress pair | `bastion_subnet_cidr` | TCP 22 | `create_bastion_subnet` | SSH admin access from bastion subnet. |
| Egress only | `0.0.0.0/0` | ALL | `allow_worker_nat_egress` | Internet egress via NAT path. |
| Ingress + Egress pair | `cp_nsg` | TCP 6443 | Always | Explicit canonical Kubernetes API path; intentionally kept with CP↔worker ALL rule for reliability. |
| Ingress + Egress pair | OCI Services CIDR (`SERVICE_CIDR_BLOCK`) | TCP (all ports) | Always | Access to OCI regional services. |
| Ingress + Egress pair | `cp_nsg` | TCP 10250 | Always | Explicit kubelet health channel; intentionally kept with CP↔worker ALL rule for operability clarity. |
| Ingress + Egress pair | `cp_nsg` | TCP 12250 | Always | Explicit kubelet data channel; intentionally kept with CP↔worker ALL rule for operability clarity. |
| Ingress + Egress pair | `fss_nsg` | UDP 111 | Always | NFS portmapper (UDP) for FSS. |
| Ingress + Egress pair | `fss_nsg` | TCP 111 | Always | NFS portmapper (TCP) for FSS. |
| Ingress + Egress pair | `fss_nsg` | TCP 2048-2050 | Always | NFS traffic to FSS mounts. |
| Ingress + Egress pair | `fss_nsg` | UDP 2048 | Always | NFS UDP traffic to FSS mounts. |
| Ingress + Egress pair | `fss_nsg` | TCP 2051 | Always | Encrypted in-transit NFS traffic. |
| Ingress + Egress pair | `db[postgres]` | TCP 5432 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"postgres")` | Worker apps to Postgres when shared app NSG model is used. |
| Ingress + Egress pair | `db[cache]` | TCP 6379 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"cache")` | Worker apps to OCI Cache. |
| Ingress + Egress pair | `db[oracledb]` | TCP 1521-1522 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"oracledb")` | Worker apps to Oracle DB. |
| Ingress + Egress pair | `db[oracledb]` | TCP 27017 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"oracledb")` | Worker apps to Oracle Mongo API. |
| Ingress + Egress pair | `db[mysql]` | TCP 3306 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"mysql")` | Worker apps to MySQL classic. |
| Ingress + Egress pair | `db[mysql]` | TCP 33060 | `!is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"mysql")` | Worker apps to MySQL X protocol. |
| Ingress + Egress pair | `streaming` NSG | TCP 9092 | `!is_npn && create_streaming_nsg` | Worker apps to OCI Streaming Kafka endpoint. |
| Ingress + Egress pair | `streaming` NSG | TCP 443 | `!is_npn && create_streaming_nsg` | Worker apps to OCI Streaming REST endpoint. |

### 2.2 Worker Subnet Security List (`worker_sl`)

| Direction | Source/Destination | Protocol | Purpose |
|---|---|---|---|
| Ingress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery from non-OCI communication. |
| Egress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery responses. |
| Ingress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP within VCN. |
| Egress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP responses within VCN. |

### 2.3 Worker Explanation

Workers are the central traffic hub: they talk to CP, pods, load balancers, OCI services, and optionally FSS/DB/Streaming. The worker NSG is intentionally broad for cluster operations (especially webhook and node-to-node traffic), while optional DB/Streaming rules are feature-driven.

### 2.4 Important design note about webhook reliability

Some CP↔worker rules may appear redundant because both broad (`protocol = "all"`) and port-specific rules are defined.  
This is intentional in this Terraform design and should be kept as-is.

Reason:
- Developers can deploy CRD-related admission/conversion webhooks that are invoked by the Kubernetes API server.
- Webhook traffic paths and serving details can vary by implementation and evolution of controllers.
- Keeping the broad CP↔worker allowance prevents accidental webhook breakage/outages during those changes, while explicit rules still document expected canonical ports.

CNI consideration:
- These webhook-related CP↔worker rules are intentionally not limited to Flannel-only deployments.
- Even with VCN-native CNI, webhook backends can still involve worker/node paths depending on workload design.
- Reliability-first posture: keep CP↔worker webhook rules for both CNI modes unless a dedicated hardening flag is introduced and validated.

## 3) Pods (`pod`)

### 3.1 NSG Rules (`pod_nsg`) (only when `local.is_npn`)

| Flow | Peer / CIDR | Protocol / Port(s) | Condition | Why this exists |
|---|---|---|---|---|
| Ingress + Egress pair | `pod_nsg` (self) | ALL | `local.is_npn` | Pod-to-pod cluster traffic. |
| Ingress + Egress pair | `worker_nsg` | ALL | `local.is_npn` | Cross-node pod traffic and hostNetwork/NodePort paths. |
| Ingress + Egress pair | `cp_nsg` | ALL | `local.is_npn` | Broad CP↔pod webhook reliability safety-net; intentionally coexists with explicit CP↔pod API rules. |
| Ingress + Egress pair | `oke_lb_nsg` | TCP (all ports) | `local.is_npn` | LB as backend to pods (TCP). |
| Ingress + Egress pair | `oke_lb_nsg` | UDP (all ports) | `local.is_npn` | LB as backend to pods (UDP). |
| Egress only | `0.0.0.0/0` | ALL | `local.is_npn && allow_pod_nat_egress` | Pod internet egress through NAT path. |
| Ingress + Egress pair | `cp_nsg` | TCP 6443 | `local.is_npn` | Explicit canonical Kubernetes API path; intentionally kept with CP↔pod ALL rule for reliability. |
| Ingress + Egress pair | OCI Services CIDR (`SERVICE_CIDR_BLOCK`) | TCP (all ports) | `local.is_npn` | Pod access to OCI regional services. |
| Ingress + Egress pair | `db[postgres]` | TCP 5432 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"postgres")` | Pod apps to Postgres when shared app NSG model is used. |
| Ingress + Egress pair | `db[cache]` | TCP 6379 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"cache")` | Pod apps to OCI Cache. |
| Ingress + Egress pair | `db[oracledb]` | TCP 1521-1522 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"oracledb")` | Pod apps to Oracle DB. |
| Ingress + Egress pair | `db[oracledb]` | TCP 27017 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"oracledb")` | Pod apps to Oracle Mongo API. |
| Ingress + Egress pair | `db[mysql]` | TCP 3306 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"mysql")` | Pod apps to MySQL classic. |
| Ingress + Egress pair | `db[mysql]` | TCP 33060 | `local.is_npn && !separate_db_nsg && create_db_subnet && contains(db_service_list,"mysql")` | Pod apps to MySQL X protocol. |
| Ingress + Egress pair | `streaming` NSG | TCP 9092 | `local.is_npn && create_streaming_nsg` | Pod apps to OCI Streaming Kafka endpoint. |
| Ingress + Egress pair | `streaming` NSG | TCP 443 | `local.is_npn && create_streaming_nsg` | Pod apps to OCI Streaming REST endpoint. |

### 3.2 Pod Subnet Security List (`pod_sl`)

| Direction | Source/Destination | Protocol | Purpose |
|---|---|---|---|
| Ingress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery from non-OCI communication. |
| Egress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery responses. |
| Ingress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP within VCN. |
| Egress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP responses within VCN. |

### 3.3 Pod Explanation

Pod NSG rules are only created in VCN-native mode. They allow pod traffic to workers, CP, load balancers, OCI services, and optional DB/Streaming endpoints. This enables pods to act as first-class network endpoints while keeping communication NSG-scoped.

### 3.4 Important design note about CP-to-Pod webhook traffic

As with worker rules, some CP↔Pod rules may look redundant because both broad (`protocol = "all"`) and port-specific (`6443`) rules are present.  
This is intentional and should be preserved.

Reason:
- Kubernetes API server can call webhooks implemented in pods (for example CRD admission/conversion webhook paths).
- Those flows can evolve with controller/webhook implementations.
- Keeping broad CP↔Pod allowances reduces risk of webhook outages, while explicit `6443` rules still document expected canonical API traffic.

## 4) Load Balancers (`lb`)

There are two LB NSGs in this module:
- `oke_lb_nsg` (backend connectivity to workers/pods)
- `oke_lb_nsg_frontend` (public 80/443 exposure)

### 4.1 LB Backend NSG Rules (`oke_lb_nsg`)

| Flow | Peer / CIDR | Protocol / Port(s) | Condition | Why this exists |
|---|---|---|---|---|
| Ingress + Egress pair | `worker_nsg` | TCP 30000-32767 | Always | NodePort service traffic between LB and workers. |
| Ingress + Egress pair | `worker_nsg` | UDP 30000-32767 | Always | NodePort service traffic between LB and workers (UDP). |
| Ingress + Egress pair | `worker_nsg` | TCP 10256 | Always | LB health-check channel to workers. |
| Ingress + Egress pair | `pod_nsg` | TCP (all ports) | `local.is_npn` | Pods as direct LB backends (TCP). |
| Ingress + Egress pair | `pod_nsg` | UDP (all ports) | `local.is_npn` | Pods as direct LB backends (UDP). |

### 4.2 LB Frontend NSG Rules (`oke_lb_nsg_frontend`)

| Flow | Peer / CIDR | Protocol / Port(s) | Condition | Why this exists |
|---|---|---|---|---|
| Ingress | `0.0.0.0/0` | TCP 80 | Always | Public HTTP ingress. |
| Egress | `0.0.0.0/0` | TCP source port 80 | Always | HTTP response/egress path. |
| Ingress | `0.0.0.0/0` | TCP 443 | Always | Public HTTPS ingress. |
| Egress | `0.0.0.0/0` | TCP source port 443 | Always | HTTPS response/egress path. |

### 4.3 LB Subnet Security Lists (`external_lb_sl`, `internal_lb_sl`)

| Subnet SL | Direction | Source/Destination | Protocol | Purpose |
|---|---|---|---|---|
| External LB | Ingress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery. |
| External LB | Egress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU responses. |
| External LB | Ingress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP within VCN. |
| External LB | Egress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP responses. |
| Internal LB | Ingress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU discovery. |
| Internal LB | Egress | `0.0.0.0/0` | ICMP type 3 code 4 | Path MTU responses. |
| Internal LB | Ingress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP within VCN. |
| Internal LB | Egress | `VCN CIDR` | ICMP type 3 | Fast-fail ICMP responses. |

### 4.4 LB Explanation

LB rules are split between backend reachability and internet-facing frontend access. Backend NSG rules allow LB-to-worker/pod service traffic and health checks. Frontend NSG rules expose 80/443 publicly.

## 5) Important conditional behavior

| Variable / Local | Effect on rules |
|---|---|
| `local.is_npn` | Enables pod subnet + pod NSG + all pod-related CP/worker/LB rules. |
| `allow_worker_nat_egress` | Enables worker egress rule to `0.0.0.0/0`. |
| `allow_pod_nat_egress` | Enables pod egress rule to `0.0.0.0/0` (NPN only). |
| `create_bastion_subnet` | Enables CP↔bastion API and worker↔bastion SSH rules. |
| `create_db_subnet` + `db_service_list` | Enables DB-related rules for selected services. |
| `separate_db_nsg` | When `false`, DB service rules are attached directly to worker/pod NSGs; when `true`, dedicated app DB NSGs are used instead. |
| `create_streaming_nsg` | Enables Streaming-related rules (Kafka 9092 and REST 443). |
| `cp_allowed_source_cidr` | Sets source/destination for CP API external 6443 rule pair. |
| `cp_egress_cidr` + `allow_external_cp_traffic` + CP subnet mode | Controls CP external egress rule creation. |

## 6) Final note

For `cp`, `worker`, `pod`, and `lb`, this Terraform uses:
- NSGs for service-level L4 policy (ports/protocols/peers)
- Security Lists mainly as subnet-level ICMP baseline

This separation is intentional and common for OKE: NSGs carry most of the operational security logic.  
In this report context, ICMP Security List rules should also be considered required for VCN-to-DRG connectivity behavior.
Additionally, overlapping stateless/stateful rules are intentionally used in selected places so OCI applies stateless behavior where preferred, while keeping broad Internet exposure under stateful control for security.
