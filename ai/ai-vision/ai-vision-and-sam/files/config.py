import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=".config")

# config, compartments and endpoints
CONFIG_FILE_PATH = os.getenv("CONFIG_FILE_PATH")
COMPARTMENT_ID = os.getenv("COMPARTMENT_ID")
ENDPOINT= os.getenv("ENDPOINT")

## Other config params
ORACLE_LOGO = "app_images/oracle_logo.png"
UPLOAD_PATH = "uploaded_images"