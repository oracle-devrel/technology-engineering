import { parseWidgetV2Complete } from "./widgetV2Parser";

export const createUserMessage = (text, userId) => {
  return {
    id: Date.now().toString(),
    userId,
    messagePayload: {
      type: "text",
      text: text.trim(),
    },
    date: new Date().toISOString(),
    from: null,
  };
};

export const createSuggestionRequest = (query, userId) => {
  return {
    userId,
    messagePayload: {
      type: "suggest",
      query: query,
      threshold: 5,
    },
  };
};

export const isFromBot = (message) => {
  return message.from && message.from.type === "bot";
};

export const isFromUser = (message) => {
  return message.from === null;
};

export const getMessageType = (message) => {
  return message.messagePayload?.type || "unknown";
};

export const getMessageText = (message) => {
  const payload = message.messagePayload;
  if (!payload) return "";

  switch (payload.type) {
    case "text":
      return payload.text;
    case "card":
      if (payload.cards && payload.cards.length > 0) {
        const card = payload.cards[0];
        return card.title || card.description || "Card message";
      }
      return "Card message";
    case "attachment":
      return `Attachment: ${payload.attachment.type}`;
    default:
      return `Message of type: ${payload.type}`;
  }
};

export const formatMessageTime = (dateString) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch (e) {
    return "";
  }
};

