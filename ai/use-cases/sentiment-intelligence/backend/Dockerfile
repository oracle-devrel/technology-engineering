FROM python:3.11-slim

WORKDIR /app

# libaio1 is required by python-oracledb when it runs in Thick mode; harmless
# for the default Thin mode used for walletless TLS connections.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libaio1 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run the FastAPI app. Configuration (DB, Select AI, OCI GenAI) is supplied via
# environment variables / the Kubernetes secret at runtime.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
