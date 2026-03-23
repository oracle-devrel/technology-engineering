# 🚗 Liability Determination Report Generator — OCI GenAI 

A Streamlit-based multimodal application that extracts **driver, vehicle, insurance**, and **damage assessment** details from uploaded documents and accident photos using **Oracle Generative AI (Llama 4 Maverick)**.

This asset automates end‑to‑end extraction for insurance reporting, producing:
- Structured Arabic JSON output  
- A professionally formatted **PDF report**  
- Car damage visualisations  
- Arabic text rendering and right‑to‑left formatting  

**Author:** Ali Ottoman  
**Reviewed date:** 11.12.2025

---

## 🔧 Features

### Full Document Extraction Pipeline
- Upload for **each party**:
  - Driving license  
  - Vehicle registration  
  - Insurance documents  
  - Damage photos (multiple supported)  
- Automatic PDF → image conversion  
- Enforcement of **Arabic‑only** values (names transliterated, no English)

### Maverick‑Powered Extraction
- One LLM call **per party**, with strict JSON schema:
  - **Driver info:** name, nationality, ID, expiry, issue date  
  - **Vehicle info:** owner, model, year/color, plate  
  - **Insurance info:** company, type, policy, dates  
  - **Damage:** affected regions + summary

### Streamlit Front-End
- Wide layout, image preview, inline debugging  
- Automatic Arabic font embedding  
- RTL display in all result sections  

### PDF Report Generation
- Clean A4 output showing:
  - Party 1 + Party 2 driver/vehicle/insurance info  
  - Arabic values rendered using embedded font  
  - Professional layout  
- First-page preview inside the app  

### Damage Map Visualisation
- Highlights impacted areas:
  - front / rear / left / right  
  - front-left / front-right  
  - rear-left / rear-right  

---

## 🗂️ Files & Structure

```
.
├── car_accident_report_generator.py        # Main Streamlit app
├── config.py                       # Compartment ID + configs
├── assets/
│   └── car_top_view.png            # Background for damage map
├── fonts/
│   └── NotoNaskhArabic-Regular.ttf # Embedded Arabic font
├── requirements.txt                # Dependencies
└── README.md                       # You are reading it
```

---

## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/car-accident-report-generator.git
cd <your-file>
```

### 2. Install Requirements
```bash
pip install -r requirements.txt
```

### 3. Configure OCI Credentials
Create or edit:

```python
# config.py
COMPARTMENT_ID = "<your_compartment_ocid>"
```

Ensure `~/.oci/config` is correctly configured with your **tenancy**, **user**, **API key**, and **region**.

---

## 🚀 Run the App
```bash
streamlit run car_accident_report_generator.py
```

---

## 📝 How to Use

1. Upload all required files for **Party 1** and **Party 2**  
2. (Optional) Upload any number of damage photos  
3. Click **Generate report**  
4. View:
   - Extracted JSON  
   - Damage visualisation  
   - Downloadable PDF report  

---

## 🧠 Example Output (JSON)

```json
{
  "party_1": {
    "driver": { "name": "عبد الله", "nationality": "سعودي", ... },
    "vehicle": { "owner_name": "محمد", "plate_no": "أ ب ج ١٢٣٤" },
    "insurance": { "company_name": "التعاونية", "policy_no": "123456789" }
  },
  "damage": {
    "party_1": {
      "primary_areas": ["rear-left", "rear"],
      "damage_summary": "أضرار متوسطة في الجزء الخلفي"
    }
  }
}
```

---

## 🔧 OCI Services Used

- **Generative AI Service (Llama 4 Maverick)**  
  Multimodal image reasoning + structured extraction  
- **Object Storage** (optional for extension)  
- **Streamlit** UI  

---

## 📄 License
MIT License — free to use and modify.

---

## 🔗 Docs & References
- OCI Generative AI: https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm
