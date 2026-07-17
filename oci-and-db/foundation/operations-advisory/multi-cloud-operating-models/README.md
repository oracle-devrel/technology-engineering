## Multi-Cloud Operating Models

Use these solutions to give Cloud Operators and Project Teams a consistent,
reviewed GitOps process for infrastructure delivery.

## Choose where to start

| Your situation | Start with |
|---|---|
| You need to establish an OCI tenancy foundation, environments, and project compartments | [OCI Landing Zone](oci-landing-zone/README.md) |
| Your foundation already exists and teams need governed project-level OCI, Azure, or Google delivery | [Multi-Cloud Control Plane](multi-cloud-control-plane/README.md) |
| You need both | Deploy the Landing Zone first, then pass its project handoff to the Control Plane |

The Landing Zone is operated by Cloud Operators. It establishes OCI through
Bootstrap and OP00–OP04, then provides the compartment and network references
needed by a project.

The Control Plane is operated by platform administrators and Project Teams. It
turns approved JSON requests into Terraform plans or Ansible checks, requires
human approval, and uses trusted runners to perform merged changes.

The two solutions exchange only `project-foundation-handoff.json`. The handoff
contains identifiers and network references, not credentials. You may adopt
either solution independently when your existing environment provides the same
required boundary.

Both solutions are currently preview releases. Evaluate them in non-production,
complete your security review, and validate every capability you plan to enable
before production rollout.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License, Version 1.0. See
[LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE).
