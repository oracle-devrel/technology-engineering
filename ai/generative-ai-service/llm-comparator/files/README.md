# LLM Performance Comparator - Technical Documentation

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Dataset Preparation](#dataset-preparation)
- [Usage Instructions](#usage-instructions)
- [Architecture](#architecture)
- [File Structure](#file-structure)
- [Supported Models](#supported-models)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Oracle Cloud Infrastructure Account** with Generative AI service access
- **Python 3.8+** environment
- **OCI CLI** configured with proper authentication
- **Required Python packages**: Available in `requirements.txt`
- **API Key authentication** set up for OCI services

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd llm-performance-comparator
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up OCI authentication**
   - Configure your `~/.oci/config` file
   - Ensure API keys are properly set up
   - Verify compartment access permissions

## Configuration

### OCI Configuration (`backend/config.py`)

Update the following variables with your OCI details:

```python
# Common Configuration
COMPARTMENT_ID = "ocid1.compartment.oc1..your-compartment-id"
AUTH_TYPE = "your_auth_type"
CONFIG_PROFILE = "your_profile"

# Regional Endpoint
ENDPOINT = "your_endpoint_url"

# Model OCIDs
VANILLA_MODEL = "ocid1.your_model_id" # add here your base model ocid id 
FT_MODEL = "ocid1.your_model_id" # add here your Host DAC endpoint ocid id 
```

### Fine-tuned Model Configuration

Users need to copy the fine-tuned model parameters from the OCI Console to configure available models in the application.

#### Steps to Configure Fine-tuned Models:

1. **Access OCI Console**
   - Navigate to "_Analytics & AI / Generative AI_" service
   - Go to "_Custom Models_" section
   - Select your fine-tuned model

2. **Copy Model Parameters**
   - Note the training parameters used during fine-tuning
   - Record the base model and training method

3. **Update Configuration**
   - Add the model configuration to `FINETUNED_MODELS` dictionary in `config.py`
   - Include all relevant training parameters from the console

#### Example Configuration from OCI Console:

**Finance Fine-tuning (LoRA)**
```python
"finance-fine-tuning": {
    "ft_model": FT_MODEL,                                           # From OCI Console
    "training_method": "LoRA",                                      # From Console Details
    "dataset": "gbharti/finance-alpaca",                            # From Console Details
    "training_epochs": 3,                                           # From Console Parameters
    "batch_size": 32,                                               # From Console Parameters
    "stopping_patience": 30,                                        # From Console Parameters
    "stopping_threshold": 0.0001,                                   # From Console Parameters
    "interval": 10,                                                 # From Console Parameters
    "lora_r": 32,                                                   # From Console Parameters
    "lora_alpha": 32,                                               # From Console Parameters
    "lora_dropout": 0.1,                                            # From Console Parameters
    "learning_rate": 0.0002                                         # From Console Parameters
}
```

**Domain Expert (T-Few)**
```python
"cohere.command-r-08-2024-domain-expert": {
    "ft_model": "ocid1.generativeaiendpoint.oc1.your-model-ocid",   # From OCI Console
    "training_method": "T-Few",                                     # From Console Details
    "dataset": "oracle-domain-expert-v2",                           # From Console Details
    "training_epochs": 1,                                           # From Console Parameters
    "batch_size": 16,                                               # From Console Parameters
    "stopping_patience": 10,                                        # From Console Parameters
    "stopping_threshold": 0.001,                                    # From Console Parameters
    "interval": 1,                                                  # From Console Parameters
    "learning_rate": 0.01                                           # From Console Parameters
}
```

- **Required Parameters from OCI Console**:
  - **Model OCID**: The fine-tuned endpoint identifier
  - **Training Method**: LoRA, T-Few, or other supported methods
  - **Dataset**: Training dataset name or identifier
  - **Hyperparameters**: All training parameters used during fine-tuning
  - **LoRA Parameters** (if applicable): rank (r), alpha, dropout values

## Dataset Preparation

The project includes a utility script for converting datasets to OCI Generative AI Service format. This is essential for preparing training data before fine-tuning models.

### Dataset Format Conversion (`format_dataset\dataset_to_oci_format.py`)

**Purpose**: Converts standard instruction-following datasets (e.g., [gbharti/finance-alpaca](https://huggingface.co/datasets/gbharti/finance-alpaca) on Hugging Face) to OCI-compatible JSONL format.

**Input Format** (e.g., `finance_data.json` in JSON format):
```json
[
  {
    "instruction": "What is compound interest?",
    "output": "Compound interest is the interest calculated on the initial principal..."
  }
]
```

**Output Format** (OCI-compatible JSONL):
```json
{"prompt": "What is compound interest?", "completion": "Compound interest is the interest calculated on the initial principal..."}
{"prompt": "How do I calculate ROI?", "completion": "Return on Investment (ROI) is calculated by..."}
```

### Using the Dataset Converter

1. **Prepare your source dataset**
   - Place your dataset file in the `data/` directory
   - Ensure it follows the instruction-output format

2. **Run the conversion script**
   ```bash
   python dataset_to_oci_format.py
   ```

3. **Upload to OCI**
   - Use the generated `output.jsonl` file for fine-tuning
   - Upload to OCI Object Storage
   - Reference in your fine-tuning job configuration

#### Script Features

- **Format Standardization**: Converts various dataset formats to OCI requirements
- **Character Encoding**: Handles UTF-8 encoding and filters problematic characters
- **Error Handling**: Skips entries with encoding issues to maintain dataset integrity
- **Quote Normalization**: Removes problematic quote characters that may interfere with JSON parsing


## Usage Instructions

### Starting the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Workflow

1. **Model Selection**
   - Choose base model from sidebar dropdown
   - Select fine-tuned model variant
   - Review displayed fine-tuning parameters

2. **Prompt Testing**
   - Enter test prompt in the main text area
   - Click "Generate Comparison" button
   - Wait for responses from both models

3. **Results Analysis**
   - Compare response quality side-by-side
   - Review inference time metrics
   - Analyze performance improvements

## Architecture

### Application Structure

```
app.py              # Main Streamlit application
├── backend/
│   ├── backend.py  # Model interaction logic
│   └── config.py   # Configuration settings
├── format_dataset/
│   └──dataset_to_oci_format.py # Dataset conversion utility
└── static/
    ├── oracle.png  # Oracle logo
    └── styles.css  # Custom CSS styling
```

### Key Components

- **Frontend**: Streamlit-based web interface with custom CSS styling
- **Backend**: LangChain integration with OCI Generative AI
- **Model Management**: Dynamic model initialization and response generation

### Data Flow

1. User selects models and enters prompt
2. Application initializes both base and fine-tuned models
3. Concurrent API calls to OCI Generative AI service
4. Response processing and timing calculation
5. Side-by-side display with performance metrics


## Supported Models

### Base Models
- Foundational Large Language Models, e.g., **Meta Llama 3.3 70B Instruct**

### Fine-tuning Methods
- **LoRA (Low-Rank Adaptation)**: Parameter-efficient fine-tuning
- **T-Few**: Task-specific few-shot learning

## Troubleshooting

### Common Issues

#### Authentication Errors
```
Error: Authentication failed
```
**Solution**: Verify OCI config file and API key permissions

#### Model Access Issues
```
Error: Model not found or access denied
```
**Solution**: Check compartment permissions and model OCIDs

#### Endpoint Connection Issues
```
Error: Connection timeout
```
**Solution**: Verify regional endpoint URL and network connectivity

#### Missing Dependencies
```
ModuleNotFoundError: No module named 'langchain_community'
```
**Solution**: Install required packages using pip

## Security Considerations

- **API Keys**: Store OCI credentials securely
- **Network Security**: Use HTTPS endpoints only
- **Access Control**: Implement proper OCI IAM policies
