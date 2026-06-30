# Exadata Cloud@Customer Infrastructure

Exadata Database Service on Cloud@Customer infrastructure brings Oracle's industry-leading Exadata platform directly into your data center, providing a dedicated, high-performance foundation for mission-critical database workloads. Fully engineered, integrated, and managed by Oracle, it combines the scalability and automation of cloud services with the security, compliance, and data sovereignty benefits of on-premises deployment.

<img src="./../images/exadb-infra.png" alt="Infrastructure">

## ECPU metric

The ExaDB-C@C X11M adopts ECPUs as the standard billing metric for the Database Service. ECPU replace the OCPU metric that has been used so far and will be the only metric on ExaDB-C@C X11M.

ECPU = Elastic Compute Units

ECPUs are an abstract measure of compute resources, dynamically allocated from a pool of compute and storage servers. 

By introducing ECPU’s, Oracle is providing a durable pricing metric which is not tied to the exact make, model, or clock speed of the underlying processor. This avoids the possibility of complex billing metric in the future (for example, as new hardware architectures are introduced).

ECPU-based databases provide the same user-experience as OCPU-based databases, and you may convert existing OCPU databases to ECPU databases without disruption or downtime.

ECPUs provide similar or better price-performance than OCPUs because

- An OCPU is the equivalent of a physical core of a processor (CPU). A billing based on OCPUs binds the price to the make, model or clock speed of the underlying CPU. But CPU capacities increase with every new release, rendering a correct price to performance metric relation too complex.
- An ECPU is based on the number of cores that are elastically allocated per hour to the VM Cluster from a pool of Exadata database servers and storage servers. This metric is independent of the underlying physical hardware, making it the basis for billing in the Cloud for the long-term future.

# Useful Links

- [Main Oracle Product Page](https://www.oracle.com/uk/engineered-systems/exadata/cloud-at-customer/)

- [Oracle Exadata Database Service on Cloud@Customer X11M datasheet](https://www.oracle.com/a/ocom/docs/engineered-systems/exadata/exadb-cc-x11m-ds.pdf)

- [Documentation Home](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/)

- [Oracle Exadata Configuration Assistant (OECA)](https://www.oracle.com/database/technologies/oeca-download.html)

- [Oracle EMCC extracts sizing script and documentaion](assets/Oracle_EMCC_sizing_extracts.zip)

- [ExaDB-C@C Data Collection for sizing](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/data-collection)

- [ExaDB-C@C Configuration Collection](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/exacc-configuration-collection)

- [ExaDB-C@C Health Check](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/exacc-healthcheck)

- [ExaDB-C@C related list of MOS notes](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/exacc-mos-note-list)

- [ExaDB-C@C Supported Database Versions](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/exacc-supported-db-versions)

- [ExaDB-C@C VM Cluster scaling](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/vm-cluster-scaling)

- [ExaDB-C@C Single Node VM Cluster](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/exacc-infra/single-node-vm-cluster)

- [VM serial consol access](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/vm-serial-consol-access)

- [VM serial consol history and Cloud Shell integration](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/database-cloud-at-customer/exadata-cloud-at-customer/vm-serial-consol-history-and-cloud-shell-integration)

## Useful Documentation
- [Managing VM Clusters](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-manage-vm-clusters.html)

- [Creating DB Homes](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-create-db-homes.html)

- [Managing Oracle Databases](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-manage-databases.html)

- [Managing Backups Destinations](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-manage-db-backup-and-recovery.html)

- [Policy details for Exadata Cloud @ Customer](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-policy-details.html)

- [Using the Dbaascli Utility](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-using-dbaascli.html)

- [Monitoring and managing storage servers with ExaCLI](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-using-exacli.html)

- [Rest API](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/rest.html)

- [Exadata Cloud API/CLI Alignment Matrix (Doc ID 2768569.1)](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2768569.1)

- [Enhanced Infrastructure Maintenance Controls for Oracle Exadata Database Service on Cloud@Customer](https://blogs.oracle.com/database/post/enhanced-infrastructure-maintenance-controls-for-oracle-exadata-database-service-on-cc)

- [Managing Exadata Cloud@Customer Resources with Oracle Enterprise Manager Cloud Control)](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-managing-resources-with-emcc.html)

- [OCI Ops Insights - Cloud native support for Exadata Cloud@Customer Databases)](https://blogs.oracle.com/observability/post/oci-ops-insights-cloud-native-support-for-exadata-cloudcustomer-databases)

Reviewed: 06/29/26

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
