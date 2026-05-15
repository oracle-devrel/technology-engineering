# AGNTCY — The Agent Internet of Things

> **AGNTCY** is an open-source initiative under the **Linux Foundation**, building the foundational stack for an **Internet of Agents (IoA)** — enabling AI agents from different vendors, environments, and frameworks to **discover, identify, communicate, and collaborate securely**.

---

## 🧭 Overview

AGNTCY provides the **infrastructure layer** for agent interoperability — much like TCP/IP did for the internet.  
It defines open standards and reference implementations for:

- **Agent discovery and directory services**
- **Verifiable identity and credentials**
- **Secure low-latency messaging**
- **Observability and evaluation**
- **Schema and capability modeling**

Originally incubated by **Cisco’s Outshift division**, AGNTCY was **donated to the Linux Foundation (2025)** to ensure vendor neutrality and ecosystem adoption.

---

## 🏗️ Technical Architecture

AGNTCY is structured as a modular, multi-layered system:

| Layer | Component | Description |
|-------|------------|-------------|
| **1. Discovery** | **Agent Directory Service (ADS)** | Distributed registry for publishing and discovering agent metadata, capabilities, and endpoints. |
| **2. Identity** | **Decentralized Identity Framework** | Uses DIDs and Verifiable Credentials (VCs) for agent authentication and authorization. |
| **3. Messaging** | **SLIM Protocol** (Secure Low-latency Interactive Messaging) | Defines how agents communicate interactively and securely, with multi-protocol support (A2A, MCP, etc.). |
| **4. Observability** | **Monitoring & Evaluation Layer** | End-to-end tracing, metrics, and benchmarking across multi-agent workflows. |
| **5. Schema** | **OASF (Open Agentic Schema Framework)** | Defines standardized schemas for describing agent capabilities, APIs, and metadata. |

---

## ⚙️ Discovery & Directory Architecture

The **Agent Directory Service (ADS)** is the cornerstone of AGNTCY.

### Features
- Distributed, peer-to-peer directory built on a **Kademlia-like DHT** (Distributed Hash Table).
- Supports **capability-based indexing** and **content-addressable metadata**.
- Metadata is **cryptographically signed** and **verifiable**.
- Uses **OCI/ORAS registry infrastructure** to store agent artifacts.
- Provides **gRPC and Protocol Buffers APIs** for lookup, registration, and synchronization.
- Supports **federation** between multiple directory instances.

### Workflow
1. An agent registers metadata (following OASF schema) into the directory.
2. The directory node validates, signs, and publishes the record.
3. Other agents query by capability, domain, or schema.
4. Lookup returns endpoints, credentials, and metadata pointers.

### Example Query
```bash
agntcy dir search capability="data-analysis"
```

---

## 🔐 Identity & Credentials

AGNTCY’s **identity framework** ensures trust, provenance, and accountability between autonomous agents.

### Core Mechanisms
- **Decentralized Identifiers (DIDs)** for agent identity.
- **Verifiable Credentials (VCs)** representing trust, capability, and roles.
- **Cryptographic keypairs** for message signing and authentication.
- **Integration with external IdPs** (Okta, Auth0, Microsoft AD) or local issuance.

### Identity Lifecycle
1. Agent requests or is assigned a DID.
2. Agent receives VCs signed by an issuer.
3. Directory verifies identity during registration.
4. Messaging layer uses identity for mutual authentication.

> **Open issue:** Revocation and key rotation are under development; credential lifecycle management is not yet fully standardized.

---

## 📡 Messaging Protocol (SLIM)

**SLIM — Secure Low-latency Interactive Messaging**  
A next-generation transport protocol for interactive multi-agent communication.

### Features
- Designed for **real-time, multi-modal messaging** (text, JSON, structured payloads).
- Built for **low-latency, encrypted** communication.
- Compatible with **existing standards**:
  - **A2A (Agent-to-Agent)** protocol
  - **MCP (Model Context Protocol)**
- Supports **hybrid messaging** — agents can interact even if they use different protocols.
- All messages are **signed, encrypted**, and **traceable**.

### Architecture Diagram (Simplified)

```
[Agent A] ←→ [SLIM Router / Gateway] ←→ [Agent B]
     ↑              ↑                         ↑
  DID Auth    TLS + Signatures           Identity Verify
```

> SLIM implementations are currently in early development; expect evolving APIs and message formats.

---

## 🔭 Observability & Evaluation

AGNTCY defines **standard observability hooks** for cross-agent visibility:

- **Distributed tracing:** Monitor request/response across agent workflows.
- **Metrics:** Measure latency, throughput, success/failure rates.
- **Logging:** Structured, identity-linked logs for compliance and debugging.
- **Evaluation:** Built-in benchmarking and behavioral scoring for agents.

