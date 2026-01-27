import sys
import os
from dotenv import load_dotenv
import logging

def load_configurations(app):
    load_dotenv()
    
    app.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
    app.config["APP_ID"] = os.getenv("APP_ID")
    app.config["APP_SECRET"] = os.getenv("APP_SECRET")
    app.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
    app.config["VERSION"] = os.getenv("VERSION")
    app.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
    app.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")
    app.config["ENDPOINT"] = os.getenv("ENDPOINT")
    app.config["EMBEDDING_MODEL"] = os.getenv("EMBEDDING_MODEL")
    app.config["GENERATE_MODEL"] = os.getenv("GENERATE_MODEL")
    app.config["COMPARTMENT_ID"] = os.getenv("COMPARTMENT_ID")

def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
