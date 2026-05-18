"""
This is an MCP Server that provides Internat Search capabilities.
"""

from typing import Dict, Any
from langchain.prompts import PromptTemplate
from langchain_core.messages import HumanMessage

from oci_models import get_llm
from mcp_utils import create_server, run_server

# using OpenAI for Internet Search
MODEL_4_SEARCH = "openai.gpt-4o-search-preview"

PROMPT_TEMPLATE_SEARCH = """
You're an expert researcher.

Provide key points and summaries from credible sources about: {topic}.
"""

mcp = create_server("OCI MCP Internet Search")


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
@mcp.tool
def internet_search(query: str) -> Dict[str, Any]:
    """
    Return the result of Internet Search for
    the provided query.

    Args:
        query (str): the request for Internet Search.

    Returns:
        str: text + the references.

    """
    llm = get_llm(model_id=MODEL_4_SEARCH)

    prompt_search = PromptTemplate(
        input_variables=["topic"], template=PROMPT_TEMPLATE_SEARCH
    ).format(topic=query)

    result = llm.invoke([HumanMessage(content=prompt_search)]).content

    return {"search_result": result}


#
# Run the MCP server
#
if __name__ == "__main__":
    run_server(mcp)
