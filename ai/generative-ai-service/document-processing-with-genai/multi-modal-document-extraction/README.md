# Multi-modal Document Extraction

*This Generative AI service application relies on OCI SDK alongside the new Llama 4 models (Scout and Maverick) to extract data from PDFs (or images) into structured data as JSON.*

Author: Ali Ottoman

Reviewed: 18.09.2025

# When to use this asset?

Developers, data scientists, or ML engineers who need to extract structured JSON from invoices or other document images and want to compare the performance of the new Llama 4 OCI vision models.

# How to use this asset?

1. Open the Streamlit app
2. Upload a PDF or image file
3. In the sidebar, select either **meta.llama-4-scout-17b-16e-instruct** or **meta.llama-4-maverick-17b-128e-instruct-fp8**
4. Wait for processing—JSON output will be displayed when finished

# Setup

To get started, clone the repository, install dependencies, and launch the app:

```bash
git clone <repository-url>
cd <repository-folder>
pip install -r requirements.txt
streamlit run <file_name>.py
```

# Useful Links (Optional)

* [More information on Llama 4 ](https://confluence.oraclecorp.com/confluence/display/EMEACSS/FAQ+for+Generative+AI+Service)

* [Pretrained Foundational Models in Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/pretrained-models.htm)

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
