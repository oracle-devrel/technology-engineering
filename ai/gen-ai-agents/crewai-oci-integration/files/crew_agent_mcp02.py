"""
CrewAI agent with MCP

This one is analyzing tenant consumption via MCP server.

see: 
    https://docs.crewai.com/en/mcp/overview
    https://docs.crewai.com/en/mcp/multiple-servers
"""
import os
from datetime import datetime
from crewai import Agent, Task, Crew, LLM
from crewai_tools import MCPServerAdapter

# Disable telemetry, tracing, and logging
os.environ["CREWAI_LOGGING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

llm = LLM(
    model="grok4-oci",
    # LiteLLM proxy endpoint
    base_url="http://localhost:4000/v1",
    api_key="sk-local-any",
    temperature=0.,
    max_tokens=4000,
)

# OCI consumption
server_params = {
    "url": "http://localhost:9500/mcp",
    "transport": "streamable-http"
}

# Create agent with MCP tools
with MCPServerAdapter(server_params, connect_timeout=60) as mcp_tools:
    print(f"Available tools: {[tool.name for tool in mcp_tools]}")

    research_agent = Agent(
        role="OCI Consumption Analyst",
        goal="Find and analyze information about OCI tenant consumption.",
        backstory="Expert analyst with access to multiple data sources",
        llm=llm,
        tools=mcp_tools,
        max_iter=30,
        max_retry_limit=5,
        verbose=True
    )

    # Create task
    research_task = Task(
        description="Identify the top 5 compartments by consumption (amount) for the OCI tenant "
        "in the  weeks of the month of september 2025, analyze the trends and provide insights on usage patterns."
        "Analyze fully the top 5 compartments. Use only the amount, not the quantity.",
        expected_output="Comprehensive report with data-backed insights.",
        agent=research_agent
    )

    # Create and run crew
    crew = Crew(agents=[research_agent], tasks=[research_task])
    
    result = crew.kickoff()

    print(result)

    # --- Save the result to a Markdown file ---
    # Create an output directory if it doesn’t exist
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)

    # Use timestamped filename for clarity
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"oci_consumption_report_{timestamp}.md")

    # Write the result
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(result))

    print(f"\n✅ Report saved successfully to: {output_path}")