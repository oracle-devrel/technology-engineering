# Codex Integration with Oracle Code Assist (OCA)
Codex is an AI coding assistant, integrated as a plugin into Visual Studio Code (VS Code), that accelerates development with context‑aware code generation and in‑editor assistance.

## Key Features
* Provides context‑aware inline code completions and multi‑line suggestions
* Converts natural language prompts into code (functions, snippets, SQL, regex)
* Explains code and errors; proposes fixes, refactors, tests, and documentation
* Adapts to project context (open files and recent edits) across many languages and frameworks
* Fits seamlessly into VS Code workflows with quick accept/edit flows and chat‑based assistance

## Resources
* Request [access](https://confluence.oraclecorp.com/confluence/display/AICODE/How+to+Request+Entitlements+for+Oracle+Code+Assist+Models) to OCA
* View [OCA on Codex ](https://oracle.sharepoint.com/sites/ai-for-employees/SitePages/Oracle-Code-Assist.aspx)for **detailed setup instructions**
* For more information, please visit: [developers.openai.com/codex/ide](https://developers.openai.com/codex/ide/)

## Step-by-Step Guide
#### 1. **Prerequisites**
* Request access to OCA API Key and specific models (e.g., via the "[How to Request Entitlements for Oracle Code Assist Models](https://confluence.oraclecorp.com/confluence/display/AICODE/How+to+Request+Entitlements+for+Oracle+Code+Assist+Models)" guide). Without these, you'll encounter errors.
* For Windows users, consider using Windows Subsystem for Linux (WSL) for Codex CLI compatibility.

#### 2. **Install Codex CLI**
* Download and install Codex CLI from the official OpenAI site: [https://developers.openai.com/codex/cli/ ](https://developers.openai.com/codex/cli/).
* Create a `.codex` folder in your home directory if it doesn't exist.
* Download the OCA-specific `config.toml` file (overwrite/create it in `~/.codex/`) with the provided content from the [Codex Setup PDF](https://oracle.sharepoint.com/sites/ai-for-employees/SitePages/Oracle-Code-Assist.aspx). This includes OCA endpoints, model providers (e.g., `oca-responses`, `oca-chat`), and profiles for models like `gpt-5-codex`, `grok-4`, etc. Key settings: Set `model = "oca/gpt-5-codex"` and `profile = "gpt-5-codex"` as defaults; enable `web_search_request = true` and `trust_level = "trusted"`.
* Generate an OCA API Key: Visit [https://apex.oraclecorp.com/pls/apex/r/oca/api-key/home ](https://apex.oraclecorp.com/pls/apex/r/oca/api-key/home), generate the key, and copy the "Codex Environment Setup Command" (e.g., `echo <api_key> | codex login --with-api-key`). Run it in your terminal.
  * **Important**: The API Key expires every 7 days; regenerate weekly to avoid errors.

#### 3. **Run and Configure Codex CLI**
* Launch with the default profile: Run `codex` in your terminal (uses `gpt-5-codex` by default).
* Avoid running `/review` or other commands without OCA config; redownload if needed.
* Change Models: Edit `~/.codex/config.toml` to update `model` and `profile` (e.g., `model = "oca/grok-code-fast-1"` and `profile = "grok-code-fast-1"`). Then run `codex -p <profile_name>` (e.g., `codex -p grok-code-fast-1`). Restart the session for changes to apply. Request access if a model is unavailable.
* Interact: Use conversational prompts for code tasks; Codex integrates with your local workspace and Git for edits and reviews.

#### 4. **Install Codex IDE Extension in VS Code (Optional, Builds on CLI)**
* **Prerequisites**: Complete Codex CLI installation first, as the extension relies on it.
* In VS Code, go to Extensions > Search for "Codex" > Install "Codex - OpenAI's coding agent".
* Generate/Regenerate OCA API Key as in Step 2 (weekly refresh required).
* Configure the Extension:
  * Open the Codex sidebar in VS Code.
  * Click the gear icon > "Sign in with ChatGPT" > "Use API Key."
  * Paste your OCA API Key and proceed through setup screens.

* The extension uses the default CLI profile (`gpt-5-codex`); changes won't apply dynamically; edit `~/.codex/config.toml` as in Step 3 and restart VS Code.

#### 5. **Test and Troubleshoot**
* In CLI: Run `codex` and test a simple prompt (e.g., code generation). In VS Code: Open the chat window and query OCA models.

* Common Issues and Fixes:
  * Errors like "no access to default model": Switch profiles (e.g., `codex -p gpt-5`) or request entitlements.
  * Login/API failures: Regenerate the API Key; ensure OCA-specific config is loaded.
  * Model changes not applying: Restart the tool/session and verify `config.toml`.
  * For advanced config (e.g., approval policies, sandbox mode), refer to [https://developers.openai.com/codex/config-advanced](https://developers.openai.com/codex/config-advanced).

* Always use OCA profiles/models; avoid external ones for compliance.

This setup allows secure, OCA-powered coding in your terminal or VS Code, emphasizing local execution and Git integration. Adhere to Oracle's data policies. For complex coding tasks, gentle reminder: Oracle Code Assist offers advanced AI-powered coding support; join the `#help-oracle-genai-chat` Slack channel for more information.
