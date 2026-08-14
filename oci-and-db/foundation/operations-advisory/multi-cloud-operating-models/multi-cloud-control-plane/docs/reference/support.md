# What MCCP supports

This page defines the supplied MCCP baseline. All requests still require a
completed environment handoff and the standard pull-request lifecycle.

## Resource requests (Day 1)

The GitHub interface, optional UI, and optional Codex plugin support every
resource in this table.

| Cloud | Resources | Testing evidence |
| --- | --- | --- |
| OCI | Project network security groups (NSGs), Compute, Autonomous Database | Live OCI smoke tests |
| Azure | Private Linux VM, Oracle Autonomous Database | Schema validation and mocked Terraform lifecycle |
| Google Cloud | Private Linux VM, Oracle Autonomous Database Serverless | Schema validation and mocked Terraform lifecycle |

Azure and Google Cloud adapters consume existing foundation references. They do
not create projects, resource groups, IAM, networks, subnets, NSGs, service
accounts, ODB Networks, or ODB Subnets.

## Lifecycle operations (Day 2)

| Operation | GitHub interface | Optional UI | Optional Codex plugin | Testing evidence |
| --- | --- | --- | --- | --- |
| OCI Autonomous Database start/stop | Yes | Yes | Yes | Live OCI smoke tests |
| OCI Compute `deploy-agent` | Yes | Yes | No | Live OCI smoke tests |
| Azure operations | No | No | No | Not supplied |
| Google Cloud operations | No | No | No | Not supplied |

## GitHub Free profile

The supplied `repository-secrets` profile is intended for controlled
non-production use on GitHub Free with procedural review. Production requires
a customer security review and a separate production runner. See
[security](security.md) for the required controls.

## What has been tested

Maintainer qualification covered:

- every supplied JSON file and catalog schema;
- supported create, update, and delete validation, including invalid handoffs,
  public IPs, secret placeholders, unknown clouds, and mixed environments;
- Terraform formatting, initialization, validation, and mocked Azure and Google
  Cloud lifecycle tests without cloud credentials;
- synthetic Git repositories for Project Team requests, project handoff, and
  environment retirement;
- workflow linting, documentation links, installation placeholders, packaging,
  and component consistency; and
- live OCI smoke tests for the supplied OCI resources and operations.

The publication does not certify every customer environment. Azure and Google
Cloud were not applied to live target clouds, and their lifecycle operations
are not supplied. Customer extensions are unqualified until the complete
[extension model](architecture.md#extension-model) is implemented and tested.

Before enabling requests, complete the customer installation, cloud handoff,
and [first-project acceptance](verify-secret-isolation.md), then run a request
through the [GitHub interface](../usage/github-interface.md) on the customer
runners and identities.
