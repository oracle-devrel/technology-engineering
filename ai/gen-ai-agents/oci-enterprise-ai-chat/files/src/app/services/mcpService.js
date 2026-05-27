const API_URL = '/api/mcp';

/**
 * MCP Server configuration
 * @typedef {Object} MCPServer
 * @property {string} id - Unique identifier
 * @property {string} name - Display name
 * @property {string} endpoint - Full URL with API key
 * @property {boolean} enabled - Whether server is enabled
 */

/**
 * MCP Tool with server info
 * @typedef {Object} MCPTool
 * @property {string} serverId - Server this tool belongs to
 * @property {string} serverName - Server display name
 * @property {string} name - Tool name
 * @property {string} description - Tool description
 * @property {Object} inputSchema - JSON schema for inputs
 * @property {boolean} enabled - Whether tool is enabled
 */

class MCPService {
  servers = new Map(); // serverId -> { config, sessionId, tools, initialized }

  /**
   * Build auth fields for the proxy request body
   */
  _authFields(server) {
    if (server.authType === 'oauth2.1') return { authType: 'oauth2.1' };
    if (server.authType === 'oauth2' && server.oauth) return { authType: 'oauth2', oauth: server.oauth };
    if (server.authType && server.authKey) return { authType: server.authType, authKey: server.authKey };
    return {};
  }

