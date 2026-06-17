# OpenShift 4.20 Agent Based Day 2: Enforce FQDN Node Names (Node joins cluster with the short name instead of the FQDN)

`Reviewed: 25.02.2026`

## When to use this asset?
Use this asset during Day 2 operations when adding new nodes to an existing OpenShift 4.20 cluster (agent-based workflow) and the node registers with a short hostname instead of the intended FQDN. Apply it if consistent FQDN naming is required for DNS alignment, certificate expectations, monitoring, logging, automation, or enterprise naming standards.

## Who would use this asset when?
This asset is typically used by OpenShift platform engineers, cluster administrators, SRE or operations teams, and infrastructure architects responsible for Day 2 node onboarding and naming compliance. It is relevant when preparing node provisioning standards, fixing naming issues discovered after a node join, or enforcing cluster-wide consistency before rolling out additional integrations.

## How to use this asset?
Use this asset as a step-by-step procedure to enforce FQDN-based node naming using OpenShift configuration (for example MachineConfig) and to validate the result on the node and in the cluster. Follow the documented steps in order, apply the configuration to the correct node role or MachineConfigPool, and confirm the node appears with the expected FQDN in the OpenShift API and related tooling.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