### Observability Stack
- Uses **OpenTelemetry** for tracing.
- Exports metrics to **Prometheus** or equivalent backends.
- Supports **correlation IDs** for linking events across asynchronous agents.

> A key goal is to ensure **auditable, privacy-aware observability** — maintaining accountability without exposing sensitive agent data.

---

## 🧩 Schema Layer — OASF (Open Agentic Schema Framework)

OASF defines how agents describe themselves.

### Highlights
- YAML/JSON schema standard for:
  - Agent name, purpose, owner
  - Capabilities & interfaces
  - Supported modalities & APIs
  - Trust attributes & compliance tags
- **Extensible:** Supports domain-specific extensions.
- **Versioned:** Maintains backward compatibility.

### Example
```yaml
agent:
  id: did:agntcy:12345
  name: "Data Insight Agent"
  capabilities:
    - data_query
    - visualization
  endpoint: https://example.org/slim
  credentials:
    issuer: "did:agntcy:root"
    trust_level: "verified"
```

---

## 🧰 Development Stack & Tooling

AGNTCY’s reference implementation is **cloud-native** and primarily written in **Go**.

### Core Technologies
| Area | Technology |
|-------|-------------|
| Language | Go (Golang) |
| API Layer | gRPC + Protocol Buffers |
| Schema | OASF (JSON/YAML) |
| Containerization | Docker, ORAS |
| Deployment | Kubernetes / kind |
| Build Tools | Taskfile, Makefile |
| Security | Sigstore, Cosign |
| Observability | OpenTelemetry, Prometheus |

### SDKs & CLI Tools
- **`agntcy-cli`** — Register, discover, and manage agents.
- **SDKs (in progress):**
  - Go SDK (reference)
  - Python and TypeScript bindings planned
- **Schema Tools:**
  - OASF Validator
  - Schema Server with hot-reload

### Example (Agent Registration)
```bash
agntcy agent register --schema agent.yaml --sign-key mykey.pem
```

---

## ☁️ Deployment Topologies

AGNTCY components can run in multiple environments:

| Mode | Description |
|------|--------------|
| **Local Dev** | Single-node ADS with CLI tools (for prototyping). |
| **Cloud / K8s** | Multi-node DHT directory with federation. |
| **Hybrid Edge** | Lightweight nodes running on edge devices, syncing with core directory. |

Each component is **containerized** and exposes health/metrics endpoints for orchestration systems.

---

## 🧠 Integration & Interoperability

AGNTCY is designed to **interoperate with existing ecosystems**, not replace them.

Supported or targeted integrations include:

- **OpenAI MCP** (Model Context Protocol)
- **LangChain / LangGraph agents**
- **A2A protocol**
- **OCI AI and Vector Stores**
- **OpenTelemetry / Prometheus**
- **Sigstore / Cosign** for supply chain security

This allows enterprise agents, cloud agents, and on-device agents to coexist within a unified trust and discovery fabric.

---

## ⚠️ Challenges & Open Questions

| Area | Challenge |
|-------|-----------|
| **Scalability** | DHT synchronization and lookup latency under high churn. |
| **Identity Lifecycle** | Revocation, key rotation, and delegation mechanisms are immature. |
| **Schema Governance** | Maintaining OASF version compatibility across vendors. |
| **Security** | Preventing malicious agent impersonation or directory poisoning. |
| **Observability Privacy** | Balancing transparency with data protection. |
| **Ecosystem Adoption** | Network effects: utility grows only with broad adoption. |

---

## 🧩 Repository References

| Repo | Description |
|------|--------------|
| [github.com/agntcy/dir](https://github.com/agntcy/dir) | Agent Directory Service implementation (Go) |
| [github.com/agntcy/oasf](https://github.com/agntcy/oasf) | Open Agentic Schema Framework |
| [agntcy.org](https://agntcy.org) | Official website |
| [docs.agntcy.org](https://docs.agntcy.org) | Developer documentation |
| [Outshift Blog](https://outshift.cisco.com/blog) | Technical articles by Cisco engineers |

---

## 🧭 Conclusion

AGNTCY is **laying the groundwork for a decentralized, interoperable Internet of Agents** — combining distributed discovery, verifiable identity, and secure messaging into a coherent architecture.

While **technically promising**, it remains **early-stage**:
- Core protocols (SLIM, OASF) are evolving.
- SDKs are limited.
- Real-world scalability and revocation handling are open issues.

However, its **architecture, neutrality, and governance model** position it as a **credible foundation for large-scale agent ecosystems** — the “TCP/IP for AI Agents”.

---

**Last Updated:** October 2025  
**Sources:** Linux Foundation, Outshift Cisco, AGNTCY.org, ArXiv 2509.18787, GitHub repositories.
