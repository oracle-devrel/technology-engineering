# ODA Multi-Agent samples

Reviewed: 22.09.2025

Author: Marc Gueury

## Installation

See Livelab: AI Agents with ODA: Simple Agent to advanced Multi-Agent Supervisors

https://livelabs.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=4212

## Import

Please import the samples in the *files* directory in your ODA 
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
Be sure to import the Weather API and mgLlama API (Type LLM Service) before to import the Skills.

## Add policies like this to allow ODA to call GenerativeAI

```
allow any-user to manage genai-agent-family in tenancy where request.principal.id='<ODA OCID>'
allow any-user to manage generative-ai-family in tenancy where request.principal.id='<ODA OCID>'
```
or
```
allow any-user to manage genai-agent-family in compartment xxx where request.principal.id='<ODA OCID>'
allow any-user to manage generative-ai-family in compartment xxx where request.principal.id='<ODA OCID>'
```

## Known issue
- RagHoliday and LLamaProd use a RAG agent (you need an OCI RAG agent ocid to use it)
- LLamaProd needs more rest API to work fully. One of them is a RAG agent (you need an OCI RAG agent ocid to use it)
