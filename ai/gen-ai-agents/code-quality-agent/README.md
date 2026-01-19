# Code Quality Agent

A lightweight **LangGraph-based** agent that scans a local codebase (read-only) to:

- ✅ **Check file headers** against a simple template policy
- ✅ **Scan for secrets** (heuristic patterns + suspicious assignments)
- ✅ **Check for license**
- ✅ **Check for dependencies licenses**
- ✅ **Generate header fixes**
- ✅ **Generate per-file documentation** (optional) in Markdown via an LLM (OCI GenAI via LangChain)

It produces artifacts in a separate output folder (no in-place edits).


---

## Features

### Header policy checks
For each discovered source file, the agent validates that a header block contains:

- `File name:`
- `Author:`
- `Date last modified:`
- `Python Version:`
- `Description:`
- `License:`

It also performs a **date alignment check** (header date vs. file `mtime` in UTC) when the file path is available.

### Secrets scanning (heuristic)
The agent searches each file for:
- known patterns (AWS keys, GitHub tokens, OCI OCIDs, private key blocks, bearer headers, etc.)
- suspicious string assignments / dict values with sensitive names (password, token, secret, api_key, …)

Findings are reported with:
- kind
- line number
- a redacted excerpt

### License check
Check that an approved LICENSE file is provided.

### Header fix generation
For each of the files where the header check fails, provide the snippet suggested to use.
- modifiy the Author field
- check the rest.

### Per-file doc generation (LLM)
For each Python file, the agent can generate Markdown documentation with sections such as:
- overview
- public API
- behaviors/edge cases
- side effects
- usage examples
- risks/TODOs

### Report generation
A final summary report is also generated, in Markdown.

### Languages supported
For now, tests have been done using:
- Python

---

## Repository layout

```text
.
├── agent/
│   ├── graph_agent.py        # LangGraph pipeline (discover → check → scan → docgen → report)
│   ├── fs_ro.py              # Read-only sandboxed filesystem access
│   ├── header_rules.py       # Header policy checker
│   ├── secrets_scan.py       # Heuristic secrets scanner
│   ├── docgen.py             # Per-file documentation generation
│   ├── docgen_prompt.py      # Prompts for doc generation + final report
│   ├── docgen_utils.py       # LLM invocation + output normalization
│   ├── oci_models.py         # OCI GenAI / OCI OpenAI LangChain adapters
│   └── utils.py              # Logging helpers, etc.
├── out/                      # Default output folder (generated artifacts)
├── run_agent.py              # CLI entry point
├── run_agent.sh              # Convenience runner
├── requirements.txt
└── LICENSE
```

## Setup
1. Create a python 3.11+ environment

For example, 
```
conda create -n code_quality_agent python==3.11
```

activate the environment. If you're using conda:
```
conda activate code_quality_agent
```

2. Install the following python libraries:
```
pip install oci -U
pip install langchain -U
pip install langchain-oci -U
pip install langgraph -U
```

3. Clone this repository
```
git clone https://github.com/luigisaetta/code_quality_agent.git
```

4. Create a config_private.py file, in the agent directory.

Start from the template provided in the repository and create a **config_private.py** file.
Put in the file your compartment's OCID.


5. Have your local OCI config setup

Setup under $HOME/.oci
See: https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm

6. Set policies to use Generative AI

See: https://docs.oracle.com/en-us/iaas/Content/generative-ai/iam-policies.htm

Ask your tenancy admin for help.

## How-to use it
Modify the [run_agent.sh](./run_agent.sh) file. 

Change the params:
- root (root directory for all the files to be scanned)
- out: with the full path to the output dir

run 
```
run_agent.sh
```

## Dependency License Checks – Execution Requirements

This agent checks license compliance for direct Python dependencies listed in `requirements.txt`.

### Recommended (deterministic & fast)
Run the agent in an environment where:
- All dependencies from `requirements.txt`, from the project to-be-scanned, are installed
- Agent runtime dependencies (see Setup above) are installed

This allows the agent to read license data from installed package metadata:
- Offline execution
- Faster and reproducible results  
**Recommended for CI and release validation.**

### Fallback (best-effort)
If some dependencies are not installed:
- Network access is required (the agent will do a PyPI JSON lookup)
- Execution may be slower
- License data may be incomplete or ambiguous

## Important Note on Results and Human Review

This agent is intended to **assist** with code quality, security, and license compliance checks, **not to replace entirely human judgment**.

While the agent applies deterministic rules and best-effort analysis, it may produce:
- **False positives** (e.g. ambiguous licenses, heuristic PII detection, conservative policy checks)
- **Incomplete results** depending on the execution environment (installed dependencies, network access, metadata quality)

For this reason:
- **All findings must be reviewed and validated by a human**
- The agent’s output should be treated as an **input to review**, not a final decision
- Final responsibility for compliance, security, and legal interpretation always remains with the user

This is especially important for compliance-critical areas such as **licenses, personal data (PII), and security findings**.

