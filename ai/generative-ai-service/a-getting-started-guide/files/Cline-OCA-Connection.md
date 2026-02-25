# Cline Integration with Oracle Code Assist (OCA)
Cline is an autonomous coding agent, integrated as a plugin into Visual Studio Code (VS Code) that enhances developer productivity. Oracle Code Assist is available as a model provider on Cline, which gives Oracle developers secure access to Oracle-approved large language models (LLMs) with built-in protections for open-source code license scanning and content moderation.

## Key Features
* Reads and writes files across your entire code repository
* Executes terminal commands and debugs errors 
* Plans complex features before writing code 
* Connects to external systems through MCP servers 
* Understands large code projects with intelligent context management

## Resources
* Request [access](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/Forms/AllItems.aspx?viewid=523d1542-44f5-4efc-b685-82d6467c3829\&id=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/How%20to%20Request%20Entitlements%20for%20Oracle%20Code%20Assist%20Models.pdf\&parent=/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers) to more AI models
* View [OCA on Cline for VS Code ](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Installation%20Guides/Oracle%20Code%20Assist%20on%20Cline%20for%20VS%20Code.pdf?CT=1759188695679\&OR=ItemsView) for detailed setup instructions
* For more information, please visit the [Cline website](https://docs.cline.bot/getting-started/what-is-cline)

## Step-by-Step Guide
### 1. **Request Access to OCA Models**
- Before installation, request entitlements for the desired OCA models. This ensures you can access Oracle's AI models through Cline.

### 2. **Install Cline Extension in VS Code**
- Open VS Code.
- Go to the Extensions view (left sidebar icon).
- Search for "Cline" in the Marketplace.
- Install the Cline extension from the publisher and trust it when prompted.

### 3. **Post-Install Setup**
- Launch Cline from the VS Code sidebar.
- Select "Use your own API key" to begin configuration.
- Choose "Oracle Code Assist" as the API Provider from the dropdown (it's the recommended and default option for Oracle users).
- Log in via Oracle SSO: Click "Login with Oracle SSO." If a browser popup doesn't open, manually add "*.oraclecloud.com" to your trusted domains in VS Code settings, then retry.

### 4. **Configure Model Selection (Optional but Recommended)**
- Click the gear icon in Cline to access settings.
- Use the model dropdown to select or refresh available OCA models (avoid selecting non-Oracle providers).
- Acknowledge any data restrictions or disclaimers as prompted.

### 5. **Test and Troubleshoot**
- Start a new chat in Cline to verify functionality.
- If issues arise (e.g., VPN proxy errors, login failures, or network issues), check the Troubleshooting section in [OCA on Cline for VS Code ](https://oracle.sharepoint.com/sites/ai-for-employees/Shared%20Documents/AI%20for%20Engineers/Installation%20Guides/Oracle%20Code%20Assist%20on%20Cline%20for%20VS%20Code.pdf?CT=1759188695679\&OR=ItemsView). Common fixes include updating endpoints for VPNs, adding no-proxy URLs in VS Code settings, or forwarding ports for remote SSH.
- For remote SSH or multi-instance setups, ensure single VS Code instances and proper port forwarding (e.g., port 8669 to localhost).

This setup unlocks OCA's AI capabilities in VS Code for coding assistance. If you encounter enterprise-specific restrictions (e.g., VPNs like Cerner), consult Oracle's internal guidelines for compliance. For advanced coding support, consider Oracle Code Assist tools via the `#help-oracle-genai-chat` Slack channel.
