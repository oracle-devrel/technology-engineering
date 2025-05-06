# Batch Message Analysis and Categorization Demo
This demo showcases an AI-powered solution for analyzing batches of customer messages, categorizing them into hierarchical levels, extracting sentiment scores, and generating structured reports.

## Key Features
* **Hierarchical Categorization**: Automatically categorizes messages into three levels of hierarchy:
	+ Primary Category: High-level categorization
	+ Secondary Category: Mid-level categorization, building upon primary categories
	+ Tertiary Category: Low-level categorization, providing increased specificity and detail
* **Sentiment Analysis**: Extracts sentiment scores for each message, ranging from very negative (1) to very positive (10)
* **Structured Reporting**: Generates a comprehensive report analyzing the batch of messages, including:
	+ Category distribution across all three levels
	+ Sentiment score distribution
	+ Summaries of key findings and insights

## Data Requirements
* Customer messages should be stored in a CSV file(s) within a folder named `data`.
* Each CSV file should contain a column with the message text.

## Python Version
This project requires **Python 3.13** or later. You can check your current Python version by running:
```
python --version
```
or
```
python3 --version
```

## Getting Started
To run the demo, follow these steps:
1. Clone the repository using `git clone`.
2. *(Optional but recommended)* Create and activate a Python virtual environment:
   - On Windows:
     ```
     python -m venv venv
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     python3 -m venv venv
     source venv/bin/activate
     ```
3. Place your CSV files containing customer messages in the `data` folder. Ensure each includes a column with the message text.
4. Install dependencies using `pip install -r requirements.txt`.
5. Run the application using `streamlit run app.py`.

## Example Use Cases
* Analyze customer feedback from surveys, reviews, or social media platforms to identify trends and patterns.
* Inform product development and customer support strategies by understanding customer sentiment and preferences.
* Optimize marketing campaigns by targeting specific customer segments based on their interests and concerns.

## Technical Details
* The solution leverages Oracle Cloud Infrastructure (OCI) GenAI, a suite of AI services designed to simplify AI adoption.
* Specifically, this demo utilizes the Cohere R+ model, a state-of-the-art language model optimized for natural language processing tasks.
* All aspects of the demo, including:
	+ Hierarchical categorization
	+ Sentiment analysis
	+ Structured report generation are powered by GenAI, ensuring accurate and efficient analysis of customer messages.


## Project Structure

The repository is organized as follows:

```plaintext
│   app.py                  # Main Streamlit application entry point
│   README.md               # Project documentation
│   requirements.txt        # Python dependencies
│
├───backend
│   │   feedback_agent.py    # Logic for feedback processing agents
│   │   feedback_wrapper.py  # Wrappers and interfaces for feedback functionalities
│   │   message_handler.py   # Utilities for handling and preprocessing messages
│   │
│   ├───data
│   │       complaints_messages.csv   # Example dataset of customer messages
│   │
│   └───utils
│           config.py        # Configuration and setup for the project
│           llm_config.py    # Model- and LLM-related configuration
│           prompts.py       # Prompt templates for language models
│
└───pages
        SentimentByCat.py    # Additional Streamlit page for sentiment by category
```
## Output
The demo will display an interactive dashboard with the generated report, providing valuable insights into customer messages, including:
* Category distribution across all three levels
* Sentiment score distribution
* Summaries of key findings and insights

## Contributing
We welcome contributions to improve and expand the capabilities of this demo. Please fork the repository and submit a pull request with your changes.

## License
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.