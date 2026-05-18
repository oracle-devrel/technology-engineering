"""
MCP server config
"""

MCP_SERVERS_CONFIG = {
    "default": {
        "transport": "streamable_http",
        "url": "http://localhost:9000/mcp/",
    },
    "oci-semantic-search": {
        "transport": "streamable_http",
        "url": "http://localhost:9000/mcp/",
    },
}
