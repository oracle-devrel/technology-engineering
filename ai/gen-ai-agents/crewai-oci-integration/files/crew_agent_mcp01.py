"""
CrewAI agent with MCP

This one is doing Deep research using internet search tools via MCP server.

see: 
    https://docs.crewai.com/en/mcp/overview
    https://docs.crewai.com/en/mcp/multiple-servers
"""
import os
from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter

# Disable telemetry, tracing, and logging
os.environ["CREWAI_LOGGING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

llm = LLM(
    model="grok4-fast-oci",
    # LiteLLM proxy endpoint
    base_url="http://localhost:4000/v1",
    api_key="sk-local-any",
    temperature=0.2,
    max_tokens=4000,
)

server_params = {
    "url": "http://localhost:8500/mcp",
    "transport": "streamable-http"
}

# Create agent with MCP tools
with MCPServerAdapter(server_params, connect_timeout=60) as mcp_tools:
    print(f"Available tools: {[tool.name for tool in mcp_tools]}")

    research_agent = Agent(
        role="Research Analyst",
        goal="Find and analyze information using advanced search tools",
        backstory="Expert researcher with access to multiple data sources",
        llm=llm,
        tools=mcp_tools,
        verbose=True
    )

    # Create task
    research_task = Task(
        description="Research the latest developments in AI agent frameworks",
        expected_output="Comprehensive research report with citations",
        agent=research_agent
    )

    # Create and run crew
    crew = Crew(agents=[research_agent], tasks=[research_task])
    
    result = crew.kickoff()

    print(result)