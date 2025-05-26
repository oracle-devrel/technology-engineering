# Patient Referral  Extraction

This is a Generative AI-powered application that extracts key information from patient referral letters (in `.docx` format) and processes them using the OCI Generative AI services. This application allows users to simply and efficiently extract key data from patient referrals for expedited patient handling.

## Features
- Upload `.docx` files containing patient referral letters.
- Process documents using Oracle Cloud Infrastructure (OCI) Generative AI.
- Extract structured data and display it in a table.
- Save extracted data as a CSV file for further use.

## Prerequisites
Before running the application, ensure you have:
- Python 3.8 or later installed
- An active Oracle Cloud Infrastructure (OCI) account
- Required Python dependencies installed
- OCI Generative AI model name and compartment ID

## How It Works
1. **Upload Files:** Users upload patient referral letters in .pdf or .docx format.
2. **Processing:**
   - Extracts text from uploaded documents.
   - Sends the text to an OCI AI model for structured data extraction.
   - Extracted data includes:
     - Referring Doctor
     - Condition
     - Recommended Clinic (chosen from predefined options)
     - Brief Summary
3. **Results Display:**
   - Extracted details are displayed in a table.
   - Data is saved to a CSV file for download.

## Example Output
```json
{
    "Referring Doctor": "Dr. Sarah Thompson",
    "Condition": "Severe plaque psoriasis",
    "Recommended Clinic": "Psoriasis",
    "Brief Summary": "Patient has been experiencing severe plaque psoriasis unresponsive to topical treatments. Referral requested for specialist evaluation and potential systemic therapy."
}
```

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
Replace `model_id` and `compartment_id` with the appropriate values.

## Running the Application
Run the Streamlit app with:
```bash
streamlit run <script-name>.py
```

Replace `<script-name>.py` with the filename of the main script (e.g., `patient_triage_extraction.py`).



