# 🚀 OCI Enterprise AI Agents

Build, orchestrate, and run **production-grade AI agents** on Oracle Cloud Infrastructure (OCI).

OCI Enterprise AI Agents (formerly *Agent Hub*) is Oracle’s fully managed platform for designing, deploying, and operating **enterprise-ready, tool-using, multi-step AI agents** with built-in orchestration, memory, governance, and observability.

---

## 📌 What are Enterprise AI Agents?

Enterprise AI Agents are **goal-driven systems** that can:
- Reason through complex tasks  
- Use tools (RAG, search, APIs, code execution)  
- Maintain memory across interactions  
- Execute multi-step workflows  
- Deliver real business outcomes (not just responses)  

Unlike chatbots, these agents **take actions** and integrate deeply with enterprise systems.

---

## ✨ Key Capabilities

### 🧠 Agent Runtime
- Multi-step reasoning & orchestration  
- Tool invocation (RAG, NL2SQL, APIs, Code Interpreter)  
- Stateful execution with short-term & long-term memory  

### 🔌 Built-in Tools
- Web Search  
- File Search (RAG)  
- NL2SQL  
- Code Interpreter  
- Function Calling / API integration  
- MCP (Model Context Protocol) support  

### 📦 Managed Infrastructure
- Vector Stores (fully managed)  
- File & data handling APIs  
- Secure execution environment  

### 🔐 Enterprise-Grade Governance
- OCI IAM integration  
- Audit logging & traceability  
- Policy enforcement & guardrails  

### 📊 Observability
- OpenTelemetry-based tracing  
- (Upcoming) Managed Langfuse integration  

---

## 🏗️ Architecture Overview

```
User / Application
        ↓
OCI Enterprise AI Agents (Runtime)
        ↓
-----------------------------------------
|  Models  |  Tools  |  Memory  |  Data  |
-----------------------------------------
        ↓
OCI Services (DB, Object Storage, OIC, OAC, etc.)
```

---

## 🧑‍💻 Who is this for?

- Developers & Architects building agentic workflows  
- Enterprise IT teams automating operations  
- Business teams (HR, Finance, CX, Supply Chain)  
- AI/ML teams building production-grade GenAI systems  

---

## ⚡ Use Cases

### 🔹 IT & Operations
- Incident troubleshooting  
- Log analysis & auto-healing  
- API debugging  

### 🔹 Business Automation
- HR assistants  
- Finance reconciliation  
- Procurement workflows  

### 🔹 Data & Analytics
- RAG-based enterprise search  
- NL → SQL reporting  
- Insight generation  

### 🔹 Industry Solutions
- Telecom support agents  
- Banking compliance agents  
- Healthcare assistants  

---

## 🛠️ Getting Started

### 🔗 Useful Examples

Explore official Oracle samples for working with OCI Generative AI (authentication, SDK usage, and model calls):

👉 https://github.com/oracle-samples/oci-genai-auth-python/tree/main/examples

### Prerequisites
- OCI Account  
- Access to OCI Generative AI / Enterprise AI services  
- Python 3.9+ (or your preferred language)  

---

### 📥 Installation

```bash
git clone https://github.com/<your-repo>/oci-enterprise-ai-agents.git
cd oci-enterprise-ai-agents
pip install -r requirements.txt
```

---

### ⚡ Quick Start Example

```python
from oci_agent import Agent

agent = Agent(
    model="gpt-4o",
    tools=["file_search", "nl2sql"],
)

response = agent.run("Analyze last quarter sales and summarize insights")

print(response)
```

---

## 📂 Repository Structure

```
.
├── examples/
│   ├── basic-agent/
│   ├── rag-agent/
│   ├── nl2sql-agent/
│   └── multi-agent/
├── notebooks/
├── utils/
├── docs/
└── README.md
```

---

## 🔄 Deployment Options

OCI Enterprise AI Agents supports flexible deployment:

- Self-Hosted – Full control within your environment  
- Customer-Managed – OCI-managed setup with your control  
- Fully Hosted – Fully managed by Oracle  

---

## 🔗 Integration Ecosystem

Works seamlessly with:
- Oracle Database  
- OCI Object Storage  
- Oracle Integration Cloud (OIC)  
- Oracle Analytics Cloud (OAC)  
- Fusion Applications  
- External APIs via MCP / Function Calling  

---

## 🌍 Open & Flexible

Supports frameworks like:
- LangChain  
- LangGraph  
- AutoGen  
- LlamaIndex  

Supports open standards:
- MCP (Model Context Protocol)  
- A2A (Agent-to-Agent)  

---

## 📈 Roadmap (Highlights)

- Managed Langfuse (Observability)  
- GenAI Skills API  
- Agent Builder (Low-code / No-code)  
- Dynamic Model Routing  
- GenAI Sandboxes  

---

## 🤝 Contributing

We welcome contributions!  

```bash
# Create a branch
git checkout -b feature/your-feature

# Commit changes
git commit -m "Add new agent example"

# Push and create PR
git push origin feature/your-feature
```

---

## 📄 License

MIT License (or your preferred license)

---

## 📢 Final Thoughts

OCI Enterprise AI Agents enables teams to move from:
> “Building demos” → “Running production-grade AI systems”

Focus on what your agents do, not how they run.

---

## ⭐ Stay Connected

- Follow Oracle Cloud updates  
- Watch this repo for new examples  