export const extractCodeBlocks = (text) => {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)\n```/g;
  const matches = [];
  let match;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    matches.push({
      language: match[1] || "",
      code: match[2],
    });
  }

  return matches;
};

export const convertMarkdownLinks = (text) => {
  const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  return text.replace(
    linkRegex,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
};

export const processMessageContent = (text) => {
  if (!text) return "";

  const codeBlocks = extractCodeBlocks(text);
  let processedText = text;

  codeBlocks.forEach((block, index) => {
    const placeholder = `__CODE_BLOCK_${index}__`;
    processedText = processedText.replace(
      /```(\w+)?\n([\s\S]*?)\n```/,
      placeholder
    );
  });

  processedText = convertMarkdownLinks(processedText);

  codeBlocks.forEach((block, index) => {
    const placeholder = `__CODE_BLOCK_${index}__`;
    const formattedCode = `<pre><code class="language-${block.language}">${block.code}</code></pre>`;
    processedText = processedText.replace(placeholder, formattedCode);
  });

  return processedText;
};

export const formatConversationTime = (dateString) => {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (diffInHours < 48) {
      return "Yesterday";
    } else {
      return date.toLocaleDateString([], { month: "short", day: "numeric" });
    }
  } catch (e) {
    return "";
  }
};

export const truncateText = (text, maxLength = 60) => {
  if (!text) return "";
  if (text.length <= maxLength) return text;

  return text.substring(0, maxLength).trim() + "...";
};

export const sanitizeHtml = (html) => {
  if (!html) return "";

  return html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, "")
    .replace(/on\w+="[^"]*"/g, "")
    .replace(/javascript:/g, "");
};

export const hasImage = (message) => {
  const payload = message.messagePayload;
  if (!payload) return false;

  if (
    payload.type === "attachment" &&
    payload.attachment &&
    payload.attachment.type.startsWith("image/")
  ) {
    return true;
  }

  if (payload.type === "card" && payload.cards) {
    return payload.cards.some((card) => card.imageUrl);
  }

  return false;
};

export const messageToShareableFormat = (message) => {
  if (!message || !message.messagePayload) return "";

  const isBot = isFromBot(message);
  const sender = isBot ? "ChatBPI" : "You";
  const content = getMessageText(message);
  const time = formatMessageTime(message.date);

  return `${sender} (${time}): ${content}`;
};

export const adaptSdkMessage = (sdkMessage, userId) => {
  if (!sdkMessage || !sdkMessage.messagePayload) {
    console.warn("Invalid message format received from SDK");
    return {
      userId: userId,
      messagePayload: {
        type: "text",
        text: "Sorry, I received an invalid message.",
      },
      date: new Date().toISOString(),
      from: { type: "bot" },
    };
  }

  return {
    userId: userId,
    messagePayload: sdkMessage.messagePayload,
    date: new Date().toISOString(),
    from: { type: "bot" },
  };
};

/**
 * Parses raw text content and extracts widgets (§§...§§) into separate message objects
 */
export const parseContentWithWidgets = (content) => {
  if (!content) return [];

  // Handle non-string content (e.g., array format from OCI messages)
  if (typeof content !== 'string') {
    if (Array.isArray(content)) {
      // Look for text content: input_text (user) or output_text (assistant)
      const textPart = content.find(item =>
        item.type === 'input_text' || item.type === 'output_text' || item.type === 'text'
      );
      if (textPart?.text) {
        // Recursively parse for widgets in the extracted text
        return parseContentWithWidgets(textPart.text);
      }
      return [{ type: "text", content: "[Non-text content]", isStreaming: false }];
    }
    return [{ type: "text", content: String(content), isStreaming: false }];
  }

  const messages = [];

  // Combined regex: match both §§...§§ (v1) and @@widget[spaces]\n...@@ (v2)
  const combinedRegex = /§§([^§]+)§§|@@widget[ \t]*\n([\s\S]*?)@@/g;
  let lastIndex = 0;
  let match;

  while ((match = combinedRegex.exec(content)) !== null) {
    // Add text before widget
    const textBefore = content.slice(lastIndex, match.index).trim();
    if (textBefore) {
      messages.push({ type: "text", content: textBefore, isStreaming: false });
    }

    if (match[1] !== undefined) {
      // V1 widget: §§...§§
      const widgetContent = match[1];
      const widgetProps = {};
      const pairs = widgetContent.split("|");
      for (const pair of pairs) {
        const colonIndex = pair.indexOf(":");
        if (colonIndex > 0) {
          const key = pair.slice(0, colonIndex).trim();
          const value = pair.slice(colonIndex + 1).trim();
          widgetProps[key] = value;
        }
      }

      messages.push({
        type: "widget",
        widgetProps,
        streamingKey: null,
        streamingValue: "",
        isComplete: true
      });
    } else if (match[2] !== undefined) {
      // V2 widget: @@widget\n...@@
      const tree = parseWidgetV2Complete(match[2]);
      messages.push({
        type: "widget_v2",
        tree,
        isComplete: true,
      });
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text after last widget
  const textAfter = content.slice(lastIndex).trim();
  if (textAfter) {
    messages.push({ type: "text", content: textAfter, isStreaming: false });
  }

  // If no widgets found, return original content as text
  if (messages.length === 0 && content.trim()) {
    messages.push({ type: "text", content: content, isStreaming: false });
  }

  return messages;
};

/**
 * Groups messages into chip rows, text blocks, widgets, and interactive elements
 */
export const groupMessages = (messages) => {
  const groups = [];
  let currentChipGroup = [];
  let currentMcpChipGroup = [];

  const flushChips = () => {
    if (currentChipGroup.length > 0) {
      groups.push({ type: "chipRow", chips: currentChipGroup });
      currentChipGroup = [];
    }
  };

  const flushMcpChips = () => {
    if (currentMcpChipGroup.length > 0) {
      groups.push({ type: "mcp_chip_row", chips: currentMcpChipGroup });
      currentMcpChipGroup = [];
    }
  };

  messages.forEach((message, index) => {
    if (message.type === "chip") {
      flushMcpChips();
      currentChipGroup.push({ ...message.chipData, messageIndex: index });
      return;
    }

    if (message.type === "mcp_chip") {
      flushChips();
      currentMcpChipGroup.push({
        server: message.server,
        tool: message.tool,
        arguments: message.arguments,
        status: message.status,
        label: message.label,
        output: message.output,
        error: message.error,
        messageIndex: index,
      });
      return;
    }

    flushChips();
    flushMcpChips();

    switch (message.type) {
      case "text":
        groups.push({ type: "text", content: message.content, sources: message.sources, messageIndex: index });
        break;
      case "sources":
        groups.push({ type: "sources", sources: message.sources, messageIndex: index });
        break;
      case "interactive":
        groups.push({ type: "interactive", interactiveData: message.interactiveData, messageIndex: index });
        break;
      case "widget":
        groups.push({
          type: "widget",
          widgetProps: message.widgetProps,
          streamingKey: message.streamingKey,
          streamingValue: message.streamingValue,
          isComplete: message.isComplete,
          selectedData: message.selectedData,
          disabled: message.disabled,
          messageIndex: index,
        });
        break;
      case "widget_v2":
        groups.push({
          type: "widget_v2",
          tree: message.tree,
          isComplete: message.isComplete,
          messageIndex: index,
        });
        break;
      case "error":
        groups.push({
          type: "error",
          content: message.content,
          serverLabel: message.serverLabel,
          serverEndpoint: message.serverEndpoint,
          serverAuthType: message.serverAuthType,
          opcRequestId: message.opcRequestId,
          model: message.model,
          timestamp: message.timestamp,
          messageIndex: index,
        });
        break;
      case "thinking":
        groups.push({ type: "thinking", messageIndex: index });
        break;
      case "mcp_connecting":
        groups.push({ type: "mcp_connecting", messageIndex: index });
        break;
      case "progress_tracker":
        groups.push({ type: "progress_tracker", progressData: message.progressData, messageIndex: index });
        break;
      case "data_table":
        groups.push({ type: "data_table", tableData: message.tableData, messageIndex: index });
        break;
      case "process_diagram":
        groups.push({ type: "process_diagram", processData: message.processData, messageIndex: index });
        break;
      case "supplier_card":
        groups.push({ type: "supplier_card", supplierData: message.supplierData, messageIndex: index });
        break;
      case "radar_chart":
        groups.push({ type: "radar_chart", radarData: message.radarData, messageIndex: index });
        break;
      case "scatter_chart":
        groups.push({ type: "scatter_chart", scatterData: message.scatterData, messageIndex: index });
        break;
      case "cost_benefit_chart":
        groups.push({ type: "cost_benefit_chart", costBenefitData: message.costBenefitData, messageIndex: index });
        break;
      case "generated_image":
        groups.push({ type: "generated_image", content: message.content, messageIndex: index });
        break;
      case "generated_image_placeholder":
        groups.push({ type: "generated_image_placeholder", revisedPrompt: message.revisedPrompt, messageIndex: index });
        break;
      case "reasoning":
        groups.push({ type: "reasoning", text: message.text, done: message.done, messageIndex: index });
        break;
      case "code_execution":
        groups.push({ type: "code_execution", id: message.id, code: message.code, output: message.output, containerId: message.containerId, status: message.status, messageIndex: index });
        break;
    }
  });

  flushChips();
  flushMcpChips();
  return groups;
};
