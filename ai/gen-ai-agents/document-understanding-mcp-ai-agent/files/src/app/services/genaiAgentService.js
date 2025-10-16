"use client";

const createGenaiAgentService = () => {
  const API_BASE_URL =
    process.env.NEXT_PUBLIC_GENAI_API_URL || "http://localhost:8000";
  let sessionId = null;

  const sendMessage = async (text) => {
    const payload = {
      question: text,
      execute_functions: true,
    };

    if (sessionId) {
      payload.session_id = sessionId;
    }

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const data = await response.json();

    if (data.session_id) {
      sessionId = data.session_id;
    }

    return data; // { answer: "...", session_id: "...", diagram_base64: "..." }
  };

  return {
    sendMessage,
  };
};

export default createGenaiAgentService;
