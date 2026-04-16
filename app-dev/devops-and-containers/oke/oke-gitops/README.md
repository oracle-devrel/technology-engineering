# OKE GitOps Solution with OCI DevOps

## Summary
This repository provides an OCI Resource Manager stack to bootstrap a GitOps operating model on OKE using OCI DevOps.

The stack creates and configures:
- An OCI DevOps project
- OCI Code Repositories for pipelines, cluster configuration, and application configuration samples
- A Build Pipeline to mirror Flux Operator Helm chart and required images into OCIR
- A Deployment Pipeline to install Flux Operator on OKE
- Required OCI DevOps integrations such as IAM policies/dynamic group, logging, and notifications

The goal is to give platform teams a repeatable foundation for secure, controlled GitOps delivery on Oracle Cloud Infrastructure.

Roadmap note:
- A GitOps solution based on ArgoCD is planned for a future iteration.

## Flux Operator Solution
For the complete operational guide (architecture, repository model, bootstrap flow, overlays, and runbook), see:

- [Flux Operator solution documentation](./flux-solution.md)

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/technology-engineering/releases/download/oke-gitops-1.2.0/stack.zip)

## IAM Policies
This stack requires specific OCI IAM policies (created by the stack when enabled, or pre-created by the user).

See the full policy list and dynamic group details here:

- [Required policies](./policies.md)
