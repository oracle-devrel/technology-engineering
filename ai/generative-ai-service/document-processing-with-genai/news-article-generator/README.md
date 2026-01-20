# 📰 News Article Generator (Style-Mimic) — OCI GenAI  
A Streamlit-based application for generating newsroom-quality articles from a headline + key facts, while mimicking the tone and structure of your own writing samples using Oracle Generative AI.

This tool lets you upload one or more `.txt` sample articles you wrote before, extracts a compact “style guide”, and then generates a fresh article in the same voice — outputting **TXT**, **Markdown**, and **JSON** formats.

Author: **Ali Ottoman**

Reviewed date: 14.01.2026

---
# When to use this asset
## 🔧 Features

### Headline + Key Facts → Full Article
- Provide a **headline** and **key facts** (bullet points).
- Generates a complete news article with a clear lede, body, and key points.

### Tone & Style Mimic (from your samples)
- Upload **1+ TXT sample articles** you wrote previously.
- App extracts a compact **style guide** (tone, phrasing, structure) and applies it to the new article.
- Works well for **Arabic** and English.

### Multi-format Output (Downloadable)
- Generates and allows download of:
  - **.txt** (plain text)
  - **.md** (markdown)
  - **.json** (structured output for downstream pipelines)

### Safety & Consistency Guardrails
- Instructs the model to use **only your provided facts** (no fabricated dates/names/quotes).
- Enforces **strict JSON-only** output for reliable parsing and file generation.

---

## 👥 Who Can Use This

**PR & Communications Teams**  
→ Draft press-style articles quickly while preserving consistent brand voice.

**News & Content Writers**  
→ Generate first drafts that match your established writing tone and structure.

**Marketing Teams**  
→ Turn bullet-point announcements into polished stories, blog-style posts, or newsroom updates.

**Developers & AI Engineers**  
→ Use structured JSON output for publishing workflows, CMS integrations, or RAG pipelines.

---

## 🗂️ Files & Structure

```
.  
├── news_generator.py                # Main Streamlit app  
├── requirements.txt      # Python dependencies  
└── README.md             # You're reading it
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

This app uses OCI API key auth via your local OCI config (typically at `~/.oci/config`).

Ensure your OCI config is set up correctly, then set these environment variables (recommended):

```bash
export OCI_GENAI_ENDPOINT="https://inference.generativeai.<region>.oci.oraclecloud.com"
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxxx"
export OCI_PROFILE="DEFAULT"
export OCI_MODEL_ID="cohere.command-a"
```

> Note: `OCI_MODEL_ID` should match the Cohere Command A model identifier available in your OCI GenAI tenancy/region.

### 3. Install Requirements

```bash
pip install -r requirements.txt
```

---

## 🚀 Run the App

```bash
streamlit run news_generator.py
```

---

## 📝 How to Use

### 1. Provide your inputs  
- **Headline** (Arabic or English)
- **Key facts** as bullet points (recommended: keep Arabic facts in Arabic for consistency)

### 2. Upload style samples (optional but recommended)  
Upload **1+ .txt** files containing your past articles.  
The app will infer tone and structure and reuse it.

### 3. Generate and download  
The app produces:
- Markdown preview
- Plain-text output
- JSON output  
And provides download buttons for **.md / .txt / .json**

---

## 🧠 Example Inputs (Arabic)

**Headline**  
إطلاق منصة رقمية جديدة لتعزيز كفاءة الخدمات الحكومية في دولة الإمارات

**Key facts**
- أعلنت جهة حكومية اتحادية في دولة الإمارات عن إطلاق منصة رقمية جديدة.
- تهدف المنصة إلى تحسين كفاءة وجودة الخدمات الحكومية المقدمة للمواطنين والمقيمين.
- تعتمد المنصة على تقنيات الذكاء الاصطناعي وتحليل البيانات لأتمتة الإجراءات.
- تتيح المنصة إنجاز المعاملات الحكومية بشكل أسرع وتقليل الحاجة إلى زيارة مراكز الخدمة.
- سيتم تطبيق المنصة بشكل تدريجي على عدد من الخدمات خلال المرحلة الأولى.
- أوضحت الجهة المطورة أن المنصة تراعي أعلى معايير أمن المعلومات وحماية البيانات.

---

## 🛠️ Customization

- **Control length**: add a selector (short/medium/long) and pass target length into the generation prompt.
- **More outputs**: generate “social post” variants (LinkedIn/X) from the same facts.
- **Tone lock**: store a preferred style guide for reuse across sessions.
- **Validation**: add a “missing essentials” checker (who/what/where/when) before generation.
- **CMS integration**: use the JSON output to publish into a content system automatically.

---

## 🔧 OCI Services Used

### 1. **OCI Generative AI – LLM (Cohere Command A)**
- Used for both:
  - style guide extraction
  - article generation (strict JSON output)

```python
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
```

---

## 🔗 Docs & References

- 📘 OCI Generative AI Overview  
  https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm

- 📘 LangChain OCI (Community) integrations  
  https://python.langchain.com/docs/integrations/providers/oci/

---

## License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
