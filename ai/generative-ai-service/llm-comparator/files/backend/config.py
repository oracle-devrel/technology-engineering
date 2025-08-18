# Common Configuration
COMPARTMENT_ID = "ocid1.compartment.oc1..your_compartment_id" # add here your compartment ocid id 
AUTH_TYPE = "your_auth_type" # add here your authentication type
CONFIG_PROFILE = "your_profile" # add here your profile

# Regional Endpoint
ENDPOINT = "your_endpoint_url" # add here your endpoint 

# Model data
PROVIDER = "your_model_provider" # add here your model provider 
VANILLA_MODEL = "ocid1.your_model_id" # add here your base model ocid id 
FT_MODEL = "ocid1.your_model_id" # add here your Host DAC endpoint ocid id 


# LLM comparator details
## Base models:
BASE_MODELS = [VANILLA_MODEL] # add here your base models

## Fine-tuned models and parameters:
FINETUNED_MODELS = {
    "finanace-fine-tunning": {
        "ft_model": FT_MODEL,
        "training_method": "LoRA",
        "dataset": "gbharti/finance-alpaca",
        "training_epochs": 3,
        "batch_size": 32,
        "stopping_patience": 30,
        "stopping_threshold": 0.0001,
        "interval": 10,
        "lora_r": 32,
        "lora_alpha": 32,
        "lora_dropout": 0.1,
        "learning_rate": 0.0002
    },
    "cohere.command-r-08-2024-domain-expert": {
        "ft_model": "cohere.command-r-ft",
        "training_method": "T-Few",
        "dataset": "oracle-domain-expert-v2",
        "training_epochs": 1,
        "batch_size": 16,
        "stopping_patience": 10,
        "stopping_threshold": 0.001,
        "interval": 1,
        "learning_rate": 0.01
    },
}