# FOCUS™ Support for OCI

# What is this asset?

This asset explains FOCUS™ support for OCI and its role in a consistent multi-cloud cost-data model.

# How to use this asset?

Use this guidance to understand how FOCUS™ can normalize OCI cost and billing data for multi-cloud reporting.

# How FOCUS™ works with OCI

FOCUS™ is a technical specification for a consistent multi-cloud experience. It enables customers to access cost, billing, and related data in a normalized, cloud-provider-agnostic format. The specification also encompasses SaaS services.

FOCUS™ specifications are available in the [FOCUS Specification repository](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec). Dedicated converters are developed for each cloud provider; their progress is available in the [FOCUS converters repository](https://github.com/finopsfoundation/focus_converters/blob/dev/progress/README.md).

The converters produce Parquet output, which allows data from different providers to be imported into Autonomous Database and [queried](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/autonomous-database-serverless/doc/query-external-parquet-avro.html). An OCI-specific converter configuration is available in the [FOCUS converters repository](https://github.com/finopsfoundation/focus_converters/tree/dev/focus_converter_base/focus_converter/conversion_configs/oci).

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
