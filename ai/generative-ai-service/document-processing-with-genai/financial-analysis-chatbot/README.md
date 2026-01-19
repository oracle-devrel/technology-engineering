# 📊 Document Analysis with Graphs  
A Streamlit-based application for extracting insights from financial documents by combining text and visual (chart/image) content using Oracle Generative AI.

This tool enables semantic search, summarization, and financial Q&A by leveraging OCI GenAI services — providing rich context-aware answers grounded in both OCR-extracted text and chart images.

Author: **Ali Ottoman**
Reviewed date: 23.09.2025

---

# When to use this asset?
## 🔧 Features

### Multimodal Financial Document Processing
- Upload PDFs or images of corporate financial documents.
- Extract both **textual data** and **visual elements** (charts, tables, graphs).

### Oracle GenAI-Powered Search & QA
- Embed documents using **Cohere Embed v4.0** via OCI Generative AI.
- Use **Llama 4 Maverick** to answer questions with visual + textual reasoning.
- "Super Searcher" mode rewrites your query with **Command A** for enhanced semantic search.

### Semantic Memory & Chat Interface
- Context-aware responses based on prior conversation.
- Semantic search across vectorized chunks using Qdrant.
- Responses grounded in document context + image evidence.

### Summary & Analytics View
- Summarizes uploaded financial reports into key highlights.
- Understand KPIs, trends, and performance across firm sizes and time periods.

---

## 👥 Who Can Use This

**Finance & Strategy Teams**  
→ Analyze trends, ratios, and balance sheet insights across time with chart references.

**Business Analysts**  
→ Automate exploration of complex PDF documents and balance sheets.

**Developers & AI Engineers**  
→ Explore multimodal document Q&A using OCI’s latest GenAI capabilities.

**Anyone using OCI AI Services**  
→ Seamlessly integrate this workflow into larger OCI-based analytics pipelines.

---

## 🗂️ Files & Structure

```
.  
├── doc_analysis_with_graphs.py  # Main Streamlit app  
├── config.py                    # OCI config & model IDs (user-provided)  
├── requirements.txt            # Python dependencies  
└── README.md                   # You're reading it
```

---
# How to use this asset
## ⚙️ Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Configure OCI Credentials

Fill out the `config.py` file:

```python
# config.py
COMPARTMENT_ID = "<your OCI Compartment OCID>"
```

Ensure you also have an OCI config file (usually at `~/.oci/config`) with proper credentials.

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

---

## 🚀 Run the App

```bash
streamlit run doc_analysis_with_graphs.py
```

---

## 📝 Flow

### 1. Upload your documents  
→ PDFs or images containing **financial reports, charts, balance sheets**

### 2. Ask your question  
→ Examples:
- “What is the change in ROA from 1990 to 2000?”
- “Summarize the key liquidity trends in small firms.”
- “Explain the data in Chart 2a on debt ratios.”

### 3. View responses  
→ AI replies with:
- Financially-grounded insights  
- Visual chart references (axes, values)  
- Source document images  
- NULL if data is unavailable

---

## 🛠️ Customization

- **Enable/disable Super Searcher** to use Command-A for rephrased queries.
- **Change model temperature or token limits** in `ChatOCIGenAI` constructor.
- **Add custom logic** to extend analysis for ratios, ROE, gearing, sector comparison, etc.

---

## 🧠 Example Chat

> **You**: What is the debt-to-assets ratio trend from 1990 to 2000?  
>  
> **AI**:
> - Debt-to-assets ratio declined from **47% in 1990** to **39% in 2000**.  
> - As per **Chart 1a**, small firms saw the sharpest drop post-1997.  
> - The Y-axis shows the ratio (%) and the X-axis is the year.

---

## 🔧 OCI Services Used

### 1. **OCI Generative AI – Embeddings**
- Used for vector search on document content.
```python
from langchain_community.embeddings.oci_generative_ai import OCIGenAIEmbeddings
```

### 2. **OCI Generative AI – LLM (Llama 4 Maverick)**
- Used to extract structured insights from text + images.
```python
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
```

---

## 🔗 Docs & References

- 📘 [OCI Generative AI Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)  
- 📘 [OCI Document Understanding](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/home.htm)  

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
