# 📄 Document Understanding with LLMs

A Streamlit-based app comparing and expanding on traditional Document Understanding (OCI DU) + LLM approach vs. a multimodal LLM for extracting structured data from documents (PDFs, images).
This is is aimed at highlighting the strengths of each of our services and the power GenAI brings in combining these approaches for the best handling of complex documents.

<img src="./image.png">
</img>

Reviewed date: 22.09.2025

---

## 🔧 Features

- **DU + LLM pipeline**:  
  OCR via OCI Document Understanding + metadata extraction using a structured LLM approach.

- **Multimodal LLM pipeline**:  
  Sends the document image directly to a multimodal LLM for field extraction.

- **Compare results**:  
  The app displays both pipelines' outputs side-by-side along with a comparison table.

---
## 👥 Who Can Use This

- **Developers / Machine Learning Engineers**  
  Looking to automate data extraction from PDFs and images with minimal setup.

- **Business Analysts / Finance Professionals**  
  Extract structured information (invoice number, total, date, etc.) from documents without manual data entry.

- **Data Engineers / Architects**  
  Integrate document extraction into data pipelines for reporting, archiving, or analytics systems.

- **Anyone using OCI AI Services**  
  Already working within Oracle Cloud Infrastructure and wanting streamlined document processing.

---

## 🗂️ Files & Structure
.
├── doc_llm.py # Main Streamlit app
├── requirements.txt # Project dependencies
├── config.py # OCI credentials & config (you must create)
└── README.md


---

## ⚙️ Setup & Installation

### 1. Clone the repo  
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Create config.py in the root directory
Populate it with your OCI and model credentials:
```bash
# config.py
COMPARTMENT_ID = "<your OCI compartment OCID>"
MODEL_ID       = "<your OCI model OCID>"
```
(OCI config file, e.g. ~/.oci/config, will be auto-detected if present)

### 3. Install dependencies  
```bash
pip install -r requirements.txt
```
---

# 🚀 Run the App

```bash
streamlit run doc_llm.py
```
1. Use the sidebar to enter three fields you want to extract (e.g., "Invoice Number", "Date", "Total").
2. Upload a PDF or image containing the document.
  - The app will process the document using:
  - OCI DU + structured LLM extraction
3. Direct multimodal LLM extraction
4. View their outputs side-by-side and inspect the JSON comparison.
---

# 🛠️ How to use this asset

- Adjust max_tokens, temperature, or model_id parameters in ChatOCIGenAI calls (du_extractor() and llm_extractor()).
- Extend the compare_outputs() logic to handle more fields or nested JSON structures.
- Though optimized for invoice-like documents, you can extract any structured data by simply changing the sidebar field inputs.

# 📝 Example

- **Sidebar inputs:**
```bash
Field 1 → Invoice Number  
Field 2 → Date  
Field 3 → Total Amount
```
- **Sample JSON comparison output:**
```bash
{
  "Invoice Number": "0001234",
  "Date": {
    "DU + LLM": "2025-07-15",
    "Multimodal LLM": "2025-07-14"
  },
  "Total Amount": "1,250.00 AED"
}
```
---
## 🔧 OCI Services Used & Documentation

This project leverages two core Oracle Cloud Infrastructure AI services:

### 1. OCI Document Understanding  
- Used for OCR and structural extraction (text, tables, key/value fields)  
- Accessed via the Python SDK:  
  ```python
  from oci.ai_document import AIServiceDocumentClient
  ```
- Official docs:
    - Service overview & getting started: https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/home.html
### 2. OCI Generative AI (ChatOCIGenAI)
- Used as a multimodal LLM to extract and format data from images
- Accessed via LangChain integration:
    ```bash
    from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
    ```
- Documentation:
    - Service overview: https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm
---

# 📄 License

Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

