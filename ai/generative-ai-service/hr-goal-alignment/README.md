# HR Goal Alignment Chatbot

This Streamlit-based application demonstrates a modular, AI-powered HR chatbot system designed to help employees and managers align their goals through structured, data-informed conversations.

The system integrates with Oracle Database and uses OCI's Generative AI models to simulate goal alignment and cascading throughout an organization.

Reviewed Date: 22.09.2025
---
# When to use this asset?
## Features

- Modular chatbot interfaces:
  - **Self-Assessment Chatbot**: guides employees in preparing for evaluations
  - **Goal Alignment Chatbot**: facilitates alignment of goals with organizational strategy
  - **Course Recommendation Chatbot**
  - **Manager Meeting Preparation Chatbot**
- Live Oracle Database integration for:
  - Self-assessments
  - Manager briefings
  - Goal sheets
- AI-powered conversations using **Oracle Generative AI** via **LangChain**
- Goal refinement tracking and database updates
- Org chart visualization using **Graphviz**
- Downloadable chat transcripts
- Modular codebase with reusable prompt templates

---

##  Project Structure

```text
.
├── app.py
├── config.py
├── course_vector_utils.py
├── data/
│   └── Full_Company_Training_Catalog.xlsx
├── data_ingestion_courses.py
├── gen_ai_service/
│   └── inference.py
├── goal_alignment_backend.py
├── org_chart_backend.py
├── org_chart.py
├── pages/
│   ├── course_recommendation_chatbot.py
│   ├── goal_alignment_chatbot.py
│   ├── manager_meeting_chatbot.py
│   └── self_assessment_chatbot.py
├── scripts/
│   ├── create_tables.py
│   └── populate_demo_data.py
├── utils.py
├── requirements.txt
└── README.md
```
# How to use this asset?
## Setup Instructions

### 1. Clone the repository
git clone https://github.com/your-username/hr-goal-alignment-chatbot.git
cd hr-goal-alignment-chatbot

### 2. Create and activate a virtual environment
python3 -m venv venv 
On Mac:
source venv/bin/activate
On Windows:
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

Setting up Graphviz in your virtual environment
Our Streamlit org‑chart relies on the Graphviz binaries as well as the Python wrapper.
Follow these steps inside the virtual environment where you’ll run the app.

On Mac:
brew install graphviz
pip install graphviz
Ensure the Graphviz /bin directory is added to your system PATH.
(export PATH="/opt/homebrew/bin:$PATH")

On Windows:
Download and install Graphviz from https://graphviz.org/download/
Ensure the Graphviz /bin directory is added to your system PATH.

### 4. Configure Oracle access
Before running the application, you need to provide your Oracle Cloud Infrastructure (OCI) and Autonomous Database credentials. This entails that you need to have an Oracle Autonomous Database set up in advance in order for this code to work.

1. Create a config file: 
    copy the provided template to a new config file
    cp config_template.py config.py

2. Edit config.py and fill in the following: 
OCI Settings:

OCI_COMPARTMENT_ID: Your OCI compartment OCID.
REGION: e.g., eu-frankfurt-1
GEN_AI_ENDPOINT: Leave as-is unless using a custom endpoint.
AUTH_TYPE: Set to "API_KEY" or "RESOURCE_PRINCIPAL" depending on your deployment.

Model Settings:

EMBEDDING_MODEL_ID: Default is a Cohere model.
GENERATION_MODEL_ID: Also Cohere, or replace with your chosen provider.

Database Credentials:

DB_USER, DB_PASSWORD: Your ADB login credentials.
DB_DSN: Your TNS-style connection string. You can get this from the Oracle Cloud Console → Autonomous Database → Database Connection → "Wallet Details" → "Connection String".

GENERATE_MODEL = "ocid1.generativemodel.oc1..xxxxx"
ENDPOINT = "https://inference.generativeai.region.oraclecloud.com"
COMPARTMENT_ID = "ocid1.compartment.oc1..xxxxx"

### 5. Populate Demo (Optional)
To populate the database with example self-assessment records, manager briefings, and goal sheets:
python scripts/populate_demo_data.py

### 6. Run the App
To start the chatbot system locally:
streamlit run app.py
You can then navigate to the provided local URL (usually http://localhost:8501) to interact with the available chatbots.

## Demo Workflow Example
A manager uses the Goal Alignment Chatbot to refine their goals with the help of Oracle Generative AI.
These refinements are tracked and optionally applied to the database.
Next, a direct report uses the same chatbot — now aligning their own goals with the updated manager goals.
This demonstrates how alignment cascades hierarchically through the organization.

Meanwhile, employees can:

Use the Self-Assessment Chatbot to reflect on performance areas.

Use the Manager Meeting Preparation Chatbot to view summaries and briefings.

Get personalized course recommendations aligned to their career goals.

View the organizational hierarchy using the integrated org chart visualizer.


## Tech Stack
Frontend: Streamlit

Backend: Python

Data Layer: Oracle Autonomous Database

AI Orchestration: LangChain

LLM Provider: Oracle Generative AI (via Cohere or other supported backends)

Graph Visualization: Graphviz (for org charts)

---

## Docs & References

📘 [OCI Generative AI Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

---

## License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
