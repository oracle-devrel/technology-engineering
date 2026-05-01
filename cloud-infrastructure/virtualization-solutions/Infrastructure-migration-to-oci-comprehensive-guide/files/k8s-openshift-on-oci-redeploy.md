# Kubernetes to OpenShift Container Platform on OCI using Redeployment

## Overview

This guide covers migrating containerized workloads from on-premises or self-managed Kubernetes environments to Red Hat OpenShift Container Platform running on Oracle Cloud Infrastructure (OCI) using a redeployment-based migration approach.

This migration path is intended exclusively for organizations that have already standardized on OpenShift, or are actively transitioning toward OpenShift as their enterprise container platform.

For customers without an OpenShift standardization requirement, Oracle Kubernetes Engine (OKE) remains the preferred and recommended target platform.

## Introduction

Oracle Cloud Infrastructure (OCI) provides multiple enterprise-grade container platforms, each optimized for different customer objectives. While OKE is the default Kubernetes platform for OCI, OpenShift on OCI exists to support customers with explicit Red Hat OpenShift operational, tooling, and subscription requirements.

Redeploying Kubernetes workloads onto OpenShift on OCI is not a generic migration choice. It is appropriate when customers:

- Have existing OpenShift clusters on-premises or in other clouds
- Are standardizing on OpenShift for regulatory, operational, or ecosystem reasons
- Require OpenShift-specific capabilities (Operators, integrated pipelines, governance)
- Already hold, or are in the process of procuring, Red Hat OpenShift subscriptions

OpenShift on OCI operates under a Bring Your Own Subscription (BYOS) model. Customers are responsible for licensing OpenShift directly from Red Hat, while OCI provides the underlying infrastructure.

## Target Platform: OpenShift Container Platform on OCI

**Key Characteristics:**
- **Container Platform:** Red Hat OpenShift Container Platform
- **Licensing Model:** Bring Your Own Subscription (BYOS)
- **Control Plane:** Customer-managed OpenShift control plane, based on OCI Compute (typically VM shapes)
- **Worker Nodes:** OCI Compute (VM, Bare Metal or GPU shapes)
- **Networking:** OCI VCN-native networking (with VCNs, Subnets, Flexible Load Balancers, DHCP and Native DNS integration)
- **Ingress:** OpenShift Router (HAProxy-based)
- **Storage:** OCI Block Volume & File Storage via CSI (with ODF as a complimentary option, if needed)
- **Best Use Case:** Enterprises standardizing on OpenShift across hybrid and multi-cloud environments

# Migration Strategy Positioning

**When to Choose This Path**
This migration approach is recommended only if one or more of the following are true:
- OpenShift is already deployed on-premises or in another cloud
- OpenShift is the declared enterprise container standard
- Red Hat tooling (Operators, Pipelines, GitOps) is a hard requirement
- OpenShift subscription costs are already budgeted or approved

**When NOT to Choose This Path**
This approach is not recommended when:
- The source environment is generic Kubernetes with no OpenShift dependency
- The primary goal is cost optimization or platform simplicity
- The customer does not hold OpenShift subscriptions

In these scenarios, Kubernetes → OKE should be the default migration path.

## Migration Approach: Container Redeployment
Just like OKE, OpenShift migrations should avoid cluster-level state transfer. The correct approach is application redeployment, preserving application artifacts while rebuilding platform components cleanly on OCI. This ensures:
- Platform consistency across environments
- Alignment with Red Hat-supported architectures
- Reduced long-term operational risk

## Core Redeployment Building Blocks

**Container Images**
- Existing images can be reused with minimal changes
- Ensure:
  - Image registries are accessible from OCI. Or evaluate if OCI Object Storage can be configured as the storage backend for the OpenShift Image Registries
  - OpenShift Security Context Constraints (SCCs) are respected
- Preferred approach would be to mirror images into OCI Container Registry (OCIR)

**Deployment Manifests**
- Kubernetes YAML or Helm charts remain largely unchanged
- OpenShift-specific resources:
  - Routes
  - Templates
  - Operators
- Minor adjustments may be required to:
  - Security contexts
  - Service exposure
  - Storage classes

**CI/CD Pipelines**
- Pipelines typically require minimal changes:
  - OpenShift Pipelines (Tekton)
  - OpenShift GitOps (Argo CD)
- Existing GitOps workflows can be reused with new cluster targets
- Pipelines require:
  - Updated kubeconfig
  - Updated registry endpoints

## Migration Workflow
1. **Assessment & Discovery**
- Inventory namespaces and workloads 
- Identify OpenShift-specific dependencies
  - Operators
  - SCCs
  - Routes
- Validate subscription coverage and sizing

2. **OpenShift on OCI Architecture Design**
Key design considerations include:
- Control plane placement
- Worker node sizing and scaling
- Networking model within OCI VCN
- Ingress and external access strategy
- Storage class alignment

3. **Registry & Image Preparation**
- Validate image compatibility with OpenShift SCCs
- Mirror images to OCI Container Registry (OCIR) where possible
- Enable scanning and policy enforcement

4. **Application Redeployment**
- Deploy OpenShift platform services first
- Redeploy application namespaces in waves
- Validate:
  - Pod admission
  - Route exposure
  - Operator health

5. **Cutover Strategy**
Typical cutover options:
- DNS switch (preferred)
- Blue/green deployment
- Parallel run with staged user migration

This enables validation before production traffic is fully shifted.

## Networking Considerations
- OpenShift Routes replace generic Kubernetes Ingress
- No IP preservation is expected or required
- Firewall and DNS updates must be planned explicitly

## Security & Governance
- OpenShift RBAC and SCCs enforce stricter defaults
- Integrate with enterprise identity providers
- Apply cluster-wide governance policies early

## Observability & Operations
- OpenShift Monitoring Stack
- Logging and alerting via OpenShift tooling
- Integration with OCI Monitoring where possible

## Special Considerations

**Stateful Workloads**
Stateful workloads are intentionally excluded from this guide and should be addressed separately using:
- CSI-based migration
- Application-level replication
- Backup/restore tooling

**Operator-Based Workloads**
Operators must be:
- Reinstalled
- Reconfigured
- Revalidated

They are not migrated automatically.

## Best Practices & Guidance
- Only choose OpenShift on OCI when OpenShift is the enterprise standard
- Avoid mixing OKE and OpenShift without a clear governance model
- Redeploy platform services, do not migrate them
- Align subscription procurement early

## Summary

Redeploying Kubernetes workloads to OpenShift on OCI is a strategic standardization decision, not a technical necessity. When OpenShift is already embedded in the organization, this approach:
- Preserves operational consistency
- Maintains Red Hat supportability
- Enables hybrid and multi-cloud alignment

Otherwise, OKE remains the preferred Kubernetes target on OCI.
