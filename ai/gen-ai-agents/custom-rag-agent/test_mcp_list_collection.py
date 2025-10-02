"""
Test Semantic Search...
"""

import asyncio
from fastmcp import Client
from jwt_utils import create_jwt_token
from utils import print_mcp_available_tools
import config

ENDPOINT = f"http://localhost:{config.PORT}/mcp/"


# The Client uses StreamableHttpTransport for HTTP URLs
async def main():
    """
    Main function to demonstrate the Semantic Search tool.
    """
    # create the JWT token
    # can pass a user here
    if config.ENABLE_JWT_TOKEN:
        token = create_jwt_token()
        client = Client(ENDPOINT, auth=token)
    else:
        token = ""
        client = Client(ENDPOINT)

    async with client:
        # get the list of available tools
        tools = await client.list_tools()

        print_mcp_available_tools(tools)

        print("")
        print("Calling get_collection tool...")
        print("")

        results = await client.call_tool(
            "get_collections",
            # {"Authorization": token},
        )

        print("List Collections Results:")
        for result in results:
            print("Collection name: ", result.text)
        print()


asyncio.run(main())
