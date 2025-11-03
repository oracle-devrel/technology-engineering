# Enterprise RAG Report Generator with Oracle OCI Gen AI

A sophisticated Retrieval-Augmented Generation (RAG) system built with Oracle OCI Generative AI, designed for enterprise document analysis and automated report generation. This application processes complex documents (PDFs, Excel files) and generates comprehensive analytical reports using multi-agent workflows.

**Reviewed: 19.09.2025**

##  Features

### Document Processing
- **Multi-format Support**: Process PDF documents and Excel spreadsheets (.xlsx, .xls)
- **Entity-aware Ingestion**: Automatically detect and tag entities within documents
- **Smart Chunking**: Intelligent document segmentation with context preservation
- **Multi-language Support**: Powered by Cohere's multilingual embedding models

### Advanced RAG Capabilities
- **Multi-Collection Search**: Query across different document collections simultaneously
- **Hybrid Search**: Combine vector similarity and keyword matching for optimal results
- **Entity Filtering**: Filter search results by specific organizations or entities
- **Dimension-aware Storage**: Automatic handling of different embedding model dimensions

### Intelligent Report Generation
- **Multi-Agent Architecture**: Specialized agents for planning, research, and writing
- **Comparison Reports**: Generate side-by-side comparisons of multiple entities
- **Structured Output**: Automated section generation with tables and charts
- **Chain-of-Thought Reasoning**: Advanced reasoning capabilities for complex queries

### Model Flexibility
- **Multiple LLM Support**: 
  - Grok-3 and Grok-4
  - Llama 3.3
  - Cohere Command
  - Dedicated AI Clusters (DAC)
- **Embedding Model Options**:
  - Cohere Multilingual (1024D)
  - ChromaDB Default (384D)
  - Custom OCI embeddings

### User Interface
- **Gradio Web Interface**: Clean, intuitive UI for document processing and querying
- **Vector Store Viewer**: Explore and manage your document collections
- **Real-time Progress Tracking**: Monitor processing and generation status
- **Report Downloads**: Export generated reports in Markdown format

## Prerequisites

### Oracle OCI Configuration
- Set up your Oracle Cloud Infrastructure (OCI) account
- Obtain the following:
  - Compartment OCID
  - Generative AI Service Endpoint
  - Model IDs for your chosen LLMs
  - API keys and authentication credentials
- Configure your `~/.oci/config` file with your profile details

### Python Environment
- Python 3.8 or later
- Virtual environment recommended
- Sufficient disk space for vector storage

##  Installation

1. **Clone the repository:**

2. **Create and activate a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r files/requirements.txt
```

4. **Configure environment variables:**
```bash
cp files/.env.example files/.env
# Edit .env with your OCI credentials and model IDs
```

5. **Set up OCI configuration:**
Ensure your `~/.oci/config` file contains:
```ini
[DEFAULT]
user=ocid1.user.oc1..xxxxx
fingerprint=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
tenancy=ocid1.tenancy.oc1..xxxxx
region=us-chicago-1
key_file=~/.oci/oci_api_key.pem
```

##  Usage

### Starting the Application
```bash
cd files
python gradio_app.py
```
The application will launch at `http://localhost:7863`

### Document Processing Workflow

1. **Upload Documents**
   - Navigate to the "DOCUMENT PROCESSING" tab
   - Select your embedding model
   - Upload PDF or Excel files
   - Specify the entity/organization name
   - Click "Process" to ingest documents

2. **Query Your Documents**
   - Go to the "INFERENCE & QUERY" tab
   - Enter your query or question
   - Select data sources (PDF/XLSX collections)
   - Choose between standard or agentic workflow
   - Click "Run Query" to generate response

3. **Generate Reports**
   - Enable "Use Agentic Workflow" for comprehensive reports
   - Specify entities for comparison reports
   - Download generated reports in Markdown format

### Advanced Features

**Vector Store Management:**
- View collection statistics
- Search across collections
- List and manage document chunks
- Delete collections when needed

**Multi-Entity Comparison:**
```python
# Example: Compare ESG metrics between two companies
Query: "Compare sustainability initiatives"
Entity 1: "CompanyA"
Entity 2: "CompanyB"
```

## 📁 File Structure
```
.
├── files/
│   ├── gradio_app.py              # Main application interface
│   ├── local_rag_agent.py         # RAG system core logic
│   ├── vector_store.py            # Vector storage management
│   ├── oci_embedding_handler.py   # OCI embedding integration
│   ├── disable_telemetry.py       # Telemetry management
│   ├── agents/                    # Multi-agent components
│   │   ├── agent_factory.py       # Agent initialization
│   │   └── report_writer_agent.py # Report generation
│   ├── handlers/                  # Document processors
│   │   ├── pdf_handler.py         # PDF processing
│   │   ├── xlsx_handler.py        # Excel processing
│   │   └── query_handler.py       # Query processing
│   └── requirements.txt           # Python dependencies
├── README.md                       # Project documentation
└── LICENSE                         # License information
```

##  Screenshots

### Main Interface
[Screenshot: Document Processing Tab]

### Query Interface
[Screenshot: Inference & Query Tab]

### Vector Store Viewer
[Screenshot: Collection Management]

### Generated Report Example
[Screenshot: Sample Report Output]

## 🔧 Configuration

### Model Selection
Configure available models in your `.env` file:
```env
# LLM Models
OCI_GROK_3_MODEL_ID=ocid1.generativeaimodel.oc1...
OCI_GROK_4_MODEL_ID=ocid1.generativeaimodel.oc1...
OCI_LLAMA_3_3_MODEL_ID=ocid1.generativeaimodel.oc1...

# Embedding Models
DEFAULT_EMBEDDING_MODEL=cohere-embed-multilingual-v3.0

# Compartment Configuration
OCI_COMPARTMENT_ID=ocid1.compartment.oc1...
```

### Performance Tuning
- Adjust chunk sizes in `ingest_pdf.py` and `ingest_xlsx.py`
- Configure parallel processing in `report_writer_agent.py`
- Modify token limits in model configurations

## 🐛 Troubleshooting

### Common Issues

**Vector Store Dimension Mismatch:**
- Ensure consistent embedding model usage
- Clear existing collections when switching models
- Check collection metadata for dimension conflicts

**OCI Authentication Errors:**
- Verify `~/.oci/config` configuration
- Check API key permissions
- Ensure compartment access rights

**Memory Issues:**
- Reduce chunk sizes for large documents
- Consider using dedicated AI clusters for heavy workloads

## Contributing

This project welcomes contributions from the community. Before submitting a pull request, please:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

Please review our contribution guidelines for coding standards and best practices.

## 🔒 Security

Please consult the security guide for our responsible security vulnerability disclosure process. Report security issues to the maintainers privately.

## 📄 License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.

## ⚠️ Disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE. FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK.

