# Select AI Getting Started - Proxy Integration
 
Use this asset as a reference for getting started with the Select AI Proxy Integration capabilities available within the Oracle AI Database. More specifically, we will take a look at setting up the Proxy Integration against a PostgreSQL database.

Reviewed: 2026.04.30
 

# When to use this asset?

Use this asset as a reference for getting started with the Select AI Proxy Integration capabilities available within the Oracle AI Database. More specifically, we will take a look at setting up the Proxy Integration against a PostgreSQL database.

Select AI runs natively inside Oracle Autonomous AI Database and Oracle AI Database, both of which can operate as an AI proxy database, also referred to as "sidecar". An AI proxy database can support both local and external data sources (on-premises, cloud, or third-party). Using standard Oracle federation mechanisms such as Database Links, Cloud Links, Table Hyperlinks, and Federated Tables, Select AI generates federated SQL from natural language prompts using metadata across Oracle and non-Oracle systems.

Autonomous AI Database hosts act as a central metadata and processing layer for both local and external data sources. The AI proxy database controls distributed query processing while external systems remain authoritative for their data.

An AI proxy database is an Autonomous AI Database instance that runs Select AI on behalf of local or external data sources. It does not contain the external data. Instead, it uses metadata exposed through local database objects (tables and views) that reference remote data sources such as views defined on Database Links or Cloud Links, External Tables over Table Hyperlinks, and Federated Tables to interpret natural language requests and generate SQL that runs across distributed systems. The AI proxy database can also contain local data in its own schema.

**Note** - Please refer to "00-getting-started-setup-guide" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.

# How to use this asset?

This asset is provided as general purpose material. Please tailor the content according to your context and needs.

This asset contains two versions of the same script, a SQL Script (`.sql`) to be used with an IDE such as SQLDeveloper Web or the VS Code Extension, and an OML Notebook (`.dsnb`) which can be used within the Oracle Machine Learning UI available through the Autonomous Oracle AI Database. Please use the version that is appropriate for your development environment.


# License
 
Copyright (c) 2026 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
