# Support matrix

This matrix describes the supplied MCCP MVP baseline. An installed customer may
extend it only through the complete [extension model](architecture.md#extension-model).

## Day 1 resources

| Cloud | Supported resource | Direct GitHub | Optional UI | Optional Codex assistant | Qualification boundary |
| --- | --- | --- | --- | --- | --- |
| OCI | Project network security groups | Yes | Yes | Yes | Live OCI smoke evidence |
| OCI | Compute | Yes | Yes | Yes | Live OCI smoke evidence |
| OCI | Autonomous Database | Yes | Yes | Yes | Live OCI smoke evidence |
| Azure | Private Linux VM | Yes | Yes | Yes | Schema validation and mocked Terraform lifecycle only |
| Azure | Oracle Autonomous Database | Yes | Yes | Yes | Schema validation and mocked Terraform lifecycle only |
| Google Cloud | Private Linux VM | Yes | Yes | Yes | Schema validation and mocked Terraform lifecycle only |
| Google Cloud | Oracle Autonomous Database Serverless | Yes | Yes | Yes | Schema validation and mocked Terraform lifecycle only |

Azure and Google Cloud requests require a completed, reviewed handoff. Their
adapters consume handed-off references and do not create foundation resources.

## Day 2 operations

| Cloud | Supported operation | Direct GitHub | Optional UI | Optional Codex assistant | Qualification boundary |
| --- | --- | --- | --- | --- | --- |
| OCI | Autonomous Database start and stop | Yes | Yes | Yes | Live OCI smoke evidence |
| OCI | Compute `deploy-agent` | Yes | Yes | No | Live OCI smoke evidence |
| Azure | Day 2 operations | No | No | No | Not supplied |
| Google Cloud | Day 2 operations | No | No | No | Not supplied |

Every request interface prepares the same pull-request artifact. Approval,
merge, and runner execution remain outside those interfaces; see the
[request lifecycle](../usage/request-lifecycle.md).

## Governance profile

The supplied `repository-secrets` profile is qualified for controlled
non-production use on GitHub Free with procedural review. Production requires
a customer security review and an isolated production runner. Enforceable
GitHub approval controls are a future hardened release, not an MVP setting.

See [qualification](qualification.md) for complete evidence and exclusions and
[security boundaries](security-boundaries.md) for the operating controls.
