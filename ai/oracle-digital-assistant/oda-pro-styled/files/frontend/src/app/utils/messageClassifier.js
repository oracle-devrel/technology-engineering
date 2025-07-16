// src/app/utils/messageClassifier.js

export const MESSAGE_TYPES = {
  TOOL_CALL: "tool_call",
  CITATION: "citation",
  RESPONSE: "response",
  IGNORE: "ignore",
};

export const classifyMessage = (data) => {
  if (!data?.messagePayload?.text) return MESSAGE_TYPES.IGNORE;

  const text = data.messagePayload.text.trim();

  // Tool calls
  if (text.startsWith('{"tool":')) {
    return MESSAGE_TYPES.TOOL_CALL;
  }

  // Citations/links
  if (text.includes("<a href=") || text.toLowerCase().includes("citation")) {
    return MESSAGE_TYPES.CITATION;
  }

  // Respuestas útiles
  if (data.endOfTurn || (text.length > 50 && !text.includes("Used tools:"))) {
    return MESSAGE_TYPES.RESPONSE;
  }

  return MESSAGE_TYPES.IGNORE;
};

export const transformBotMessage = (data, messageType, userId) => {
  const baseMessage = {
    ...data,
    userId,
    from: { type: "bot" },
  };

  switch (messageType) {
    case MESSAGE_TYPES.TOOL_CALL:
      try {
        const toolData = JSON.parse(data.messagePayload.text);
        return {
          ...baseMessage,
          messagePayload: {
            type: "tool_chip",
            toolName: toolData.tool,
          },
        };
      } catch (e) {
        return null;
      }

    case MESSAGE_TYPES.CITATION:
      return {
        ...baseMessage,
        messagePayload: {
          type: "citation",
          text: data.messagePayload.text,
        },
      };

    case MESSAGE_TYPES.RESPONSE:
      return {
        ...baseMessage,
        messagePayload: {
          type: "text",
          text: data.messagePayload.text,
        },
      };

    default:
      return null;
  }
};
