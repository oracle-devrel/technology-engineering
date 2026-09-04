# OpenShift to OpenShift Container Platform on OCI using Migration Toolkit for Containers (MTC)

## Overview

This guide covers migrating containerized workloads from on-premises or self-managed Red Hat OpenShift clusters to Red Hat OpenShift Container Platform running on Oracle Cloud Infrastructure (OCI) using the OpenShift Migration Toolkit for Containers (MTC).

Unlike Kubernetes redeployment scenarios, this approach is designed for OpenShift-native environments where it is a priority to preserve:
- Namespace structure
- Kubernetes and OpenShift resources
- Persistent volume data
- Application configuration

This is the preferred migration approach when both the source and target platforms are OpenShift.

## Introduction

Organizations that have standardized on Red Hat OpenShift often rely heavily on:
- OpenShift Operators
- Integrated CI/CD pipelines
- Platform-level services
- Persistent application data

In these environments, a full redeployment may introduce unnecessary disruption and operational risk. Migration Toolkit for Containers (MTC) provides a supported, OpenShift-native mechanism for migrating workloads between OpenShift clusters, including data and configuration.

When migrating OpenShift workloads to OCI without changing the container platform, MTC offers the highest fidelity migration path.

OpenShift on OCI operates under a Bring Your Own Subscription (BYOS) model. Customers are responsible for licensing OpenShift directly from Red Hat, while OCI provides the underlying infrastructure.

## Target Platform: OpenShift Container Platform on OCI

**Key Characteristics:**
- **Container Platform:** Red Hat OpenShift Container Platform
- **Licensing Model:** Bring Your Own Subscription (BYOS)
- **Control Plane:** Customer-managed OpenShift control plane, based on OCI Compute (typically VM shapes)
- **Worker Nodes:** OCI Compute (VM, Bare Metal or GPU shapes)
- **Networking:** OCI VCN-native networking (with VCNs, Subnets, Flexible Load Balancers, DHCP and Native DNS integration)
- **Ingress:** OpenShift Router
- **Storage:** OCI Block Volume & File Storage via CSI (with ODF as a complimentary option, if needed)
- **Best Use Case:** Enterprises with established OpenShift estates migrating to OCI

# Migration Tooling: OpenShift Migration Toolkit for Containers (MTC)

Migration Toolkit for Containers ([MTC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/migration_toolkit_for_containers/index)) is Red Hat’s supported solution for migrating workloads between OpenShift clusters. MTC enables:
- Namespace-level migration
- Persistent volume data transfer
- Application configuration migration
- Selective workload cutover

MTC operates using a push or pull model, depending on network connectivity between clusters.

**Use MTC When:**
- Both source and target environments are OpenShift
- Applications depend on OpenShift-specific features
- Persistent data must be migrated
- Minimal application refactoring is desired

**Do NOT Use MTC When:**
- The source environment is generic Kubernetes
- The target platform is OKE
- A full application modernization or refactor is planned

In these cases, redeployment remains the preferred strategy.

## Migration Architecture Overview
MTC consists of the following components:
- MTC Operator installed on the target OpenShift cluster
- Velero for backup and restore orchestration
- Restic / CSI snapshots for persistent volume migration
- Migration Controller coordinating execution

The target cluster pulls workloads from the source, ensuring control remains on the destination side.

## Migration Workflow
1. **Assessment & Discovery**
- Inventory namespaces and workloads 
- Identify:
  - Operators in use
  - Custom Resource Definitions (CRDs)
  - Persistent volumes and storage classes
- Validate:
  - Kubernetes version compatibility
  - OpenShift version support matrix
  - Network connectivity between clusters

2. **Target OpenShift on OCI Preparation**
- Deploy OpenShift cluster on OCI
- Configure:
  - Networking and ingress
  - Storage classes
  - Registry access
- Install MTC Operator on both source and target cluster and define one of them as the "control cluster" (typically the target one)

3. **Source Cluster Registration**
- Register source OpenShift cluster with MTC
- Validate authentication and connectivity
- Confirm namespace visibility

4. **Migration Planning**
Migration plans define:
- Namespaces to migrate
- Data migration method:
  - Snapshot-based
  - File-system copy
- Pre- and post-migration hooks
- Cutover behavior

Multiple dry runs are strongly recommended.

5. **Migration Execution**
- Execute migration plan
- Monitor:
  - Data transfer progress
  - Resource creation
  - Application readiness
- Address conflicts or warnings as they arise

6. **Cutover & Validation**
- Freeze writes on source (if required)
- Perform final sync
- Validate application functionality
- Update DNS or ingress endpoints

## Persistent Data Considerations
MTC supports migrating persistent data, but results depend on:
- Storage class compatibility
- CSI driver support
- Data size and churn rate

For mission-critical databases:
- Application-level replication may still be preferred
- MTC should be used cautiously

## Networking Considerations
- No Layer-2 extension is used
- Applications will receive new IPs
- DNS and ingress updates are required
- Network policies must be validated post-migration

## Security & Governance
- OpenShift RBAC and SCCs are migrated where supported
- Secrets are transferred securely
- Identity provider integration must be revalidated on target

## Observability & Operations
- OpenShift Monitoring Stack is redeployed natively
- Logs and metrics history are not migrated
- Post-migration operational validation is required

## Limitations & Considerations
- Some Operators require manual reinstallation
- Cluster-level components are not migrated
- Cross-version migrations must follow Red Hat compatibility guidance
- Performance during migration depends on network throughput

## Best Practices & Guidance
- Use MTC only for OpenShift-to-OpenShift migrations
- Perform multiple dry runs
- Validate storage behavior early
- Do not migrate platform components
- Plan cutover windows carefully

## Summary
Migration Toolkit for Containers provides a supported, high-fidelity migration path for OpenShift workloads moving to OCI. When OpenShift is the source and destination platform, MTC:
- Minimizes disruption
- Preserves application structure and data
- Reduces refactoring effort
- Maintains Red Hat supportability

For all other Kubernetes scenarios, redeployment remains the recommended approach.
