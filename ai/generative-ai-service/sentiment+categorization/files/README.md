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

## Getting Started
To run the demo, follow these steps:
1. Clone the repository using `git clone`.
2. Place your CSV files containing customer messages in the `data` folder.
3. Install dependencies using `pip install -r requirements.txt`.
4. Run the application using `streamlit run app.py`.

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
	+ Structured report generation
are powered by GenAI, ensuring accurate and efficient analysis of customer messages.

## Output
The demo will display an interactive dashboard with the generated report, providing valuable insights into customer messages, including:
* Category distribution across all three levels
* Sentiment score distribution
* Summaries of key findings and insights

## Contributing
We welcome contributions to improve and expand the capabilities of this demo. Please fork the repository and submit a pull request with your changes.

## License
Copyright (c) [Year] Oracle Corporation. All rights reserved.

This demo is proprietary software owned by Oracle Corporation. Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
* Neither the name of Oracle Corporation nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.