FROM python:3.13-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ARG ORACLE_MCP_REF=f0f7862bff4b52676354688c9ac8d3fd03a1b1a2
ARG LOGAN_MCP_REF=ca98c3d094086d685dc3689bd633356db9294a0f
RUN git init /src/oracle && git -C /src/oracle remote add origin https://github.com/oracle/mcp.git && git -C /src/oracle fetch --depth 1 origin "$ORACLE_MCP_REF" && git -C /src/oracle checkout --detach FETCH_HEAD
RUN git init /src/logan && git -C /src/logan remote add origin https://github.com/rishabh-ghosh24/logan-mcp-server.git && git -C /src/logan fetch --depth 1 origin "$LOGAN_MCP_REF" && git -C /src/logan checkout --detach FETCH_HEAD
WORKDIR /app
COPY pyproject.toml /app/
COPY assistant /app/assistant
RUN python -m venv /opt/app && /opt/app/bin/pip install --no-cache-dir /app
# Upstream DBO pins OCI 2.182.1 while this common package requires >=2.185.
# Resolve the runtime explicitly, then install the DBO wheel without its conflicting pin.
RUN python -m venv /opt/db && /opt/db/bin/pip install --no-cache-dir /src/oracle/src/common fastmcp==3.4.5 pydantic==2.13.4 oci==2.185.0 jsonschema==4.26.0 && /opt/db/bin/pip install --no-cache-dir --no-deps /src/oracle/src/oci-db-observability-mcp-server
# Avoid duplicate package-data entries in the pinned upstream Hatch wheel metadata.
RUN sed -i '/packages = \["src\/oci_logan_mcp"\]/a exclude = ["/src/oci_logan_mcp/data/**"]' /src/logan/pyproject.toml
RUN python -m venv /opt/logan && /opt/logan/bin/pip install --no-cache-dir /src/logan

FROM python:3.13-slim
RUN groupadd -g 10001 assistant && useradd -u 10001 -g 10001 -d /data/runtime assistant && mkdir -p /data /config && chown -R 10001:10001 /data
COPY --from=build /opt /opt
WORKDIR /app
COPY assistant /app/assistant
COPY skills /app/skills
COPY prompts /app/prompts
COPY static /app/static
COPY scripts /app/scripts
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app HOME=/data/runtime
USER 10001:10001
EXPOSE 8000
CMD ["/opt/app/bin/uvicorn", "assistant.web:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-access-log"]
