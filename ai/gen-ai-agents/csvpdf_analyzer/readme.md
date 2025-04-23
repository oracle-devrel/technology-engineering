# CSV Analyzer Agent

CSV Analyzer Agent is an AI-Agent assistant designed to automate document understanding and analysis.  
It intelligently routes user questions through a multi-step process that includes PDF information extraction, CSV data analysis, code generation, execution, and natural language explanation.  
It supports dynamic workflows like PDF parsing, CSV querying, and context-aware reporting through a Streamlit UI.

Reviewed: April 18, 2025

---

# When to use this asset?

Use this asset when you want to:
- Parse and extract information from PDF documents  
- Ask questions about CSV files and receive data-backed answers  
- Automate code generation for data analysis  
- Get human-readable summaries of complex analytics  
- Demonstrate AI-powered multi-modal document analysis in action  

Ideal for:
- AI developers building document understanding tools  
- Oracle Cloud users integrating GenAI into document workflows  
- Data analysts exploring LLM + document orchestration using LangGraph  

---

# How to use this asset?

This assistant can be launched via:
- Streamlit UI  

It supports:
- CSV uploading and querying  
- PDF form parsing and field extraction  
- Secure Python code generation using OCI GenAI  
- Real-time execution and explanation of generated code  
- State-aware multi-turn conversation  

## Setup Instructions

### OCI Generative AI Model (Cohere or LLaMA on OCI)

1. Go to: OCI Console → Generative AI  
2. Select a model like:  
   `meta.llama-3.3-70b-instruct`  
3. Copy the following values:
   - model_id  
   - compartment_id  
   - endpoint (e.g., `https://inference.generativeai.us-chicago-1.oci.oraclecloud.com`)  
4. Paste them in `config.py`  

Documentation:  
[OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

No API key is required — authentication is handled via OCI identity.

Ensure your OCI CLI credentials are configured.  
Edit or create the following config file at `~/.oci/config`:

```
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=c6:4f:66:e7:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

### Start the Chatbot

Streamlit UI:
```bash
streamlit run assistant_ui_langgraph.py
```

You will see a full chat interface with support for uploading CSVs and PDFs, asking questions, and receiving answers backed by the AI Agent (`csv_analyzer_agent.py`).

## Key Features

| Tool                     | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| CSV Upload               | Load a CSV file and analyze it with questions                              |
| PDF Extraction           | Extracts structured fields like title, items, department, justification     |
| Request Routing          | Determines if user input relates to CSV or PDF                              |
| Secure Code Generation   | Uses OCI GenAI to generate Python code to analyze your data                 |
| Security Check           | Prevents execution of harmful code (e.g., delete, drop)                     |
| Code Execution           | Executes LLM-generated Python code safely in a sandboxed context            |
| Answer Generation        | Summarizes execution results into a final natural language response         |
| State Management         | Remembers chat history, extracted information, and uploaded files           |
| Sidebar Display          | Shows PDF structured data and generated code for full transparency          |

## Notes

- Supports both document inputs (CSV + PDF)  
- Uses LangGraph to orchestrate tool routing and execution  
- Modular design — individual tools can be expanded or replaced  
- Streamlit UI provides a fully interactive interface with visual progress and outputs  
- Built to run on Oracle Cloud Infrastructure with native LLM integration  

## Prompt Customization

All core prompts used by the agent are stored in `prompts.py`.

You can easily modify or extend these prompts to change how the agent performs routing, extraction, analysis, and natural language response generation.

The prompt for extraction can be found in `csv_analyzer_agent.py`.

---

# Useful Links (Optional)

- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)  
  Official documentation for Oracle Generative AI
---

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

