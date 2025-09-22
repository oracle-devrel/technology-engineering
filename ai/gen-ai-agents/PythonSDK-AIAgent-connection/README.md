
# Generative AI Chatbot

This repository contains a Flask-based application utilizing Oracle's Generative AI agent that allows usage of OCI Agents and LLMs with OpenAI Gateway.

**Author**: matsliwins

**Last review date**: 19/09/2025

![](images/n8n_image.png)
## Getting Started

1. **Clone the Repository**:
```bash
git clone [your-repository-link]
cd [your-repository-folder]
```

2. **Configuration**:
- Open the Python file and replace the `AGENT_ENDPOINT_ID` with your Oracle Generative AI agent endpoint OCID:

```python
AGENT_ENDPOINT_ID = "your-agent-endpoint-ocid-here"
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the Application**:
```bash
python [your-main-file].py
```

## Usage

Access the chatbot via your browser:
```
http://localhost:5000
```

Enter messages in the web interface to interact with your generative AI agent.

## Requirements
- Python 3.8+
- OCI SDK
- Flask
- qrcode

Ensure your OCI configuration is properly set in `~/.oci/config`.

