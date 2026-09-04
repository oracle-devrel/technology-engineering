import { useState, useRef, useEffect } from 'react';
import { sendQuery, sendRAGQuery } from '../services/api';
import type { QueryResult, RAGResult } from '../services/api';

type ChatMode = 'nl2sql' | 'rag';

interface ChatMessage {
  id: number;
  question: string;
  mode: ChatMode;
  result: QueryResult | null;
  ragResult: RAGResult | null;
  error: string | null;
  loading: boolean;
}

interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
}

const NL2SQL_SUGGESTIONS = [
  'Negative trends this month',
  'Top complaints by product',
  'Sentiment by source',
  'Which products have the best reviews?',
  'Average rating over time',
];

const RAG_SUGGESTIONS = [
  'What are the best practices for sentiment analysis?',
  'How should we respond to negative customer reviews?',
  'What campaign strategy works for at-risk customers?',
  'Explain the crisis communication severity levels',
  'What AI use cases can we implement with Oracle?',
];

export default function ChatPanel({ open, onClose }: ChatPanelProps) {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isQuerying, setIsQuerying] = useState(false);
  const [mode, setMode] = useState<ChatMode>('nl2sql');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when modal opens
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  const handleSubmit = async (question: string) => {
    if (!question.trim() || isQuerying) return;

    const msgId = Date.now();
    const currentMode = mode;
    const newMessage: ChatMessage = {
      id: msgId,
      question: question.trim(),
      mode: currentMode,
      result: null,
      ragResult: null,
      error: null,
      loading: true,
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput('');
    setIsQuerying(true);

    try {
      if (currentMode === 'rag') {
        const ragResult = await sendRAGQuery(question.trim());
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId ? { ...m, ragResult, loading: false } : m
          )
        );
      } else {
        const result = await sendQuery(question.trim());
        setMessages((prev) =>
          prev.map((m) =>
            m.id === msgId ? { ...m, result, loading: false } : m
          )
        );
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Query failed';
      setMessages((prev) =>
        prev.map((m) =>
          m.id === msgId ? { ...m, error: errorMessage, loading: false } : m
        )
      );
    } finally {
      setIsQuerying(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  const suggestions = mode === 'rag' ? RAG_SUGGESTIONS : NL2SQL_SUGGESTIONS;

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-2xl bg-white rounded-xl border border-gray-200 p-6 animate-fade-in shadow-xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
            <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clipRule="evenodd" />
            </svg>
            Ask AI
          </h3>
          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <button
                onClick={() => { setMessages([]); setInput(''); }}
                className="px-2.5 py-1.5 rounded-lg text-[10px] font-medium text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all flex items-center gap-1.5"
                title="New chat"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Chat
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all"
              title="Close (Esc)"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex gap-1 p-1 rounded-lg bg-gray-100 mb-4">
          <button
            onClick={() => setMode('nl2sql')}
            className={`flex-1 px-3 py-2 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
              mode === 'nl2sql'
                ? 'bg-white text-accent border border-gray-200 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
            Data Query
            <span className="text-[9px] opacity-60">(NL2SQL)</span>
          </button>
          <button
            onClick={() => setMode('rag')}
            className={`flex-1 px-3 py-2 rounded-md text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
              mode === 'rag'
                ? 'bg-white text-purple-600 border border-gray-200 shadow-sm'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
            }`}
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Knowledge Base
            <span className="text-[9px] opacity-60">(RAG)</span>
          </button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto mb-4 space-y-4 pr-1 min-h-0">
        {messages.length === 0 && (
          <div className="text-center py-6 text-gray-400">
            {mode === 'rag' ? (
              <>
                <svg className="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                <p className="text-sm">Ask questions about your document knowledge base.</p>
                <p className="text-xs mt-1 text-gray-300">Powered by Oracle Select AI RAG with vector search</p>
              </>
            ) : (
              <>
                <svg className="w-10 h-10 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <p className="text-sm">Ask questions about your sentiment data in natural language.</p>
                <p className="text-xs mt-1 text-gray-300">Powered by Oracle Select AI NL2SQL</p>
              </>
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className="animate-fade-in">
            {/* Question */}
            <div className="flex items-start gap-2 mb-2">
              <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg className="w-3.5 h-3.5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex items-center gap-2 pt-0.5">
                <p className="text-sm text-gray-900">{msg.question}</p>
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full font-medium ${
                  msg.mode === 'rag'
                    ? 'bg-purple-50 text-purple-600 border border-purple-200'
                    : 'bg-accent/5 text-accent border border-accent/20'
                }`}>
                  {msg.mode === 'rag' ? 'RAG' : 'SQL'}
                </span>
              </div>
            </div>

            {/* Response */}
            {msg.loading ? (
              <div className="ml-8 flex items-center gap-2 text-gray-400 text-sm">
                <svg className="w-4 h-4 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                {msg.mode === 'rag' ? 'Searching knowledge base...' : 'Querying database...'}
              </div>
            ) : msg.error ? (
              <div className="ml-8 chat-response border-l-red-500">
                <p className="text-sm text-red-600">{msg.error}</p>
              </div>
            ) : msg.mode === 'rag' && msg.ragResult ? (
              /* RAG Response */
              <div className="ml-8 space-y-2">
                <div className="chat-response border-l-purple-400">
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {msg.ragResult.answer}
                  </p>
                </div>
              </div>
            ) : msg.result ? (
              /* NL2SQL Response */
              <div className="ml-8 space-y-2">
                <div className="chat-response">
                  <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {msg.result.narrative || 'Query completed.'}
                  </p>
                </div>
                {msg.result.sql && (
                  <details className="group">
                    <summary className="text-[10px] uppercase tracking-wider text-gray-400 cursor-pointer hover:text-gray-600 transition-colors flex items-center gap-1">
                      <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                      Generated SQL
                    </summary>
                    <div className="chat-sql mt-2 text-blue-700">
                      {msg.result.sql}
                    </div>
                  </details>
                )}
                {msg.result.data && msg.result.data.length > 0 && (
                  <details className="group">
                    <summary className="text-[10px] uppercase tracking-wider text-gray-400 cursor-pointer hover:text-gray-600 transition-colors flex items-center gap-1">
                      <svg className="w-3 h-3 transition-transform group-open:rotate-90" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                      Raw Data ({msg.result.data.length} row{msg.result.data.length !== 1 ? 's' : ''})
                    </summary>
                    <div className="chat-sql mt-2 text-gray-700 overflow-x-auto">
                      <table className="w-full text-left">
                        <thead>
                          <tr>
                            {Object.keys(msg.result.data[0]).map((key) => (
                              <th key={key} className="px-2 py-1 text-[10px] uppercase tracking-wider text-gray-400 border-b border-gray-200">
                                {key}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {msg.result.data.slice(0, 10).map((row, i) => (
                            <tr key={i} className="border-b border-gray-100">
                              {Object.values(row).map((val, j) => (
                                <td key={j} className="px-2 py-1 text-xs">
                                  {String(val ?? '-')}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      {msg.result.data.length > 10 && (
                        <p className="text-[10px] text-gray-400 mt-1 text-center">
                          Showing 10 of {msg.result.data.length} rows
                        </p>
                      )}
                    </div>
                  </details>
                )}
              </div>
            ) : null}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

        {/* Quick Suggestions */}
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                onClick={() => handleSubmit(suggestion)}
                disabled={isQuerying}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all disabled:opacity-50 ${
                  mode === 'rag'
                    ? 'bg-purple-50 text-purple-600 border-purple-200 hover:bg-purple-100'
                    : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                {suggestion}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              mode === 'rag'
                ? "Ask about documents... (e.g., 'What are the prescribing guidelines?')"
                : "Ask about sentiment... (e.g., 'Which products have negative reviews?')"
            }
            disabled={isQuerying}
            className={`flex-1 px-4 py-2.5 rounded-lg bg-gray-50 border text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-1 transition-all disabled:opacity-50 ${
              mode === 'rag'
                ? 'border-purple-200 focus:border-purple-400 focus:ring-purple-200'
                : 'border-gray-200 focus:border-accent/50 focus:ring-accent/20'
            }`}
          />
          <button
            onClick={() => handleSubmit(input)}
            disabled={!input.trim() || isQuerying}
            className={`px-4 py-2.5 rounded-lg text-white text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 ${
              mode === 'rag'
                ? 'bg-purple-600 hover:bg-purple-700'
                : 'bg-accent hover:bg-accent/90'
            }`}
          >
            {isQuerying ? (
              <svg className="w-4 h-4 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )}
            Ask
          </button>
        </div>
      </div>
    </div>
  );
}
