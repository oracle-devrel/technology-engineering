# Introduction

This document articulates the best practices for OCI Goldengate N-way replication in terms of generic capabilities and provides guidance and options on how those capabilities can be implemented.

This will provide methods and best practices to achieve real-time data replication using OCI GoldenGate for bi-directional cross-region setup and uni-directional setup  across the same region between Database Cloud Service(DBCS) and Autonomous Data Warehouse(ADW).
However, the same asset can be used to perform replication between other Oracle Databases as well.

Owners: Saravanadurai Rajendran and Divya Batra

## Logical Architecture

![Logical Architecture](Architecture.png)

### Scope & Context

This solution has been built to create a resilient infrastructure capable to withstand planned/unplanned outages of any critical component/service for the following scenarios while achieving the recovery point objective (RPO) and recovery time objective (RTO).

- Planned maintenance, including upgrades.
- Recoverable local failure.
- Unrecoverable or site failure.

 ### Considerations

Application in each region will function independently. However, the databases between the two regions (Region1 and Region2) are synchronized via bi-directional change replication using Oracle GoldenGate. During normal operation, database connection requests will be distributed to one of the systems in either region. 
In case of disaster recovery, all  requests will be directed to the available database system. This active/active architecture will be able to handle the following planned and unplanned outages.
Also, Uni-directional replication has been set up between DBCS and ADW in the same region (for reporting needs).

#### GoldenGate Configuration
GoldenGate configuration/parameter files for this N-way and cross-region replication between DBCS and ADW can be referred to in “GoldenGate-N-way-replication-config.md”.








