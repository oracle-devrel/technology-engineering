# ODA Multi-Agent samples

## Installation
Please import the sample below in your ODA 
- Llm1
     - contains a agent calling tools
- LlmHistory1
     - contains an agent calling tools
     - and history of conversation
- RagHoliday
     - contains an agent calling other agent
- Unity
     - contains an supervisor that calls other agents
- LLamaProd
     - contains an supervisor that calls other agents
     - translation

## Configuration
Be sure to import the Weather API before to import the Skills.

## Known issue
- RagHoliday and LLamaProd use a RAG agent (you need an OCI RAG agent ocid to use it)
- LLamaProd needs more rest API to work fully. One of them is a RAG agent (you need an OCI RAG agent ocid to use it)
