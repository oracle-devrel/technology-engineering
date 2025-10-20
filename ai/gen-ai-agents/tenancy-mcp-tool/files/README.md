# MCP Server and Agent to Explore OCI Tenancies

This asset shows how to set up a simple MCP server to interface with an OCI
tenancy, and how to integrate this with a simple agent.

## Requirements

When deploying this demo on your local machine, the requirements are fairly basic:

- Access to the OCI Generative AI service
- A configuration file for the OCI SDK as per
  instructions](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm)
- Python and [`uv`](https://docs.astral.sh/uv/) or another Python package manager

## Setup

1. Set up a virtual environment, for example with `uv`:
   ```console
   uv venv
   uv pip install -r requirements.txt
   ```
   The resulting virtual environment will be in `.venv` in the local directory.
2. Run the application:
   ```console
   uv run streamlit run agent.py
   ```
   This should open a page with the agent in your browser. Alternatively,
   Streamlit will also print a link in your terminal to open the application.

## Technical Details

The MCP server is defined in [`oci_mcp_server.py`](./oci_mcp_server.py) and can
be started independently of the agent.  For simplicity, the agent will
automatically start the MCP server.

## Authors

- Omar Salem
- Matthias Wolf

## Contributing

We welcome contributions to improve and expand the capabilities of this demo.
Please fork the repository and submit a pull request with your changes.

## License
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](../LICENSE) for more details.
