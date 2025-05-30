# Creating Metric Extensions for Oracle Database using OCI Database Management Service

Metric extensions are useful when the metric you are looking for does not exist out of the box. In such cases, you can create your own custom metric and use it for monitoring your database.

This guide explains how to create metric extensions step by step.

## What Are Metric Extensions?

**Metric extensions** are custom, user-defined, SQL-based metrics collected by OCI Database Management. They supplement standard metrics, providing additional insights (for example, error counts, job statuses, or resource KPIs not tracked by default).

## Note
[Metric extensions](https://docs.oracle.com/en-us/iaas/database-management/doc/work-metric-extensions.html#DBMGM-GUID-6D5E80AA-ABA5-4FBA-A63F-106CEE39C3F7) are currently available **only for External Databases**. Therefore, if your database is an OCI database (as in this case, Oracle Base Database), it must be registered in Database Management as an External Database.

## Prerequisites

- OCI tenancy with Database Management enabled.
- Target Oracle Database registered in Database Management as an [External Database](https://docs.oracle.com/en-us/iaas/database-management/doc/external-database-related-prerequisite-tasks.html#DBMGM-GUID-84B74F18-F672-4DDC-8505-ACF249293D64).
- Required [policies](https://docs.oracle.com/en-us/iaas/database-management/doc/perform-general-oracle-cloud-infrastructure-prerequisite-tasks.html#DBMGM-GUID-DCC3067D-5123-468E-A938-D310CC685674) in place.

## Step-by-Step Guide

See [Implementation Steps](./create_metric_extension.md) for details.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.