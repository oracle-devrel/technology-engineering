"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import createGenaiAgentService from "../services/genaiAgentService";
import createOracleSpeechService from "../services/oracleSpeechService";
import createSpeechService from "../services/speechService";
import { createUserMessage } from "../utils/messageUtils";
import { useProject } from "./ProjectsContext";

const ChatContext = createContext(null);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

const createSpeechServiceFactory = (speechProvider) => {
  switch (speechProvider) {
    case "oracle":
      return createOracleSpeechService();
    case "browser":
    default:
      return createSpeechService();
  }
};

export const ChatProvider = ({ children }) => {
  const { getCurrentProject } = useProject();
  const [messages, setMessages] = useState([]);
  const [connected, setConnected] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [userId, setUserId] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [genaiService, setGenaiService] = useState(null);
  const [speechService, setSpeechService] = useState(null);
  const [currentSpeechProvider, setCurrentSpeechProvider] = useState("browser");
  const [playingMessageId, setPlayingMessageId] = useState(null);

  useEffect(() => {
    const storedUserId =
      typeof window !== "undefined"
        ? window.localStorage.getItem("chatUserId")
        : null;

    const newUserId =
      storedUserId || `user${Math.random().toString(36).substring(2, 10)}`;

    setUserId(newUserId);

    if (typeof window !== "undefined") {
      window.localStorage.setItem("chatUserId", newUserId);
    }
  }, []);

  useEffect(() => {
    const currentProject = getCurrentProject();
    const provider = currentProject.speechProvider || "browser";

    if (currentSpeechProvider !== provider) {
      setSpeechService(createSpeechServiceFactory(provider));
      setCurrentSpeechProvider(provider);
      setMessages([]);
      setIsWaitingForResponse(false);
    }
  }, [getCurrentProject, currentSpeechProvider]);

  useEffect(() => {
    if (!userId) return;
    setGenaiService(createGenaiAgentService());
  }, [userId]);

  const sendMessage = useCallback(
    async (text) => {
      if (!text.trim() || !genaiService) return false;

      const message = createUserMessage(text, userId);
      setMessages((prev) => [...prev, message]);
      setIsWaitingForResponse(true);
      setError("");

      try {
        const response = await genaiService.sendMessage(text);

        const botMessage = {
          userId: "bot",
          messagePayload: processResponse(response),
          date: new Date().toISOString(),
          from: { type: "bot" },
        };

        setMessages((prev) => [...prev, botMessage]);
        setIsWaitingForResponse(false);
        return true;
      } catch (error) {
        setError(`Error: ${error.message}`);
        setIsWaitingForResponse(false);
        return false;
      }
    },
    [genaiService, userId]
  );

  const processResponse = (apiResponse) => {
    const { answer, diagram_base64, citations } = apiResponse;

    if (diagram_base64) {
      return {
        type: "diagram",
        text: answer,
        diagram_base64: diagram_base64,
      };
    }

    try {
      const parsed = JSON.parse(answer);
      if (parsed.executionResult) {
        return {
          type: "sql_result",
          generatedQuery: parsed.generatedQuery || "",
          executionResult: parsed.executionResult || [],
          text: `Query executed: ${parsed.generatedQuery || "SQL query"}`,
        };
      }
    } catch {}

    return {
      type: "text",
      text: answer,
      citations: citations || [],
    };
  };

  const sendAttachment = useCallback(
    async (file) => {
      if (!file || !genaiService) return false;
  
      setIsWaitingForResponse(true);
      setError("");
  
      // Step 1: Show file preview in UI
      const attachmentMessage = {
        userId: userId,
        messagePayload: {
          type: "attachment",
          attachment: {
            type: file.type,
            title: file.name,
            url: URL.createObjectURL(file),
          },
        },
        date: new Date().toISOString(),
        from: { type: "user" },
      };
      setMessages((prev) => [...prev, attachmentMessage]);
  
      // Step 2: Upload file to FastAPI backend
      try {
        const formData = new FormData();
        formData.append("message", "Extract text from uploaded file");
        formData.append("file", file);
  
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_GENAI_API_URL}/chat`,
          {
            method: "POST",
            body: formData,
          }
        );
  
        const data = await response.json();
  
        const botMessage = {
          userId: "bot",
          messagePayload: {
            type: "text",
            text: data.text || "No response from server.",
          },
          date: new Date().toISOString(),
          from: { type: "bot" },
        };
  
        setMessages((prev) => [...prev, botMessage]);
        setIsWaitingForResponse(false);
        return true;
      } catch (error) {
        console.error("Attachment upload error:", error);
        setError("Error uploading file.");
        setIsWaitingForResponse(false);
        return false;
      }
    },
    [genaiService, userId]
  );
  

  const clearChat = useCallback(() => {
    setMessages([]);
    setIsWaitingForResponse(false);
  }, []);

  const toggleSpeechRecognition = useCallback(() => {
    if (!speechService || !speechService.isSupported()) {
      setError("Speech recognition is not supported");
      return;
    }

    if (isListening) {
      if (speechService.stopListening) {
        speechService.stopListening();
      } else if (speechService.stopRecording) {
        speechService.stopRecording();
      }
      setIsListening(false);
      return;
    }

    let started = false;

    if (currentSpeechProvider === "oracle") {
      started = speechService.startRecording(
        (result) => {
          if (result.isFinal && result.transcript) {
            sendMessage(result.transcript);
          }
        },
        (error) => {
          setIsListening(false);
          setError(`Speech recognition error: ${error}`);
        }
      );
    } else {
      started = speechService.startListening(
        (result) => {
          if (result.stopped) {
            setIsListening(false);
            return;
          }

          if (result.isFinal || result.stopped) {
            setIsListening(false);
            if (result.transcript) {
              sendMessage(result.transcript);
            }
          }
        },
        (error) => {
          setIsListening(false);
          setError(`Speech recognition error: ${error}`);
        }
      );
    }

    setIsListening(started);
  }, [isListening, sendMessage, speechService, currentSpeechProvider]);

  useEffect(() => {
    if (!speechService) {
      setSpeechService(createSpeechServiceFactory("browser"));
    }
  }, [speechService]);

  const value = {
    messages,
    connected,
    loading,
    error,
    isListening,
    isWaitingForResponse,
    userId,
    sendMessage,
    sendAttachment,
    clearChat,
    toggleSpeechRecognition,
    setError,
    currentSpeechProvider,
    speakMessage: () => false,
    cancelAudio: () => setPlayingMessageId(null),
    playingMessageId,
    setPlayingMessageId,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
