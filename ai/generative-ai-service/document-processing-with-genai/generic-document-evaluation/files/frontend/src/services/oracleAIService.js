const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:3001';

export async function queryOracleAI(inputText) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/oracle-ai`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ input: inputText }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to get response");
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error in oracleAIService:", error);
    throw error;
  }
}

// Mock service for testing
export async function queryOracleAIMock(inputText) {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  return {
    success: true,
    data: {
      response: `Mock response for: ${inputText}`,
      timestamp: new Date().toISOString(),
      model: "oracle-ai-mock"
    }
  };
}
