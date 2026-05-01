# Decode Images and Videos with OCI GenAI
Unlock insights from images and videos using Oracle Cloud Infrastructure (OCI) Generative AI. This app analyzes images and video frames to produce detailed, multi-language summaries with customizable processing options.

Reviewed: 29.01.2026

# When to use this asset?
Content creators, researchers, solution engineers, and media analysts can use this asset to:
- Summarize image content in multiple languages.
- Extract and analyze video frames at custom intervals.
- Generate cohesive summaries from combined frame analyses.
- Accelerate visual content understanding with parallel processing.

# How to use this asset?
1. Prerequisites:
   - Python 3.8+ installed.
   - OCI credentials configured in ~/.oci/config with a valid profile.
   - Set your compartmentId, llm_service_endpoint, and visionModel values in the code.

2. Install dependencies:
   - Clone the repository.
   - Run: pip install -r requirements.txt

3. Run the application:
   - streamlit run app.py

4. Upload and analyze:
   - Upload an image (.png, .jpg, .jpeg) or a video (.mp4, .avi, .mov).
   - For videos, set frame extraction interval and (optionally) a frame range.
   - Enter a custom prompt and choose an output language (English, French, Arabic, Spanish, Italian, German, Portuguese, Japanese, Korean, Chinese).
   - View detailed image summaries or cohesive video summaries in the app.


# Useful Links (Optional)
- OCI Generative AI Documentation: https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm
  - Service overview and API references for OCI Generative AI.
- [Oracle](https://www.oracle.com)
  - Oracle Website

# License
Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal Permissive License (UPL), Version 1.0.
See LICENSE at https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt for more details.