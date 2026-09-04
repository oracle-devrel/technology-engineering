# Direct to Target Table Loading in SQL*Loader with Oracle Data Integrator

Reviewed: 08.07.2026

This post is a continuation of [Automated Parallelism with SQL-Loader and ODI post](https://github.com/oracle-devrel/technology-engineering/tree/main/oci-and-db/database/data-integration/shared-assets/parallel-sqlloader-odi-aidatabase26)
First version of the custom SQL*Loader Knowledge Module focused on bringing Oracle AI Database 26ai client automatic parallelism into ODI.
This improved version adds a second major capability: direct target table loading.
With this KM, ODI can now use SQL*Loader in two ways:
- Load directly into the target table for fast, simple, high-volume file loads.
- Load into a temporary work table when the mapping needs transformations, joins, validation, or more complex integration logic.

## How to use this asset?
This blog post explains steps to utilize direct to target table loading via a new custom [Knowledge Module](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/database/data-integration/shared-assets/parallel-sqlloader-odi-aidatabase26/files/KM_LKM_File_to_Oracle__SQLLDR__Plus.xml) which can be downloaded from files subfolder.

[Link to full blog post in Medium](https://medium.com/@hncelebi/direct-target-loads-with-sql-loader-in-oracle-data-integrator-16b07d23b267)


# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/database/data-integration/shared-assets/parallel-sqlloader-odi-aidatabase26/LICENSE) for more details.