  /**
   * Send a request to the MCP proxy, handling needs_auth for OAuth 2.1
   */
  async _proxyRequest(server, method, params, sessionId, timeout = 15000) {
    const body = {
      endpoint: server.endpoint,
      method,
      params,
      ...this._authFields(server),
    };
    if (sessionId && method !== 'initialize') {
      body.sessionId = sessionId;
    }

    const response = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeout),
    });

    if (response.status === 401) {
      const data = await response.json();
      if (data.error === 'needs_auth') {
        const err = new Error('needs_auth');
        err.authorizeUrl = data.authorizeUrl;
        throw err;
      }
    }

    if (!response.ok) {
      throw new Error(`MCP request failed: ${response.status}`);
    }

    return response.json();
  }

  /**
   * Initialize a specific MCP server
   */
  async initializeServer(server) {
    try {
      const data = await this._proxyRequest(server, 'initialize', {
        protocolVersion: '2024-11-05',
        capabilities: {},
        clientInfo: { name: 'OCI-Chat', version: '1.0.0' },
      });

      if (data.result) {
        const serverState = this.servers.get(server.id) || { config: server };
        serverState.initialized = true;
        serverState.sessionId = data._sessionId || null;
        serverState.serverInfo = data.result.serverInfo;
        this.servers.set(server.id, serverState);
        console.log(`[MCP] Server ${server.name} initialized:`, data.result.serverInfo);
        return data.result;
      }
      throw new Error(data.error?.message || 'Unknown error');
    } catch (error) {
      console.error(`[MCP] Initialize error for ${server.name}:`, error);
      throw error;
    }
  }

  /**
   * List tools from a specific server
   */
  async listToolsFromServer(server) {
    try {
      let serverState = this.servers.get(server.id);

      if (!serverState?.initialized) {
        await this.initializeServer(server);
        serverState = this.servers.get(server.id);
      }

      const data = await this._proxyRequest(server, 'tools/list', {}, serverState?.sessionId);
      if (data.result?.tools) {
        // Add server info to each tool
        const tools = data.result.tools.map(tool => ({
          ...tool,
          serverId: server.id,
          serverName: server.name
        }));

        serverState.tools = tools;
        this.servers.set(server.id, serverState);

        console.log(`[MCP] ${server.name}: ${tools.length} tools loaded`);
        return tools;
      }
      throw new Error(data.error?.message || 'No tools found');
    } catch (error) {
      console.error(`[MCP] List tools error for ${server.name}:`, error);
      throw error;
    }
  }

  /**
   * List tools from all enabled servers
   */
  async listAllTools() {
    const servers = MCPService.getServers().filter(s => s.enabled);
    const allTools = [];

    for (const server of servers) {
      try {
        const tools = await this.listToolsFromServer(server);
        allTools.push(...tools);
      } catch (error) {
        console.warn(`[MCP] Skipping server ${server.name}:`, error.message);
      }
    }

    return allTools;
  }

  /**
   * Call a tool on its server
   */
  async callTool(serverId, toolName, args) {
    try {
      const serverState = this.servers.get(serverId);
      if (!serverState) {
        throw new Error(`Server ${serverId} not initialized`);
      }

      const server = serverState.config;
      console.log(`[MCP] Calling ${toolName} on ${server.name}`, args);

      const data = await this._proxyRequest(
        server, 'tools/call',
        { name: toolName, arguments: args },
        serverState.sessionId, 60000
      );
      console.log(`[MCP] Tool ${toolName} result:`, data);

      if (data.result) {
        return data.result;
      }
      if (data.error) {
        throw new Error(data.error.message || 'Tool call failed');
      }
      return data;
    } catch (error) {
      console.error(`[MCP] Call tool error:`, error);
      throw error;
    }
  }

  /**
   * Generate system prompt section for enabled tools
   */
  getToolsForPrompt() {
    const enabledToolNames = MCPService.getEnabledTools();
    if (enabledToolNames.length === 0) return '';

    const allTools = [];
    for (const [serverId, state] of this.servers) {
      if (state.tools) {
        allTools.push(...state.tools);
      }
    }

    const enabledTools = allTools.filter(t =>
      enabledToolNames.includes(`${t.serverId}:${t.name}`)
    );

    if (enabledTools.length === 0) return '';

    const toolDescriptions = enabledTools.map(tool => {
      const params = tool.inputSchema?.properties || {};
      const required = tool.inputSchema?.required || [];

      const paramList = Object.entries(params).map(([key, val]) => {
        const req = required.includes(key) ? ' (required)' : '';
        return `  - ${key}: ${val.description || val.type}${req}`;
      }).join('\n');

      return `### ${tool.name} (${tool.serverName})
${tool.description}
Parameters:
${paramList}`;
    }).join('\n\n');

    return `
## Available Tools

You have access to external tools. When you need to use a tool, output:
<tool_call>{"server": "server_id", "name": "tool_name", "arguments": {...}}</tool_call>

${toolDescriptions}
`;
  }

  // ==================== Storage Helpers ====================

  static STORAGE_KEYS = {
    SERVERS: 'mcpServers',
    ENABLED_TOOLS: 'mcpEnabledTools',
    MCP_ENABLED: 'mcpEnabled'
  };

  /**
   * Get configured MCP servers
   * @returns {MCPServer[]}
   */
  static getServers() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.SERVERS);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Save MCP servers configuration
   * @param {MCPServer[]} servers
   */
  static setServers(servers) {
    localStorage.setItem(this.STORAGE_KEYS.SERVERS, JSON.stringify(servers));
  }

  /**
   * Add a new MCP server
   * @param {Omit<MCPServer, 'id'>} server
   * @returns {MCPServer}
   */
  static addServer(server) {
    const servers = this.getServers();
    const newServer = {
      ...server,
      id: `mcp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      enabled: true
    };
    servers.push(newServer);
    this.setServers(servers);
    return newServer;
  }

  /**
   * Update an existing server
   * @param {string} serverId
   * @param {Partial<MCPServer>} updates
   */
  static updateServer(serverId, updates) {
    const servers = this.getServers();
    const index = servers.findIndex(s => s.id === serverId);
    if (index !== -1) {
      servers[index] = { ...servers[index], ...updates };
      this.setServers(servers);
    }
  }

  /**
   * Remove a server
   * @param {string} serverId
   */
  static removeServer(serverId) {
    const servers = this.getServers().filter(s => s.id !== serverId);
    this.setServers(servers);
  }

  /**
   * Get enabled tool IDs (format: "serverId:toolName")
   * @returns {string[]}
   */
  static getEnabledTools() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEYS.ENABLED_TOOLS);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  /**
   * Set enabled tools
   * @param {string[]} toolIds - Array of "serverId:toolName"
   */
  static setEnabledTools(toolIds) {
    localStorage.setItem(this.STORAGE_KEYS.ENABLED_TOOLS, JSON.stringify(toolIds));
  }

  /**
   * Toggle a specific tool
   * @param {string} serverId
   * @param {string} toolName
   * @param {boolean} enabled
   */
  static toggleTool(serverId, toolName, enabled) {
    const toolId = `${serverId}:${toolName}`;
    const enabledTools = this.getEnabledTools();

    if (enabled && !enabledTools.includes(toolId)) {
      enabledTools.push(toolId);
    } else if (!enabled) {
      const index = enabledTools.indexOf(toolId);
      if (index !== -1) enabledTools.splice(index, 1);
    }

    this.setEnabledTools(enabledTools);
  }

  /**
   * Check if MCP is globally enabled
   */
  static isMcpEnabled() {
    return localStorage.getItem(this.STORAGE_KEYS.MCP_ENABLED) === 'true';
  }

  /**
   * Set MCP global enabled state
   */
  static setMcpEnabled(enabled) {
    localStorage.setItem(this.STORAGE_KEYS.MCP_ENABLED, enabled ? 'true' : 'false');
  }
}

// Export singleton
const mcpService = new MCPService();
export default mcpService;
export { MCPService };
