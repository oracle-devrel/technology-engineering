# Oracle AI Database MCP Server Product Scenarios
[//]: # (SQLDev Copilot Integration VSCode & SQLcl MCP Support)

Model Context Protocol is an open protocol which standardizes how applications provide context to LLMs.

Launched in November 2024 by Anthropic, it can be considered as a "USB-C" port for AI applications and, like a USB-C, provides a standardized way to connect AI models to different data sources and tools. To accomplish this, It provides a singular interface to have standard interactions with database, files, business applications, developer tools and more.

MCP has three primary constructs:
- Resources: provide data that an MCP server wants to make available to clients like documents, Database records, API responses, screenshots and images and more;

- Tools: essentially function calls (with input/output arguments) in the MCP which enable servers to expose executable functionality to clients. Through tools, LLMs can interact with external systems, perform computations and take actions in a real world context.

- Prompts:  define reusable prompt templates than can be surfaced by clients to LLMs provide a powerful way to standardize and share common LLM interactions.

In July 2025, Oracle release his first MCP Server Tools supportability with the use of SQL Command Line Interface (SQLcl).
Oracle, since this first adoption have committed to helping organizations bring AI agents and assistants closer to trusted enterprise data.
Oracle provides MCP servers for some of its most popular platforms, including Oracle AI Database, so developers, DBAs, and business users can connect large language models to approved tools and data through the Model Context Protocol.

Oracle ai Database MCP has three deployment models that can be chosen to fit at best customer environment:
- <b>Oracle SQLcl</b> (since version 25.2) for developers and local STDIO environment (test, dev environments);
- <b>OCI Database Tools MCP Server</b> for native-managed Oracle Cloud Infrastructure deployments and HTTPS experience for any Oracle AI Database in the cloud;
- <b>Oracle REST Data Services MCP Server</b> for any HTTPS-secure streaming access

<i><b>SQLcl MCP Mode</i></b>:
Oracle SQLcl version 25.2 extends Oracle SQLcl to support MCP-based communication. It enables you to perform operations, create reports, and run queries on Oracle Database using natural language through AI-powered interactions allowing STDIO-only connection for starting point as Developer and DBAs experience.
Main properties:
- Works with all supported Oracle Database releases (19c, 21c, 23ai) on-prem and in the Cloud (OCI, Azure, AWS, GCP)
- Comes with an offer of Server Tools (SQLcl MCP Server Tools):
  - <i><b>list-connections</b></i>: discovers all saved Oracle DB connections
  - <i><b>connect</b></i>: establishes a connection to DB
  - <i><b>disconnect</b></i>: terminates the current DB connection
  - <i><b>run-sql</b></i>: runs standard SQL queries/DDLs/DMLs and PL/SQL code against DB
  - <i><b>run-sqlcl</b></i>: runs specific SQLcl commands
  - <i><b>schema-information</b></i>: provides insight metadata details about currently connected schema enriching info returned by query executions (from 25.3.1 version)

The SQL Developer Extension for VS Code, from version 25.2 on, offers Oracle SQLcl MCP Server Integration. The extension when install auto-registers our MCP Server for Copilot, making your SQL Developer database connections available for agentic chat requests, including running SQL and PL/SQL against your database.

<i><b>OCI Database Tools MCP Server</i></b>: cloud-based serverless solution that enables you to connect Large Language Models (LLMs) to your Oracle AI database in the Cloud and Multicloud.
Main properties:
- Database Tools MCP Server enables you to connect external AI applications to databases supported by Database Tools Connections;
- Managed deployment, centralized administration, OCI security integration, enterprise-scale access without local infrastructure;
- Comes with the following Toolset to interact with the database:
  - <i><b>Built-in SQL Tools</i></b>: execution of ad-hoc SQL or PL/SQL commands (sql_run, request_status, schema_information);
  - <i><b>Custom SQL Tools</i></b>: enable execution of a predefined, parametrized SQL or PL/SQL commands for repeteable executions;
  - <i><b>Reporting Tools</i></b>: consistent, customizable and reusable SQL Reports for data analysis.

<i><b>ORDS MCP Server</i></b>: Since version 26.2 it supports a streaming HTTPS /mcp endpoint, enabling it to act as a remote MCP server for Oracle Database (on-premise/cloud) for your enterprise deployments.
Main properties:
- Deployment with your Identity Provider supporting OAuth 2.0 JWT Token is required (OCI IAM, MS Entra ID,..);
- Requires ORDS Standalone deployments with direct user database connection pools including a "/mcp" as endpoint (different from ordinary ORDS database pools);
- OAuth2/JWT authentication, automatic client registration for your preferred identity provider, and secure access to authorized schemas;
- Comes with the following set of tools:
  - <i><b>database_list</i></b>: Lists the MCP database connections that the caller is authorized to access;
  - <i><b>schema_informations</i></b>: returns schema metadata for a MCP-authorized database connection;
  - <i><b>sql_run</i></b>: Executes SQL or PL/SQL for an authorized MCP database connection

Reviewed: 26.08.2026

# Team Publications
- [Introducing SQL Developer SQLcl integration in MS VSCode & MCP support for Oracle Database](https://www.youtube.com/watch?v=521GBhrmrmw&t=2s)
- [Unlocking EM and RMAN Catalog data with SQLcl Oracle MCP Server AI Bridge - Medium article](https://medium.com/@umutnazlica/unlocking-oracle-enterprise-manager-and-rman-catalog-data-with-oracle-mcp-servers-ai-bridge-sqlcl-e05dd4aa01d9)

# Useful Links
- [Oracle MCP Servers](https://www.oracle.com/mcp/#3-added-tab-2)
- [OCI Managed MCP Service for Oracle AI Database](https://blogs.oracle.com/database/gain-agentic-access-to-any-oracle-database-in-the-cloud-with-native-enterprise-grade-managed-mcp-servers-in-oci)
- [ORDS as an MCP Server](https://www.thatjeffsmith.com/archive/2026/07/ords-now-a-streaming-http-mcp-server-for-oracle-database/)
- [Oracle SQLcl MCP Page](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/26.1/sqcug/using-oracle-sqlcl-mcp-server.html)
- [Model Context Protocol - Overview](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Introducing SQL Developer Copilot Integration in Microsoft VSCode & MCP Support for Oracle Database](https://www.youtube.com/watch?v=hj6WoZVGUBg)
- [Introducing MCP Server for Oracle Database](https://blogs.oracle.com/database/post/introducing-mcp-server-for-oracle-database)
- [Jeff Smith AI/MCP Page](https://www.thatjeffsmith.com/ai/)
- [How can Developers and DBAs benefit from MCP Server for Oracle Database?](https://blogs.oracle.com/database/post/how-can-developers-and-dbas-benefit-from-mcp-server-for-oracle-database)
- [What's all the fuss about MCP? See some amazing things that you can really do with SQLcl MCP server](https://www.youtube.com/watch?v=8NNypzsRa0g)
- [Elevating Oracle Database Security for Safer SQLcl MCP Server and Agentic AI Usage](https://medium.com/@thomas.minne/elevating-oracle-database-security-for-safer-sqlcl-mcp-server-and-agentic-ai-usage-1adb976d0f92)
- [Unlocking the Power of Model Context Protocol (MCP) and Oracle Database 23ai: A Step-by-Step Guide](https://www.linkedin.com/pulse/unlocking-power-model-context-protocol-mcp-oracle-database-rao-l2hsf/)
- [Oracle DB Skills](https://github.com/krisrice/oracle-db-skills)
- [Having a go with 100+ new AI Skills for Oracle AI Database](https://www.thatjeffsmith.com/archive/2026/03/having-a-go-with-100-new-ai-skills-for-oracle-ai-database/)
- [Oracle github mcp repo](https://github.com/oracle/mcp/tree/main/src)

# Reusable Assets Overview

## Latest SQLcl Version

- [SQLcl 26.1](https://docs.oracle.com/en/database/oracle/sql-developer-command-line/26.1/sqcug/changes-release-26.1-oracle-sqlcl.html)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.