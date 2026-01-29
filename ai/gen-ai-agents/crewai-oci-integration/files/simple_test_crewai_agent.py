"""
Test CrewAI with LiteLLM and OCI Generative AI
"""

import os
from crewai import Agent, Task, Crew, LLM

# Disable telemetry, tracing, and logging
os.environ["CREWAI_LOGGING_ENABLED"] = "false"
os.environ["CREWAI_TELEMETRY_ENABLED"] = "false"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Configure the LLM (Grok model served via LiteLLM proxy on OCI)
print("\n=== CONFIGURING LLM ===")

llm = LLM(
    model="grok4-fast-oci",
    # LiteLLM proxy endpoint
    base_url="http://localhost:4000/v1",
    api_key="sk-local-any",
    temperature=0.2,
    max_tokens=4000,
)

# Define the agent
print("=== DEFINING AGENT ===")
researcher = Agent(
    role="Researcher",
    goal="Analyze documents and synthesize insights.",
    backstory="Expert in enterprise Generative AI.",
    llm=llm,
)

# Define the task assigned to the agent
print("=== DEFINING TASK ===")
task = Task(
    description="Summarize in 10 bullet points the pros and cons of using LiteLLM with OCI Generative AI.",
    expected_output="A 10-bullet summary, clear and non-redundant.",
    agent=researcher,
)

# Create the crew (collection of agents and tasks)
print("=== CREATING CREW ===")
crew = Crew(agents=[researcher], tasks=[task])

# Execute the crew and print the result
print("")
print("\n=== EXECUTING CREW ===\n")

result = crew.kickoff()

print("\n=== CREW RESULT ===\n")
print(result)
