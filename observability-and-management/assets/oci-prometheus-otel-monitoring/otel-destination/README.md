# OTEL Destination Stack (test / reference)

A self-contained **OpenTelemetry Collector → Prometheus → Grafana** stack that
stands in for "the user's OTEL collector / Prometheus / Grafana / 3rd-party tool".
Use it to validate the proxy's OTEL export end-to-end, or as a reference for what
the receiving side looks like.

```
proxy OTEL Collector ──OTLP/HTTP(4318)──▶ otel-collector ──remote_write──▶ prometheus ──▶ grafana
proxy OTEL Collector ──remote_write(9090/api/v1/write)──────────────────▶ prometheus ──▶ grafana
```

## Run

```bash
# On a Docker host (Ubuntu): see cloud-init-docker.sh to install Docker, then:
cd otel-destination
docker compose up -d
```

Ports: Grafana **3000** (anonymous admin, light theme), Prometheus **9090**
(remote-write receiver enabled), OTEL Collector OTLP **4317/4318**.

## Point the proxy at it

In the proxy `config.json` (or the script prompts):

```json
"OtelEnabled": true,
"OtelOtlpEndpoint": "http://<DEST_HOST>:4318",
"OtelPromRemoteWriteEndpoint": "http://<DEST_HOST>:9090/api/v1/write"
```

## Verify

- Prometheus: `http://<DEST_HOST>:9090/api/v1/label/__name__/values` should list
  `node_*` and `windows_*` series.
- Grafana: dashboard **"OCI Prometheus → OTEL → Grafana (e2e test)"**.

> Security note: this stack is wide open (anonymous Grafana, no TLS/auth) for test
> convenience. Do not expose it publicly; lock it down for any real use.
