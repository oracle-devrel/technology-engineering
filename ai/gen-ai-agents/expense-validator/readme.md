# Expense Validator Agent

Expense Validator Agent is an AI-powered assistant that automates employee expense claim validation.  
It extracts structured data from uploaded PDFs, checks policy compliance, detects category mismatches, and compares declared amounts with expenses (invoice) total cost.  
It runs as an interactive Streamlit app backed by a LangGraph-based workflow and Oracle GenAI models.

Reviewed: August 20, 2025

# When to use this asset?

Use this asset when you want to:
- Extract structured fields (employee name, items, total) from PDF invoices  
- Automatically check claims against internal policy  
- Validate if item categories are consistent and logical  
- Compare declared amount with invoice total  
- Demonstrate step-by-step document validation using OCI GenAI  

Ideal for:
- AI engineers building automated compliance tools  
- Finance/HR teams processing reimbursements  
- OCI customers integrating GenAI into expense workflows  
- Anyone showcasing LangGraph + PDF-based validation agents  

# How to use this asset?

This assistant can be launched via:
- Streamlit UI  

It supports:
- PDF uploading and expense extraction  
- Backend amount cross-check  
- Multi-step validation: policy, category, and total  
- Visual feedback and structured validation messages  
- Stateless interaction per submission  

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

### Start the Validator

Streamlit UI:
```bash
streamlit run frontend.py
```

You will see a clean interface where you can upload a PDF, enter a declared amount, and get a full validation report.

## Key Features

| Tool                        | Description                                                                 |
|-----------------------------|-----------------------------------------------------------------------------|
| PDF Upload                  | Load a PDF expense receipt for processing                                  |
| Declared Amount Input       | Specify the expected total for backend comparison                         |
| LLM-Based Extraction        | Extracts structured fields like name, date, items, and total               |
| Policy Check                | Uses OCI GenAI to validate conformance to internal policy rules            |
| Category Check              | Flags mismatched expense categories using LLM reasoning                    |
| Declared vs Invoice Check   | Compares declared and extracted totals, highlights discrepancies           |
| LangGraph Workflow          | Modular nodes for extraction, validation, and result compilation           |
| Error Handling              | Shows clear messages when input is invalid or unprocessable                |

## Notes

- Prompts can be easily edited to reflect real policy documents  
- Designed to run with Oracle Cloud Infrastructure + Generative AI
- Example expense documents are in /Expenses.

## Prompt Customization

You can modify:
- The extraction prompt  
- The policy checking logic  
- The category verification question  

These control the agent’s reasoning behavior and result formatting.

# Useful Links (Optional)

- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)  
  Official documentation for Oracle Generative AI

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.


