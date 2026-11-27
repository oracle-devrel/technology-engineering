import React, { useState, useRef, useEffect } from 'react';
import { api } from '../../services/api';
import { Document, ChatMessage, ChatSource, ChatHistoryMessage, ModelSettings, DEFAULT_MODEL_SETTINGS, WebSource } from '../../types';

interface ChatProps {
  documents: Document[];
  webSources?: WebSource[];
  projectName?: string;
  onBack: () => void;
  inferenceModel?: string;
}

interface MessageBubbleProps {
  message: ChatMessage;
  isUser: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  const [showSources, setShowSources] = useState(false);

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-oracle-red/20 text-oracle-red'
            : 'bg-dark-600 text-dark-200'
        }`}
      >
        {isUser ? (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
            <path
              fillRule="evenodd"
              d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </div>

      {/* Message content */}
      <div
        className={`flex flex-col max-w-[80%] ${
          isUser ? 'items-end' : 'items-start'
        }`}
      >
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? 'bg-oracle-red text-white rounded-tr-sm'
              : message.isError
              ? 'bg-red-900/20 border border-red-500/30 text-red-300 rounded-tl-sm'
              : 'bg-dark-700 text-dark-100 rounded-tl-sm'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Sources section for assistant messages */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 w-full">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 text-xs text-dark-400 hover:text-dark-200 transition-colors"
            >
              <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>
                {message.sources.length} source
                {message.sources.length > 1 ? 's' : ''}
              </span>
              <svg
                className={`h-3 w-3 transition-transform ${
                  showSources ? 'rotate-180' : ''
                }`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source: ChatSource, idx: number) => (
                  <div
                    key={idx}
                    className="bg-dark-800 border border-dark-600 rounded-lg p-3"
                  >
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {source.document_name && (
                        <span className="text-xs font-medium text-oracle-red truncate max-w-[200px]">
                          {source.document_name}
                        </span>
                      )}
                      {source.page_number && (
                        <span className="text-xs text-dark-400">
                          Page {source.page_number}
                        </span>
                      )}
                      <span className="text-xs text-dark-500 ml-auto">
                        {Math.round(source.relevance_score * 100)}% relevant
                      </span>
                    </div>
                    <p className="text-xs text-dark-300 line-clamp-3">
                      {source.snippet}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Confidence indicator */}
        {!isUser && message.confidence !== undefined && !message.isError && (
          <div className="mt-1 flex items-center gap-1">
            <div
              className={`h-1.5 w-1.5 rounded-full ${
                message.confidence >= 0.7
                  ? 'bg-green-500'
                  : message.confidence >= 0.4
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-dark-500">
              {Math.round(message.confidence * 100)}% confidence
            </span>
          </div>
        )}

        {/* Timestamp */}
        {message.timestamp && (
          <span className="text-xs text-dark-500 mt-1">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        )}
      </div>
    </div>
  );
};

const TypingIndicator: React.FC = () => {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-dark-600 flex items-center justify-center">
        <svg className="h-4 w-4 text-dark-200" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
          <path
            fillRule="evenodd"
            d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
            clipRule="evenodd"
          />
        </svg>
      </div>
      <div className="bg-dark-700 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1">
          <span
            className="h-2 w-2 bg-dark-400 rounded-full animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <span
            className="h-2 w-2 bg-dark-400 rounded-full animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <span
            className="h-2 w-2 bg-dark-400 rounded-full animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  );
};

interface SettingSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  defaultValue: number;
  description: string;
  onChange: (value: number) => void;
}

const SettingSlider: React.FC<SettingSliderProps> = ({
  label,
  value,
  min,
  max,
  step,
  defaultValue,
  description,
  onChange,
}) => (
  <div className="space-y-1.5">
    <div className="flex items-center justify-between">
      <label className="text-sm font-medium text-dark-200">{label}</label>
      <div className="flex items-center gap-2">
        <span className="text-sm font-mono text-oracle-red">{value}</span>
        {value !== defaultValue && (
          <button
            onClick={() => onChange(defaultValue)}
            className="text-xs text-dark-500 hover:text-dark-300 transition-colors"
            title="Reset to default"
          >
            reset
          </button>
        )}
      </div>
    </div>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      className="w-full h-1.5 bg-dark-600 rounded-full appearance-none cursor-pointer accent-oracle-red"
    />
    <div className="flex justify-between text-xs text-dark-500">
      <span>{min}</span>
      <span className="text-dark-500">{description}</span>
      <span>{max}</span>
    </div>
  </div>
);

