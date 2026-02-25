# Aider Integration with Oracle Code Assist (OCA)
Aider is a command-line tool (CLI) that leverages AI to help developers modify and write code. It enables users to chat with AI directly from their terminal, allowing for code edits, suggestions, and explanations in their project files through conversational interaction. Aider integrates with local Git repositories, making it easy to review and manage code changes proposed by the AI. 

## Key Features
* Interactive code editing with AI suggestions and explanations 
* Works changes and integrates with Git for version control 
* Can automate code refactoring, documentation, bug fixes, and more 

## Resources
* Request [access](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/Forms/AllItems.aspx?viewid=523d1542-44f5-4efc-b685-82d6467c3829\&id=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/How%20to%20Request%20Entitlements%20for%20Oracle%20Code%20Assist%20Models.pdf\&parent=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers) to more AI models
* Download the latest [OCA on Aider client](https://oracle.sharepoint.com/:f:/r/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Plugin%20Downloads/Aider%20-%20CLI?csf=1\&web=1\&e=aPt5Ra)
* View [OCA on Aider guide](https://oracle.sharepoint.com/:f:/r/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Installation%20Guides?csf=1\&web=1\&e=ylt36M) for **detailed setup instructions**
* For more information, please visit the [Aider website](https://aider.chat/docs/)

## Step-by-Step Guide
### 1. **Request Access to OCA Models**
* Prior to installation, request entitlements for the desired OCA models by following the guide in the PDF (e.g., via Oracle's internal process). This grants access to Oracle's AI models within Aider.

### 2. **Install Aider (ocaider)**
* Download the latest `ocaider_chat-0.1.3-py3-none-any.whl` file from the provided Oracle [SharePoint link](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/Forms/AllItems.aspx?csf=1&web=1&e=cwasJL&CID=b1be9fa4%2D6ac6%2D4e2d%2D9eef%2D58fde111effc&FolderCTID=0x01200008E7535C0D00CD448E4A8499AAC8B8AE&id=%2Fsites%2Fai%2Dfor%2Demployees%2FShared%20Documents%2FAI%20for%20Engineers%2FPlugin%20Downloads%2FAider%20%2D%20CLI).

* **Option 1: Install with uv (Recommended for Python 3.8-3.13)**:
  * Install uv if needed: `python -m pip install uv`.
  * Run: `uv tool install --force --python python3.12 --with pip ocaider_chat-0.1.3-py3-none-any.whl`.
  * This handles Python versioning automatically.

* **Option 2: Install with pipx (For Python 3.9-3.12)**:
  * Install pipx if needed: `python -m pip install pipx`.
  * Run: `pipx install ocaider_chat-0.1.3-py3-none-any.whl`.

### 3. **Basic Setup and Model Selection**
* Launch Aider: Run `ocaider` in your terminal from your project's Git repository directory.
* **Before Starting**: List available models with `ocaider --list-models oca` and select an OCA model (e.g., `ocaider --model oca/gpt-4.1`). is the default and only recommended provider; avoid others.
* **During Runtime**: Use in-chat commands like `/models oca` to list and `/model oca/openai-o3` to switch models.

### 4. **General Usage and Key Commands**
* Add files to edit: Include them on the command line (e.g., `ocaider file1.py file2.js`) or use `/add filename` in-chat. Aider auto-includes related context; avoid adding unnecessary files to prevent token overload.
  
* Interact conversationally: Describe tasks (e.g., "Refactor this function"). Aider suggests edits, integrates with Git for reviews, and tracks changes.

* Essential Commands:
  * `/help`: List commands or get dynamic help (e.g., `/help What is the best way to use Aider?`).
  * `/ask`: Switch to query-only mode without editing files.
  * `/code`: Default mode for code modifications.
  * `/architect`: For high-level task guidance.
  * `/clear`: Reset chat history; `/drop`: Remove files from context.
  * `!` or `/run`: Execute terminal commands (e.g., `!git status`).
  * Reference code elements: Type file/method names for autocomplete and context.

* Include Rules/Conventions: Load a file like `CONVENTIONS.md` with `--read` on startup or `/read` in-chat for persistent guidance.

### 5. **Advanced Tips**
* **Verbose Mode**: Run `ocaider --verbose` for detailed logs of AI interactions if responses seem off.
* **IDE Integration**: Use `--watch-files` to monitor repo files for AI comments (e.g., `# Make a snake game. AI!` triggers edits; `AI?` asks questions).
* Work in your project's Git repo for seamless version control.

### 6. **Troubleshooting**
* For issues, run `/opc-request-id` to get the request ID and include it when reporting to the OCA team (attach chat history).
* Common fixes: Ensure Git integration, limit file additions, or check Python compatibility. Refer to the PDF's troubleshooting section or Aider docs for errors like model access or command failures.

This setup enables terminal-based AI coding assistance with OCA, focusing on secure, compliant use at Oracle. Always select only Oracle providers. For advanced coding support,. offers enhanced tools. join the `#help-oracle-genai-chat` Slack channel for more info.
