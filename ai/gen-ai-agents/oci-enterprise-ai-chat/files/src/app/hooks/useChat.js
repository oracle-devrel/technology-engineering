"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import createGenaiAgentService from "../services/genaiAgentsService";
import ConversationStorage from "../services/conversationStorage";
import { generateTitle } from "../services/titleService";
import { groupMessages, parseContentWithWidgets } from "../utils/messageUtils";
import { createWidgetStreamParser } from "../utils/widgetParser";
import { createWidgetV2StreamParser, serializeWidgetV2Tree } from "../utils/widgetV2Parser";

// Friendly names for OCI internal tools
const OCI_INTERNAL_LABELS = {
  oci_internal_search_memory: 'Memory',
};

// Format tool names: "text_to_speech" -> "Text to speech"
const formatToolName = (name) => {
  if (!name) return name;
  if (OCI_INTERNAL_LABELS[name]) return OCI_INTERNAL_LABELS[name];
  return name
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\b\w/, c => c.toUpperCase());
};

export default function useChat({ initialConversationId = null, selectedModel, onError }) {
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingConversation, setIsLoadingConversation] = useState(false);
  const [genaiService, setGenaiService] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [activeChips, setActiveChips] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [spacerHeight, setSpacerHeight] = useState(0);
  const [recentConversations, setRecentConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(true);

  const latestMessageRef = useRef(null);
  const chatContainerRef = useRef(null);
  const streamingStateRef = useRef(null);
  const loadedConversationRef = useRef(null);
  const inputRef = useRef(null);

  const resetChatState = useCallback(() => {
    setChatHistory([]);
    setActiveChips({});
    loadedConversationRef.current = null;
  }, []);

  const [recentConversationsPage, setRecentConversationsPage] = useState({ hasMore: true, isLoadingMore: false });
  const RECENT_PAGE_SIZE = 20;

  const refreshRecentConversations = useCallback(async () => {
    try {
      const page = await ConversationStorage.getPage(0, RECENT_PAGE_SIZE);
      setRecentConversations(page.items);
      setRecentConversationsPage({ hasMore: page.hasMore, isLoadingMore: false });
    } catch (e) {
      console.error("Error refreshing conversations:", e);
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  const loadMoreConversations = useCallback(async () => {
    if (recentConversationsPage.isLoadingMore || !recentConversationsPage.hasMore) return;
    setRecentConversationsPage(prev => ({ ...prev, isLoadingMore: true }));
    try {
      const current = recentConversations.length;
      const page = await ConversationStorage.getPage(current, RECENT_PAGE_SIZE);
      setRecentConversations(prev => [...prev, ...page.items]);
      setRecentConversationsPage({ hasMore: page.hasMore, isLoadingMore: false });
    } catch (e) {
      console.error("Error loading more conversations:", e);
      setRecentConversationsPage(prev => ({ ...prev, isLoadingMore: false }));
    }
  }, [recentConversations.length, recentConversationsPage.hasMore, recentConversationsPage.isLoadingMore]);

  const scrollToLatestMessage = useCallback(() => {
    setTimeout(() => {
      if (!latestMessageRef.current || !chatContainerRef.current) return;
      const container = chatContainerRef.current;
      const message = latestMessageRef.current;
      const containerRect = container.getBoundingClientRect();
      const messageRect = message.getBoundingClientRect();
      const scrollOffset = messageRect.top - containerRect.top + container.scrollTop - 60;
      container.scrollTo({ top: scrollOffset, behavior: 'smooth' });
    }, 150);
  }, []);

  const updateLatestExchange = useCallback((updater) => {
    setChatHistory(prev => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;
      if (lastIndex >= 0 && updated[lastIndex].isLatest) {
        updated[lastIndex] = updater(updated[lastIndex]);
      }
      return updated;
    });
  }, []);

  const createNewExchange = useCallback((userMessage, extras = {}) => ({
    id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    userMessage,
    responses: [],
    sources: [],
    isLatest: true,
    ...extras,
  }), []);

  const initStreamingState = useCallback(() => {
    streamingStateRef.current = {
      responses: [],
      sources: [],
      accumulatedText: "",
      currentTextContent: "",
      widgetParser: createWidgetStreamParser(),
      // V2 widget support
      widgetV2Parser: createWidgetV2StreamParser(),
      v2DetectBuffer: "",      // Buffer to detect @@widget opener
      v2Active: false,         // Currently inside a @@widget...@@ block
      v2CloseBuffer: "",       // Buffer to detect @@ closer
      streamCompleted: false,  // Track if OCI sent response.completed (done: true)
      streamStartedAt: Date.now(),  // For debugging timing
      streamError: null,            // Capture the actual error reason
    };
  }, []);

  const parseWidgetResponse = useCallback((content) => {
    if (typeof content !== 'string') return null;
    const match = content.trim().match(/^§>(.+)§$/s);
    if (!match) return null;

    const data = {};
    const pairs = match[1].split("|");
    for (const pair of pairs) {
      const colonIdx = pair.indexOf(":");
      if (colonIdx > 0) {
        const key = pair.slice(0, colonIdx);
        const value = pair.slice(colonIdx + 1);
        data[key] = value;
      }
    }

    const { _action, ...displayData } = data;
    return { action: _action, data: displayData };
  }, []);

  // Parse <pasted_content> tags from loaded messages
  const parsePastedContent = useCallback((text) => {
    if (typeof text !== 'string') return { userText: text, attachedTexts: [] };

    const pastedRegex = /<pasted_content index="(\d+)"(?:\s+name="([^"]*)")?>\n([\s\S]*?)\n<\/pasted_content>/g;
    const attachedTexts = [];
    let match;

    while ((match = pastedRegex.exec(text)) !== null) {
      const name = match[2] || null;
      const content = match[3];
      const ext = name ? (name.match(/\.([^.]+)$/) || [])[1]?.toLowerCase() || null : null;
      attachedTexts.push({
        id: `loaded-${match[1]}-${Date.now()}`,
        name,
        ext,
        content,
        preview: content.slice(0, 200).replace(/\n/g, ' ') + (content.length > 200 ? '...' : ''),
      });
    }

    // Remove pasted content tags to get the user's typed text
    const userText = text.replace(pastedRegex, '').replace(/\n\n+/g, '\n\n').trim();

    return { userText, attachedTexts };
  }, []);

  const processStreamingChunk = useCallback((chunk, state) => {
    // Track stream completion and capture trace
    if (typeof chunk === 'object' && chunk.done) {
      state.streamCompleted = true;
      if (chunk.trace) state.trace = chunk.trace;
      return [...state.responses];
    }

    // Capture response.id as soon as OCI emits it (response.created). Stored on the
    // streaming state so any approval card created mid-stream can read it.
    if (typeof chunk === 'object' && chunk.response_id) {
      state.responseId = chunk.response_id;
      // Backfill any approval card that was created before the id arrived
      for (const r of state.responses) {
        if (r.type === 'mcp_approval_request' && !r.responseId) r.responseId = chunk.response_id;
      }
      return [...state.responses];
    }

    // MCP approval request — push a card that the user must Approve or Reject.
    if (typeof chunk === 'object' && chunk.mcp_approval_request) {
      const ar = chunk.mcp_approval_request;
      state.responses = state.responses.filter(r => r.type !== 'thinking');
      state.responses.push({
        type: 'mcp_approval_request',
        requestId: ar.request_id,
        serverLabel: ar.server_label,
        toolName: ar.tool_name,
        arguments: ar.arguments,
        responseId: state.responseId || null,
        decision: null, // 'approved' | 'rejected' | null
      });
      return [...state.responses];
    }

    // Capture trace from error path
    if (typeof chunk === 'object' && chunk.trace && !chunk.done) {
      state.trace = chunk.trace;
      return [...state.responses];
    }

    // Handle thinking indicator
    if (typeof chunk === 'object' && chunk.thinking) {
      // Add thinking indicator if not already present
      if (!state.responses.some(r => r.type === "thinking")) {
        state.responses.push({ type: "thinking" });
      }
      return [...state.responses];
    }

    // Handle generated image from image_generation tool
    if (typeof chunk === 'object' && chunk.generated_image) {
      state.responses = state.responses.filter(r => r.type !== "thinking");
      // Remove the image_generation mcp_chip if present
      const chipIdx = state.responses.findLastIndex(r => r.type === "mcp_chip" && r.tool === "image_generation");
      if (chipIdx >= 0) {
        state.responses.splice(chipIdx, 1);
      }
      state.responses.push({
        type: "generated_image",
        content: chunk.generated_image,
      });
      return [...state.responses];
    }

    // Reasoning streaming.
    // OCI emits sub-topic headers inline in the text — typically a short line
    // starting with a gerund like "Considering", "Designing", "Evaluating".
    // We detect by that pattern (not by \n\n separators because OCI doesn't
    // always emit them) to (a) update the chip label live and (b) wrap each
    // header in bold with blank-line padding in the expanded panel.
    if (typeof chunk === 'object' && chunk.reasoning) {
      if (chunk.reasoning.type === 'start' || chunk.reasoning.type === 'part_start' || chunk.reasoning.type === 'part_end') {
        // lifecycle events — no content change
      } else if (chunk.reasoning.type === 'delta' && chunk.reasoning.text) {
        const activeReasoning = state.responses.findLast(r => r.type === "reasoning" && !r.done);
        if (activeReasoning) {
          activeReasoning.text += chunk.reasoning.text;
        } else {
          const lastReasoningIdx = state.responses.findLastIndex(r => r.type === "reasoning");
          const hasContentAfter = lastReasoningIdx >= 0 && state.responses.slice(lastReasoningIdx + 1).some(
            r => r.type !== "thinking" && r.type !== "mcp_connecting"
          );
          if (lastReasoningIdx >= 0 && !hasContentAfter) {
            state.responses[lastReasoningIdx].done = false;
            state.responses[lastReasoningIdx].text += chunk.reasoning.text;
          } else {
            state.responses = state.responses.filter(r => r.type !== "thinking");
            state.responses.push({ type: "reasoning", text: chunk.reasoning.text, done: false });
          }
        }
      } else if (chunk.reasoning.type === 'done' || chunk.reasoning.type === 'item_end') {
        const reasoningItem = state.responses.findLast(r => r.type === "reasoning" && !r.done);
        if (reasoningItem) reasoningItem.done = true;
        if (!state.responses.some(r => r.type === "thinking")) {
          state.responses.push({ type: "thinking" });
        }
      }
      return [...state.responses];
    }

    // Code interpreter — streaming code as it is written by the model.
    // Keyed by item id so multiple interpreter calls in the same response don't collide.
    if (typeof chunk === 'object' && chunk.code_delta) {
      const { id, text, done } = chunk.code_delta;
      state.responses = state.responses.filter(r => r.type !== "thinking");
      let ce = id ? state.responses.find(r => r.type === "code_execution" && r.id === id) : null;
      if (!ce) {
        // Replace the "Using code_interpreter..." chip with a live code block
        const chipIdx = state.responses.findLastIndex(r => r.type === "mcp_chip" && r.tool === "code_interpreter");
        if (chipIdx >= 0) state.responses.splice(chipIdx, 1);
        ce = { type: "code_execution", id: id || null, code: "", output: "", status: "writing" };
        state.responses.push(ce);
      }
      if (done) {
        // Final code snapshot from OCI — replace to ensure perfect fidelity
        ce.code = text || ce.code;
      } else if (text) {
        ce.code = (ce.code || "") + text;
      }
      return [...state.responses];
    }

    // Code interpreter status transitions: in_progress → interpreting → completed
    if (typeof chunk === 'object' && chunk.code_status) {
      const { id, status } = chunk.code_status;
      const ce = id ? state.responses.find(r => r.type === "code_execution" && r.id === id) : null;
      if (ce) {
        ce.status = status;
      }
      return [...state.responses];
    }

    // Code interpreter final result with output (arrives via output_item.done)
    if (typeof chunk === 'object' && chunk.code_execution) {
      state.responses = state.responses.filter(r => r.type !== "thinking");
      // Prefer to update the live streaming block if present; otherwise create a fresh one.
      let ce = state.responses.find(r => r.type === "code_execution" && !r.output);
      if (!ce) {
        const chipIdx = state.responses.findLastIndex(r => r.type === "mcp_chip" && r.tool === "code_interpreter");
        if (chipIdx >= 0) state.responses.splice(chipIdx, 1);
        ce = { type: "code_execution" };
        state.responses.push(ce);
      }
      ce.code = chunk.code_execution.code || ce.code || "";
      ce.output = chunk.code_execution.output || "";
      ce.containerId = chunk.code_execution.containerId || ce.containerId || null;
      ce.status = "completed";
      return [...state.responses];
    }

    // OCI ended the response with status "incomplete" or "failed".
    // Show the reason so the user knows why generation stopped.
    if (typeof chunk === 'object' && chunk.response_incomplete) {
      const { status, reason } = chunk.response_incomplete;
      state.responses = state.responses.filter(r => r.type !== "thinking");
      const reasonMap = {
        max_output_tokens: "Response stopped: hit the output token limit.",
        content_filter: "Response stopped by content filter.",
        max_tool_calls: "Response stopped: hit the tool-call limit.",
        stream_final_event_missing: "OCI closed the stream before sending the final event. Please try again.",
        oci_silent_failure: "OCI returned a successful response but never ran the model (likely an MCP server issue on OCI's side). Please try again.",
      };
      const message = reasonMap[reason] || `Response ended with status "${status}"${reason ? `: ${reason}` : ''}.`;
      state.responses.push({ type: "error", content: message });
      return [...state.responses];
    }

    // Non-completed status for non-MCP items (message/reasoning truncated, etc.)
    if (typeof chunk === 'object' && chunk.item_error) {
      const { itemType, status } = chunk.item_error;
      state.responses = state.responses.filter(r => r.type !== "thinking");
      state.responses.push({
        type: "error",
        content: `Response ${itemType} ended with status "${status}" (not completed).`,
      });
      return [...state.responses];
    }

    // Handle function call (client-side tool or OCI internal tool)
    if (typeof chunk === 'object' && chunk.function_call) {
      const fcName = chunk.function_call.name;
      const isOciInternal = fcName?.startsWith('oci_internal_');
      state.responses = state.responses.filter(r => r.type !== "thinking");
      state.responses.push({
        type: "mcp_chip",
        mcpItemId: chunk.function_call.id,
        server: isOciInternal ? 'oci' : 'function',
        tool: fcName,
        arguments: chunk.function_call.arguments,
        status: isOciInternal ? "calling" : "completed",
        label: isOciInternal ? 'Using memory...' : formatToolName(fcName),
        output: isOciInternal ? null : chunk.function_call.arguments,
        isOciInternal,
      });
      return [...state.responses];
    }

    // Handle annotations (url citations from web search, file citations from RAG).
    // Multiple `annotations` events can arrive per response (inline emit + end-of-message
    // emit + our file_search enrichment). Merge them into a single sources group, deduped
    // by url/file_id/filename so duplicates from different paths collapse to one chip.
    if (typeof chunk === 'object' && chunk.annotations) {
      const citations = chunk.annotations.filter(a => a.type === 'url_citation' || a.type === 'file_citation');
      if (citations.length > 0) {
        let sourcesGroup = state.responses.find(r => r.type === 'sources');
        if (!sourcesGroup) {
          sourcesGroup = { type: 'sources', sources: [] };
          state.responses.push(sourcesGroup);
        }
        // Each file_search chunk (same file_id, different snippet) is its own entry —
        // dedup by (query, file_id, snippet) so the same chunk found by multiple
        // file_search invocations shows under each query group in the dialog.
        const keyOf = (s) => s.url || (s.file_id ? `${s.query || ''}::${s.file_id}::${(s.snippet || '').slice(0, 80)}` : s.filename);
        const seen = new Set(sourcesGroup.sources.map(keyOf).filter(Boolean));
        for (const c of citations) {
          const k = keyOf(c);
          if (k && !seen.has(k)) {
            sourcesGroup.sources.push(c);
            seen.add(k);
          }
        }
        // Update chunk counts on file_search chips so the chip can show "N chunks"
        const chunksByFsId = new Map();
        for (const s of sourcesGroup.sources) {
          if (s.type === 'file_citation' && s.file_search_call_id) {
            chunksByFsId.set(s.file_search_call_id, (chunksByFsId.get(s.file_search_call_id) || 0) + 1);
          }
        }
        state.responses.forEach((r, idx) => {
          if (r.type === 'mcp_chip' && r.tool === 'file_search' && r.mcpItemId && chunksByFsId.has(r.mcpItemId)) {
            state.responses[idx] = { ...r, chunkCount: chunksByFsId.get(r.mcpItemId) };
          }
        });
      }
      return [...state.responses];
    }

    if (typeof chunk === 'object' && chunk.mcp) {
      const { mcp } = chunk;

      // Remove thinking indicator when MCP event arrives
      state.responses = state.responses.filter(r => r.type !== "thinking");

      if (mcp.type === 'connecting') {
        // Show inline loader if content already exists, otherwise use thinking indicator
        const hasContent = state.responses.some(r => r.type === "text" || r.type === "widget");
        if (hasContent) {
          if (!state.responses.some(r => r.type === "mcp_connecting")) {
            state.responses.push({ type: "mcp_connecting" });
          }
        } else {
          if (!state.responses.some(r => r.type === "thinking")) {
            state.responses.push({ type: "thinking" });
          }
        }
      } else if (mcp.type === 'calling') {
        // Remove mcp_connecting indicator — chip replaces it
        state.responses = state.responses.filter(r => r.type !== "mcp_connecting");

        // Finalize any existing streaming text so post-chip text creates a new entry AFTER the chip
        const streamingIdx = state.responses.findIndex(r => r.type === "text" && r.isStreaming);
        if (streamingIdx >= 0) {
          state.responses[streamingIdx].isStreaming = false;
          state.currentTextContent = "";
        }

        // Deduplicate: skip if a chip with the same id or same tool already in "calling" status
        const isDuplicate = mcp.id
          ? state.responses.some(r => r.type === "mcp_chip" && r.mcpItemId === mcp.id)
          : state.responses.some(r => r.type === "mcp_chip" && r.tool === mcp.tool && r.status === "calling");

        if (!isDuplicate) {
          state.responses.push({
            type: "mcp_chip",
            mcpItemId: mcp.id || null,
            server: mcp.server,
            tool: mcp.tool,
            arguments: mcp.arguments,
            status: "calling",
            label: `Using ${formatToolName(mcp.tool)}...`,
          });
        }
      } else if (mcp.type === 'tool_output') {
        // Find the chip and mark it as completed — match by ID first, fallback to tool name
        const chipIdx = mcp.id
          ? state.responses.findLastIndex(r => r.type === "mcp_chip" && r.mcpItemId === mcp.id)
          : state.responses.findLastIndex(r => r.type === "mcp_chip" && r.tool === mcp.tool && r.status === "calling");
        if (chipIdx >= 0) {
          state.responses[chipIdx].output = mcp.output;
          state.responses[chipIdx].status = "completed";
          state.responses[chipIdx].label = formatToolName(mcp.tool) || "Completed";
          // Update arguments if they weren't available at the calling stage
          if (mcp.arguments && !state.responses[chipIdx].arguments) {
            state.responses[chipIdx].arguments = mcp.arguments;
          }
        }
        // Re-add thinking indicator while the model generates text after the tool call
        if (!state.responses.some(r => r.type === "thinking")) {
          state.responses.push({ type: "thinking" });
        }
      } else if (mcp.type === 'error') {
        // Handle MCP error
        const chipIdx = state.responses.findLastIndex(r =>
          r.type === "mcp_chip" && (r.status === "calling" || r.status === "connecting")
        );
        if (chipIdx >= 0) {
          state.responses[chipIdx].status = "failed";
          state.responses[chipIdx].error = mcp.error || mcp.message || "Unknown error";
          state.responses[chipIdx].label = state.responses[chipIdx].tool || "Failed";
        }
      }
      return [...state.responses];
    }

    // Remove thinking/connecting indicators when text arrives
    // After tool completion, keep thinking until text has actually started rendering
    // (prevents React batching from swallowing the indicator when tool_output and first text delta arrive in the same chunk)
    const hasCompletedChips = state.responses.some(r => r.type === "mcp_chip" && r.status === "completed");
    if (!hasCompletedChips || state.currentTextContent.length > 0) {
      state.responses = state.responses.filter(r => r.type !== "thinking");
    }
    state.responses = state.responses.filter(r => r.type !== "mcp_connecting");

    // Mark ALL MCP chips that have output as completed (not just the last one)
    // Also mark OCI internal tools as completed when text arrives (they have no output)
    state.responses.forEach((r, idx) => {
      if (r.type === "mcp_chip" && r.status === "calling") {
        if (r.output || r.isOciInternal) {
          state.responses[idx].status = "completed";
          state.responses[idx].label = formatToolName(r.tool) || "Completed";
        }
      }
    });

    state.accumulatedText += chunk;

    const V2_OPEN = "@@widget\n";
    const V2_CLOSE = "@@";

    const findStreamingText = () => state.responses.findIndex(r => r.type === "text" && r.isStreaming);
    const findIncompleteV2 = () => state.responses.findLastIndex(r => r.type === "widget_v2" && !r.isComplete);

    const appendTextChar = (ch) => {
      state.currentTextContent += ch;
      const idx = findStreamingText();
      if (idx >= 0) {
        state.responses[idx].content = state.currentTextContent;
      } else {
        state.responses.push({ type: "text", content: state.currentTextContent, isStreaming: true });
      }
    };

    const flushV2DetectBuffer = () => {
      // Send buffered chars through v1 parser since they weren't @@widget
      for (const ch of state.v2DetectBuffer) {
        processV1Char(ch, state);
      }
      state.v2DetectBuffer = "";
    };

    const processV1Char = (char, st) => {
      const result = st.widgetParser.processChar(char);
      const findIncompleteWidget = () => st.responses.findLastIndex(r => r.type === "widget" && !r.isComplete);

      switch (result.action) {
        case "append": {
          appendTextChar(result.char);
          break;
        }
        case "start_widget": {
          if (st.currentTextContent) {
            const idx = findStreamingText();
            if (idx >= 0) st.responses[idx].isStreaming = false;
            st.currentTextContent = "";
          }
          st.responses.push({ type: "widget", widgetProps: {}, streamingKey: null, streamingValue: "", isComplete: false });
          break;
        }
        case "new_key": {
          const idx = findIncompleteWidget();
          if (idx >= 0) {
            st.responses[idx].streamingKey = result.key;
            st.responses[idx].streamingValue = "";
          }
          break;
        }
        case "stream_value": {
          const idx = findIncompleteWidget();
          if (idx >= 0) {
            st.responses[idx].streamingValue = result.value;
            st.responses[idx].widgetProps = { ...result.widget };
          }
          break;
        }
        case "update_widget": {
          const idx = findIncompleteWidget();
          if (idx >= 0) {
            st.responses[idx].widgetProps = { ...result.widget };
            st.responses[idx].streamingKey = null;
            st.responses[idx].streamingValue = "";
          }
          break;
        }
        case "close_widget": {
          const idx = findIncompleteWidget();
          if (idx >= 0) {
            st.responses[idx].widgetProps = { ...result.widget };
            st.responses[idx].isComplete = true;
            st.responses[idx].streamingKey = null;
            st.responses[idx].streamingValue = "";
          }
          break;
        }
      }
    };

    for (const char of chunk) {
      // === V2 close detection (inside a @@widget block) ===
      if (state.v2Active) {
        // Check for @@ closer (but only at top level, not inside a tag attribute)
        state.v2CloseBuffer += char;

        if (V2_CLOSE.startsWith(state.v2CloseBuffer)) {
          if (state.v2CloseBuffer === V2_CLOSE) {
            // Found closing @@ — finalize the v2 widget
            const idx = findIncompleteV2();
            if (idx >= 0) {
              state.responses[idx].tree = state.widgetV2Parser.finalize();
              state.responses[idx].isComplete = true;
            }
            state.v2Active = false;
            state.v2CloseBuffer = "";
            state.widgetV2Parser.reset();
          }
          // Still accumulating potential closer — don't feed to parser yet
          continue;
        }

        // Not a closer — flush buffered chars to v2 parser
        const buffered = state.v2CloseBuffer;
        state.v2CloseBuffer = "";
        for (const bch of buffered) {
          const result = state.widgetV2Parser.processChar(bch);
          if (result.tree) {
            const idx = findIncompleteV2();
            if (idx >= 0) {
              state.responses[idx].tree = result.tree;
            }
          }
        }
        continue;
      }

      // === V2 open detection (not inside any widget block) ===
      // Check if current char could be part of @@widget\n (tolerates trailing spaces)
      if (state.v2DetectBuffer.length > 0 || char === '@') {
        state.v2DetectBuffer += char;

        // Check for completed opener: @@widget followed by optional spaces then \n
        const base = "@@widget";
        if (state.v2DetectBuffer.length <= base.length) {
          // Still accumulating "@@widget"
          if (base.startsWith(state.v2DetectBuffer)) {
            continue;
          }
          // Doesn't match — flush
          flushV2DetectBuffer();
          continue;
        }
        // Past "@@widget" — accept spaces, wait for \n
        if (char === ' ' || char === '\t') {
          continue; // skip trailing whitespace
        }
        if (char === '\n') {
          // Found @@widget[spaces]\n — start v2 widget block
          if (state.currentTextContent) {
            const idx = findStreamingText();
            if (idx >= 0) state.responses[idx].isStreaming = false;
            state.currentTextContent = "";
          }
          state.v2Active = true;
          state.v2DetectBuffer = "";
          state.v2CloseBuffer = "";
          state.widgetV2Parser.reset();
          state.responses.push({ type: "widget_v2", tree: { tag: "root", children: [], attrs: {}, isComplete: false }, isComplete: false });
          continue;
        }
        // Non-whitespace, non-newline after @@widget — not a v2 opener
        flushV2DetectBuffer();
        continue;
      }

      // === Normal: v1 parser ===
      processV1Char(char, state);
    }

    return [...state.responses];
  }, []);

  const markIncompleteMcpChipsAsFailed = useCallback(() => {
    const state = streamingStateRef.current;
    const streamCompleted = state?.streamCompleted || false;
    const streamError = state?.streamError;
    const elapsed = state?.streamStartedAt ? Math.round((Date.now() - state.streamStartedAt) / 1000) : null;

    updateLatestExchange(exchange => {
      const sourcesCount = exchange.responses.filter(r => r.type === 'sources').length;
      if (sourcesCount > 0) console.log('[Sources] Before cleanup:', sourcesCount, 'sources entries in', exchange.responses.length, 'total responses');
      const responses = exchange.responses
        .filter(r => r.type !== "thinking" && r.type !== "mcp_connecting") // Remove leftover indicators
        .map(r => {
          if (r.type === "mcp_chip" && (r.status === "connecting" || r.status === "calling")) {
            // Build a descriptive error message for debugging
            const toolName = formatToolName(r.tool) || r.server || "unknown tool";
            let reason;
            if (r.error) {
              reason = r.error;
            } else if (streamCompleted) {
              reason = `OCI completed the response while ${toolName} was still running (${elapsed}s). The tool was called but OCI closed the stream before receiving its result. This is a known OCI behavior when an MCP tool call is the model's last action.`;
            } else if (streamError?.name === 'AbortError') {
              reason = `Stopped by user while ${toolName} was running (${elapsed}s)`;
            } else if (streamError?.name === 'StreamStallError' || streamError?.message?.includes('STREAM_STALL')) {
              reason = `Stream stalled — no data from server for 2+ min while ${toolName} was ${r.status} (${elapsed}s). ${streamError.message}`;
            } else if (streamError?.name === 'PrematureStreamClose') {
              reason = `OCI closed connection while ${toolName} was ${r.status} (${elapsed}s). ${streamError.message}`;
            } else if (streamError?.message?.includes('Failed to fetch') || streamError?.message?.includes('NetworkError')) {
              reason = `Network error while ${toolName} was ${r.status} (${elapsed}s) — check connection or server`;
            } else if (streamError) {
              reason = `${toolName} interrupted after ${elapsed}s: ${streamError.message || String(streamError)}`;
            } else {
              reason = `${toolName} was still ${r.status} when stream ended (${elapsed}s) — no error captured, possible silent disconnect`;
            }
            console.error(`[MCP] Tool failed: ${toolName}`, { status: r.status, elapsed, streamCompleted, error: streamError?.message });
            return {
              ...r,
              status: "failed",
              label: formatToolName(r.tool) || r.server || "Failed",
              error: reason
            };
          }
          // Stream ended while a reasoning block was still open — close it so
          // the UI stops showing the loading dots.
          if (r.type === "reasoning" && r.done === false) {
            return { ...r, done: true };
          }
          // Code interpreter block still writing/interpreting when stream died.
          if (r.type === "code_execution" && r.status && r.status !== "completed") {
            return { ...r, status: "failed" };
          }
          return r;
        });
      // Attach trace to exchange for UI diagnostics
      const requestTrace = streamingStateRef.current?.trace || null;
      return { ...exchange, responses, ...(requestTrace && { trace: requestTrace }) };
    });
  }, [updateLatestExchange]);

  /**
   * Send a message - OCI manages conversation history automatically
   */
  const sendAndStreamMessage = useCallback(async (input, options = {}) => {
    const { isNewConversation = false, inputText = "", previousResponseId } = options;
    const sessionActiveServers = inputRef.current?.getSessionActiveServers?.() || undefined;

    try {
      if (isNewConversation) {
        await genaiService.createConversation("New conversation");
        const newConvId = genaiService.getConversationId();
        if (newConvId) {
          const storedConv = await ConversationStorage.get(newConvId);
          if (storedConv?.urlId) {
            window.history.pushState(null, "", `/c/${storedConv.urlId}`);
            loadedConversationRef.current = storedConv.urlId;
          }
        }
      }

      const result = await genaiService.sendMessage(
        input,
        (chunk) => {
          const responsesCopy = processStreamingChunk(chunk, streamingStateRef.current);
          updateLatestExchange(exchange => ({
            ...exchange,
            responses: responsesCopy,
          }));
        },
        { model: selectedModel || undefined, sessionActiveServers, previousResponseId }
      );

      // Persist the raw accumulated text and trace for export/diagnostics
      const rawText = streamingStateRef.current.accumulatedText || '';
      const requestTrace = streamingStateRef.current.trace || null;
      if (rawText || requestTrace) {
        updateLatestExchange(exchange => ({
          ...exchange,
          ...(rawText && { rawAssistantText: rawText }),
          ...(requestTrace && { trace: requestTrace }),
        }));
      }

      // Generate title for new conversations or conversations that were stopped before getting a title
      if (result.answer && inputText) {
        const convId = genaiService.getConversationId();
        if (convId) {
          const needsTitle = isNewConversation || await ConversationStorage.get(convId).then(c => !c?.title || c.title === "New conversation").catch(() => false);
          if (needsTitle) {
            generateTitle(inputText, result.answer).then(title => {
              if (title) {
                ConversationStorage.update(convId, { title }).then(refreshRecentConversations);
              }
            });
          }
        }
      }

      return result;
    } catch (error) {
      // Capture error for markIncompleteMcpChipsAsFailed
      if (streamingStateRef.current) {
        streamingStateRef.current.streamError = error;
      }
      if (error.name === 'AbortError') {
        // User stopped generation — keep partial content, don't show error
        return { answer: streamingStateRef.current?.accumulatedText || '', stopped: true };
      }
      console.error("Error calling agent:", error);
      if (error.type === 'mcp_auth_expired') {
        updateLatestExchange(exchange => ({
          ...exchange,
          responses: [...(exchange.responses || []), {
            type: "error",
            content: "mcp_auth_expired",
            serverLabel: error.serverLabel || null,
            serverEndpoint: error.serverEndpoint || null,
            serverAuthType: error.serverAuthType || null,
          }],
        }));
      } else {
        updateLatestExchange(exchange => ({
          ...exchange,
          responses: [...(exchange.responses || []), {
            type: "error",
            content: error?.message || String(error),
            opcRequestId: error?.opcRequestId || null,
            model: error?.model || null,
            timestamp: error?.timestamp || null,
          }],
        }));
      }
      throw error;
    }
  }, [genaiService, selectedModel, processStreamingChunk, updateLatestExchange, refreshRecentConversations]);

  useEffect(() => {
    ConversationStorage.initFromSession().then(() => {
      setGenaiService(createGenaiAgentService());
      refreshRecentConversations();
    });
  }, [refreshRecentConversations]);

  useEffect(() => {
    if (!initialConversationId || !genaiService || loadedConversationRef.current === initialConversationId) return;

    const loadFromUrl = async () => {
      setIsLoadingConversation(true);  // Disable chat while loading conversation
      try {
        loadedConversationRef.current = initialConversationId;
        const conversation = await ConversationStorage.getByUrlId(initialConversationId);
        if (conversation) {
          await handleConversationClick(conversation);
        } else {
          loadedConversationRef.current = null;
          window.history.replaceState(null, "", "/");
          setIsLoadingConversation(false);
        }
      } catch (error) {
        console.error("Error loading conversation from URL:", error);
        loadedConversationRef.current = null;
        window.history.replaceState(null, "", "/");
        setIsLoadingConversation(false);
      }
    };
    loadFromUrl();
  }, [initialConversationId, genaiService]);

  useEffect(() => {
    const handlePopState = async () => {
      const path = window.location.pathname;
      const match = path.match(/^\/c\/(.+)$/);

      if (match) {
        const urlId = match[1];
        if (loadedConversationRef.current !== urlId && genaiService) {
          const conversation = await ConversationStorage.getByUrlId(urlId);
          if (conversation) await handleConversationClick(conversation);
        }
      } else if (path === "/" || path === "") {
        if (genaiService?.getConversationId()) {
          genaiService.resetConversation();
          resetChatState();
        }
      }
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [genaiService, resetChatState]);

  useEffect(() => {
    const updateSpacerHeight = () => {
      if (!chatContainerRef.current || !latestMessageRef.current || chatHistory.length === 0) {
        setSpacerHeight(0);
        return;
      }
      const containerHeight = chatContainerRef.current.clientHeight;
      const messageHeight = latestMessageRef.current.offsetHeight;
      setSpacerHeight(Math.max(0, containerHeight - 80 - messageHeight));
    };

    updateSpacerHeight();
    const resizeObserver = new ResizeObserver(updateSpacerHeight);
    if (chatContainerRef.current) resizeObserver.observe(chatContainerRef.current);
    if (latestMessageRef.current) resizeObserver.observe(latestMessageRef.current);

    return () => resizeObserver.disconnect();
  }, [chatHistory]);

  const handleCopy = useCallback(async (text, id) => {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.cssText = "position:fixed;opacity:0";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch { /* ignore */ }
  }, []);

  const getExchangeCopyContent = useCallback((exchange) => {
    return groupMessages(exchange.responses)
      .map(group => {
        if (group.type === "text") return group.content;
        if (group.type === "widget" && group.widgetProps) {
          const { t, s, ...rest } = group.widgetProps;
          const title = t || s || "Widget";
          const data = Object.entries(rest)
            .filter(([k]) => !k.startsWith("_"))
            .map(([k, v]) => `${k}: ${v}`)
            .join(", ");
          return data ? `[${title}: ${data}]` : `[${title}]`;
        }
        if (group.type === "widget_v2" && group.tree) {
          // Serialize v2 tree back to XML for copy
          return `@@widget\n${serializeWidgetV2Tree(group.tree)}\n@@`;
        }
        return "";
      })
      .filter(Boolean)
      .join("\n\n");
  }, []);

  const handleChipChange = useCallback((chip, chipKey) => {
    setActiveChips(prev => {
      if (!chip) {
        const { [chipKey]: _, ...rest } = prev;
        return rest;
      }
      const parts = chipKey.split('-');
      const prefix = `${parts[0]}-${parts[1]}-`;
      const filtered = Object.fromEntries(
        Object.entries(prev).filter(([key]) => !key.startsWith(prefix) || key === chipKey)
      );
      return { ...filtered, [chipKey]: chip };
    });
  }, []);

  const handleNewConversation = useCallback(() => {
    genaiService?.resetConversation();
    resetChatState();
    inputRef.current?.clear();
    window.history.pushState(null, "", "/");
    setTimeout(() => inputRef.current?.focus(), 100);
  }, [genaiService, resetChatState]);

  const handleConversationDelete = useCallback(async (conversation) => {
    if (!conversation?.id) return;

    try {
      const deleted = await ConversationStorage.delete(conversation.id);
      if (!deleted) {
        console.warn('[useChat] delete returned false for:', conversation.id);
      }

      // Refresh from localStorage to ensure UI matches persisted state
      await refreshRecentConversations();

      if (genaiService?.getConversationId() === conversation.id) {
        genaiService.resetConversation();
        resetChatState();
        window.history.pushState(null, "", "/");
      }
    } catch (error) {
      console.error("Error deleting conversation:", error);
      onError?.("Error deleting conversation");
    }
  }, [genaiService, onError, resetChatState, refreshRecentConversations]);

  const handleConversationClick = useCallback(async (conversation) => {
    if (!genaiService) return;

    loadedConversationRef.current = conversation.urlId || conversation.id;
    genaiService.setConversationId(conversation.id);
    resetChatState();
    setIsLoadingConversation(true);

    try {
      const items = await genaiService.getConversationItems(conversation.id);

      if (items?.length > 0) {
        const sortedItems = [...items].reverse();
        console.log('[History] Items:', sortedItems.map(i => `${i.type}(${i.role||'-'}) ann:${(i.content||[]).flatMap?.(c=>c.annotations||[]).length||0}`));

        const exchanges = [];
        let currentExchange = null;

        for (const item of sortedItems) {
          // Approval items don't follow the role-based pattern even if OCI tags them
          // with role='user'. Route them to the dedicated branches below before the
          // generic user-message branch can spawn a spurious new exchange.
          if (item.type === 'mcp_approval_request' && currentExchange) {
            currentExchange.responses.push({
              type: 'mcp_approval_request',
              requestId: item.id,
              serverLabel: item.server_label,
              toolName: item.name,
              arguments: item.arguments,
              decision: null,
            });
            continue;
          }
          if (item.type === 'mcp_approval_response' && currentExchange) {
            const card = currentExchange.responses.find(
              r => r.type === 'mcp_approval_request' && r.requestId === item.approval_request_id
            );
            if (card) card.decision = item.approve ? 'approved' : 'rejected';
            continue;
          }
          if (item.role === 'user') {
            if (currentExchange) exchanges.push(currentExchange);

            // Handle array content (image messages) - extract displayable text
            let displayContent = item.content;
            let imageCount = 0;
            let rawTextContent = '';
            if (Array.isArray(item.content)) {
              const textPart = item.content.find(c => c.type === 'input_text');
              const imageParts = item.content.filter(c => c.type === 'input_image');
              imageCount = imageParts.length;
              rawTextContent = textPart?.text || '';
              displayContent = rawTextContent || (imageCount > 0 ? '' : '[Content]');
            } else {
              rawTextContent = typeof item.content === 'string' ? item.content : '';
            }

            // Parse widget response §>...§ from raw text (after extracting from array if needed)
            const widgetData = parseWidgetResponse(rawTextContent.trim());

            // Parse pasted content tags
            const { userText, attachedTexts } = parsePastedContent(rawTextContent);
            if (attachedTexts.length > 0) {
              displayContent = userText || '[Pasted content]';
            }

            const exchangeExtras = { isLatest: false };

            // Detect image generation messages saved via addItemTo
            const isImageGen = typeof rawTextContent === 'string' && rawTextContent.startsWith('[Image Generation] ');
            if (isImageGen) {
              displayContent = rawTextContent.replace('[Image Generation] ', '');
              exchangeExtras.isImageGenRequest = true;
            }

            if (imageCount > 0) {
              exchangeExtras.hasImageAttachment = true;
              exchangeExtras.imageCount = imageCount;
            }
            if (attachedTexts.length > 0) {
              exchangeExtras.attachedTexts = attachedTexts;
            }
            if (widgetData) {
              exchangeExtras.widgetResponse = widgetData;
              // Format widget response for display instead of showing raw §>...§
              const dataEntries = Object.entries(widgetData.data).filter(([k]) => !k.startsWith('_'));
              displayContent = dataEntries.length > 0
                ? dataEntries.map(([k, v]) => `${k}: ${v}`).join(' · ')
                : widgetData.action || 'Submitted';
            }
            currentExchange = createNewExchange(displayContent, exchangeExtras);
          } else if (item.role === 'assistant' && currentExchange) {
            // Detect image generation response saved via addItemTo
            const assistantText = typeof item.content === 'string' ? item.content
              : Array.isArray(item.content) ? (item.content.find(c => c.type === 'output_text' || c.type === 'text')?.text || '') : '';
            const imageGenMatch = assistantText.match(/^!\[Generated Image\]\(prompt: (.+)\)$/);
            if (imageGenMatch) {
              currentExchange.responses = [{ type: 'generated_image_placeholder', revisedPrompt: imageGenMatch[1] }];
              continue;
            }

            // Extract annotations from content array (OCI url_citation format)
            const contentArr = Array.isArray(item.content) ? item.content : [];
            const urlCitations = contentArr.flatMap(c => c.annotations || []).filter(a => a.type === 'url_citation');

            // Dedup: OCI stores 2 assistant items for web_search responses:
            //   - rich version (longer text, may have annotations)
            //   - plain version (matches what was streamed, no annotations)
            // After .reverse(), order is: rich first, plain second.
            // Strategy: when a second assistant message arrives, replace text
            // with the latest (plain = matches streaming), harvesting any
            // annotations from the first (rich).
            const existingHasText = currentExchange.responses.some(r => r.type === 'text');

            if (existingHasText) {
              // Second assistant message — replace text with this one (plain)
              const parsedMessages = parseContentWithWidgets(item.content);
              currentExchange.responses = currentExchange.responses.filter(r => r.type !== 'text');

              // Merge annotations: from previous (rich) + from current
              const allCitations = [...(currentExchange._harvestedAnnotations || []), ...urlCitations];
              console.log(`[History] Dedup: replacing text, harvested=${(currentExchange._harvestedAnnotations||[]).length} + current=${urlCitations.length} = ${allCitations.length} citations`);
              if (allCitations.length > 0) {
                const lastText = [...parsedMessages].reverse().find(m => m.type === 'text');
                if (lastText) lastText.sources = allCitations;
              }

              currentExchange.responses.push(...parsedMessages);
              delete currentExchange._harvestedAnnotations;
              continue;
            }

            // First assistant message — store it, save annotations for potential dedup
            // Extract raw text for export
            const rawText = Array.isArray(item.content)
              ? (item.content.find(c => c.type === 'output_text' || c.type === 'text')?.text || '')
              : (typeof item.content === 'string' ? item.content : '');
            if (rawText) currentExchange.rawAssistantText = rawText;
            const parsedMessages = parseContentWithWidgets(item.content);
            console.log(`[History] First assistant: ${urlCitations.length} citations, text length=${(parsedMessages.find(m=>m.type==='text')?.content||'').length}`);
            if (urlCitations.length > 0) {
              currentExchange._harvestedAnnotations = urlCitations;
              const lastText = [...parsedMessages].reverse().find(m => m.type === 'text');
              if (lastText) lastText.sources = urlCitations;
            }

            currentExchange.responses.push(...parsedMessages);
          } else if (item.type === 'reasoning' && currentExchange) {
            // Reasoning output from history
            const summaryTexts = (item.summary || []).map(s => s.text).filter(Boolean);
            if (summaryTexts.length > 0) {
              currentExchange.responses.push({
                type: "reasoning",
                text: summaryTexts.join('\n'),
              });
            }
          } else if (item.type === 'code_interpreter_call' && currentExchange) {
            // Code execution from history
            currentExchange.responses.push({
              type: "code_execution",
              code: item.code || item.input || '',
              output: (item.outputs || item.results || []).map(r => r.logs || r.output || r.text || '').join('\n').trim(),
              containerId: item.container_id || null,
            });
          } else if (item.type === 'image_generation_call' && currentExchange) {
            // Image generation: OCI doesn't store the base64 in history, show placeholder
            currentExchange.responses.push({
              type: "generated_image_placeholder",
              revisedPrompt: item.revised_prompt || item.result || '',
            });
          } else if (item.type?.endsWith('_call') && currentExchange) {
            // Generic tool call handling: mcp_call, web_search_call, file_search_call, etc.
            const toolType = item.type.replace(/_call$/, '');
            const toolOutput = item.output || item.error || (item.action?.query) || '';
            const toolStatus = item.status === 'incomplete' ? 'failed' : (item.status || 'completed');
            console.log(`[History] Tool call: ${item.name || toolType}, status=${item.status}, output=${(toolOutput || '').substring(0, 100)}, keys=${Object.keys(item).join(',')}`);
            currentExchange.responses.push({
              type: "mcp_chip",
              server: item.server_label || toolType,
              tool: item.name || toolType,
              arguments: item.arguments || (item.action ? JSON.stringify(item.action) : ''),
              output: toolOutput,
              status: toolStatus,
              label: item.name || formatToolName(toolType),
              error: toolStatus === 'failed' ? (item.error || '') : undefined,
            });
            // Track file_search queries on the exchange so we can re-enrich
            // sources after the loop (OCI returns results=null in stored items).
            if (item.type === 'file_search_call' && Array.isArray(item.queries) && item.queries.length > 0) {
              if (!currentExchange._fileSearchQueries) currentExchange._fileSearchQueries = [];
              currentExchange._fileSearchQueries.push(...item.queries);
            }
          }
        }
        if (currentExchange) exchanges.push(currentExchange);

        // Mark widgets as used based on next exchange's widgetResponse
        for (let i = 0; i < exchanges.length - 1; i++) {
          const nextExchange = exchanges[i + 1];
          if (nextExchange.widgetResponse) {
            const currentEx = exchanges[i];
            const widgetIdx = currentEx.responses.findIndex(r => r.type === "widget");
            if (widgetIdx >= 0) {
              currentEx.responses[widgetIdx].selectedData = {
                ...nextExchange.widgetResponse.data,
                _action: nextExchange.widgetResponse.action
              };
              currentEx.responses[widgetIdx].disabled = true;
            }
          }
        }

        // Re-run file_search enrichment for history (OCI stores file_search_call
        // items with `results: null`, so the source chunks are missing on reload).
        // Use vsIds from current settings — if user changed them since the conversation,
        // results may differ slightly, but it's the best we can do without server-side persistence.
        try {
          const vsIds = typeof window !== 'undefined'
            ? JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]')
            : [];
          if (vsIds.length > 0) {
            await Promise.all(exchanges.map(async (ex) => {
              const queries = ex._fileSearchQueries;
              if (!queries?.length) return;
              const fsCitations = [];
              const seen = new Set();
              await Promise.all(
                queries.flatMap(query =>
                  vsIds.map(async (vsId) => {
                    try {
                      const res = await fetch(`/api/vector-stores?id=${vsId}&action=search`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ query, max_num_results: 5 }),
                      });
                      if (!res.ok) return;
                      const sd = await res.json();
                      for (const r of (sd.data || [])) {
                        if (!r.file_id) continue;
                        const snippet = (r.content || [])
                          .map(c => typeof c === 'string' ? c : c?.text || '')
                          .join('')
                          .slice(0, 3000);
                        const key = `${r.file_id}::${snippet.slice(0, 80)}`;
                        if (seen.has(key)) continue;
                        seen.add(key);
                        fsCitations.push({
                          type: 'file_citation',
                          file_id: r.file_id,
                          filename: r.filename,
                          score: r.score,
                          snippet,
                          vector_store_id: vsId,
                        });
                      }
                    } catch { /* skip on error */ }
                  })
                )
              );
              if (fsCitations.length > 0) {
                fsCitations.sort((a, b) => (b.score || 0) - (a.score || 0));
                ex.responses.push({ type: 'sources', sources: fsCitations });
              }
              delete ex._fileSearchQueries;
            }));
          }
        } catch (e) {
          console.warn('[History] file_search enrichment failed:', e.message);
        }

        // Debug: verify sources are set
        exchanges.forEach((ex, i) => {
          const sourcesCount = groupMessages(ex.responses).filter(g => g.sources?.length > 0).length;
          if (sourcesCount > 0) console.log(`[History] Exchange ${i}: ${sourcesCount} groups with sources`);
        });

        setChatHistory(exchanges);
      }

      if (conversation.urlId && !window.location.pathname.includes(`/c/${conversation.urlId}`)) {
        window.history.pushState(null, "", `/c/${conversation.urlId}`);
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
      onError?.("Error loading conversation");
    } finally {
      setIsLoadingConversation(false);
    }
  }, [genaiService, onError, resetChatState, createNewExchange, parseWidgetResponse, parsePastedContent]);

  const handleSubmit = useCallback(async (inputText, attachedImages = [], attachedTexts = []) => {
    const trimmedInput = inputText?.trim();
    const hasImages = attachedImages && attachedImages.length > 0;
    const hasTexts = attachedTexts && attachedTexts.length > 0;

    if (!trimmedInput && !hasImages && !hasTexts) return;
    if (!genaiService) return;

    setIsLoading(true);
    setActiveChips({});

    // --- Normal Chat Mode ---
    // Build full text content (user input + attached texts with XML tags)
    let fullTextContent = trimmedInput || '';
    if (hasTexts) {
      const textsContent = attachedTexts.map((t, idx) =>
        `<pasted_content index="${idx + 1}"${t.name ? ` name="${t.name}"` : ''}>\n${t.content}\n</pasted_content>`
      ).join('\n\n');
      fullTextContent = fullTextContent
        ? `${fullTextContent}\n\n${textsContent}`
        : textsContent;
    }

    // Build input - string or array with images
    let input;
    if (hasImages) {
      input = [];
      if (fullTextContent) {
        input.push({ type: 'input_text', text: fullTextContent });
      }
      for (const img of attachedImages) {
        input.push({
          type: 'input_image',
          image_url: img.base64,
          detail: 'high'
        });
      }
    } else {
      input = fullTextContent;
    }

    const isNewConversation = !genaiService.getConversationId();

    // Display message (just the typed text, attachments shown separately)
    const displayMessage = trimmedInput || (hasTexts ? '[Pasted content]' : '');

    setChatHistory(prev => [
      ...prev.map(ex => ({ ...ex, isLatest: false })),
      createNewExchange(displayMessage, {
        attachedImages: hasImages ? attachedImages.map(img => ({ preview: img.preview, name: img.name })) : undefined,
        attachedTexts: hasTexts ? attachedTexts.map(t => ({ id: t.id, name: t.name, ext: t.ext, content: t.content, preview: t.preview })) : undefined
      }),
    ]);

    scrollToLatestMessage();
    initStreamingState();

    try {
      await sendAndStreamMessage(input, {
        isNewConversation,
        inputText: trimmedInput || (hasTexts ? 'Pasted content analysis' : 'Image analysis')
      });
    } finally {
      setIsLoading(false);
      markIncompleteMcpChipsAsFailed();
      refreshRecentConversations();
    }
  }, [genaiService, createNewExchange, scrollToLatestMessage, initStreamingState, sendAndStreamMessage, markIncompleteMcpChipsAsFailed, refreshRecentConversations, updateLatestExchange]);

  const handleWidgetSubmit = useCallback(async (data, widgetId) => {
    if (!genaiService) return;

    const parts = Object.entries(data)
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `${k}:${v}`);

    const widgetResponse = `§>${parts.join("|")}§`;
    const { _action, ...displayData } = data;

    // Format display message instead of showing raw §>...§
    const dataEntries = Object.entries(displayData).filter(([k]) => !k.startsWith('_'));
    const displayMessage = dataEntries.length > 0
      ? dataEntries.map(([k, v]) => `${k}: ${v}`).join(' · ')
      : _action || 'Submitted';

    setChatHistory(prev => [
      ...prev.map(ex => ({ ...ex, isLatest: false })),
      createNewExchange(displayMessage, { widgetResponse: { action: _action, data: displayData, widgetId } }),
    ]);

    scrollToLatestMessage();
    setTimeout(() => inputRef.current?.focus(), 150);

    setIsLoading(true);
    initStreamingState();

    try {
      await sendAndStreamMessage(widgetResponse);
    } finally {
      setIsLoading(false);
      markIncompleteMcpChipsAsFailed();
      refreshRecentConversations();
    }
  }, [genaiService, createNewExchange, scrollToLatestMessage, initStreamingState, sendAndStreamMessage, markIncompleteMcpChipsAsFailed, refreshRecentConversations]);

  const stopGeneration = useCallback(() => {
    if (genaiService) {
      genaiService.abortCurrentRequest();
      setIsLoading(false);
    }
  }, [genaiService]);

  const handleOptionSelect = useCallback((optionLabel) => {
    handleSubmit(optionLabel);
  }, [handleSubmit]);

  /**
   * User clicked Approve / Reject on an MCP approval card.
   * Submits an mcp_approval_response item under the same `conversation` — OCI
   * locates the pending approval_request_id from the conversation context, no
   * previous_response_id needed (and OCI rejects sending both together).
   * The new stream appends into the SAME exchange — no new user message.
   */
  const handleApprovalSubmit = useCallback(async (requestId, approve) => {
    if (!genaiService) return;

    let existingResponses = null;
    setChatHistory(prev => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      const updated = (last.responses || []).map(r => {
        if (r.type === 'mcp_approval_request' && r.requestId === requestId) {
          return { ...r, decision: approve ? 'approved' : 'rejected' };
        }
        return r;
      });
      existingResponses = updated;
      return [...prev.slice(0, -1), { ...last, responses: updated, isLatest: true }];
    });

    setIsLoading(true);
    initStreamingState();
    // Preserve already-rendered content so the new stream appends below the card.
    streamingStateRef.current.responses = [...(existingResponses || [])];

    try {
      await sendAndStreamMessage(
        [{ type: 'mcp_approval_response', approval_request_id: requestId, approve }]
      );
    } finally {
      setIsLoading(false);
      markIncompleteMcpChipsAsFailed();
    }
  }, [genaiService, initStreamingState, sendAndStreamMessage, markIncompleteMcpChipsAsFailed]);

  const handleRetry = useCallback(() => {
    setChatHistory(prev => {
      if (prev.length === 0) return prev;
      const last = prev[prev.length - 1];
      const userMessage = last.userMessage || '';
      const attachedTexts = last.attachedTexts || [];
      setTimeout(() => handleSubmit(userMessage, [], attachedTexts), 0);
      return prev.slice(0, -1);
    });
  }, [handleSubmit]);

  return {
    isLoading,
    isLoadingConversation,
    chatHistory,
    activeChips,
    copiedId,
    spacerHeight,
    recentConversations,
    loadingConversations,
    hasMoreConversations: recentConversationsPage.hasMore,
    isLoadingMoreConversations: recentConversationsPage.isLoadingMore,
    loadMoreConversations,
    genaiService,
    latestMessageRef,
    chatContainerRef,
    inputRef,
    handleSubmit,
    handleRetry,
    handleApprovalSubmit,
    stopGeneration,
    handleWidgetSubmit,
    handleOptionSelect,
    handleChipChange,
    handleCopy,
    handleNewConversation,
    handleConversationClick,
    handleConversationDelete,
    getExchangeCopyContent,
    refreshRecentConversations,
  };
}
