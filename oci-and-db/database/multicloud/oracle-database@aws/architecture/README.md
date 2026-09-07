# Oracle Database@AWS Architecture Diagrams Examples

This repository contains a curated collection of architecture diagrams for **Oracle Database@AWS** deployments and integration patterns.

The goal is to provide:
- Reference architectures
- Design inspiration
- Common deployment patterns
- Integration examples with AWS services
- Reusable draw.io diagrams for workshops, presentations, and technical discussions

All diagrams are provided in editable **draw.io (`.drawio`)** format so they can be customized for your own environments and use cases.

Reviewed: 18.08.2026



# When to use this asset?

Use this asset when you need a proven starting point for designing, documenting, or presenting Oracle Database@AWS architectures. It is ideal for:
- Exploring common Oracle Database@AWS deployment patterns and best practices
- Designing new architectures or validating existing solutions
- Creating technical presentations, workshops, or technical discussions
- Accelerating solution design by reusing editable reference diagrams

These examples are intended for:
- Solution Architects
- Cloud Architects
- Oracle DBAs
- AWS Architects
- Technical Sales teams
- Anyone evaluating Oracle Database@AWS solution



# How to use this asset?

All diagrams are created using: [draw.io / diagrams.net](https://www.diagrams.net/)
You can:
- Open them directly in draw.io
- Edit and customize them
- Export to PNG, SVG, or PDF
- Embed them in documentation or presentations

Browse the collection to find the architecture diagram that best matches your use case. Customize the diagram to reflect your environment by adding, removing, or modifying components, labels, and integrations. The diagrams are intended as reference examples and can be adapted to meet your organization's specific requirements and deployment scenarios.



# Repository Structure

| Diagram | Description |
|---|---|
| [01_DB@AWS_RAM_3Envs_Cross_AZ.drawio](./files/01_DB@AWS_RAM_3Envs_Cross_AZ.drawio) | DB@AWS target architecture with ODB network segmentation across three environments plus DR. Internal network traffic is routed through ODB peering, while external traffic uses a TGW hub-and-spoke configuration. MAA Cross-AZ setup. |
| [02_DB@AWS_LSM(NetAccGovernance)_RAM_2Envs_Cross_Region.drawio](./files/02_DB@AWS_LSM(NetAccGovernance)_RAM_2Envs_Cross_Region.drawio) | DB@AWS target architecture with account segregation. The AWS Network Account owns all network components, including the ODB networks and Transit VPCs. The AWS PROD Account owns the PROD VM Cluster and the AWS TEST Account owns the TEST VM Cluster. ODB network segmentation covers two environments plus DR, with internal traffic routed through ODB peering and external traffic through a TGW hub-and-spoke configuration. MAA Cross-Region setup. |
| [03_DB@AWS_LSM(Payer)_RAM_7Envs_Consolidation_9Avmc_Cros_AZ.drawio](./files/03_DB@AWS_LSM(Payer)_RAM_7Envs_Consolidation_9Avmc_Cros_AZ.drawio) | DB@AWS target architecture with ODB network segmentation across seven environments plus DR. Internal network traffic is routed through ODB peering, while external traffic uses a TGW hub-and-spoke configuration. MAA Cross-AZ setup. ADB-D consolidation requires two additional CNs (Compute Nodes) in the Exadata Basic configuration to provide enough local storage to host six AVMCs (Autonomous VM Clusters), with five ACDBs (Autonomous Container Databases) each. |
| [04_DB@AWS_RAM_4Envs_Hub_Spoke_FireWallVPC_Cross_AZ.drawio](./files/04_DB@AWS_RAM_4Envs_Hub_Spoke_FireWallVPC_Cross_AZ.drawio) | DB@AWS target architecture with ODB network segmentation across four environments plus DR. Internal network traffic is routed through ODB peering, while external traffic uses a TGW hub-and-spoke configuration plus a Firewall VPC. MAA Cross-AZ setup. |



# Disclaimer

These diagrams are provided as reference examples only.

They are:
- Not production deployment guides
- Not official Oracle reference architectures
- Subject to change as DB@AWS capabilities evolve

Always validate architecture decisions against:
- Current Oracle and AWS documentation
- Oracle and AWS best practices
- Security and compliance requirements
- Specific operational constraints



# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
