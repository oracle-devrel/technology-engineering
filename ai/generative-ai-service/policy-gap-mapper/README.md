# 📚 Policy Gap Mapper

A Streamlit-based compliance application that uses **Oracle Document Understanding (DU)** and **Generative AI** to analyze regulatory documents and internal policies, then highlight **coverage gaps**.

Upload regulation PDFs/images and your internal policy documents, and the app will:
- Extract text via **OCI Document Understanding**
- Use an **LLM** to break regulations into atomic obligations
- Extract control statements from your policies
- Map obligations to controls and score coverage
- Generate an interactive **gap report** and downloadable **CSV**

**Author:** Ali Ottoman  
**Reviewed date:** 05.12.2025  

---

## 🔧 Features

### End-to-End DU + LLM Pipeline
- Upload multiple **regulation** documents and **internal policy** documents (PDF, JPG, PNG).
- Text is extracted using **OCI Document Understanding** (general text extraction).
- All downstream reasoning is performed with an **LLM** hosted on OCI Generative AI.

### Obligation Extraction from Regulations
- Splits regulatory text into manageable chunks.
- LLM extracts **atomic, testable obligations**, each enriched with:
  - `obligation_text`
  - `article_reference`
  - `category`
  - `criticality`
  - `keywords`

### Control Extraction from Internal Policies
- LLM identifies **control statements**, each with:
  - `control_text`
  - `control_type`
  - `owner_department`
  - `keywords`

---

## 🗂️ Files & Structure

```
.
├── files
   ├── policy_gap_mapper.py      # Main Streamlit app
   ├── config.py                 # OCI config & model IDs
├── requirements.txt    # Dependencies
└── README.md           # This file
```

---

## ⚙️ Setup & Installation

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
pip install -r requirements.txt
```

Configure `~/.oci/config` and edit:

```python
COMPARTMENT_ID = "<your-compartment-ocid>"
MODEL_ID = ["meta.llama-4-maverick-17b-128e-instruct-fp8"]
```

---

## 🚀 Run the App

```bash
streamlit run policy_gap_mapper.py
```

---

## 📝 How to Use

1. Upload regulation & policy documents.
2. Click **Analyze**.
3. Review extracted obligations & controls.
4. Inspect mapping results.
5. Download the CSV gap report.

---

## 🔧 OCI Services Used

- **OCI Document Understanding**: [Link](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/home.htm)
- **OCI Generative AI — ChatOCIGenAI**: [Link](https://www.oracle.com/ae/artificial-intelligence/generative-ai/generative-ai-service/)

---

## 📄 License

MIT License — see `LICENSE` for details.
