# Autonomous Database Service on Cloud@Customer

Autonomous Database on Exadata Cloud@Customer combines Oracle's self-managing, self-securing, and self-repairing database technology with the performance and scalability of Exadata infrastructure deployed in your data center. Organizations can benefit from automated database operations and reduced administrative overhead while maintaining control over data location, security, and compliance requirements.

# Resource Allocation for ADB-C@C

The Autonomous Database documentation is not specifying a hard limit for the number of VM clusters (AVMCs) supported. It rather says that you can keep provisioning AVMCs and ACDs (Autonomous Container Databases) as long as the minimum amount of required resources are available.

- 1 ACD: 80 ECPU, 320 GB memory, 677 GB local storage, 6.61 TB Exadata Storage
- 2 ACD: 80 ECPU, 320 GB memory, 780 GB local storage, 6.73 TB Exadata Storage
- 3 ACD: 80 ECPU, 780 GB memory, 883 GB local storage, 6.86 TB Exadata Storage
- 16 ACD: 80 ECPU, 1616 GB memory, 2222 GB local storage, 8.45 TB Exadata Storage

**Note:** that there is a maximum number of supported ACDs per AVMC is 16, although we not recommending to create more than 6 in a single AVMC. The mapping between Oracle Homes and ACDs on ADB-C@C is always 1:1.

# Useful Links

- [Autonomous AI Database on Oracle Technology Engineering GitHub](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/autonomous-ai-database)

- [Oracle Autonomous Database landing page on oracle.com](https://www.oracle.com/autonomous-database/)

- [Autonomous Database on Exadata Cloud@Customer - documentation](https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/adbcc-index.html)

- [What's New on Oracle Autonomous Database](https://docs.oracle.com/en/cloud/paas/autonomous-database/dedicated/nfccyy/index.html)

Reviewed: 06/11/26

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
