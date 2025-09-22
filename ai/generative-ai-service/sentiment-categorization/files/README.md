# Customer-Agent Conversation Analysis and Categorization Demo

This demo showcases an AI-powered solution for analyzing batches of customer messages, categorizing them into hierarchical levels, extracting sentiment scores, and generating structured reports. The latest version adds a professional, corporate UI theme, CSV upload/validation in the sidebar, and step-aware progress feedback during processing.

## Key Features
- Hierarchical Categorization
  - Primary Category: High-level categorization
  - Secondary Category: Mid-level categorization, building upon primary categories
  - Tertiary Category: Low-level categorization, providing increased specificity and detail
- Sentiment Analysis
  - Extracts sentiment scores for each message, from very negative (1) to very positive (10)
- Structured Reporting
  - Category distribution across all three levels
  - Sentiment score distribution
  - Summaries of key findings and insights
- CSV Upload and Validation
  - Upload CSV in the sidebar; validates required columns ID and Message before running
  - Displays a preview in the sidebar and a full interactive table in the main area
- Execution Progress and Status
  - Step-aware progress bar with status text showing the currently running stage and total steps


## Technical Details
- Built on Oracle Cloud Infrastructure (OCI) GenAI services
- End-to-end flow powered by GenAI for:
  - Hierarchical categorization
  - Sentiment analysis
  - Structured report generation

## Project Structure
```plaintext
│   app.py                  # Main Streamlit application entry point
│   README.md               # Project documentation
│   requirements.txt        # Python dependencies
│
├───backend
│   │   feedback_agent.py    # Logic for feedback processing agents
│   │   feedback_wrapper.py  # Wrappers and interfaces for feedback functionalities
│   │
│   ├───data
│   │       complaints_messages.csv   # Example dataset of customer messages
│   │
│   └───utils
│           config.py        # Configuration and setup for the project
│           prompts.py       # Prompt templates for language models
│
└───data
        complaints_messages.csv   # Example dataset of customer messages
```

## Getting Started
1. Clone the repository using git clone.  
2. (Optional) Create and activate a Python virtual environment:
   - Windows:
     - python -m venv venv
     - venv\Scripts\activate
   - macOS/Linux:
     - python3 -m venv venv
     - source venv/bin/activate
3. Place your CSV files in the data folder. Ensure each includes the required columns ID and Message.
4. Install dependencies with pip install -r requirements.txt.
5. Run the application with `streamlit run app.py`.

## Data Requirements
- Input format: CSV with two columns: ID and Message
- The app validates:
  - File extension is CSV
  - Both required columns are present
- The full dataset is visualized in the main view after successful validation.

## Output
The dashboard displays an interactive report with:
- Category distribution across all three levels
- Sentiment score distribution
- Summaries of key findings and insights
- Step-by-step execution status and overall progress of the analysis run

## License
Copyright (c) 2025 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.