"use client";

import ConversationStorage from './conversationStorage';
import { BASE_SYSTEM_PROMPT } from '../utils/baseSystemPrompt';
import { WIDGET_INLINE_PROMPT } from '../utils/widgetInlinePrompt';
import { WIDGET_LAYOUT_PROMPT } from '../utils/widgetLayoutPrompt';
import { CONCISE_SYSTEM_PROMPT } from '../utils/concisePrompt';
import { MCPService } from './mcpService';

const createGenaiAgentService = () => {
  const API_BASE_URL =
    process.env.NEXT_PUBLIC_GENAI_API_URL || "http://localhost:3000/api";
  let conversationId = null;

  /**
   * Create a new conversation in OCI and store locally
   */
  const createConversation = async (title) => {
    // Build conversation metadata with optional LTM and STMO settings
    const metadata = { topic: title || "New conversation" };

    if (typeof window !== 'undefined') {
      try {
        const aiSettings = JSON.parse(localStorage.getItem('aiSettings') || '{}');
        if (aiSettings.ltmEnabled && aiSettings.ltmSubjectId) {
          metadata.memory_subject_id = aiSettings.ltmSubjectId;
          metadata.memory_access_policy = aiSettings.ltmAccessPolicy || 'recall_and_store';
        }
        metadata.short_term_memory_optimization = aiSettings.stmoEnabled ? 'True' : 'False';
      } catch { /* ignore */ }
    }

    const response = await fetch(`${API_BASE_URL}/conversations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        metadata,
        items: [],
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create conversation: ${response.status}`);
    }

    const data = await response.json();
    conversationId = data.id;

    await ConversationStorage.add({
      id: data.id,
      title: title || ConversationStorage._generateTitle(),
      metadata: data.metadata,
    });

    return data.id;
  };

  /**
   * Load an existing conversation
   */
  const loadConversation = async (id) => {
    conversationId = id;
    return await ConversationStorage.get(id);
  };

  /**
   * Get conversation messages from OCI
   */
  const getConversationItems = async (id) => {
    const convId = id || conversationId;
    if (!convId) return [];

    try {
      const response = await fetch(`${API_BASE_URL}/conversations?id=${convId}&getItems=true`);
      if (response.ok) {
        const data = await response.json();
        return data.data || [];
      }
    } catch (error) {
      console.warn('Could not fetch conversation items:', error);
    }
    return [];
  };

  /**
   * Send a message - OCI manages conversation history automatically
   * @param {string|Array} input - Message content (string or array for images)
   * @param {Function} onChunk - Callback for streaming text chunks
   * @param {Object} options - Options like model, sessionActiveServers
   */
  let currentAbortController = null;

  const abortCurrentRequest = () => {
    if (currentAbortController) {
      currentAbortController.abort();
      currentAbortController = null;
    }
  };

  const sendMessage = async (input, onChunk, options = {}) => {
    currentAbortController = new AbortController();
    const payload = { input };

    // Add conversation ID if we have one
    if (conversationId) {
      payload.conversationId = conversationId;
    }

    if (options.model) {
      payload.model = options.model;
    }

    // Add previous response ID for function calling round-trips
    if (options.previousResponseId) {
      payload.previousResponseId = options.previousResponseId;
    }

    // Build system prompt: BASE + user custom + widgets (if enabled)
    if (typeof window !== 'undefined') {
      const customPrompt = localStorage.getItem('systemPrompt') || '';
      const widgetsEnabled = localStorage.getItem('widgetsEnabled') === 'true';

      const now = new Date();
      const today = now.toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
      });
      const time = now.toLocaleTimeString('en-US', {
        hour: '2-digit', minute: '2-digit', hour12: true
      });
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      let systemPrompt = `Today is ${today}. Current time: ${time} (${timezone}).\n\n${BASE_SYSTEM_PROMPT}`;

      if (customPrompt) {
        systemPrompt += `\n\n## ADDITIONAL INSTRUCTIONS\n${customPrompt}`;
      }

      if (widgetsEnabled) {
        systemPrompt += `\n\n${WIDGET_INLINE_PROMPT}`;
        systemPrompt += `\n\n${WIDGET_LAYOUT_PROMPT}`;
      }

      const conciseEnabled = localStorage.getItem('conciseEnabled') === 'true';
      if (conciseEnabled) {
        systemPrompt += `\n\n${CONCISE_SYSTEM_PROMPT}`;
      }

      // Add RAG instruction if file_search is enabled with vector stores
      try {
        const nativeState = JSON.parse(localStorage.getItem('nativeToolsEnabled') || '{}');
        if (nativeState.native_rag) {
          const vsIds = JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]');
          const validVsIds = JSON.parse(localStorage.getItem('ragValidVectorStoreIds') || '[]');
          const activeIds = vsIds.filter(id => validVsIds.includes(id));
          if (activeIds.length > 0) {
            systemPrompt += `\n\n## KNOWLEDGE BASE (RAG)\nYou have access to a knowledge base via the file_search tool. ALWAYS search the knowledge base FIRST before answering questions, especially when the user asks about specific topics, projects, documents, or data. Use file_search proactively — do not rely solely on your training data when relevant documents may exist in the knowledge base.`;
          }
        }
      } catch { /* ignore */ }

      payload.systemPrompt = systemPrompt;

      // Add MCP tools for OCI native execution
      const appMode = localStorage.getItem('appMode') || 'internal';
      const allServers = MCPService.getServers().filter(s => s.enabled && !s.isNative && s.endpoint && !(appMode === 'client' && s.isAddon));
      const sessionActiveServers = options.sessionActiveServers;
      const activeServers = sessionActiveServers
        ? allServers.filter(s => sessionActiveServers.includes(s.id))
        : allServers;

      const sanitizeLabel = (name) => {
        let label = name.replace(/[^a-zA-Z0-9_-]/g, '_');
        if (!/^[a-zA-Z]/.test(label)) {
          label = 'mcp_' + label;
        }
        return label;
      };

      // Pre-flight: identify exactly which active server can't get a token.
      // Better to abort here with the server's identity than to call OCI and
      // try to parse a generic 424 that doesn't tell us who failed.
      const tokenMissing = [];
      const mcpTools = await Promise.all(activeServers.map(async (server) => {
        const tool = {
          type: 'mcp',
          server_label: sanitizeLabel(server.name),
          server_url: server.endpoint,
          require_approval: 'never'
        };
        if (server.authType === 'oauth2.1') {
          try {
            const res = await fetch(`/api/mcp/oauth/token?endpoint=${encodeURIComponent(server.endpoint)}`);
            const data = await res.json();
            if (data.hasToken && data.accessToken) {
              // OCI rejects requests that include BOTH `authorization` and `Authorization`
              // header (400 invalid_value). Use only the top-level field — OCI handles
              // injecting the Bearer header into the upstream MCP call.
              tool.authorization = data.accessToken;
            } else {
              tokenMissing.push({ name: server.name, endpoint: server.endpoint, authType: 'oauth2.1' });
            }
          } catch {
            tokenMissing.push({ name: server.name, endpoint: server.endpoint, authType: 'oauth2.1' });
          }
        } else if (server.authType === 'oauth2' && server.oauth?.tokenUrl && server.oauth?.clientId && server.oauth?.clientSecret) {
          // OAuth 2.0 Client Credentials Grant — fetched server-side (CORS + secret hygiene)
          try {
            const res = await fetch('/api/mcp/oauth2-cc/token', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                tokenUrl: server.oauth.tokenUrl,
                clientId: server.oauth.clientId,
                clientSecret: server.oauth.clientSecret,
                scope: server.oauth.scope,
              }),
            });
            const data = await res.json();
            if (data.accessToken) {
              tool.authorization = data.accessToken;
            } else {
              tokenMissing.push({ name: server.name, endpoint: server.endpoint, authType: 'oauth2' });
            }
          } catch {
            tokenMissing.push({ name: server.name, endpoint: server.endpoint, authType: 'oauth2' });
          }
        } else if (server.authType && server.authKey) {
          if (server.authType === 'api-key') {
            tool.headers = { 'X-API-KEY': server.authKey };
          } else if (server.authType === 'bearer') {
            tool.headers = { 'Authorization': `Bearer ${server.authKey}` };
          }
        }
        return tool;
      }));

      // If any active server can't get its token, abort with the exact identity.
      // Banner will then open the correct authorize flow (or surface a credential error
      // for client_credentials). Never guess. Never touch disabled servers.
      if (tokenMissing.length > 0) {
        const first = tokenMissing[0];
        const err = new Error('mcp_oauth_required');
        err.type = 'mcp_auth_expired';
        err.serverLabel = first.name;
        err.serverEndpoint = first.endpoint;
        err.serverAuthType = first.authType;
        err.pendingServers = tokenMissing;
        throw err;
      }

      // Add OCI native tools (web_search, etc.) based on enabled state
      const nativeTools = [];
      try {
        const stored = localStorage.getItem('nativeToolsEnabled');
        if (stored) {
          const nativeState = JSON.parse(stored);
          // Web Search temporarily disabled (coming soon) — ignore stored flag
          // if (nativeState.native_web_search) {
          //   nativeTools.push({ type: 'web_search' });
          // }
          if (nativeState.native_image_generation) {
            nativeTools.push({ type: 'image_generation' });
          }
          if (nativeState.native_code_interpreter) {
            nativeTools.push({
              type: 'code_interpreter',
              container: { type: 'auto', memory_limit: '4g' }
            });
          }
          if (nativeState.native_rag) {
            const vsIds = JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]');
            const validVsIds = JSON.parse(localStorage.getItem('ragValidVectorStoreIds') || '[]');
            const activeIds = vsIds.filter(id => validVsIds.includes(id));
            if (activeIds.length > 0) nativeTools.push({ type: 'file_search', vector_store_ids: activeIds });
          }
          if (nativeState.native_text_to_sql) {
            const semanticStoreId = localStorage.getItem('nl2sqlSemanticStoreId') || '';
            if (semanticStoreId) {
              nativeTools.push({ type: 'nl2sql', semantic_store_id: semanticStoreId });
            }
          }
        }
      } catch { /* ignore */ }

      const allTools = [...mcpTools, ...nativeTools];
      if (allTools.length > 0) {
        payload.tools = allTools;
        console.log('[Tools] Passing to OCI:', allTools.map(t => t.type === 'mcp' ? t.server_label : t.type));
      }

      // Add reasoning params automatically for reasoning-capable models
      const reasoningPatterns = ['o4-mini', 'gpt-5.4', 'grok-4-reasoning', 'o3', 'o4'];
      const currentModel = options.model || '';
      if (reasoningPatterns.some(p => currentModel.includes(p))) {
        const effort = localStorage.getItem('reasoningEffort') || 'off';
        if (effort !== 'off') {
          payload.reasoning = { effort, summary: 'auto' };
        }
      }
    }

    const response = await fetch(`${API_BASE_URL}/responses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: currentAbortController.signal,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      if (errorData.error === 'mcp_auth_expired') {
        const err = new Error('mcp_auth_expired');
        err.type = 'mcp_auth_expired';
        err.serverLabel = errorData.server_label || null;
        err.serverEndpoint = errorData.server_url || null;
        err.serverAuthType = null;
        throw err;
      }
      const err = new Error(errorData.error || `API Error: ${response.status}`);
      err.opcRequestId = errorData.opc_request_id || null;
      err.model = errorData.model || null;
      err.timestamp = errorData.timestamp || null;
      throw err;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullAnswer = '';
    let lastResponseId = null;
    const streamStartTime = Date.now();
    let lastChunkTime = Date.now();
    let chunkCount = 0;
    let serverDone = false;        // Did we receive { done: true } from server?
    let lastEventTypes = [];       // Last N event types for debugging

    // Client-side stall detection (mirrors server-side, but catches network-level hangs too)
    const STALL_TIMEOUT_MS = 130_000; // 2m10s (slightly longer than server-side 2m to let server abort first)

    const readWithTimeout = () => {
      let timer;
      const timeout = new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error('STREAM_STALL')), STALL_TIMEOUT_MS);
      });
      return Promise.race([reader.read(), timeout]).finally(() => clearTimeout(timer));
    };

    try {
      while (true) {
        let readResult;
        try {
          readResult = await readWithTimeout();
        } catch (stallErr) {
          if (stallErr.message === 'STREAM_STALL') {
            const elapsed = Math.round((Date.now() - streamStartTime) / 1000);
            const sinceLast = Math.round((Date.now() - lastChunkTime) / 1000);
            console.error(`[Stream] STALL after ${elapsed}s total, ${sinceLast}s since last chunk, ${chunkCount} chunks received, answer length: ${fullAnswer.length}`);
            const err = new Error(`STREAM_STALL: No data for ${sinceLast}s (${elapsed}s total, ${chunkCount} chunks received)`);
            err.name = 'StreamStallError';
            throw err;
          }
          throw stallErr;
        }
        const { done, value } = readResult;
        if (done) break;
        lastChunkTime = Date.now();
        chunkCount++;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine) continue;

          let data;
          try {
            data = JSON.parse(trimmedLine);
          } catch (parseError) {
            if (parseError.message !== 'Unexpected end of JSON input') {
              console.warn('Failed to parse chunk:', trimmedLine);
            }
            continue;
          }

          // Track event types for debugging (keep last 20)
          const eventKeys = Object.keys(data).filter(k => k !== 'text').join('+') || 'text-only';
          lastEventTypes.push(eventKeys);
          if (lastEventTypes.length > 20) lastEventTypes.shift();

          // Any `done:true` marks the stream as cleanly finished — even if it
          // carries an error. Without this, the real OCI error gets swallowed by
          // the "PrematureStreamClose" thrown in the finally block and the user
          // sees a misleading "OCI dropped the connection" message.
          if (data.done) {
            serverDone = true;
            if (onChunk) onChunk({ done: true, trace: data.trace || null });
          }

          if (data.error) {
            // Forward trace even on error so UI can show diagnostics
            if (data.trace && onChunk) onChunk({ trace: data.trace });
            throw new Error(data.error);
          }

          if (data.response_incomplete && onChunk) {
            onChunk({ response_incomplete: data.response_incomplete });
          }

          // Update conversation ID (OCI returns one for project-scoped RAG sessions)
          if (data.conversation_id) {
            conversationId = data.conversation_id;
          }

          if (data.text) {
            fullAnswer += data.text;
            if (onChunk) {
              onChunk(data.text);
            }
          }

          // Forward MCP events to UI
          if (data.mcp && onChunk) {
            onChunk({ mcp: data.mcp });
          }

          // Forward thinking indicator to UI
          if (data.thinking && onChunk) {
            onChunk({ thinking: true });
          }

          // Forward annotations (url citations from web search, file citations from RAG)
          if (data.annotations && onChunk) {
            console.log('[Stream] Forwarding annotations to UI:', data.annotations.length, data.annotations);
            onChunk({ annotations: data.annotations });
          }

          // Forward generated image from image_generation tool
          if (data.generated_image && onChunk) {
            onChunk({ generated_image: data.generated_image });
          }

          // Forward reasoning summary
          if (data.reasoning && onChunk) {
            onChunk({ reasoning: data.reasoning });
          }

          // Forward code execution results
          if (data.code_execution && onChunk) {
            onChunk({ code_execution: data.code_execution });
          }

          // Forward streaming code interpreter code tokens
          if (data.code_delta && onChunk) {
            onChunk({ code_delta: data.code_delta });
          }

          // Forward code interpreter status (in_progress / interpreting / completed)
          if (data.code_status && onChunk) {
            onChunk({ code_status: data.code_status });
          }

          // Forward item-level errors (message/reasoning/etc. finished with non-completed status)
          if (data.item_error && onChunk) {
            onChunk({ item_error: data.item_error });
          }

          // Forward function call (client-side tool execution)
          if (data.function_call && onChunk) {
            onChunk({ function_call: data.function_call });
          }

          // Track response ID for potential chaining
          if (data.response_id) {
            lastResponseId = data.response_id;
          }

          // Log unhandled chunk types for debugging
          if (!data.text && !data.mcp && !data.thinking && !data.annotations && !data.generated_image && !data.reasoning && !data.code_execution && !data.code_delta && !data.code_status && !data.item_error && !data.function_call && !data.done && !data.text_done && !data.conversation_id && !data.response_id && !data.error && !data.response_incomplete) {
            console.warn('[Stream] Unhandled chunk type:', Object.keys(data), data);
          }
        }
      }
    } finally {
      const elapsed = Math.round((Date.now() - streamStartTime) / 1000);
      // Process any remaining data in buffer
      if (buffer.trim()) {
        console.warn('[Stream] Leftover buffer data:', buffer);
        try {
          const data = JSON.parse(buffer.trim());
          if (data.done) serverDone = true;
          if (data.annotations && onChunk) {
            console.log('[Stream] Processing leftover annotations:', data.annotations.length);
            onChunk({ annotations: data.annotations });
          }
        } catch (e) {
          console.warn('[Stream] Could not parse leftover buffer');
        }
      }
      reader.releaseLock();

      // Detect premature stream close — server never sent { done: true }
      if (!serverDone) {
        const debugInfo = {
          elapsed,
          chunks: chunkCount,
          answerLength: fullAnswer.length,
          lastEvents: lastEventTypes.slice(-10),
          hadResponseId: !!lastResponseId,
          buffer: buffer.trim().slice(0, 200) || '(empty)',
        };
        console.error('[Stream] PREMATURE CLOSE — server never sent done:true', debugInfo);
        const err = new Error(
          `Stream closed after ${elapsed}s without completion. ` +
          `Received ${chunkCount} chunks, ${fullAnswer.length} chars of text. ` +
          `Last events: [${lastEventTypes.slice(-5).join(', ')}]. ` +
          `This usually means OCI dropped the connection while an MCP tool was executing.`
        );
        err.name = 'PrematureStreamClose';
        throw err;
      }
    }

    // Update local storage with last message info
    if (conversationId && fullAnswer) {
      await ConversationStorage.update(conversationId, {
        lastMessage: fullAnswer.substring(0, 100),
        messageCount: (await ConversationStorage.get(conversationId))?.messageCount + 1 || 1,
      });
    }

    return { answer: fullAnswer, conversation_id: conversationId, response_id: lastResponseId };
  };

  const resetConversation = () => {
    conversationId = null;
  };

  const getConversationId = () => conversationId;

  const setConversationId = (id) => {
    conversationId = id;
  };

  return {
    sendMessage,
    abortCurrentRequest,
    resetConversation,
    createConversation,
    loadConversation,
    getConversationItems,
    getConversationId,
    setConversationId,
    storage: ConversationStorage,
  };
};

export default createGenaiAgentService;
