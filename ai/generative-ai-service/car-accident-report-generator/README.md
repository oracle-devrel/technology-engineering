# Liability Determination Report Generator — OCI GenAI

*A Streamlit-based multimodal application that extracts driver, vehicle, insurance, and damage assessment details from uploaded documents and accident photos using Oracle Generative AI (Llama 4 Maverick). The asset automates end‑to‑end extraction for insurance reporting, producing structured Arabic JSON output, a professionally formatted PDF report, car damage visualisations, and full Arabic RTL rendering.*

Author: Ali Ottoman

Reviewed: 19.01.2026

# When to use this asset?

*This asset is used by insurance and digital transformation teams when automated, Arabic-first accident and liability reporting is required.*

### Who
- Motor insurance teams handling accident and liability reports  
- Claims adjusters requiring fast, structured damage assessments  
- Digital transformation teams modernising manual accident workflows  

### When
- Accident cases contain mixed documents and photos  
- Arabic-only extraction and RTL rendering are mandatory  
- Consistent, schema-validated JSON and PDF outputs are required  
- Reducing manual data entry and report preparation time is a priority  

# How to use this asset?

*The asset is deployed as a Streamlit application and guides users through uploading accident documents and images, extracting structured data, and generating reports.*

### Application Workflow
1. Upload all required files for Party 1 and Party 2:
   - Driving license  
   - Vehicle registration  
   - Insurance documents  
   - Damage photos (multiple supported)  
2. Click **Generate report**
3. Review:
   - Extracted structured Arabic JSON  
   - Damage visualisation map  
   - Downloadable professionally formatted PDF report  

### Key Capabilities
- Automatic PDF-to-image conversion  
- One multimodal LLM call per party with strict JSON schema:
  - Driver information  
  - Vehicle information  
  - Insurance details  
  - Damage regions and summary  
- Arabic-only value enforcement with proper font embedding  
- RTL rendering across UI, JSON, and PDF outputs  

### Damage Visualisation
- Highlights impacted vehicle areas:
  - front / rear / left / right  
  - front-left / front-right  
  - rear-left / rear-right  

### File Structure
```
.
├── car_accident_report_generator.py
├── config.py
├── assets/
│   └── car_top_view.png
├── fonts/
│   └── NotoNaskhArabic-Regular.ttf
├── requirements.txt
└── README.md
```

### Setup
```bash
pip install -r requirements.txt
streamlit run car_accident_report_generator.py
```

Ensure OCI credentials are configured correctly and the compartment OCID is set in `config.py`.

# Useful Links (Optional)

- OCI Generative AI Documentation  
  - https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm  

# License

Copyright (c) 2026 Oracle and/or its affiliates.  
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