interface SettingsPanelProps {
  settings: ModelSettings;
  onChange: (settings: ModelSettings) => void;
  onReset: () => void;
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({ settings, onChange, onReset }) => {
  const isModified = JSON.stringify(settings) !== JSON.stringify(DEFAULT_MODEL_SETTINGS);

  return (
    <div className="bg-dark-800 border border-dark-600 rounded-xl p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white">Model Parameters</h3>
        {isModified && (
          <button
            onClick={onReset}
            className="text-xs px-2 py-1 text-dark-400 hover:text-white hover:bg-dark-600 rounded transition-colors"
          >
            Reset All
          </button>
        )}
      </div>

      <SettingSlider
        label="Temperature"
        value={settings.temperature}
        min={0}
        max={2}
        step={0.1}
        defaultValue={DEFAULT_MODEL_SETTINGS.temperature}
        description="Low = focused, High = creative"
        onChange={(v) => onChange({ ...settings, temperature: v })}
      />

      <SettingSlider
        label="Max Tokens"
        value={settings.max_tokens}
        min={256}
        max={8192}
        step={256}
        defaultValue={DEFAULT_MODEL_SETTINGS.max_tokens}
        description="Maximum response length"
        onChange={(v) => onChange({ ...settings, max_tokens: v })}
      />

      <SettingSlider
        label="Top P"
        value={settings.top_p}
        min={0}
        max={1}
        step={0.05}
        defaultValue={DEFAULT_MODEL_SETTINGS.top_p}
        description="Nucleus sampling"
        onChange={(v) => onChange({ ...settings, top_p: v })}
      />

      <SettingSlider
        label="Frequency Penalty"
        value={settings.frequency_penalty}
        min={0}
        max={2}
        step={0.1}
        defaultValue={DEFAULT_MODEL_SETTINGS.frequency_penalty}
        description="Reduce repetition"
        onChange={(v) => onChange({ ...settings, frequency_penalty: v })}
      />

      <SettingSlider
        label="Presence Penalty"
        value={settings.presence_penalty}
        min={0}
        max={2}
        step={0.1}
        defaultValue={DEFAULT_MODEL_SETTINGS.presence_penalty}
        description="Encourage new topics"
        onChange={(v) => onChange({ ...settings, presence_penalty: v })}
      />
    </div>
  );
};

type SourceFilter = 'all' | string; // 'all', document_id, or 'web:sourceId'

const Chat: React.FC<ChatProps> = ({ documents, webSources = [], projectName, onBack, inferenceModel }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [modelSettings, setModelSettings] = useState<ModelSettings>({ ...DEFAULT_MODEL_SETTINGS });
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');
  const [showSourceDropdown, setShowSourceDropdown] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const isSettingsModified = JSON.stringify(modelSettings) !== JSON.stringify(DEFAULT_MODEL_SETTINGS);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowSourceDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Compute active document IDs based on source filter
  // Web source IDs are included alongside document IDs — the backend
  // resolves both types from the same document_ids array.
  const getActiveDocumentIds = (): string[] => {
    if (sourceFilter === 'all') {
      return [
        ...documents.map((d) => d.id),
        ...webSources.map((ws) => ws.id),
      ];
    }
    if (sourceFilter.startsWith('web:')) {
      const wsId = sourceFilter.slice(4);
      return [wsId]; // Web source ID acts as document ID in the vector store
    }
    // Single document selected
    return [sourceFilter];
  };

  const getSourceLabel = (): string => {
    if (sourceFilter === 'all') {
      const total = documents.length + webSources.length;
      return `All sources (${total})`;
    }
    if (sourceFilter.startsWith('web:')) {
      const wsId = sourceFilter.slice(4);
      const ws = webSources.find((w) => w.id === wsId);
      return ws ? (ws.title || ws.url) : 'Web source';
    }
    const doc = documents.find((d) => d.id === sourceFilter);
    return doc ? doc.metadata.filename : 'Unknown';
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Check RAG health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await api.checkRAGHealth();
        setIsHealthy(health.status === 'healthy');
      } catch {
        setIsHealthy(false);
      }
    };
    checkHealth();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedInput = input.trim();
    if (!trimmedInput || isLoading) return;

