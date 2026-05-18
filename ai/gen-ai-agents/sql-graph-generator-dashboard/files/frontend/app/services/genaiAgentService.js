"use client";

const createGenaiAgentService = () => {
  const API_BASE_URL =
    process.env.NEXT_PUBLIC_GENAI_API_URL || "http://localhost:8000";
  let sessionId = null;

  const sendMessage = async (text) => {
    const payload = {
      question: text,
      context: "",
    };

    const response = await fetch(`${API_BASE_URL}/query`, {
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

    // Transform backend response to match frontend expectations
    return {
      answer: data.agent_response || data.text_response || "No response",
      response_type: data.response_type,
      query: data.query,
      dashboard: data.dashboard,
      data: data.data,
      insights: data.insights,
      diagram_base64: data.chart_base64, // Map chart_base64 to diagram_base64 for frontend display
      chart_config: data.chart_config,
      method: data.method,
    };
  };

  return {
    sendMessage,
  };
};

export default createGenaiAgentService;
