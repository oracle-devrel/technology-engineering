# High Availability

This area focuses on technologies supporting High Availability and best practices.

Specifically Oracle RAC and Application Continuity

# RAC

Oracle Real Application Clusters (RAC) allow customers to run a single Oracle Database across multiple servers in order to maximize availability and enable horizontal scalability while accessing shared storage. User sessions connecting to Oracle RAC instances can failover and safely replay changes during outages, without any changes to end-user applications, hiding the impact of the outages from end users.

# Application Continuity

Application Continuity (AC) is a feature available with the Oracle Real Application Clusters (RAC), Oracle RAC One Node, and Oracle Active Data Guard options that masks outages from end users and applications by recovering the in-flight database sessions following recoverable outages.

Application Continuity masks outages from end users and applications by recovering the in-flight work for impacted database sessions following outages. Application Continuity performs this recovery beneath the application so that the outage appears to the application as a slightly delayed execution.

Application Continuity improves the user experience for both unplanned outages and planned maintenance. Application Continuity enhances the fault tolerance of systems and applications that use an Oracle database.

Transparent Application Continuity
Transparent Application Continuity (TAC) transparently tracks and records the session and transactional state so that the database session can be recovered following recoverable outages.

With no reliance on application knowledge or application code changes
Transparency is achieved by consuming the state-tracking information that captures and categorizes the session state usage as the application issues the user calls.


# Useful Links

- [RAC Architecture](https://www.oracle.com/webfolder/technetwork/tutorials/architecture-diagrams/19/rac/pdf/rac-19c-architecture.pdf)
- [Application Continuity](https://www.oracle.com/uk/database/technologies/high-availability/app-continuity.html)
 

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
