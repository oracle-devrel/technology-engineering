# Architecture

The completed agent uses one AIDP visual flow.

```text
Chat Trigger → AIDP Agent
                 ├─ Select AI Custom Tool → Autonomous Database MCP → Select AI profile/table
                 └─ HTTP tool → OCI Generative AI Vector Store → retrieved document passages
```

The custom Python tool gets the database username/password from AIDP Credential Store and requests a short-lived database token at runtime. The HTTP tool calls the Vector Store search endpoint with the Generative AI API key. AIDP Compute runs both tool calls under the workspace's egress rules.

The agent combines the returned rows and passages into one answer. The vector-store key and caller authentication for a deployed AIDP endpoint are separate credentials. Neither belongs in source code or a browser app.
