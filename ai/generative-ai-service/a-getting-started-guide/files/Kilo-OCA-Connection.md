# Kilo Integration with Oracle Code Assist (OCA)
Kilo is an autonomous coding agent, integrated as a plugin into IntelliJ that enhances developer productivity. Oracle Code Assist is available as a model provider on Kilo, which gives Oracle developers secure access to Oracle-approved large language models (LLMs) with built-in protections for open-source code license scanning and content moderation.

## Key Features
* Reads and writes files across your entire code repository
* Executes terminal commands and debugs errors 
* Plans complex features before writing code 
* Connects to external systems through MCP servers 
* Understands large code projects with intelligent context management
  
## Resources
* Request [access](https://oracle.sharepoint.com/sites/ai-for-employees/SitePages/Oracle-Code-Assist.aspx) OCA
* View [OCA on Kilo Code for IntelliJ](https://oracle.sharepoint.com/sites/ai-for-employees/SitePages/Oracle-Code-Assist.aspx) for **detailed setup instructions**
* For more information visit: https://kilocode.ai/docs 

## Step-by-Step Guide
### 1. **Request Access to OCA Models**
* Before proceeding, request entitlements for the desired OCA models using the guide in the PDF (e.g., via Oracle's internal process). This enables access to Oracle's AI models through Kilocode.

### 2. **Prerequisites**
* Ensure Node.js version 20.6.0 or higher is installed on your machine (macOS, Windows, or Linux). Verify with `node -v` and `which node`.
* If needed, install or update Node.js (e.g., via `brew install node` on macOS or nvm). For proxy users, ensure the path points to the correct version.

### 3. **Download and Install Kilocode Plugin**
* Download the latest Kilocode binary (e.g., `Kilo Code-0.0.1.zip`) from the latest version specified in the `OCA on Kilo Code for IntelliJ PDF`
* Do **not** install from the marketplace; uninstall any existing marketplace version if present.
* Go to Settings > Plugins > Gear icon > "Install Plugin from Disk" > Select the downloaded ZIP > Apply > OK.
* Disable auto-updates in plugin settings to prevent overwrites from external sources.
* Kilocode icon appears in the sidebar; click it to open. It may initialize for up to a minute.

### 4. **Post-Install Setup**
* In the Kilocode window, select "Use your own API key."
* Change the API Provider to "Oracle Code Assist" (the only recommended option; avoid others).
* Click "Login with Oracle SSO" and complete authentication. If login fails (e.g., due to proxy or trusted domains), remove PAC/WPAD references from IntelliJ proxy settings and set proxies via environment variables (e.g., in `.zshrc`).
* After login, select a model from the dropdown (request access if empty). Click "Let's Go" to start.

### 5. **Configure Model Selection (Optional but Recommended)**
* Click the gear icon in Kilocode settings.
* Use the model dropdown to view or refresh available OCA models.
* Acknowledge any data restrictions or disclaimers (especially for OpenAI models).

### 6. **Test and Troubleshoot**
* Open a project and interact with Kilocode (e.g., prompt for code suggestions).
* Common Issues and Fixes:
  * "Node.js environment missing" or endless initialization: Run `sudo rm /usr/local/bin/node` followed by `ln -s "$(which node)" /usr/local/bin/node`, then restart IntelliJ.
  * SSO login errors: Ensure no PAC files (e.g., `http://wpad/wpad.dat`) in proxy settings; use environment variables only.
  * Full reset: Kill IntelliJ processes and clear JetBrains caches/directories as outlined in [OCA on Kilo Code for IntelliJ](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/Forms/AllItems.aspx?viewid=523d1542-44f5-4efc-b685-82d6467c3829&id=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Installation%20Guides/Oracle%20Code%20Assist%20on%20Kilocode.pdf&parent=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Installation%20Guides)

* For proxy/VPN users, verify Node.js path and proxy configurations.

This setup integrates OCA's AI features into IntelliJ for secure coding support. Always use only Oracle providers for compliance. If this is a complex coding task, gentle reminder: Oracle Code Assist offers advanced AI-powered coding support. check the `#help-oracle-genai-chat` Slack channel for more details.
