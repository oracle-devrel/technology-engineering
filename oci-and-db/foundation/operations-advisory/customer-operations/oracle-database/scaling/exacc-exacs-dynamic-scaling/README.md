# ExaCC and ExaCS Dynamic Scaling

Last reviewed: 2026-06-16

This asset introduces a Dynamic Scaling operating pattern for Oracle Exadata Cloud@Customer (ExaCC) and Oracle Exadata Cloud Service (ExaCS) deployments operated through OCI-side control-plane automation.

In this context, ExaCS includes native OCI ExaCS and ExaCS delivered through Oracle Database@Google Cloud, Oracle Database@Azure, and Oracle Database@AWS.

The goal is simple: align OCPU capacity with real workload demand. Instead of keeping peak capacity allocated all the time, teams can scale up for known business windows, batch workloads, maintenance events, or seasonal demand, and scale down when the extra capacity is no longer needed. That makes Dynamic Scaling a practical FinOps pattern: it connects cost optimization to repeatable operations, not to manual, one-off changes.

Dynamic Scaling is a Day 2 workflow. It should normally run through OCI-native REST/API automation, supported CLI/SDK flows, or orchestration around those APIs. Terraform can still create and own the baseline service topology, but it should not be treated as a scheduler or autoscaler. If Terraform state also models OCPU or sizing fields, external scale actions must be handled deliberately so expected drift is visible, understood, and reconciled by the owning operating model.

Oracle Dynamic CPU Count (ODCC) complements this pattern at the database layer. Dynamic Scaling changes the Exadata capacity available to the VM Cluster; ODCC keeps database `cpu_count` aligned with that capacity for CDBs and PDBs. This matters when `cpu_count` is explicitly set for instance caging or CPU governance: if it is not adjusted after a scale event, adding OCPUs may not give the database the CPU headroom teams expect, and reducing OCPUs may leave database limits out of sync with the new shape.

Treat ODCC as part of the same FinOps operating model: Dynamic Scaling changes the capacity envelope, and ODCC helps the databases consume that envelope according to policy. The detailed reference for this operating model is the local [ODyS and ODCC](./files/OdyS_ODCC_v0.1.pdf) asset.

Use this material as an introductory reference for:

- understanding the FinOps value of scheduled Exadata capacity changes;
- understanding where ODCC fits alongside Exadata OCPU scaling;
- defining when scale-up and scale-down windows should run;
- separating baseline infrastructure ownership from operational scaling workflows;
- designing evidence, approval, and drift checks around each scaling action.

The detailed walkthrough is available in the same local asset.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
