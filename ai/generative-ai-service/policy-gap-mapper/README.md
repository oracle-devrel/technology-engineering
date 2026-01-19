# Policy Gap Mapper

*A Streamlit-based compliance application that uses Oracle Document Understanding (DU) and Generative AI to analyze regulatory documents and internal policies, identify coverage gaps, and produce structured gap analysis outputs.*

Author: Ali Ottoman
Reviewed: 05.12.2025

# When to use this asset?

*This asset is used when organizations need to assess whether internal policies adequately cover external regulatory obligations.*

### Who
- Compliance and risk management teams  
- Internal audit and governance teams  
- Legal and regulatory affairs teams  
- Digital transformation teams modernizing compliance workflows  

### When
- New regulations must be assessed against existing internal policies  
- Periodic compliance reviews or audits are required  
- Manual obligation-to-control mapping is time-consuming  
- A structured, repeatable gap analysis process is needed  

# How to use this asset?

*The asset is deployed as a Streamlit application that guides users through uploading documents, extracting obligations and controls, and reviewing coverage gaps.*

### Application Workflow
1. Upload regulatory documents and internal policy documents (PDF, JPG, PNG).
2. Text is extracted from all documents using **OCI Document Understanding**.
3. An LLM breaks regulations into **atomic, testable obligations**.
4. The LLM extracts **control statements** from internal policies.
5. Obligations are mapped to controls and coverage is scored.
6. Review the interactive gap analysis results.
7. Download the coverage gap report as a CSV file.

### Key Capabilities
- End-to-end DU + LLM pipeline hosted on OCI  
- Obligation extraction enriched with:
  - obligation text  
  - article reference  
  - category  
  - criticality  
  - keywords  
- Control extraction enriched with:
  - control text  
  - control type  
  - owner department  
  - keywords  
- Automated obligation-to-control mapping with coverage scoring  

### File Structure
```
.
├── files/
│   ├── policy_gap_mapper.py
│   └── config.py
├── requirements.txt
└── README.md
```

### Setup
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

Configure OCI credentials in `~/.oci/config` and set the following in `config.py`:
```python
COMPARTMENT_ID = "<your-compartment-ocid>"
MODEL_ID = ["meta.llama-4-maverick-17b-128e-instruct-fp8"]
```

Run the application:
```bash
streamlit run policy_gap_mapper.py
```

---
# Useful Links
- OCI Document Understanding  
  - https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/home.htm  
- OCI Generative AI Service  
  - https://www.oracle.com/ae/artificial-intelligence/generative-ai/generative-ai-service/  

# License

Copyright (c) 2026 Oracle and/or its affiliates.  
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
