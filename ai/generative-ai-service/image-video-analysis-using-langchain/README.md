# Video Content PG Rating Analyzer

This is a Generative AI-powered application that analyzes frames from uploaded videos or images to determine their suitability for PG-rated audiences. The application leverages Oracle Cloud Infrastructure (OCI) Generative AI Vision models, specifically Llama 3.2 in this case, to evaluate visual content for explicit or age-inappropriate material. This can also be adapted as needed to extract specific elements, text (such as license plates) and other use-cases.

<img src="./image.png">
</img>

Reviewed date: 19.01.2026

## Features
- Upload image or video files (`.jpg`, `.png`, `.mp4`, `.avi`, `.mov`).
- Automatically extract frames from videos at a user-defined interval.
- Use OCI Generative AI to assess frame content for PG-appropriateness.
- Highlight frames flagged as inappropriate with detailed reasons and timecodes.
- Adjust AI confidence threshold and frame extraction interval. (Effects the prompt for confidence)

## When to Use This Asset (Who & When)

### Who
- **Media & content moderation teams** reviewing user-generated content  
- **Streaming platforms & broadcasters** enforcing age-rating policies  
- **Compliance & trust & safety teams** monitoring visual content  

### When
- When images or videos must be checked for **PG-rating compliance**  
- When large volumes of **visual media** require automated screening  
- When flagged content must include **explanations and timecodes**  
- When configurable **confidence thresholds** are required for review workflows  

## How to use this asset
1. **Upload Media:**
   - Users upload a video or image file for analysis.
2. **Frame Extraction:**
   - For videos, the app extracts frames at a selected interval.
3. **AI Analysis:**
   - Each frame is encoded and sent to an OCI Vision model for analysis.
   - The AI responds with structured output indicating whether content is PG-appropriate.
4. **Result Display:**
   - Inappropriate frames (based on confidence threshold) are displayed along with the reason and timecode.
   - A final PG-rating verdict is shown at the end.

## Prerequisites
Before running the application, ensure you have:
- Python 3.8 or later installed
- An active Oracle Cloud Infrastructure (OCI) account
- Required Python dependencies installed
- OCI Generative AI model name and compartment ID

## Installation
Clone this repository and navigate to the project directory:
```bash
git clone <repository-url>
cd <repository-folder>
```

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Configuration
To integrate with OCI Generative AI, update the following parameters in the code:
```python
llm = ChatOCIGenAI(
    model_id="Add your model name",
    compartment_id="Add your compartment ID",
    model_kwargs={"temperature": 0, "max_tokens": 2000},
)
```

Replace `model_id` and `compartment_id` with the appropriate values from your OCI console.

## Running the Application
Run the Streamlit app using:
```bash
streamlit run <script-name>.py
```

Replace `<script-name>.py` with the filename of your main script (e.g., `video_analyzer.py`).

## Example Output
```json
{
    "AgeAppropriate": "not-appropriate",
    "response": "Shows intense violence and blood spatter.",
    "ConfidenceLevel": 0.97
}
```

---

## Docs & References

- [OCI Generative AI Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

---

## License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.

