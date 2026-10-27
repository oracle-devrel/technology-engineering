# 🚗 Insurance Image/Video Analyzer — OCI GenAI

A Streamlit-based multimodal application that analyzes **vehicle images or videos** for insurance claim triage using **Oracle Generative AI**.

This tool allows insurance professionals and adjusters to upload accident images or a short video clip, and receive a concise, expert-style report summarizing vehicle condition, visible damages, and safety concerns — all generated through a single multimodal LLM call.

**Author:** Ali Ottoman  

**Reviewed date:** 04.08.2026

---

# When to use this asset?
## 🔧 Features

### Unified Image & Video Analysis
- Upload multiple **images**, a single **video**.
- For videos: frames are extracted automatically (at a user-set interval) and analyzed **collectively** in one final pass (per 10 frames).
- Generates one unified report summarizing all perspectives.

### Insurance-Focused Vehicle Damage Report
- Custom prompt tuned for **insurance adjuster** workflows.
- Structured output covering:
  - Vehicle details (make, model, color, visible plates)
  - Damage assessment by section (front, rear, sides, roof, wheels)
  - Safety & driveability insights
  - ADAS & sensor recalibration notes
  - Prior damage indicators
  - Concise summary for claims review

### Multimodal LLM (Llama 4 Maverick)
- Performs reasoning across **all frames and views** to remove duplicates and highlight consistent damage regions.
- Handles both still images and continuous video input.
- Supports temperature control and token limit configuration.

### Streamlit Front-End
- Simple upload interface with thumbnail previews.
- Real-time progress indicators and structured results display.
- Sidebar controls for frame interval, max frames, and temperature.

---

## 👥 Who Can Use This

**Insurance Adjusters & Claims Teams**  
→ Rapidly review visual evidence from claim submissions with a single summarized analysis.

**Fleet Managers & Repair Centers**  
→ Assess damage consistency across multiple images or dashcam videos.

**Developers & AI Engineers**  
→ Extend or integrate the workflow into enterprise insurance platforms on OCI.

---

## 🗂️ Files & Structure

```
.
├── motor-insurance-chatbot.py   # Main Streamlit app  
├── config.py                    # OCI config & model IDs (user-provided)  
├── requirements.txt             # Python dependencies  
└── README.md                    # You're reading it
```

---

# How to use this asset?
## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### 2. Configure OCI Credentials
Edit your `config.py` file:

```python
# config.py
COMPARTMENT_ID = "<your OCI Compartment OCID>"
MODEL_ID = ["meta.llama-4-maverick-17b-128e-instruct-fp8"]
```

Ensure your OCI credentials file (`~/.oci/config`) is correctly configured with API keys and region.

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

---

## 🚀 Run the App
```bash
streamlit run motor-insurance-chatbot.py
```

---

## 📝 Get it running

1. **Upload your files**  
   → Images (`.jpg`, `.png`) or one video (`.mp4`, `.avi`, `.mov`)  
   → PDFs are also supported (converted to images internally)

2. **Set parameters**  
   - Choose frame extraction interval (default = 12)  
   - Limit total frames (default = 120)  
   - Adjust temperature (default = 0 for deterministic outputs)

3. **Ask your question**  
   Example queries:
   - “Describe the visible vehicle damages.”
   - “Summarize the safety concerns.”
   - “What parts likely need recalibration?”

4. **View results**  
   → The app displays:
   - Frame thumbnails  
   - A single final LLM report combining all inputs  
   - Structured markdown-formatted sections  

---

## 🛠️ Customization

- Modify `INSURANCE_PROMPT` to tailor report tone or add fields (e.g., **cost estimate**, **liability hints**, **repair recommendations**).
- Adjust `MAX_VIDEO_FRAMES` and `MAX_TOKENS` for performance vs detail.
- Add export features (CSV, PDF) via Streamlit’s `st.download_button`.

---

## 🧠 Example Interaction

**You:** *Describe visible damages and safety concerns.*

**AI (Maverick):**
> **Vehicle Details:** Red Toyota Corolla 2021, rear plate visible.  
> **Damage Assessment:** Moderate rear bumper impact with scratched paint; left taillight cracked; minor dent on rear quarter panel.  
> **Safety & Driveability:** Lights partially damaged but vehicle likely drivable; no airbag deployment visible.  
> **Summary:** Rear collision impact focused on left side; requires bumper and light replacement.

---

## 🔧 OCI Services Used

1. **OCI Generative AI – Llama 4 Maverick**  
   → Multimodal text + image/video reasoning  
   ```python
   from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
   ```

---

# Docs & References

📘 [OCI Generative AI Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
