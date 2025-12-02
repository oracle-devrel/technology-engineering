# SQLDev Copilot Integration VSCode & SQLcl MCP Support

Model Context Protocol is an open protocol which standardizes how applications provide context to LLMs.

Launched in November 2024 by Anthropic, it can be considered as a "USB-C" port for AI applications and, like a USB-C, provides a standardized way to connect AI models to different data sources and tools. To accomplish this, It provides a singular interface to have standard interactions with database, files, business applications, developer tools and more.

MCP has three primary constructs:
- Resources: provide data that an MCP server wants to make available to clients like documents, Database records, API responses, screenshots and images and more;

- Tools: essentially function calls (with input/output arguments) in the MCP which enable servers to expose executable functionality to clients. Through tools, LLMs can interact with external systems, perform computations and take actions in a real world context.  

- Prompts:  define reusable prompt templates than can be surfaced by clients to LLMs provide a powerful way to standardize and share common LLM interactions.

Oracle SQLcl version 25.2 extends Oracle SQLcl to support MCP-based communication. It enables you to perform operations, create reports, and run queries on Oracle Database using natural language through AI-powered interactions.

SQLcl MCP Mode:
- Works with all supported Oracle Database releases (19c, 21c, 23ai) on-prem and in the Cloud (OCI, Azure, AWS, GCP)
- Comes with an offer of Server Tools (SQLcl MCP Server Tools):
  - <i><b>list-connections</b></i>: discovers all saved Oracle DB connections
  - <i><b>connect</b></i>: establishes a connection to DB
  - <i><b>disconnect</b></i>: terminates the current DB connection
  - <i><b>run-sql</b></i>: runs standard SQL queries/DDLs/DMLs and PL/SQL code against DB
  - <i><b>run-sqlcl</b></i>: runs specific SQLcl commands
  - <i><b>schema-information</b></i>: provides insight metadata details about currently connected schema enriching info returned by query executions (from 25.3.1 version)  

The SQL Developer Extension for VS Code 25.2 offers Oracle SQLcl MCP Server Integration. The extension when install auto-registers our MCP Server for Copilot, making your SQL Developer database connections available for agentic chat requests, including running SQL and PL/SQL against your database.


Reviewed: 12.12.2025


# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)


# Team Publications
- [Introducing SQL Developer SQLcl integration in MS VSCode & MCP support for Oracle Database](https://www.youtube.com/watch?v=521GBhrmrmw&t=2s)

# Useful Links
- [Model Context Protocol - Overview](https://modelcontextprotocol.io/docs/getting-started/intro)
- [Introducing SQL Developer Copilot Integration in Microsoft VSCode & MCP Support for Oracle Database](https://www.youtube.com/watch?v=hj6WoZVGUBg)
- [Introducing MCP Server for Oracle Database](https://blogs.oracle.com/database/post/introducing-mcp-server-for-oracle-database)
- [AI/MCP Page](https://www.thatjeffsmith.com/ai/)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
