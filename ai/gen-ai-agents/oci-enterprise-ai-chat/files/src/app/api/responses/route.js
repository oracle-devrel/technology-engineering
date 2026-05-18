import { NextResponse } from 'next/server';
import { ociRequest } from '../../lib/oci-proxy';
import { Langfuse } from 'langfuse';
import { createLogger } from '../../lib/logger';

// Allow long-running MCP tool calls (up to 5 minutes)
export const maxDuration = 300;

export async function POST(request) {
  const requestId = crypto.randomUUID();
  const log = createLogger('responses-api', { requestId });

  try {
    const { input, conversationId, model, systemPrompt, tools, reasoning, previousResponseId } = await request.json();

    if (!input) {
      return NextResponse.json({ error: 'Input is required' }, { status: 400 });
    }

    const modelId = model || 'openai.gpt-4.1';

    // Multi-agent models use /v1, all others use /openai/v1
    const basePath = modelId.includes('multi-agent') ? '/v1' : '/openai/v1';

    // Build request - OCI manages history via conversation parameter
    // For multimodal input (arrays with input_text/input_image), wrap in message object
    let formattedInput = input;
    if (Array.isArray(input) && input.some(item => item.type === 'input_text' || item.type === 'input_image')) {
      formattedInput = [{
        type: 'message',
        role: 'user',
        content: input
      }];
    }

    const requestBody = {
      model: modelId,
      input: formattedInput,
      stream: true,
      store: true,  // Let OCI store messages automatically
      max_output_tokens: 65535,
    };

    // Add system instructions if provided
    if (systemPrompt) {
      requestBody.instructions = systemPrompt;
    }

    // Add conversation ID if continuing existing conversation
    if (conversationId) {
      requestBody.conversation = conversationId;
    }

    // Add MCP tools if provided (OCI handles execution natively)
    if (tools && Array.isArray(tools) && tools.length > 0) {
      requestBody.tools = tools;
    }

    // Add reasoning params (effort + summary) — only for reasoning-capable models
    if (reasoning && typeof reasoning === 'object') {
      const reasoningModels = ['o4-mini', 'gpt-5.4', 'grok-4-reasoning', 'o3', 'o4'];
      const supportsReasoning = reasoningModels.some(rm => modelId.includes(rm));
      if (supportsReasoning) {
        requestBody.reasoning = reasoning;
      }
    }

    // Chain to a previous response (for function calling round-trips)
    if (previousResponseId) {
      requestBody.previous_response_id = previousResponseId;
    }

    log.info('OCI request payload', {
      model: requestBody.model,
      hasInstructions: !!requestBody.instructions,
      instructionsLen: requestBody.instructions?.length || 0,
      hasConversation: !!requestBody.conversation,
      toolCount: requestBody.tools?.length || 0,
      toolTypes: requestBody.tools?.map(t => t.type) || [],
      stream: requestBody.stream,
      store: requestBody.store,
      max_output_tokens: requestBody.max_output_tokens,
    });

    let response = await ociRequest('POST', '/responses', {
      body: requestBody,
      basePath,
      extraHeaders: { accept: 'text/event-stream' },
    });

    // Log OCI request ID for debugging/support
    const opcRequestId = response.headers.get('opc-request-id');
    if (opcRequestId) log.info('OCI request started', { opcRequestId });

    if (!response.ok) {
      const errorText = await response.text();
      log.error('OCI API error', { status: response.status, body: errorText.slice(0, 4000), opcRequestId });

      // MCP tool auth expired — tell client to re-authorize
      // 424 + external_connector_error typically indicates either expired OAuth tokens
      // or upstream MCP failure; in both cases, re-authorizing is the user's best action.
      if (response.status === 424 && errorText.includes('external_connector_error')) {
        // Try to surface which MCP server failed so the UI can open the correct
        // re-authorize flow instead of guessing.
        let failedServer = null;
        try {
          const parsed = JSON.parse(errorText);
          failedServer = parsed?.error?.server_label
            || parsed?.error?.metadata?.server_label
            || parsed?.error?.details?.server_label
            || null;
          if (!failedServer && typeof parsed?.error?.message === 'string') {
            const m = parsed.error.message.match(/server[_ ]?(?:label)?\s*[:=]?\s*['"]?([a-zA-Z0-9_-]+)['"]?/i);
            if (m) failedServer = m[1];
          }
        } catch { /* errorText not JSON */ }

        // Look up the actual server_url + headers from the request we just sent,
        // so the client has the exact endpoint (no fragile name-sanitize match).
        let failedServerUrl = null;
        if (failedServer && Array.isArray(requestBody.tools)) {
          const tool = requestBody.tools.find(t => t.type === 'mcp' && t.server_label === failedServer);
          failedServerUrl = tool?.server_url || null;
        }

        return NextResponse.json(
          { error: 'mcp_auth_expired', server_label: failedServer, server_url: failedServerUrl, details: errorText },
          { status: 424 }
        );
      }
      // Retry without file_search if a VectorStore is not found (stale/deleted VS)
      else if (response.status === 400 && errorText.includes('VectorStore') && errorText.includes('not found') && requestBody.tools?.some(t => t.type === 'file_search')) {
        log.warn('Retrying without file_search (stale vector store)');
        requestBody.tools = requestBody.tools.filter(t => t.type !== 'file_search');
        if (requestBody.tools.length === 0) delete requestBody.tools;

        response = await ociRequest('POST', '/responses', {
          body: requestBody,
          basePath,
          extraHeaders: { accept: 'text/event-stream' },
        });

        if (!response.ok) {
          const retryError = await response.text();
          const retryOpc = response.headers.get('opc-request-id');
          return NextResponse.json({
            error: `OCI API Error: ${response.status} - ${retryError}`,
            opc_request_id: retryOpc,
            model: modelId,
            timestamp: new Date().toISOString(),
          }, { status: response.status });
        }
      } else {
        return NextResponse.json({
          error: `OCI API Error: ${response.status} - ${errorText}`,
          opc_request_id: opcRequestId,
          model: modelId,
          timestamp: new Date().toISOString(),
        }, { status: response.status });
      }
    }

    // LangFuse tracing (non-blocking, fire-and-forget)
    let langfuseTrace = null;
    let langfuseGeneration = null;
    const langfuseEnabled = process.env.LANGFUSE_SECRET_KEY && process.env.LANGFUSE_PUBLIC_KEY;
    let langfuse = null;
    if (langfuseEnabled) {
      try {
        langfuse = new Langfuse({
          secretKey: process.env.LANGFUSE_SECRET_KEY,
          publicKey: process.env.LANGFUSE_PUBLIC_KEY,
          baseUrl: process.env.LANGFUSE_BASE_URL || 'https://cloud.langfuse.com',
        });
        const inputPreview = typeof input === 'string' ? input.slice(0, 200) : JSON.stringify(input).slice(0, 200);
        langfuseTrace = langfuse.trace({
          name: 'oci-responses-api',
          metadata: { model: modelId, conversationId, hasTools: !!(tools?.length), basePath },
          input: inputPreview,
        });
        langfuseGeneration = langfuseTrace.generation({
          name: 'llm-call',
          model: modelId,
          input: formattedInput,
          metadata: { systemPrompt: systemPrompt?.slice(0, 500), tools: tools?.map(t => t.type || t.name) },
        });
      } catch (e) {
        log.warn('LangFuse init error', { error: e.message });
      }
    }

    // Stream the response back to the client
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      async start(controller) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        const startTime = Date.now();
        let fullOutputText = '';
        let toolCalls = [];
        const fileSearchOutputsSent = new Set();
        let usageData = null;
        let responseCompleted = false;
        let completedResponseData = null;
        let lastEventType = null;
        let eventCount = 0;
        // When OCI sends `event: error`, the following `data:` line carries the real
        // error payload (provider message, code, details). Capture it to surface to UI.
        let pendingErrorEvent = false;

        // ── Request trace: structured timeline for diagnostics ──
        const trace = {
          requestId,
          opcRequestId: null,
          model: modelId,
          startedAt: new Date().toISOString(),
          events: [],       // [{ts, type, detail}]
          tools: {},        // {itemId: {tool, server, status, startMs, endMs, outputSize}}
          completion: null,  // {status, outputItems, outputTokens, totalTokens, elapsed}
          error: null,       // string if something went wrong
        };
        const traceEvent = (type, detail) => {
          trace.events.push({ ts: Date.now() - startTime, type, ...(detail || {}) });
        };

        // Send thinking indicator IMMEDIATELY when stream starts
        log.info('Stream started');
        controller.enqueue(encoder.encode(JSON.stringify({ thinking: true }) + '\n'));

        // Stall detection: if OCI sends no data for STALL_TIMEOUT_MS, abort the stream
        const STALL_TIMEOUT_MS = 120_000; // 2 minutes
        let lastChunkTime = Date.now();
        let stalled = false;

        const readWithTimeout = async () => {
          const timeout = new Promise((_, reject) => {
            const id = setTimeout(() => {
              clearTimeout(id);
              reject(new Error('OCI_STREAM_STALL'));
            }, STALL_TIMEOUT_MS);
            // Store the timer id so we can clear it when we get data
            readWithTimeout._timer = id;
          });
          try {
            const result = await Promise.race([reader.read(), timeout]);
            if (readWithTimeout._timer) clearTimeout(readWithTimeout._timer);
            lastChunkTime = Date.now();
            return result;
          } catch (e) {
            if (readWithTimeout._timer) clearTimeout(readWithTimeout._timer);
            throw e;
          }
        };

        try {
          while (true) {
            let readResult;
            try {
              readResult = await readWithTimeout();
            } catch (stallErr) {
              if (stallErr.message === 'OCI_STREAM_STALL') {
                stalled = true;
                const stallElapsed = Date.now() - startTime;
                log.error('Stream stalled — no data from OCI', { elapsed: stallElapsed, lastChunkAge: Date.now() - lastChunkTime, opcRequestId });
                trace.opcRequestId = opcRequestId;
                trace.error = `Stream stalled — no data from OCI for 2+ minutes. Total elapsed: ${Math.round(stallElapsed / 1000)}s, ${eventCount} events received, last event: "${lastEventType || 'none'}".`;
                traceEvent('stall', { elapsed: stallElapsed, lastEventType });
                controller.enqueue(encoder.encode(JSON.stringify({
                  error: trace.error,
                  done: true,
                  trace,
                }) + '\n'));
                break;
              }
              throw stallErr;
            }
            const { done, value } = readResult;
            if (done) break;

            const elapsed = Date.now() - startTime;
            const chunk = decoder.decode(value, { stream: true });
            log.debug('Chunk received', { elapsed, bytes: chunk.length });

            buffer += chunk;
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // Keep incomplete line in buffer
            if (buffer.length > 1000) {
              log.debug('Large buffer pending', { bufferLen: buffer.length, elapsed, preview: buffer.substring(0, 200) });
            }

            for (const line of lines) {
              // Log ALL non-data lines — never silently skip
              if (line.trim() && !line.startsWith('data: ')) {
                // SSE event lines (event:, id:, retry:) get logged as info, not debug
                log.info('SSE control line', { elapsed: Date.now() - startTime, line: line.trim() });
              }

              // Handle SSE error/event lines — catch ANY event type, not just "error"
              const trimmedLine = line.trim();
              if (trimmedLine.startsWith('event:')) {
                const eventName = trimmedLine.slice(6).trim();
                log.warn('SSE event received', { event: eventName, elapsed: Date.now() - startTime });
                if (eventName === 'error') {
                  log.error('OCI upstream error event — waiting for data payload', { opcRequestId, elapsed: Date.now() - startTime });
                  // Flag the next `data:` line as the payload for this error event so
                  // we can forward OCI's actual error message/code to the client.
                  pendingErrorEvent = true;
                }
                continue;
              }

              if (!line.startsWith('data: ')) continue;

              try {
                const data = JSON.parse(line.slice(6));
                const elapsed = Date.now() - startTime;

                // This data line is the payload of a preceding `event: error` SSE line.
                // Forward the full error from the provider to the client + trace so the
                // user sees the actual cause instead of a generic message.
                if (pendingErrorEvent) {
                  pendingErrorEvent = false;
                  responseCompleted = true;
                  const providerMessage = data.error?.message || data.message || data.error || JSON.stringify(data);
                  const providerCode = data.error?.code || data.code || null;
                  const providerType = data.error?.type || data.type || null;
                  log.error('OCI upstream error payload', { opcRequestId, elapsed, providerMessage, providerCode, providerType, raw: JSON.stringify(data).substring(0, 2000) });
                  trace.opcRequestId = opcRequestId;
                  trace.error = `OCI upstream error after ${Math.round(elapsed / 1000)}s: ${providerMessage}${providerCode ? ` [code: ${providerCode}]` : ''}${providerType ? ` [type: ${providerType}]` : ''}. opc-request-id: ${opcRequestId || 'unknown'}.`;
                  traceEvent('upstream_error_payload', { elapsed, providerMessage, providerCode, providerType });
                  const friendly = providerMessage && providerMessage !== '[object Object]'
                    ? `Upstream error: ${providerMessage}${providerCode ? ` (${providerCode})` : ''}${opcRequestId ? ` — opc-request-id: ${opcRequestId}` : ''}`
                    : `The model provider returned an error${opcRequestId ? ` (opc-request-id: ${opcRequestId})` : ''}.`;
                  controller.enqueue(encoder.encode(JSON.stringify({
                    error: friendly,
                    done: true,
                    trace,
                    raw_error: data,
                  }) + '\n'));
                  completedResponseData = null;
                  continue;
                }

                const eventType = data.type;
                const itemType = data.item?.type;
                const itemStatus = data.item?.status;
                const itemId = data.item?.id || data.item_id;
                lastEventType = eventType;
                eventCount++;

                // DEBUG: Log every SSE event type for full visibility
                log.debug('SSE event', { event: eventType, itemType, itemId: itemId?.slice(-12), elapsed, lineLen: line.length });

                // ═══ LOG EVERY EVENT — no silent drops ═══
                // Lifecycle events (created, in_progress) — debug level
                if (eventType === 'response.created' || eventType === 'response.in_progress') {
                  log.debug('Response lifecycle', { event: eventType, elapsed, responseId: data.response?.id });
                }

                // ═══ TEXT STREAMING ═══
                else if (eventType === 'response.output_text.delta' && data.delta) {
                  fullOutputText += data.delta;
                  controller.enqueue(encoder.encode(JSON.stringify({ text: data.delta }) + '\n'));
                }
                else if (eventType === 'response.output_text.done') {
                  controller.enqueue(encoder.encode(JSON.stringify({ text_done: data.text }) + '\n'));
                }

                // ═══ OUTPUT ITEMS ADDED ═══
                else if (eventType === 'response.output_item.added') {
                  log.info('Output item added', { itemType, itemId, elapsed, server: data.item?.server_label, phase: data.item?.phase });

                  if (itemType === 'mcp_list_tools') {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'connecting', server: data.item.server_label }
                    }) + '\n'));
                  }
                  else if (itemType === 'mcp_call') {
                    toolCalls.push({ id: itemId, tool: data.item.name, server: data.item.server_label });
                    trace.tools[itemId] = { tool: data.item.name, server: data.item.server_label, status: 'calling', startMs: elapsed };
                    traceEvent('tool_call', { tool: data.item.name, server: data.item.server_label, id: itemId });
                    log.info('MCP tool calling', { tool: data.item.name, server: data.item.server_label, args: (data.item.arguments || '').substring(0, 300), elapsed });
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'calling', id: itemId, server: data.item.server_label, tool: data.item.name, arguments: data.item.arguments }
                    }) + '\n'));
                  }
                  else if (itemType === 'web_search_call') {
                    const query = data.item.action?.query || '';
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'calling', id: itemId, server: 'web_search', tool: 'web_search', arguments: query ? JSON.stringify({ query }) : '' }
                    }) + '\n'));
                  }
                  else if (itemType === 'code_interpreter_call') {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'calling', id: itemId, server: 'code_interpreter', tool: 'code_interpreter', arguments: '' }
                    }) + '\n'));
                  }
                  else if (itemType === 'image_generation_call') {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'calling', id: itemId, server: 'image_generation', tool: 'image_generation', arguments: '' }
                    }) + '\n'));
                  }
                  else if (itemType === 'nl2sql_call') {
                    const query = data.item.input_natural_language_query || data.item.query || '';
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'calling', id: itemId, server: 'nl2sql', tool: 'nl2sql', arguments: query ? JSON.stringify({ query }) : '' }
                    }) + '\n'));
                  }
                  // File search added — emit calling chip early with vector_store info
                  // (query isn't available yet — OCI only sends it in output_item.done).
                  else if (itemType === 'file_search_call') {
                    const fsToolCfgs = (tools || []).filter(t => t.type === 'file_search');
                    const vsIdsForCfg = fsToolCfgs.flatMap(t => t.vector_store_ids || []);
                    const maxNumResults = fsToolCfgs[0]?.max_num_results || null;
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: {
                        type: 'calling',
                        id: itemId,
                        server: 'file_search',
                        tool: 'file_search',
                        arguments: JSON.stringify({ vector_store_ids: vsIdsForCfg, max_num_results: maxNumResults }),
                      }
                    }) + '\n'));
                  }
                  else if (itemType === 'reasoning') {
                    controller.enqueue(encoder.encode(JSON.stringify({ reasoning: { type: 'start' } }) + '\n'));
                  }
                  else if (itemType === 'message') {
                    log.debug('Message item added', { role: data.item.role, phase: data.item.phase, elapsed });
                  }
                }

                // ═══ OUTPUT ITEMS DONE ═══
                else if (eventType === 'response.output_item.done') {
                  log.info('Output item done', { itemType, itemId, status: itemStatus, elapsed, tool: data.item?.name, server: data.item?.server_label });

                  // MCP tool completed
                  if (itemType === 'mcp_call') {
                    const rawOutput = data.item.output || '';
                    const outputSize = rawOutput.length;
                    const MAX_SIZE = 5000;
                    let truncatedOutput = rawOutput;
                    let truncated = false;

                    const containsBinaryData = rawOutput.includes('"audioBase64"') || rawOutput.includes('"imageBase64"') || rawOutput.includes('"fileBase64"');
                    const isError = itemStatus === 'incomplete' || itemStatus === 'failed';

                    // Update trace
                    if (trace.tools[itemId]) {
                      trace.tools[itemId].status = isError ? 'failed' : 'completed';
                      trace.tools[itemId].endMs = elapsed;
                      trace.tools[itemId].outputSize = outputSize;
                    }
                    traceEvent(isError ? 'tool_failed' : 'tool_done', { tool: data.item.name, id: itemId, outputSize, status: itemStatus });

                    if (isError) {
                      log.error('MCP TOOL FAILED', { tool: data.item.name, server: data.item.server_label, status: itemStatus, output: rawOutput.substring(0, 2000), elapsed });
                    } else {
                      log.info('MCP tool succeeded', { tool: data.item.name, server: data.item.server_label, outputSize, elapsed });
                    }

                    if (outputSize > MAX_SIZE && !containsBinaryData && !isError) {
                      const head = rawOutput.slice(0, 2000);
                      const tail = rawOutput.slice(-1000);
                      truncatedOutput = `${head}\n\n... [${(outputSize - 3000).toLocaleString()} chars omitted] ...\n\n${tail}`;
                      truncated = true;
                    }

                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'tool_output', id: itemId, tool: data.item.name, server: data.item.server_label, output: truncatedOutput, outputSize, truncated, arguments: data.item.arguments }
                    }) + '\n'));
                    // Mark this tool as having sent its output (for dedup in response.completed)
                    const tc = toolCalls.find(t => (t.id === itemId) || (t.tool === data.item.name && t.server === data.item.server_label && !t.outputSent));
                    if (tc) { tc.outputSent = true; tc.id = tc.id || itemId; }
                    // Update trace — if completion arrives after response.completed, this still marks it done
                    if (trace.tools[itemId]) trace.tools[itemId].status = 'completed';
                  }
                  // Web search completed
                  else if (itemType === 'web_search_call') {
                    const query = data.item.action?.query || 'web search';
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'tool_output', tool: 'web_search', server: 'web_search', output: query }
                    }) + '\n'));
                  }
                  // File search completed — emit tool_output with id so the chip
                  // can show queries/vector_stores/chunk count instead of just "File Search"
                  else if (itemType === 'file_search_call') {
                    const queries = data.item.queries || [];
                    const fsToolCfgs = (tools || []).filter(t => t.type === 'file_search');
                    const vsIdsForCfg = fsToolCfgs.flatMap(t => t.vector_store_ids || []);
                    const maxNumResults = fsToolCfgs[0]?.max_num_results || null;
                    const summary = queries.length > 0
                      ? `Searched: ${queries.map(q => `"${q}"`).join(', ')}`
                      : 'Search completed';
                    fileSearchOutputsSent.add(itemId);
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: {
                        type: 'tool_output',
                        id: itemId,
                        tool: 'file_search',
                        server: 'file_search',
                        output: summary,
                        arguments: JSON.stringify({ queries, vector_store_ids: vsIdsForCfg, max_num_results: maxNumResults }),
                      }
                    }) + '\n'));
                  }
                  // Code interpreter completed
                  else if (itemType === 'code_interpreter_call') {
                    const results = data.item.outputs || data.item.results || [];
                    const outputText = results.map(r => r.logs || r.output || r.text || '').join('\n').trim();
                    controller.enqueue(encoder.encode(JSON.stringify({
                      code_execution: { code: data.item.code || data.item.input || '', output: outputText, containerId: data.item.container_id || null }
                    }) + '\n'));
                  }
                  // NL2SQL completed
                  else if (itemType === 'nl2sql_call') {
                    const sql = data.item.generated_sql || data.item.sql || '';
                    const results = data.item.results || data.item.output || '';
                    const output = sql ? `**Generated SQL:**\n\`\`\`sql\n${sql}\n\`\`\`${results ? `\n\n**Results:**\n${typeof results === 'string' ? results : JSON.stringify(results, null, 2)}` : ''}` : 'Query completed';
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'tool_output', id: itemId, tool: 'nl2sql', server: 'nl2sql', output, arguments: data.item.input_natural_language_query || data.item.query || '' }
                    }) + '\n'));
                  }
                  // Image generation completed
                  else if (itemType === 'image_generation_call') {
                    controller.enqueue(encoder.encode(JSON.stringify({ generated_image: data.item.result || '' }) + '\n'));
                  }
                  // Function call completed
                  else if (itemType === 'function_call') {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      function_call: { id: itemId, callId: data.item.call_id, name: data.item.name, arguments: data.item.arguments }
                    }) + '\n'));
                  }
                  // Reasoning item done — signal end-of-reasoning to the UI
                  else if (itemType === 'reasoning') {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      reasoning: { type: 'item_end', id: itemId }
                    }) + '\n'));
                  }
                  // Message item done — extract final annotations from content parts
                  else if (itemType === 'message') {
                    const itemAnnotations = (data.item.content || [])
                      .flatMap(part => part.annotations || [])
                      .filter(a => a.type === 'url_citation' || a.type === 'file_citation');
                    if (itemAnnotations.length > 0) {
                      controller.enqueue(encoder.encode(JSON.stringify({ annotations: itemAnnotations }) + '\n'));
                    }
                  }

                  // Surface any non-completed status to the client.
                  // mcp_call already has its own handling above; others (message, reasoning, etc.)
                  // need an explicit signal so the UI doesn't show incomplete output as final.
                  if (itemStatus && itemStatus !== 'completed') {
                    log.error('Output item finished with non-completed status', {
                      itemType, itemId, status: itemStatus, tool: data.item?.name, server: data.item?.server_label,
                      output: (data.item?.output || '').substring(0, 2000), elapsed
                    });
                    if (itemType !== 'mcp_call') {
                      controller.enqueue(encoder.encode(JSON.stringify({
                        item_error: { id: itemId, itemType, status: itemStatus }
                      }) + '\n'));
                    }
                  }
                }

                // ═══ MCP LIFECYCLE EVENTS ═══
                else if (eventType === 'response.mcp_list_tools.in_progress') {
                  log.debug('MCP list tools in progress', { itemId, elapsed });
                }
                else if (eventType === 'response.mcp_list_tools.completed') {
                  log.debug('MCP list tools completed', { itemId, elapsed });
                }
                else if (eventType === 'response.mcp_call.in_progress') {
                  log.debug('MCP call in progress', { itemId, elapsed });
                }
                else if (eventType === 'response.mcp_call.completed') {
                  log.info('MCP call completed (OCI side)', { itemId, elapsed });
                }
                else if (eventType === 'response.mcp_call.failed') {
                  log.error('MCP CALL FAILED (OCI side)', { itemId, elapsed, data: JSON.stringify(data).substring(0, 1000) });
                }

                // ═══ CODE INTERPRETER EVENTS ═══
                // Stream Python code being written by the interpreter token-by-token,
                // and surface execution phases (in_progress → interpreting → completed)
                // so the UI can show real-time code + status.
                else if (eventType === 'response.code_interpreter_call.in_progress') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    code_status: { id: itemId, status: 'in_progress' }
                  }) + '\n'));
                }
                else if (eventType === 'response.code_interpreter_call_code.delta' && data.delta) {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    code_delta: { id: itemId, text: data.delta }
                  }) + '\n'));
                }
                else if (eventType === 'response.code_interpreter_call_code.done') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    code_delta: { id: itemId, done: true, text: data.code || '' }
                  }) + '\n'));
                }
                else if (eventType === 'response.code_interpreter_call.interpreting') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    code_status: { id: itemId, status: 'interpreting' }
                  }) + '\n'));
                }
                else if (eventType === 'response.code_interpreter_call.completed') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    code_status: { id: itemId, status: 'completed' }
                  }) + '\n'));
                }

                // ═══ INLINE ANNOTATIONS (emitted during streaming) ═══
                else if (eventType === 'response.output_text.annotation.added') {
                  const ann = data.annotation;
                  if (ann && (ann.type === 'url_citation' || ann.type === 'file_citation')) {
                    controller.enqueue(encoder.encode(JSON.stringify({
                      annotations: [ann]
                    }) + '\n'));
                  }
                }

                // ═══ FILE SEARCH EVENTS ═══
                else if (eventType === 'response.file_search_call.in_progress') {
                  // Defensive: same payload as the output_item.added branch above so that
                  // the chip is created even if OCI skips output_item.added for this item.
                  // useChat.js dedups on mcpItemId so a second emit with the same id is harmless.
                  const fsToolCfgs = (tools || []).filter(t => t.type === 'file_search');
                  const vsIdsForCfg = fsToolCfgs.flatMap(t => t.vector_store_ids || []);
                  const maxNumResults = fsToolCfgs[0]?.max_num_results || null;
                  controller.enqueue(encoder.encode(JSON.stringify({
                    mcp: {
                      type: 'calling',
                      id: itemId,
                      server: 'file_search',
                      tool: 'file_search',
                      arguments: JSON.stringify({ vector_store_ids: vsIdsForCfg, max_num_results: maxNumResults }),
                    }
                  }) + '\n'));
                }
                else if (eventType === 'response.file_search_call.searching') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    mcp: { type: 'tool_output', tool: 'file_search', server: 'file_search', output: 'Searching knowledge base...', status: 'searching' }
                  }) + '\n'));
                }
                else if (eventType === 'response.file_search_call.completed') {
                  log.debug('File search completed', { itemId, elapsed });
                }

                // ═══ NL2SQL EVENTS ═══
                else if (eventType === 'response.nl2sql_call.in_progress') {
                  const query = data.query || data.input_natural_language_query || '';
                  controller.enqueue(encoder.encode(JSON.stringify({
                    mcp: { type: 'calling', id: itemId, server: 'nl2sql', tool: 'nl2sql', arguments: query ? JSON.stringify({ query }) : '' }
                  }) + '\n'));
                }
                else if (eventType === 'response.nl2sql_call.completed') {
                  const sql = data.generated_sql || data.sql || '';
                  const results = data.results || data.output || '';
                  const output = sql ? `**Generated SQL:**\n\`\`\`sql\n${sql}\n\`\`\`${results ? `\n\n**Results:**\n${typeof results === 'string' ? results : JSON.stringify(results, null, 2)}` : ''}` : 'Query completed';
                  controller.enqueue(encoder.encode(JSON.stringify({
                    mcp: { type: 'tool_output', id: itemId, tool: 'nl2sql', server: 'nl2sql', output }
                  }) + '\n'));
                }

                // ═══ REASONING EVENTS ═══
                else if (eventType === 'response.reasoning_summary_text.delta' && data.delta) {
                  controller.enqueue(encoder.encode(JSON.stringify({ reasoning: { type: 'delta', text: data.delta } }) + '\n'));
                }
                else if (eventType === 'response.reasoning_summary_text.done') {
                  controller.enqueue(encoder.encode(JSON.stringify({ reasoning: { type: 'done' } }) + '\n'));
                }
                else if (eventType === 'response.reasoning_summary_part.added') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    reasoning: { type: 'part_start' }
                  }) + '\n'));
                }
                else if (eventType === 'response.reasoning_summary_part.done') {
                  controller.enqueue(encoder.encode(JSON.stringify({
                    reasoning: { type: 'part_end' }
                  }) + '\n'));
                }

                // ═══ CONTENT PART EVENTS ═══
                else if (eventType === 'response.content_part.added') {
                  log.debug('Content part added', { type: data.part?.type, elapsed });
                }
                else if (eventType === 'response.content_part.done') {
                  if (data.part?.annotations?.length > 0) {
                    controller.enqueue(encoder.encode(JSON.stringify({ annotations: data.part.annotations }) + '\n'));
                  }
                }

                // ═══ RESPONSE TERMINAL EVENTS (completed / incomplete / failed) ═══
                // All three carry the same `data.response` shape; differences are in
                // `data.response.status`, `incomplete_details.reason`, and `error`.
                // Treat all as terminal so the stream closes cleanly and the UI stops
                // showing "premature close" for legitimate incomplete/failed responses.
                else if (eventType === 'response.completed' || eventType === 'response.incomplete' || eventType === 'response.failed') {
                  responseCompleted = true;
                  const returnedConvId = data.response?.conversation;
                  if (returnedConvId) {
                    controller.enqueue(encoder.encode(JSON.stringify({ conversation_id: returnedConvId }) + '\n'));
                  }

                  const outputs = data.response?.output || [];
                  const respStatus = data.response?.status;
                  const incompleteDetails = data.response?.incomplete_details;
                  const usage = data.response?.usage;
                  const error = data.response?.error;

                  // Log EVERY output item in the completed response
                  outputs.forEach((o, i) => {
                    const summary = { index: i, type: o.type, status: o.status, role: o.role };
                    if (o.name) summary.tool = o.name;
                    if (o.server_label) summary.server = o.server_label;
                    if (o.type === 'mcp_call') {
                      summary.hasOutput = !!o.output;
                      summary.outputLen = o.output?.length || 0;
                      summary.hasArguments = !!o.arguments;
                      summary.argsLen = o.arguments?.length || 0;
                    }
                    if (o.type === 'mcp_call' && o.status !== 'completed') {
                      log.error('MCP call in completed response has bad status', { ...summary, output: (o.output || '').substring(0, 1000) });
                    }
                    log.info('Completed output item', summary);
                  });
                  // Log all mcp_call items from response to see if create_oci_diagram is there
                  const mcpItems = outputs.filter(o => o.type === 'mcp_call');
                  log.info('All MCP calls in completed response', { count: mcpItems.length, tools: mcpItems.map(m => ({ name: m.name, server: m.server_label, status: m.status, id: m.id })) });

                  // Log completion
                  log.info('Response completed', {
                    status: respStatus,
                    error: error || null,
                    outputTokens: usage?.output_tokens,
                    totalTokens: usage?.total_tokens,
                    outputItems: outputs.length,
                    elapsed: Date.now() - startTime,
                    opcRequestId,
                  });

                  if (respStatus !== 'completed') {
                    log.error('RESPONSE NOT COMPLETED', { status: respStatus, error, incompleteDetails, opcRequestId });
                  }
                  if (incompleteDetails) log.warn('Response incomplete', { details: incompleteDetails });

                  // Emit tool_output for MCP calls that arrived in response.completed
                  // but never got an individual output_item.done event
                  for (const mc of outputs.filter(o => o.type === 'mcp_call' && o.output)) {
                    const alreadySent = toolCalls.some(tc => tc.tool === mc.name && tc.server === mc.server_label && tc.outputSent);
                    if (!alreadySent) {
                      log.info('Emitting late MCP tool_output from response.completed', { tool: mc.name, server: mc.server_label, outputSize: mc.output.length });
                      controller.enqueue(encoder.encode(JSON.stringify({
                        mcp: { type: 'tool_output', id: mc.id, tool: mc.name, server: mc.server_label, output: mc.output, outputSize: mc.output.length, truncated: false, arguments: mc.arguments }
                      }) + '\n'));
                    }
                  }

                  // Fallback: emit tool_output for any file_search_call whose
                  // output_item.done branch never fired (rare, but keeps the chip in sync)
                  const fsToolCfgs = (tools || []).filter(t => t.type === 'file_search');
                  const vsIds = fsToolCfgs.flatMap(t => t.vector_store_ids || []);
                  // Read max_num_results from tool config — default 20 (was hardcoded 5)
                  const maxNumResults = fsToolCfgs[0]?.max_num_results || 20;
                  for (const fs of outputs.filter(o => o.type === 'file_search_call')) {
                    if (fileSearchOutputsSent.has(fs.id)) continue;
                    const queries = fs.queries || [];
                    const summary = queries.length > 0
                      ? `Searched: ${queries.map(q => `"${q}"`).join(', ')}`
                      : 'Search completed';
                    fileSearchOutputsSent.add(fs.id);
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: {
                        type: 'tool_output',
                        id: fs.id,
                        tool: 'file_search',
                        server: 'file_search',
                        output: summary,
                        arguments: JSON.stringify({ queries, vector_store_ids: vsIds, max_num_results: maxNumResults }),
                      }
                    }) + '\n'));
                  }

                  // OCI returns file_search_call with results: null. Re-run the search ourselves
                  // against the vector_store(s) attached to this request so we can emit the
                  // matching documents as `file_citation` annotations the UI renders as chips.
                  // Each citation carries `file_search_call_id` so the chip can count chunks per call.
                  const fsCalls = outputs.filter(o => o.type === 'file_search_call' && o.queries?.length > 0);
                  if (fsCalls.length > 0 && vsIds.length > 0) {
                    const fsCitations = [];
                    const seen = new Set();
                    await Promise.all(
                      fsCalls.flatMap(fs => fs.queries.flatMap(query =>
                        vsIds.map(async (vsId) => {
                          try {
                            const sr = await ociRequest('POST', `/vector_stores/${vsId}/search`, {
                              body: { query, max_num_results: maxNumResults },
                            });
                            if (!sr.ok) return;
                            const sd = await sr.json();
                            for (const r of (sd.data || [])) {
                              if (!r.file_id) continue;
                              const snippet = (r.content || [])
                                .map(c => (typeof c === 'string' ? c : c?.text || ''))
                                .join('')
                                .slice(0, 3000);
                              // Dedup at (file_search_call, query, chunk) level so the same chunk
                              // can appear under different file_search invocations.
                              const key = `${fs.id}::${query}::${r.file_id}::${snippet.slice(0, 80)}`;
                              if (seen.has(key)) continue;
                              seen.add(key);
                              fsCitations.push({
                                type: 'file_citation',
                                file_id: r.file_id,
                                filename: r.filename,
                                score: r.score,
                                snippet,
                                vector_store_id: vsId,
                                query,
                                file_search_call_id: fs.id,
                              });
                            }
                          } catch (e) {
                            log.warn('file_search source enrichment failed', { vsId, query, error: e.message });
                          }
                        })
                      ))
                    );
                    if (fsCitations.length > 0) {
                      // Highest score first
                      fsCitations.sort((a, b) => (b.score || 0) - (a.score || 0));
                      log.info('Emitting file_search source citations', { count: fsCitations.length });
                      controller.enqueue(encoder.encode(JSON.stringify({ annotations: fsCitations }) + '\n'));
                    }
                  }

                  // Enrich nl2sql with results
                  for (const ns of outputs.filter(o => o.type === 'nl2sql_call')) {
                    const sql = ns.generated_sql || ns.sql || '';
                    const results = ns.results || ns.output || '';
                    const output = sql ? `**Generated SQL:**\n\`\`\`sql\n${sql}\n\`\`\`${results ? `\n\n**Results:**\n${typeof results === 'string' ? results : JSON.stringify(results, null, 2)}` : ''}` : 'Query completed';
                    controller.enqueue(encoder.encode(JSON.stringify({
                      mcp: { type: 'tool_output', tool: 'nl2sql', server: 'nl2sql', output }
                    }) + '\n'));
                  }

                  // Extract all annotations
                  const allAnnotations = outputs
                    .filter(item => Array.isArray(item.content))
                    .flatMap(item => item.content)
                    .flatMap(part => part.annotations || [])
                    .filter(a => a.type === 'url_citation' || a.type === 'file_citation');

                  if (allAnnotations.length > 0) {
                    controller.enqueue(encoder.encode(JSON.stringify({ annotations: allAnnotations }) + '\n'));
                  }

                  usageData = data.response?.usage || null;

                  // Build completion trace
                  const completedElapsed = Date.now() - startTime;
                  trace.opcRequestId = opcRequestId;
                  trace.completion = {
                    status: respStatus,
                    error: error || null,
                    outputTokens: usage?.output_tokens,
                    totalTokens: usage?.total_tokens,
                    outputItems: outputs.length,
                    outputItemTypes: outputs.map(o => ({ type: o.type, tool: o.name, status: o.status })),
                    elapsed: completedElapsed,
                    incompleteDetails: incompleteDetails || null,
                  };
                  traceEvent('response_completed', { status: respStatus, outputItems: outputs.length, elapsed: completedElapsed });

                  // Surface terminal-but-not-completed reason to the client so the
                  // UI can show a clear message instead of "premature close".
                  if (respStatus !== 'completed') {
                    const reason = incompleteDetails?.reason || error?.message || error?.code || respStatus || 'unknown';
                    trace.error = `Response ended with status "${respStatus}": ${reason}`;
                    controller.enqueue(encoder.encode(JSON.stringify({
                      response_incomplete: { status: respStatus, reason, error: error || null, incompleteDetails: incompleteDetails || null }
                    }) + '\n'));
                  }
                  // OCI silent failure: status="completed" but no input/output tokens and
                  // outputs only contain mcp_list_tools (no message/reasoning/tool_call).
                  // Verified reproducible upstream — surface as an error so the UI doesn't
                  // hang on a "successful" response that never actually ran the model.
                  else if (
                    (usage?.output_tokens === 0 || usage?.total_tokens === 0) &&
                    !outputs.some(o => o.type === 'message' || o.type === 'mcp_call' || o.type === 'function_call' || o.type === 'code_interpreter_call' || o.type === 'reasoning')
                  ) {
                    trace.error = `OCI returned status="completed" with 0 output tokens and no model output. ` +
                      `Only ${outputs.length} mcp_list_tools item(s) returned. This is an OCI silent-failure bug ` +
                      `(model never ran). opc-request-id: ${opcRequestId || 'unknown'}.`;
                    log.error('OCI silent failure: completed with no model output', {
                      outputItems: outputs.length, outputTypes: outputs.map(o => o.type), usage, opcRequestId,
                    });
                    controller.enqueue(encoder.encode(JSON.stringify({
                      response_incomplete: {
                        status: 'completed',
                        reason: 'oci_silent_failure',
                        error: null,
                        incompleteDetails: { reason: 'oci_silent_failure', outputItems: outputs.length, outputTypes: outputs.map(o => o.type) },
                      }
                    }) + '\n'));
                  }

                  // Cache for end-of-stream finalization.
                  // Do NOT declare tools orphaned or emit done:true yet —
                  // OCI sometimes emits tool results (response.output_item.done with mcp_call output)
                  // AFTER response.completed when the tool was slow. Wait until the stream actually closes.
                  completedResponseData = { outputs, respStatus, data, completedElapsed };
                }

                // ═══ ANYTHING ELSE — log it, never silently drop ═══
                else {
                  log.warn('Unknown SSE event', { type: eventType, itemType, elapsed, data: JSON.stringify(data).substring(0, 500) });
                }

              } catch (e) {
                log.warn('Unparseable SSE line', { line: line.substring(0, 200), error: e.message });
              }
            }
          }
        } finally {
          // Log leftover buffer — could contain error info OCI sent at the end
          if (buffer.trim()) {
            log.warn('Leftover buffer after stream ended', { buffer: buffer.substring(0, 2000) });
            // Try to parse it
            try {
              const leftover = buffer.trim().startsWith('data: ') ? JSON.parse(buffer.trim().slice(6)) : null;
              if (leftover) log.warn('Leftover parsed data', { type: leftover.type, data: JSON.stringify(leftover).substring(0, 1000) });
            } catch (_) {}
          }

          const elapsed = Date.now() - startTime;
          log.info('Stream ended', { elapsed, toolCalls: toolCalls.length, textLength: fullOutputText.length, responseCompleted, eventCount, lastEventType, stalled, opcRequestId });

          // Finalize completed response: check orphaned tools and emit done:true.
          // Deferred from response.completed because OCI sometimes sends tool results AFTER it.
          if (responseCompleted && completedResponseData) {
            const { outputs, completedElapsed, data: completedData } = completedResponseData;
            const completedToolIds = new Set(outputs.filter(o => o.type === 'mcp_call').map(o => o.id));
            // Also consider tools whose output arrived after response.completed via output_item.done
            const postCompletionToolIds = new Set(toolCalls.filter(tc => tc.outputSent).map(tc => tc.id).filter(Boolean));
            for (const [tid, tinfo] of Object.entries(trace.tools)) {
              if (tinfo.status === 'calling' && !completedToolIds.has(tid) && !postCompletionToolIds.has(tid)) {
                tinfo.status = 'orphaned';
                traceEvent('tool_orphaned', { tool: tinfo.tool, server: tinfo.server, id: tid, detail: 'OCI closed stream without this tool result' });
                trace.error = trace.error || `OCI completed response while "${tinfo.tool}" (${tinfo.server}) was still executing. The tool was called at ${tinfo.startMs}ms but OCI closed the stream at ${completedElapsed}ms without including its result. This is an OCI Responses API issue.`;
              }
            }
            try {
              controller.enqueue(encoder.encode(JSON.stringify({
                done: true, response_id: completedData.response?.id || null, opc_request_id: opcRequestId || null, trace
              }) + '\n'));
            } catch (_) { /* controller may already be closing */ }
          }

          // Detect premature close: OCI dropped connection without response.completed
          if (!responseCompleted && !stalled) {
            log.error('PREMATURE STREAM CLOSE — OCI never sent response.completed', {
              elapsed, eventCount, lastEventType, toolCalls, textLength: fullOutputText.length, opcRequestId,
              buffer: buffer.substring(0, 500),
            });
            trace.opcRequestId = opcRequestId;
            trace.error = `OCI closed connection after ${Math.round(elapsed / 1000)}s without response.completed. ` +
              `Received ${eventCount} events, last was "${lastEventType || 'none'}". ` +
              `${toolCalls.length > 0 ? `Active tools: ${toolCalls.map(t => t.tool).join(', ')}. ` : ''}` +
              `This is an OCI Responses API issue — the upstream closed the SSE stream prematurely.`;
            traceEvent('premature_close', { eventCount, lastEventType });
            try {
              controller.enqueue(encoder.encode(JSON.stringify({
                error: trace.error,
                done: true,
                trace,
              }) + '\n'));
            } catch (_) { /* controller may already be closing */ }
          }

          reader.releaseLock();
          controller.close();

          // Finalize LangFuse trace (non-blocking)
          if (langfuseGeneration) {
            try {
              const duration = Date.now() - startTime;
              langfuseGeneration.end({
                output: fullOutputText.slice(0, 10000),
                usage: usageData ? {
                  input: usageData.input_tokens || usageData.prompt_tokens,
                  output: usageData.output_tokens || usageData.completion_tokens,
                  total: usageData.total_tokens,
                } : undefined,
                metadata: { duration, toolCalls, opcRequestId },
              });
              langfuseTrace.update({ output: fullOutputText.slice(0, 500) });
              langfuse.flushAsync().catch(() => {});
            } catch (e) {
              log.warn('LangFuse finalize error', { error: e.message });
            }
          }
        }
      }
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error) {
    log.error('Unhandled error', { error: error.message, stack: error.stack });
    // Log error to LangFuse if available
    if (langfuseGeneration) {
      try {
        langfuseGeneration.end({ level: 'ERROR', statusMessage: error.message });
        langfuse?.flushAsync().catch(() => {});
      } catch (_) {}
    }
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
