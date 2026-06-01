# Overview

This notebook demonstrates how to use **Oracle Agent Memory** for managing and retrieving conversational memory in AI applications.

The notebook includes:

* An overview of how memory is structured and managed within Oracle Agent Memory
* An end-to-end example demonstrating how to use the OAM API, including setup and configuration steps
* Practical examples of creating, storing, retrieving, and managing memory objects

This notebook does not cover agent creation. Instead, it focuses on using Large Language Models (LLMs) to explore and demonstrate Oracle Agent Memory capabilities and API usage.

# Environment

Conda environment: python3 (ipykernel)

Created: 15/05/2026

# Prerequisites
* Access to an Oracle Database 26ai instance with Oracle Agent Memory enabled
* Installation of the oracleagentmemory Python package
* Access to at least one LLM model and one embedding model from the supported model list: https://docs.oracle.com/en/database/oracle/agent-memory/26.4/agmea/get-started.html#GUID-1DC2BEC9-4CAF-4668-BBBB-E9FC57C7E71E
* Authentication and connectivity configuration for the Oracle Database 26ai instance, including:
    - Database username, password, and connection string (DSN)
    - Wallet file for mTLS network configuration (if Mutual TLS (mTLS) authentication is enabled or required)
    - OCI configuration file when running from a local environment and accessing OCI-hosted models

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
