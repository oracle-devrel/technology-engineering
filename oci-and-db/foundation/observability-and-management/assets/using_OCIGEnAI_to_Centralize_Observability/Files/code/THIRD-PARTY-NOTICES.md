# Third-party dependencies and publication

This package includes original project integration code and references external dependencies. It does not include a copied upstream MCP repository, dependency environment or container image.

The Dockerfile fetches these projects at the source commits declared in its build arguments:

- [Oracle MCP repository](https://github.com/oracle/mcp), including its common library and OCI Database Observability MCP package. Consult the [upstream license](https://github.com/oracle/mcp/blob/main/LICENSE.txt) at the selected revision.
- [LogAn MCP](https://github.com/rishabh-ghosh24/logan-mcp-server). Consult its license and distribution requirements at the selected revision.

Application dependencies are declared in `pyproject.toml`. The base image, Python packages and upstream MCP dependencies each retain their own licensing obligations. A binary/container distribution must retain required license notices, including those required for OCI SDK and other transitive components. Produce a dependency inventory/SBOM and review the resulting image before distribution.

This notice does not assign a new license to the application or grant rights to third-party material. The publisher must confirm ownership and select an appropriate application license before public release.