    // Add user message
    const userMessage: ChatMessage = {
      role: 'user',
      content: trimmedInput,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      // Prepare conversation history (excluding the current message)
      const conversationHistory: ChatHistoryMessage[] = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp,
      }));

      const activeDocIds = getActiveDocumentIds();

      const response = await api.chat(
        trimmedInput,
        activeDocIds,
        conversationHistory,
        5,
        modelSettings,
        inferenceModel
      );

      // Add assistant message with sources and confidence
      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.message,
        sources: response.sources,
        confidence: response.confidence,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : (err as { response?: { data?: { detail?: string } } })?.response?.data
              ?.detail || 'Failed to get response';
      setError(errorMessage);

      // Add error message to chat
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'I apologize, but I encountered an error processing your request. Please try again.',
          timestamp: new Date().toISOString(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const suggestions = [
    'What are the key points in this document?',
    'Summarize the main findings',
    'What dates are mentioned?',
    'What are the monetary values?',
  ];

  return (
    <div className="flex-1 flex flex-col bg-dark-900 overflow-hidden">
      {/* Chat header */}
      <div className="bg-dark-800 border-b border-dark-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 text-dark-400 hover:text-white hover:bg-dark-700 rounded-md transition-colors"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 19l-7-7 7-7"
                />
              </svg>
            </button>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-oracle-red/20 flex items-center justify-center">
                <svg
                  className="h-5 w-5 text-oracle-red"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">
                  AI-Q Assistant
                </h2>
                <p className="text-sm text-dark-400">
                  {projectName ? `${projectName} — ` : ''}
                  {documents.length} file{documents.length !== 1 ? 's' : ''}
                  {webSources.length > 0 && `, ${webSources.length} web source${webSources.length !== 1 ? 's' : ''}`}
                </p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Settings toggle */}
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`relative p-2 rounded-md transition-colors ${
                showSettings
                  ? 'bg-oracle-red/20 text-oracle-red'
                  : 'text-dark-400 hover:text-white hover:bg-dark-700'
              }`}
              title="Model Parameters"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
              </svg>
              {isSettingsModified && (
                <span className="absolute -top-0.5 -right-0.5 h-2 w-2 bg-oracle-red rounded-full" />
              )}
            </button>

            {/* Health indicator */}
            <div className="flex items-center gap-2">
              <span
                className={`h-2 w-2 rounded-full ${
                  isHealthy === null
                    ? 'bg-dark-500'
                    : isHealthy
                    ? 'bg-green-500 animate-pulse'
                    : 'bg-yellow-500'
                }`}
              />
              <span className="text-xs text-dark-400">
                {isHealthy === null
                  ? 'Checking...'
                  : isHealthy
                  ? 'Online'
                  : 'Degraded'}
              </span>
            </div>
          </div>
        </div>

        {/* Source selector */}
        <div className="mt-4 flex items-center gap-3">
          <span className="text-sm text-dark-400">Source:</span>
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setShowSourceDropdown(!showSourceDropdown)}
              className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-sm text-white transition-colors min-w-[200px] max-w-[400px]"
            >
              {sourceFilter === 'all' ? (
                <svg className="w-4 h-4 text-oracle-red flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              ) : sourceFilter.startsWith('web:') ? (
                <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
              )}
              <span className="truncate">{getSourceLabel()}</span>
              <svg className={`w-4 h-4 text-dark-400 ml-auto flex-shrink-0 transition-transform ${showSourceDropdown ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showSourceDropdown && (
              <div className="absolute top-full left-0 mt-1 w-80 bg-dark-700 border border-dark-600 rounded-lg shadow-modal z-50 overflow-hidden animate-scale-in">
                <div className="max-h-64 overflow-y-auto">
                  {/* All sources option */}
                  <button
                    onClick={() => { setSourceFilter('all'); setShowSourceDropdown(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors ${
                      sourceFilter === 'all' ? 'bg-oracle-red/10 text-oracle-red' : 'text-dark-200 hover:bg-dark-600'
                    }`}
                  >
                    <svg className="w-4 h-4 text-oracle-red flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                    <span>All sources ({documents.length + webSources.length})</span>
                    {sourceFilter === 'all' && (
                      <svg className="w-4 h-4 ml-auto" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>

                  {/* Files section */}
                  {documents.length > 0 && (
                    <>
                      <div className="px-4 py-1.5 text-xs font-semibold text-dark-400 uppercase tracking-wider bg-dark-800/50">
                        Files
                      </div>
                      {documents.map((doc) => (
                        <button
                          key={doc.id}
                          onClick={() => { setSourceFilter(doc.id); setShowSourceDropdown(false); }}
                          className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors ${
                            sourceFilter === doc.id ? 'bg-oracle-red/10 text-oracle-red' : 'text-dark-200 hover:bg-dark-600'
                          }`}
                        >
                          <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                          </svg>
                          <span className="truncate">{doc.metadata.filename}</span>
                          {sourceFilter === doc.id && (
                            <svg className="w-4 h-4 ml-auto flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                      ))}
                    </>
                  )}

                  {/* Web sources section */}
                  {webSources.length > 0 && (
                    <>
                      <div className="px-4 py-1.5 text-xs font-semibold text-dark-400 uppercase tracking-wider bg-dark-800/50">
                        Web Sources
                      </div>
                      {webSources.map((ws) => (
                        <button
                          key={ws.id}
                          onClick={() => { setSourceFilter(`web:${ws.id}`); setShowSourceDropdown(false); }}
                          className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors ${
                            sourceFilter === `web:${ws.id}` ? 'bg-oracle-red/10 text-oracle-red' : 'text-dark-200 hover:bg-dark-600'
                          }`}
                        >
                          <svg className="w-4 h-4 text-blue-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          <span className="truncate">{ws.title || ws.url}</span>
                          {sourceFilter === `web:${ws.id}` && (
                            <svg className="w-4 h-4 ml-auto flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </button>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Settings panel (collapsible) */}
      {showSettings && (
        <div className="px-6 pt-4 pb-2 border-b border-dark-700 bg-dark-900/50">
          <SettingsPanel
            settings={modelSettings}
            onChange={setModelSettings}
            onReset={() => setModelSettings({ ...DEFAULT_MODEL_SETTINGS })}
          />
        </div>
      )}

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="h-16 w-16 rounded-2xl bg-dark-700 flex items-center justify-center mb-4">
              <svg
                className="h-8 w-8 text-dark-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path
                  fillRule="evenodd"
                  d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-2">
              Start a conversation
            </h3>
            <p className="text-dark-400 text-sm max-w-md">
              Ask questions about your selected documents. I can help you find
              information, analyze content, and answer questions using the
              knowledge base.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-2 max-w-lg">
              {suggestions.map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => setInput(suggestion)}
                  className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 text-sm rounded-full transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, index) => (
              <MessageBubble
                key={index}
                message={message}
                isUser={message.role === 'user'}
              />
            ))}
            {isLoading && <TypingIndicator />}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-6 mb-4 flex items-center gap-2 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <svg
            className="h-4 w-4 text-red-400 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
          <p className="text-sm text-red-400 flex-1">{error}</p>
          <button
            onClick={() => setError(null)}
            className="text-red-400 hover:text-red-300"
          >
            &times;
          </button>
        </div>
      )}

      {/* Input area */}
      <form
        onSubmit={handleSubmit}
        className="bg-dark-800 border-t border-dark-700 p-4"
      >
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              rows={1}
              className="w-full px-4 py-3 bg-dark-700 border border-dark-600 rounded-xl text-white placeholder-dark-400 resize-none focus:outline-none focus:ring-2 focus:ring-oracle-red/50 focus:border-oracle-red transition-all"
              style={{ minHeight: '48px', maxHeight: '200px' }}
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-12 w-12 flex items-center justify-center bg-oracle-red hover:bg-oracle-red/90 disabled:bg-dark-600 disabled:cursor-not-allowed rounded-xl transition-colors"
          >
            {isLoading ? (
              <svg
                className="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
            ) : (
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                />
              </svg>
            )}
          </button>
        </div>
        <p className="text-xs text-dark-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </form>
    </div>
  );
};

export default Chat;
