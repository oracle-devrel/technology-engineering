"""
Test Semantic Search...
"""

import asyncio
import json
from fastmcp import Client
from jwt_utils import create_jwt_token
import config

ENDPOINT = f"http://localhost:{config.PORT}/mcp/"


async def main():
    """
    Main function to demonstrate the semantic search tool.
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
        print("")
        print("\nCalling semantic_search tool...")
        print("")

        query = "What is Oracle AI Vector Search?"

        results = await client.call_tool(
            "semantic_search",
            {
                "query": query,
                "top_k": 5,
                "collection_name": "BOOKS",
            },
        )

        relevant_docs = json.loads(results[0].text)["relevant_docs"]

        print("--- Query: ", query)
        print("Search Results:")
        print("")
        for doc in relevant_docs:
            print(doc["page_content"])
            print("Metadata:", doc["metadata"])
            print("")


asyncio.run(main())
