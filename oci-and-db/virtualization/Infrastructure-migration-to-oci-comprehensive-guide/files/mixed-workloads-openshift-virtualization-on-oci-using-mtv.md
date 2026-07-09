# Mixed Containerized and VM-based Workloads to OpenShift Virtualization on OCI

## Overview

This guide covers migrating mixed VM-based and containerized workloads from on-premises or hybrid environments to Red Hat OpenShift Virtualization running on Oracle Cloud Infrastructure (OCI).

This migration path is intended for organizations that have made a strategic decision to consolidate and standardize on OpenShift as their primary application platform, bringing virtual machines and containers together under a single operational, governance, and lifecycle model.

## Introduction

Many enterprises operate hybrid application estates, where:
- Legacy or stateful applications continue to run on virtual machines
- Modern applications are delivered using containers and Kubernetes
- Operational teams must manage two parallel platforms

OpenShift Virtualization enables these organizations to collapse this split architecture, allowing both VMs and containers to run on a single OpenShift platform, using shared:
- Networking
- Storage
- Security
- CI/CD
- Governance tooling

Migrating mixed workloads to OpenShift Virtualization on OCI is a platform consolidation strategy designed to simplify operations and enable gradual modernization. It is not a lift-and-shift strategy from one virtualization platform to another.

## OpenShift Virtualization Overview
OpenShift Virtualization enables virtual machines to run as first-class Kubernetes resources inside OpenShift. Virtual Machines:
- Are managed using Kubernetes APIs
- Share the same networking and storage abstractions
- Can be integrated into GitOps and CI/CD workflows

## Target Platform: OpenShift Virtualization on OCI

**Key Characteristics:**
- **Container Platform:** Red Hat OpenShift Container Platform with OpenShift Virtualization
- **Virtualization Technology:** KubeVirt, also leveraging QEMU for emulation and KVM for virtualization
- **Licensing Model:** Bring Your Own Subscription (BYOS)
- **Control Plane:** Customer-managed OpenShift control plane, based on OCI Compute (typically VM shapes)
- **Worker Nodes:** OCI Compute (VM, Bare Metal or GPU shapes)
- **Networking:** OCI VCN-native networking (with VCNs, Subnets, Flexible Load Balancers, DHCP and Native DNS integration)
- **Ingress:** OpenShift Router
- **Storage:** OCI Block Volume & File Storage via CSI (with ODF as a complimentary option, if needed)
- **Best Use Case:** Enterprises standardizing on OpenShift for both VMs and containers

# Migration Tooling: OpenShift Migration Toolkit for Virtualization (MTV)

