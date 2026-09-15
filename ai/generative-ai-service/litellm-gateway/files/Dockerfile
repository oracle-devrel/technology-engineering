# LiteLLM proxy image + OCI SDK (for the OCI Guardrails hook) + Langfuse
FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app

# The upstream image ships a venv without pip; bootstrap it first.
RUN python3 -m ensurepip && \
    python3 -m pip install --no-cache-dir "oci>=2.150.0" "langfuse>=3.0.0"

COPY config/ /app/config/
COPY guardrails/ /app/guardrails/

# Image entrypoint is `litellm`
CMD ["--config", "/app/config/config.yaml", "--port", "4000"]
