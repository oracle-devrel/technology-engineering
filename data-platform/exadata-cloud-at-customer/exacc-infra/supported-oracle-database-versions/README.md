# Supported Oracle Database versions

As of 2nd of May, 2024, Oracle Database 23ai is available on Exadata Database Service on Cloud@Customer (ExaDB-C@C / Gen2). Please note that, you need to have grid infrastructure version 23.1.x or later to be able to create 23ai Database environments. The 23.1.x grid infrastructure version is only available with Oracle Linux 8 and it is backward compatible with the previous Gen2 ExaCC versions. Please check the Exadata Cloud Service Software Versions (Doc ID 2333222.1) MoS note for supported Database and Grid infrastructure versions.

The currently supported Oracle Database versions are listed in the Service Description part of the ExaCC documentation.

These are currently:

- [Oracle Database 23ai]
- [Oracle Database 19c (19.x)]
- [Oracle Database 12c Release 2 (12.2.0.1) (requires a valid Upgrade Support contract)]
- [Oracle Database 12c Release 1 (12.1.0.2) (requires a valid Upgrade Support contract)]
- [Oracle Database 11g Release 2 (11.2.0.4) (requires a valid Upgrade Support contract)]

# Support for legacy Database releases

**From 31st of December, 2024, the cloud automation support for ALL Legacy Database Releases will be suspended. This applies for all 11.2.04, 12.1.0.2 or 12.2.0.1 Databases.** 

18c version is already completely unsupported.

Please note, that currently for creation and operating versions bellow 19c you need to have a valid Upgrade Support contract (formerly Market Driven Support) and an approval from Product Management. **We are encouraging everyone to engage in a discussion as early as possible to upgrade these Databases.** In 2024 it is not feasible anymore to try to deploy new workloads on ExaCC with these legacy Database versions. 

For guidance please refer to the MoS notes linked below. As of 31st of December, 2024 it won't be possible to create a new Database environment with these versions using the cloud tooling.

If we were running legacy versions without upgrade support in 2024 or keep running those in 2025, dbaascli is the only tool, that can be used to manage those environments. Furthermore, there is no guarantee, that future upgrades of the underlying infrastructure are not introducing unexpected behaviours for these Database environments after 15th of January, 2025. There is no official published end date when existing legacy DBs will stop working.

# Useful Links

- [Oracle Database 23ai Now Available in Cloud blog post](https://blogs.oracle.com/database/post/oracle-database-23ai-now-available-in-the-cloud)
- [Oracle Exadata Database Service on Cloud@Customer Service Description](https://docs.oracle.com/en/engineered-systems/exadata-cloud-at-customer/ecccm/ecc-system-config-options.html#GUID-D35869C4-7F3F-423A-A498-1E74A4BD5F0C)
- [Release Schedule of Current Database Releases (Doc ID 742060.1) MoS note](https://support.oracle.com/epmos/faces/DocContentDisplay?id=742060.1)
- [Patching Guidelines for 18c and lower Database versions on ExaCC (Doc ID 2997504.1) MoS note](https://support.oracle.com/epmos/faces/DocumentDisplay?_afrLoop=461464200650747&id=2997504.1&_adf.ctrl-state=cpak90hw7_252)
- [Exadata Cloud Service Software Versions (Doc ID 2333222.1) MoS note](https://support.oracle.com/epmos/faces/DocumentDisplay?id=2333222.1&displayIndex=6#aref_section21)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