Migration Toolkit for Virtualization ([MTV](https://docs.redhat.com/en/documentation/migration_toolkit_for_virtualization)) is Red Hat’s supported tool for migrating VMs into OpenShift Virtualization. MTV supports:
- VMware vSphere as a source
- Disk-based VM migration
- Network and storage mapping
- Incremental synchronization prior to cutover

MTV supports migration of virtual machines from multiple virtualization platforms into OpenShift Virtualization (KubeVirt), including:
- VMware vSphere
- OVA files repository (useful if it is not possible to create direct network connection with the vSphere source environment)
- Red Hat Virtualization (RHV or oVirt)
- Red Hat OpenStack Platform
- Other KVM-based environments

MTV is a virtualization-platform-agnostic migration tool.

**When to choose this path**
This migration approach is recommended when:
- OpenShift is the target enterprise platform
- Both VM and container workloads must coexist
- Immediate application refactoring is not feasible
- A single operational model is preferred
- Long-term modernization is planned, but phased

**When NOT to choose this path**
This approach is not recommended when:
- The goal is pure VM lift-and-shift with minimal platform change
- VMware operational continuity is required
- No OpenShift adoption strategy exists

## Migration Workflow
1. **Assessment & Planning**
- Inventory VM workloads and containerized applications
- Identify candidates for:
  - Direct VM migration
  - Container redeployment
  - Future refactoring
- Validate OpenShift subscription sizing

2. **OpenShift Virtualization on OCI Deployment**
- Deploy OpenShift cluster on OCI
- Enable OpenShift Virtualization
- Configure:
  - Node pools (VM-capable nodes)
  - Storage classes
  - Networking and ingress

3. **Container Workload Transition**
At this stage, containerized workloads are transitioned to OpenShift on OCI.
The approach taken depends on whether the source container platform is already OpenShift or not.

This step intentionally supports two valid paths, while keeping the end goal consistent: standardization on OpenShift as the application platform.

**3a. Container Redeployment (Non-OpenShift Source)**
This approach applies when containerized workloads originate from:
- Generic Kubernetes clusters
- Mixed or inconsistent Kubernetes platforms
- Environments where OpenShift is the target standard, not the existing platform

**Approach:**
- Deploy OpenShift platform services
- Redeploy containerized applications
- Recreate OpenShift-native constructs as required
- Validate application connectivity and scaling

**Key Characteristics:**
- No cluster-level state is preserved
- No migration tooling is used
- This represents a clean OpenShift adoption model
- Aligns with long-term OpenShift governance and security standards

This is the preferred path when the source platform is not already OpenShift.

**3b. Container Redeployment (OpenShift Source)**
This approach applies when:
- Containerized workloads are already consolidated on OpenShift
- The objective is to relocate the OpenShift platform to OCI
- Preservation of application structure and configuration is required

**Approach:**
- Use Migration Toolkit for Containers ([MTC](https://docs.redhat.com/en/documentation/openshift_container_platform/4.20/html/migration_toolkit_for_containers/index)) to migrate:
  - Namespaces
  - Kubernetes and OpenShift resources
  - Persistent volumes (where supported)
- Perform test migrations prior to final cutover
- Validate application readiness on the target cluster

**Key Characteristics:**
- High-fidelity migration of OpenShift workloads
- Minimal application change required
- Preserves OpenShift operational consistency
- Mirrors the approach described in the OpenShift to OpenShift on OCI using MTC guide

This path should be used only when the source platform is already OpenShift.

4. **VM Migration Using MTV**
- Install MTV Operator on OpenShift
- Register source virtualization environment
- Define migration plans:
  - VM selection
  - Network mapping
  - Storage mapping
- Perform test migrations

5. **Cutover & Validation**
- Perform final synchronization
- Shut down source VMs
- Start VMs on OpenShift Virtualization
- Validate application behavior and performance

## Networking Considerations
- VM IP addresses may change depending on network design
- No Layer-2 extension is assumed
- DNS and firewall rules must be updated
- Network policies apply uniformly to VMs and pods

## Storage Considerations
- VM disks are stored as Kubernetes Persistent Volumes
- Storage performance must be validated for VM workloads
- Backup and snapshot strategies should be updated to Kubernetes-native tooling

## Security & Governance
- Unified RBAC across VMs and containers
- OpenShift SCCs apply to container workloads
- VM access is controlled via OpenShift constructs
- Centralized policy enforcement becomes possible

## Operational Model
OpenShift Virtualization enables:
- Single monitoring and logging stack
- Unified CI/CD pipelines
- GitOps-driven lifecycle management
- Simplified day-2 operations

This significantly reduces platform sprawl.

## Limitations & Considerations
- VM performance characteristics differ from hypervisor-native platforms
- Not all VM workloads are ideal candidates
- Hardware-specific features may not be supported
- This is a convergence platform, not a hypervisor replacement for all use cases

## Best Practices & Guidance
- Adopt OpenShift Virtualization as a consolidation layer
- Migrate VMs first, modernize later
- Avoid forcing refactoring during migration
- Validate performance expectations early
- Keep OCVS as an option where appropriate

## Summary
Migrating mixed VM-based and containerized workloads to OpenShift Virtualization on OCI is a strategic platform consolidation decision.

This approach:
- Unifies infrastructure and application operations
- Enables gradual modernization
- Reduces operational complexity
- Aligns with OpenShift-centric enterprise strategies

It is the right choice when OpenShift is the destination platform, not simply a hosting environment.
