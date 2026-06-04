from dataclasses import dataclass, field


@dataclass
class OCIConfig:
    # ── OCI identity ──────────────────────────────────────────────────────────
    COMPARTMENT_ID: str
    CONFIG_FILE_PATH: str = "~/.oci/config"
    PROFILE_NAME: str = "DEFAULT"

    # ── Generative AI endpoint ────────────────────────────────────────────────
    ENDPOINT: str = (
        "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
    )

    # ── Default model – can be any on-demand or BYOM model ID ─────────────────
    CHAT_MODEL_ID: str = "meta.llama-3-70b-instruct"

    # ── Generation hyper-parameters ───────────────────────────────────────────
    TEMPERATURE: float = 0.5
    TOP_P: float = 0.8
    TOP_K: int = -1
    MAX_TOKENS: int = 128_000
    FREQUENCY_PENALTY: float = 0.0
    PRESENCE_PENALTY: float = 0.0

    # ── OCI Object Storage (used by SpeechPipeline) ───────────────────────────
    BUCKET_NAMESPACE: str = ""
    BUCKET_NAME: str = ""
    BUCKET_FILE_PREFIX: str = "audio/"
    SPEECH_BUCKET_OUTPUT_PREFIX: str = "transcripts/"

    ## Other config params
    ORACLE_LOGO = "app_images/oracle_logo.png"
    UPLOAD_PATH = "uploaded_files"
    GENAI_MODELS = {
        "OpenAI GPT-OSS 120b": "openai.gpt-oss-120b",
        "OpenAI GPT-OSS 20b": "openai.gpt-oss-20b",

    }
    LIST_GENAI_MODELS = list(GENAI_MODELS.keys())

