import { create } from 'zustand';
import type { Message, Conversation, ModelId, GenAIConfig } from '@/types';

interface ChatState {
  // Conversations
  conversations: Conversation[];
  currentConversationId: string | null;

  // Current conversation messages
  messages: Message[];

  // Input state
  inputMessage: string;
  isTyping: boolean;
  isProcessing: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;

  // Configuration
  config: GenAIConfig;

  // Debug mode
  debugMode: boolean;
  lastCuOptRequest: object | null;
  lastCuOptResponse: object | null;
  lastGenAIPrompt: string | null;

  // Actions - Conversations
  createConversation: () => string;
  setCurrentConversation: (id: string) => void;
  deleteConversation: (id: string) => void;

  // Actions - Messages
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  addStreamingMessage: () => string;
  appendToStreamingMessage: (chunk: string) => void;
  finalizeStreamingMessage: (metadata?: object) => void;
  updateLastMessage: (content: string) => void;
  clearMessages: () => void;

  // Actions - Input
  setInputMessage: (message: string) => void;
  setIsTyping: (typing: boolean) => void;
  setIsProcessing: (processing: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;

  // Actions - Config
  setConfig: (config: Partial<GenAIConfig>) => void;
  setModel: (model: ModelId) => void;
  setTemperature: (temp: number) => void;

  // Actions - Debug
  toggleDebugMode: () => void;
  setDebugData: (data: {
    cuoptRequest?: object;
    cuoptResponse?: object;
    genaiPrompt?: string;
  }) => void;

  // Reset
  reset: () => void;
}

const defaultConfig: GenAIConfig = {
  endpoint: import.meta.env.VITE_OCI_GENAI_ENDPOINT || '',
  compartmentId: import.meta.env.VITE_OCI_COMPARTMENT_ID || '',
  model: 'openai.gpt-4o-mini',
  temperature: 0.7,
  maxTokens: 2048,
  topP: 0.9,
};

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  conversations: [],
  currentConversationId: null,
  messages: [],
  inputMessage: '',
  isTyping: false,
  isProcessing: false,
  isStreaming: false,
  streamingMessageId: null,
  config: defaultConfig,
  debugMode: false,
  lastCuOptRequest: null,
  lastCuOptResponse: null,
  lastGenAIPrompt: null,

  // Conversation actions
  createConversation: () => {
    const id = `conv-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const conversation: Conversation = {
      id,
      messages: [],
      model: get().config.model,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    set((state) => ({
      conversations: [...state.conversations, conversation],
      currentConversationId: id,
      messages: [],
    }));
    return id;
  },

  setCurrentConversation: (id) => {
    const conversation = get().conversations.find((c) => c.id === id);
    set({
      currentConversationId: id,
      messages: conversation?.messages || [],
    });
  },

  deleteConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      currentConversationId:
        state.currentConversationId === id ? null : state.currentConversationId,
      messages: state.currentConversationId === id ? [] : state.messages,
    })),

  // Message actions
  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
    };
    set((state) => {
      const updatedMessages = [...state.messages, newMessage];
      // Update conversation
      const conversations = state.conversations.map((c) =>
        c.id === state.currentConversationId
          ? { ...c, messages: updatedMessages, updatedAt: new Date() }
          : c
      );
      return { messages: updatedMessages, conversations };
    });
  },

  addStreamingMessage: () => {
    const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newMessage: Message = {
      id,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };
    set((state) => {
      const updatedMessages = [...state.messages, newMessage];
      const conversations = state.conversations.map((c) =>
        c.id === state.currentConversationId
          ? { ...c, messages: updatedMessages, updatedAt: new Date() }
          : c
      );
      return {
        messages: updatedMessages,
        conversations,
        streamingMessageId: id,
        isStreaming: true,
      };
    });
    return id;
  },

  appendToStreamingMessage: (chunk) => {
    set((state) => {
      const streamingId = state.streamingMessageId;
      if (!streamingId) return state;

      const messages = state.messages.map((m) =>
        m.id === streamingId
          ? { ...m, content: m.content + chunk }
          : m
      );
      const conversations = state.conversations.map((c) =>
        c.id === state.currentConversationId
          ? { ...c, messages, updatedAt: new Date() }
          : c
      );
      return { messages, conversations };
    });
  },

  finalizeStreamingMessage: (metadata) => {
    set((state) => {
      const streamingId = state.streamingMessageId;
      if (!streamingId) return state;

      const messages = state.messages.map((m) =>
        m.id === streamingId
          ? { ...m, metadata: metadata as any }
          : m
      );
      const conversations = state.conversations.map((c) =>
        c.id === state.currentConversationId
          ? { ...c, messages, updatedAt: new Date() }
          : c
      );
      return {
        messages,
        conversations,
        streamingMessageId: null,
        isStreaming: false,
      };
    });
  },

  updateLastMessage: (content) =>
    set((state) => {
      const messages = [...state.messages];
      if (messages.length > 0) {
        messages[messages.length - 1] = {
          ...messages[messages.length - 1],
          content,
        };
      }
      return { messages };
    }),

  clearMessages: () => set({ messages: [] }),

  // Input actions
  setInputMessage: (message) => set({ inputMessage: message }),
  setIsTyping: (typing) => set({ isTyping: typing }),
  setIsProcessing: (processing) => set({ isProcessing: processing }),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),

  // Config actions
  setConfig: (config) =>
    set((state) => ({ config: { ...state.config, ...config } })),
  setModel: (model) =>
    set((state) => ({ config: { ...state.config, model } })),
  setTemperature: (temperature) =>
    set((state) => ({ config: { ...state.config, temperature } })),

  // Debug actions
  toggleDebugMode: () => set((state) => ({ debugMode: !state.debugMode })),
  setDebugData: (data) =>
    set({
      lastCuOptRequest: data.cuoptRequest ?? null,
      lastCuOptResponse: data.cuoptResponse ?? null,
      lastGenAIPrompt: data.genaiPrompt ?? null,
    }),

  // Reset
  reset: () =>
    set({
      conversations: [],
      currentConversationId: null,
      messages: [],
      inputMessage: '',
      isTyping: false,
      isProcessing: false,
      isStreaming: false,
      streamingMessageId: null,
      config: defaultConfig,
      debugMode: false,
      lastCuOptRequest: null,
      lastCuOptResponse: null,
      lastGenAIPrompt: null,
    }),
}));
