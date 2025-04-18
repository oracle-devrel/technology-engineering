CSV Analyzer Agent  
By Omar Salem & Luigi Saetta

CSV Analyzer Agent is an AI-Agent assistant designed to automate document understanding and analysis. 
It intelligently routes user questions through a multi-step process that includes PDF information extraction, CSV data analysis, code generation, execution, and natural language explanation. 
It supports dynamic workflows like PDF parsing, CSV querying, and context-aware reporting through a Streamlit UI.

Reviewed: April 18, 2025

1. Prepare Your Configuration

☁️ OCI Generative AI Model (Cohere/Llama on OCI)  
Go to: OCI Console → Generative AI

Select a model like:  
meta.llama-3.3-70b-instruct

Copy:

- model_id  
- compartment_id  
- endpoint (e.g., https://inference.generativeai.us-chicago-1.oci.oraclecloud.com)

Paste them in `config.py`

Documentation:  
https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm

No API key is required — authentication is handled via OCI identity.

Also ensure your **OCI CLI credentials** are correctly set up. Create or edit the following config file at `config`:

```
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=c6:4f:66:e7:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key.pem
```

2. Start the Chatbot

Streamlit UI  
streamlit run assistant_ui_langgraph.py


You will see a full chat interface with support for uploading CSVs and PDFs, asking questions, and receiving answers backed by the AI Agent (csv_analyzer_agent.py).

3. Key Features

Tool                     | Description  
------------------------|-------------  
CSV Upload              | Load a CSV file and analyze it with questions  
PDF Extraction          | Extracts structured fields like title, items, department, justification from uploaded PDFs  
Request Routing         | Determines if user input relates to CSV or PDF  
Secure Code Generation  | Uses OCI GenAI to generate Python code to analyze your data  
Security Check          | Prevents execution of harmful code (e.g., delete, drop)  
Code Execution          | Executes LLM-generated Python code safely in a sandboxed context  
Answer Generation       | Summarizes execution results into a final natural language response  
State Management        | Remembers chat history, extracted information, and uploaded files  
Sidebar Display         | Shows PDF structured data and generated code for full transparency  

4. Notes

- Supports both document inputs (CSV + PDF)
- Uses LangGraph to orchestrate tool routing and execution
- Modular design — individual tools can be expanded or replaced
- Streamlit UI provides a fully interactive interface with visual progress and outputs
- Built to run on Oracle Cloud Infrastructure with native LLM integration

## Prompt Customization

All core prompts used by the agent are stored in `prompts.py`.

You can easily **modify or extend these prompts** to change how the agent performs routing, extraction, analysis, and natural language response generation.

The prompt for extraction can be found in csv_analyzer_agent.py.

5. License  
Licensed under the MIT License.  
See `LICENSE` for details.

