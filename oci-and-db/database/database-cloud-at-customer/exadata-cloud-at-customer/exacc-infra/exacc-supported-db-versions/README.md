# Exadata Cloud@Customer Supported Database versions

Currently supported versions:

- Oracle AI Database 26ai
- Oracle Database 23ai
- Oracle Database 19c (19.x)
- Oracle Database 12c Release 2 (12.2.0.1) (requires a valid Upgrade Support contract)
- Oracle Database 12c Release 1 (12.1.0.2) (requires a valid Upgrade Support contract)
- Oracle Database 11g Release 2 (11.2.0.4) (requires a valid Upgrade Support contract)

## Support for legacy Database releases

**According to the current status, from the 31st of December, 2026, the cloud automation support for ALL Legacy Database Releases will be suspended. This applies for all 11.2.04, 12.1.0.2 or 12.2.0.1 Databases.** 

18c version is already completely unsupported.

Please note, that currently for creation and operating versions below 19c you need to have a valid Upgrade Support contract (formerly Market Driven Support) and an approval from Product Management. We are encouraging everyone to engage in a discussion as early as possible to upgrade these Databases. 

For guidance please refer to the MOS notes linked below and for the Legacy Support Einstein note, which is getting updated regularly. As of 31st of December, 2026 it won't be possible to create a new Database environment with these versions using the cloud tooling.

If we were running legacy versions without upgrade support in 2025 or keep running those in 2026, dbaascli is the only tool, that can be used to manage those environments. Furthermore, there is no guarantee, that future upgrades of the underlying infrastructure are not introducing unexpected behaviors for these Database environments after 31st of December, 2026. There is no official published end date when existing legacy DBs will stop working.

Recent information indicates that in CY27, the Exadata storage server software will be upgraded to a version that is incompatible with any pre-19c Oracle Database release. The upgraded storage software will no longer include compatibility code pre-19c database behaviors. As a result, key Exadata “smart” features (for example, Smart Scan, Storage Indexes, and Columnar Cache) will not operate with pre-19c databases. In that scenario, the storage servers would fall back to block mode, which could lead to a significant performance degradation.

We don’t yet have confirmed dates, but this is expected to occur at some point during CY27 as part of the quarterly infrastructure maintenance cycle. Customers will be able to defer the update by up to 180 days from their previous maintenance window.

# Useful Links

- [Introducing Oracle AI Database 26ai](https://blogs.oracle.com/database/oracle-announces-oracle-ai-database-26ai)

- [Oracle Exadata Database Service on Cloud@Customer Service Description](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-system-config-options.html#GUID-D35869C4-7F3F-423A-A498-1E74A4BD5F0C)

- [Release Schedule of Current Database Releases (Doc ID 742060.1) MOS note](https://support.oracle.com/epmos/faces/DocContentDisplay?id=742060.1)

- [Patching Guidelines for 18c and lower Database versions on ExaDB-C@C (Doc ID 2997504.1) MOS note](https://support.oracle.com/epmos/faces/DocumentDisplay?_afrLoop=461464200650747&id=2997504.1&_adf.ctrl-state=cpak90hw7_252)

Reviewed: 06/29/26

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
