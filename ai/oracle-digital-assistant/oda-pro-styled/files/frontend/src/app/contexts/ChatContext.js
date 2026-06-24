"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import createOdaService from "../services/odaService";
import createOracleSpeechService from "../services/oracleSpeechService";
import createSpeechService from "../services/speechService";
import {
  classifyMessage,
  MESSAGE_TYPES,
  transformBotMessage,
} from "../utils/messageClassifier";
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
  const [connected, setConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [userId, setUserId] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [odaService, setOdaService] = useState(null);
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
    switch (connectionStatus) {
      case 0:
        setConnected(false);
        setLoading(true);
        break;
      case 1:
        setConnected(true);
        setLoading(false);
        setError("");
        break;
      case 2:
        setConnected(false);
        break;
      case 3:
        setConnected(false);
        setLoading(false);
        break;
      default:
        break;
    }
  }, [connectionStatus]);

  useEffect(() => {
    const currentProject = getCurrentProject();
    const provider = currentProject.speechProvider || "browser";

    if (currentSpeechProvider !== provider) {
      const newService = createSpeechServiceFactory(provider);

      if (provider === "oracle" && newService && newService.initialize) {
        newService.initialize();
      }

      setSpeechService(newService);
      setCurrentSpeechProvider(provider);

      setMessages([]);
      setIsWaitingForResponse(false);
    }
  }, [getCurrentProject, currentSpeechProvider]);

  useEffect(() => {
    if (!userId) return;

    const handleMessage = (data) => {
      console.log("data -> ", data);

      if (!data || data.source !== "BOT" || !data.messagePayload) {
        return;
      }

      const messageType = classifyMessage(data);

      if (messageType === MESSAGE_TYPES.IGNORE) {
        console.debug("⚠️ [Chat] Message ignored:", data.messagePayload.text);
        return;
      }

      const processedMessage = transformBotMessage(data, messageType, userId);

      if (processedMessage) {
        if (data.endOfTurn) {
          setIsWaitingForResponse(false);
        }

        setMessages((prev) => [...prev, processedMessage]);
      }
    };

    const service = createOdaService();

    service.addMessageListener(handleMessage);
    service.addStatusChangeListener(setConnectionStatus);

    const sdk = service.initialize({ userId });
    if (sdk) {
      setOdaService(service);
      service.connect();
    }

    return () => {
      if (service) {
        service.disconnect();
      }
    };
  }, [userId]);

  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    if (
      lastMessage.from?.type === "bot" &&
      currentSpeechProvider === "oracle" &&
      isListening &&
      odaService?.speakMessage
    ) {
      if (odaService.cancelAudio) {
        odaService.cancelAudio();
      }
      odaService.speakMessage(lastMessage);
    }
  }, [messages, currentSpeechProvider, isListening, odaService]);

  const sendMessage = useCallback(
    (text) => {
      if (!text.trim() || !connected || !odaService) return false;

      const message = createUserMessage(text, userId);

      setMessages((prev) => [...prev, message]);
      setIsWaitingForResponse(true);

      return odaService.sendMessage(message);
    },
    [connected, userId, odaService]
  );

  const sendAttachment = useCallback(
    async (file) => {
      if (!file || !connected || !odaService) return false;

      try {
        const attachmentMessage = {
          userId: userId,
          messagePayload: {
            type: "attachment",
            attachment: {
              type: file.type,
              title: file.name,
              url: URL.createObjectURL(file), // Para preview local
            },
          },
          date: new Date().toISOString(),
          from: null, // null = usuario
        };

        setMessages((prev) => [...prev, attachmentMessage]);

        await odaService.sendAttachment(file);
        return true;
      } catch (error) {
        setError(`Failed to send attachment: ${error.message}`);
        return false;
      }
    },
    [connected, userId, odaService]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setIsWaitingForResponse(false);

    const newUserId = `user${Math.random().toString(36).substring(2, 10)}`;
    setUserId(newUserId);

    if (typeof window !== "undefined") {
      window.localStorage.setItem("chatUserId", newUserId);
    }
  }, []);

  const toggleSpeechRecognition = useCallback(() => {
    let currentService = speechService;

    if (
      !currentService ||
      !currentService.isSupported ||
      (currentSpeechProvider === "oracle" && !currentService.startRecording)
    ) {
      currentService = createSpeechServiceFactory(currentSpeechProvider);
      setSpeechService(currentService);
    }

    if (!currentService || !currentService.isSupported()) {
      setError("Speech recognition is not supported");
      return;
    }

    if (isListening) {
      if (currentService.stopListening) {
        currentService.stopListening();
      } else if (currentService.stopRecording) {
        currentService.stopRecording();
      }
      setIsListening(false);
      return;
    }

    let started = false;

    if (currentSpeechProvider === "oracle") {
      started = currentService.startRecording(
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
      started = currentService.startListening(
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
    speakMessage: odaService?.speakMessage || (() => false),
    cancelAudio: () => {
      if (odaService?.cancelAudio) {
        odaService.cancelAudio();
      }
      setPlayingMessageId(null);
    },
    playingMessageId,
    setPlayingMessageId,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
};
