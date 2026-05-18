# SKU Image Studio — OCI GenAI

*A Streamlit-based application that generates lifestyle and product imagery for retail SKUs using Oracle Generative AI. The asset automates the creation of market-localised, shot-type-specific product visuals from structured product inputs, eliminating manual photography briefing and reducing time-to-asset for high-volume SKU catalogues.*

Author: Ali Ottoman

Reviewed date: 27.03.2026
---

![Demo](sku_image_generation_studio.gif)

---

# When to use this asset?

*This asset is used by retail, e-commerce, and digital transformation teams when high-volume, market-localised product imagery is required without manual photography overhead.*

### Who
- E-commerce teams managing large SKU catalogues requiring frequent visual refresh
- Retail marketing teams producing localised imagery across multiple target markets
- Digital transformation teams modernising manual product photography workflows

### When
- SKU volume makes per-product photography cost-prohibitive
- Market-specific visual variants are required (regional demographics, settings, tone)
- Rapid concept visualisation is needed before committing to a full production shoot
- Consistent, brand-aligned output is required at scale

# How to use this asset?

*The asset is deployed as a Streamlit application and guides users through entering product details, selecting visual parameters, and generating imagery.*

### Application Workflow
1. Enter product details:
   - Product name
   - Description (positioning, materials, key attributes)
2. Select visual parameters:
   - Target market
   - Shot type
   - Setting / context
3. Click **Generate Image**
4. Review:
   - Generated product image
   - Metadata summary (market, shot type, setting, resolution)
   - Prompt sent to the model (for auditability and iteration)
   - Downloadable PNG output

### Key Capabilities
- Structured prompt construction from discrete UI inputs — no prompt engineering required from the operator
- Market localisation across five regional profiles (Middle East, Western Europe, North America, South & Southeast Asia, Global)
- Shot type control: Editorial, Candid, Flat Lay, On-Model, Product Only
- Setting control: Studio, Home, Urban, Café, Nature
- Full prompt transparency — the model prompt is surfaced in the UI for review and iteration
- One-click PNG download per generated asset

### File Structure
```
.
├── app.py
├── prompt_builder.py
├── oci_client.py
├── requirements.txt
└── README.md
```

### Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

Update `oci_client.py` with your `COMPARTMENT_ID` and `PROFILE_NAME`. 

# Useful Links

- OCI Generative AI Documentation
  - https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.