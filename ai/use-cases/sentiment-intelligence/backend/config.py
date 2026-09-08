"""
Configuration module for Sentiment Intelligence.
Loads settings from environment variables and .env file using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Database Configuration
    DB_USER: str
    DB_PASSWORD: str
    DB_DSN: str
    USE_WALLET: bool = True
    WALLET_LOCATION: Optional[str] = None
    WALLET_PASSWORD: Optional[str] = None
    DB_POOL_MIN: int = 1
    DB_POOL_MAX: int = 8
    DB_POOL_WAIT_TIMEOUT: int = 10

    # Select AI Profile (already created in database)
    SELECT_AI_PROFILE: str = "SENTIMENT_PROFILE"

    # OCI Configuration
    OCI_COMPARTMENT_ID: Optional[str] = None
    OCI_GENAI_ENDPOINT: str = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
    OCI_GENAI_MODEL: str = "cohere.command-a-03-2025"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    # Agent Timeouts (seconds)
    SENTIMENT_AGENT_TIMEOUT: int = 120
    ACTION_AGENT_TIMEOUT: int = 120
    WEB_SOURCE_AGENT_TIMEOUT: int = 45

    # Pipeline concurrency. Keep database inference deliberately bounded: each
    # sentiment worker owns an Oracle connection while DBMS_CLOUD_AI.GENERATE runs.
    SENTIMENT_CONCURRENCY: int = 3
    WEB_SEARCH_CONCURRENCY: int = 3
    WEB_SCRAPE_CONCURRENCY: int = 5

    # Web Search Configuration
    MAX_SEARCH_QUERIES: int = 4
    MAX_WEB_SEARCH_RESULTS: int = 10
    MAX_SCRAPE_TARGETS: int = 10
    SEARCH_RESULTS_PER_QUERY: int = 8

    # Application Metadata
    APP_NAME: str = "Sentiment Intelligence"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
