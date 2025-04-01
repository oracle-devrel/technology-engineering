Assistant Secretary Agent
By Omar Salem

Assistant Secretary Agent is a powerful AI chatbot that dynamically routes user input to different tools including mail, Google Calendar, Weather, Calculator, and OCI GenAI (Cohere) for general questions and OCI AI Agent RAG-based answers. It includes a Streamlit UI and supports multi-tool workflows like reading emails, summarizing, replying, scheduling meetings, fetching weather, and more.

Reviewed: March 31, 2025

1. Prepare Your Credentials
Google API (Gmail + Calendar)
Go to: Google Cloud Console

Enable Gmail API and Calendar API

Create OAuth 2.0 credentials and download credentials.json

Place it in the project root directory

The first time you run the assistant, a token.json will be created automatically after login.

☁️ OCI Generative AI (Cohere on OCI)
Go to: OCI Console → Generative AI

Select a model like cohere.command-r-plus-08-2024

Copy:

model_id

compartment_id

endpoint (e.g., https://inference.generativeai.us-chicago-1.oci.oraclecloud.com)

Paste them in oci_models.py

https://docs.oracle.com/en-us/iaas/Content/generative-ai-agents/overview.htm
Do the same for the OCI AI AGENT endpoint. Create an AI Agent with a knowledge base and add your RAG documents in that knowledge base.

Weather API
Get a free API key from: weatherapi.com

Add the key to tools.py in:

python
Copy
Edit

WEATHER_API_KEY = "your_api_key_here"

2. Start the Chatbot
Terminal Mode
bash
Copy
Edit
python assistant.py
Streamlit UI
bash
Copy
Edit
streamlit run ui.py
You’ll see the full chat interface with interactive steps and decision routing.

3. Key Features
Tool	Description
 Fetch Gmail	Retrieves unread emails, summarizes them
 Select Email	Lets you read the full email body
 OCI AI Agent (RAG)	Provides answers from RAG agent based on sender's country
 Smart Replies	Generates professional replies using OCI GenAI
 Send Email	Sends reply to the original sender
 Schedule Emails	Delay sending with background job
 Weather + Advice	Current weather or forecast with clothing tips
 Book Meetings	Books Google Calendar events & fetches weather for the date
 Fallback Q&A	General questions or how-to help using OCI GenAI
 Calculator	Extracts & evaluates math from user input

4. Notes
Fully dynamic: user messages are routed in real-time using Cohere model hosted on OCI.

Each tool is modular and can be expanded or replaced.

Streamlit UI shows each step with visual feedback.

5. License
Licensed under the Universal Permissive License (UPL), Version 1.0.
See LICENSE for details.

