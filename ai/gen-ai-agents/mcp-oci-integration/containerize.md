# Run MCP server in a container
Here you'll find the step-by-step instructions to build a container where you run your MCP server

Details:
* all variables (ENABLE_JWT_TOKENS...) passed from the environment at start
* ready to use JWT tokens
* instructions to start with **docker-compose**

### Project Layout
```
mcp-server/
├─ app.py                  # your code (rename from the snippet if needed)
├─ config.py               # reads env vars (see below)
├─ requirements.txt
├─ Dockerfile
├─ .dockerignore
└─ docker-compose.yml      # optional convenience
```

### config.py
```
import os

def _bool(env, default="false"):
    return os.getenv(env, default).strip().lower() in {"1", "true", "yes", "y"}

# Security / JWT (optional)
ENABLE_JWT_TOKEN = _bool("ENABLE_JWT_TOKEN", "false")
IAM_BASE_URL     = os.getenv("IAM_BASE_URL", "")       # e.g., https://idcs-xxx.identity.oraclecloud.com
ISSUER           = os.getenv("ISSUER", "")             # e.g., https://idcs-xxx.identity.oraclecloud.com/
AUDIENCE         = os.getenv("AUDIENCE", "")           # e.g., your-api-audience

# Transport
TRANSPORT = os.getenv("TRANSPORT", "streamable-http")  # "stdio" or "streamable-http"
HOST      = os.getenv("HOST", "0.0.0.0")
PORT      = int(os.getenv("PORT", "8080"))

# Oracle DB (thin mode – no Instant Client required)
# Use only if/when you actually connect in your tools
ADB_USER     = os.getenv("ADB_USER", "")
ADB_PASSWORD = os.getenv("ADB_PASSWORD", "")
ADB_DSN      = os.getenv("ADB_DSN", "")  # e.g., "myadb_tp.adb.eu-frankfurt-1.oraclecloud.com"
```

### requirements.txt
```
fastmcp>=2.10.0
oracledb>=2.4.0
uvicorn>=0.30.0  # handy for local testing; FastMCP can run HTTP itself
```

### Dockerfile
```
# ---- build stage (to isolate deps if you add extras later) ----
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System updates + runtime deps (keep minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl tini && \
    rm -rf /var/lib/apt/lists/*

# Create app user and dir
RUN useradd -m -u 10001 appuser
WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app.py config.py ./

# Expose only for streamable-http mode
EXPOSE 8080

# Healthcheck (simple TCP hit if HTTP mode)
HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD sh -c 'test "${TRANSPORT}" = "streamable-http" && nc -z localhost ${PORT:-8080} || exit 0'

# Drop privileges
USER appuser

# Entrypoint via tini for signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command: streamable-http (override as needed)
CMD ["python", "app.py"]
```

### .dockerignore
```
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
.env
.git
.gitignore
venv/
.idea/
.DS_Store
```

### Build the image
```
docker build -t mcp-fastmcp-oracle:latest .
```

### Run (with streamable-http)
```
docker run --rm -it \
  -e TRANSPORT=streamable-http \
  -e HOST=0.0.0.0 \
  -e PORT=8080 \
  -e ENABLE_JWT_TOKEN=true \
  -e IAM_BASE_URL="https://idcs-EXAMPLE.identity.oraclecloud.com" \
  -e ISSUER="https://idcs-EXAMPLE.identity.oraclecloud.com/" \
  -e AUDIENCE="your-audience" \
  -p 8080:8080 \
  --name mcp-http \
  mcp-fastmcp-oracle:latest
```

### docker-compose-yml
```
version: "3.9"
services:
  mcp:
    image: mcp-fastmcp-oracle:latest
    container_name: mcp-http
    environment:
      TRANSPORT: "streamable-http"
      HOST: "0.0.0.0"
      PORT: "8080"
      ENABLE_JWT_TOKEN: "true"
      IAM_BASE_URL: "https://idcs-EXAMPLE.identity.oraclecloud.com"
      ISSUER: "https://idcs-EXAMPLE.identity.oraclecloud.com/"
      AUDIENCE: "your-audience"
      # DB (only if you actually use oracledb in your tools)
      ADB_USER: "myuser"
      ADB_PASSWORD: "mypassword"
      ADB_DSN: "myadb_tp.adb.eu-frankfurt-1.oraclecloud.com"
    ports:
      - "8080:8080"
    restart: unless-stopped
```

```
docker compose up -d
```
