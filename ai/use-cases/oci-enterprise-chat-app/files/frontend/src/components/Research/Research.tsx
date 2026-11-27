import React, { useState, useEffect } from 'react';
import {
  Search,
  FileText,
  Loader2,
  BookOpen,
  Shield,
  GitCompare,
  Clock,
  ExternalLink,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import Markdown from 'react-markdown';
import { api } from '../../services/api';
import {
  Document,
  ReportTemplate,
  ResearchSource,
  TimelineEvent,
} from '../../types';

const TEMPLATE_ICONS: Record<string, React.ElementType> = {
  summary: BookOpen,
  compliance: Shield,
  comparison: GitCompare,
  timeline: Clock,
};

const Research: React.FC = () => {
  const [query, setQuery] = useState('');
  const [reportType, setReportType] = useState('summary');
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedDocs, setSelectedDocs] = useState<string[]>([]);
  const [report, setReport] = useState('');
  const [sources, setSources] = useState<ResearchSource[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [stats, setStats] = useState({ searched: 0, used: 0 });
  const [docSearch, setDocSearch] = useState('');
  const [showSources, setShowSources] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);

  useEffect(() => {
    api.listDocuments().then((documents) => {
      const completed = documents.filter((d) => d.status === 'completed');
      setDocs(completed);
      if (completed.length > 0) setSelectedDocs([completed[0].id]);
    });
    api.getReportTemplates().then(setTemplates).catch(() => {});
  }, []);

  const generate = async () => {
    if (!query.trim() || selectedDocs.length === 0) return;
    setLoading(true);
    setReport('');
    setSources([]);
    setTimeline([]);
    try {
      const res = await api.generateReport(query, selectedDocs, reportType);
      setReport(res.report);
      setSources(res.sources || []);
      setTimeline(res.timeline || []);
      setStats({ searched: res.chunks_searched, used: res.chunks_used });
    } catch {
      setReport('Error generating report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Left panel — Query & Document selector */}
      <div className="w-80 shrink-0 border-r border-dark-700 flex flex-col bg-dark-800">
        <div className="p-4 border-b border-dark-700 space-y-3 shrink-0">
          {/* Header */}
          <div>
            <h2 className="text-lg font-semibold text-white">Research</h2>
            <p className="text-xs text-dark-300">Generate structured reports from your documents</p>
          </div>

          {/* Query input */}
          <div>
            <label className="text-xs text-dark-400 uppercase tracking-wider font-medium">
              Research Query
            </label>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="What do you want to research? e.g., 'What are the key findings?'"
              className="w-full mt-1 bg-dark-900 border border-dark-700 rounded-lg px-3 py-2 text-sm text-white placeholder-dark-400 focus:outline-none focus:border-oracle-red/50 resize-none h-20"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  generate();
                }
              }}
            />
          </div>

          {/* Report type selector */}
          <div>
            <label className="text-xs text-dark-400 uppercase tracking-wider font-medium">
              Report Type
            </label>
            <div className="grid grid-cols-2 gap-1.5 mt-1">
              {templates.map((t) => {
                const Icon = TEMPLATE_ICONS[t.id] || BookOpen;
                return (
                  <button
                    key={t.id}
                    onClick={() => setReportType(t.id)}
                    className={`flex items-center gap-2 px-2.5 py-2 rounded-lg text-left text-xs transition-colors ${
                      reportType === t.id
                        ? 'bg-oracle-red/10 border border-oracle-red/30 text-oracle-red'
                        : 'bg-dark-900 border border-dark-700 text-dark-200 hover:text-white hover:border-dark-600'
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span>{t.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Generate button */}
          <button
            onClick={generate}
            disabled={loading || !query.trim() || selectedDocs.length === 0}
            className="w-full py-2.5 bg-oracle-red text-white rounded-lg text-sm font-medium hover:bg-red-700 disabled:opacity-40 transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Generating...
              </>
            ) : (
              <>
                <Search className="h-4 w-4" /> Generate Report
              </>
            )}
          </button>
        </div>

        {/* Document selector */}
        <div className="flex-1 overflow-y-auto p-3" style={{ minHeight: 0 }}>
          <p className="text-xs text-dark-400 uppercase tracking-wider font-medium mb-1.5">
            Documents ({selectedDocs.length} selected)
          </p>
          <div className="relative mb-2">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-dark-400 h-3 w-3" />
            <input
              value={docSearch}
              onChange={(e) => setDocSearch(e.target.value)}
              placeholder="Search documents..."
              className="w-full bg-dark-900 border border-dark-700 rounded pl-7 pr-2 py-1 text-xs text-white placeholder-dark-400 focus:outline-none focus:border-oracle-red/50"
            />
          </div>
          <div className="space-y-1">
            {docs
              .filter((d) =>
                d.metadata.filename.toLowerCase().includes(docSearch.toLowerCase())
              )
              .map((doc) => (
                <label
                  key={doc.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-dark-700 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedDocs.includes(doc.id)}
                    onChange={(e) =>
                      setSelectedDocs((prev) =>
                        e.target.checked
                          ? [...prev, doc.id]
                          : prev.filter((x) => x !== doc.id)
                      )
                    }
                    className="accent-oracle-red w-3.5 h-3.5"
                  />
                  <FileText className="h-3.5 w-3.5 text-oracle-red shrink-0" />
                  <span className="text-xs text-dark-200 truncate">
                    {doc.metadata.filename}
                  </span>
                </label>
              ))}
            {docs.length === 0 && (
              <p className="text-xs text-dark-400 text-center py-4">
                No completed documents found
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Right panel — Report */}
      <div className="flex-1 flex flex-col bg-dark-900 overflow-hidden">
        {/* Report header */}
        <div className="h-12 bg-dark-800 border-b border-dark-700 flex items-center px-4 gap-2 shrink-0">
          <BookOpen className="h-4 w-4 text-oracle-red" />
          <span className="text-sm text-dark-300 flex-1">
            {report
              ? `Report — ${stats.used} chunks from ${stats.searched} searched`
              : 'Report will appear here'}
          </span>
        </div>

        {!report && !loading ? (
          <div className="flex-1 flex items-center justify-center text-dark-400 text-sm">
            Enter a query and click Generate Report
          </div>
        ) : loading ? (
          <div className="flex-1 flex flex-col items-center justify-center gap-3">
            <Loader2 className="h-8 w-8 text-oracle-red animate-spin" />
            <p className="text-dark-300 text-sm">Analyzing document chunks...</p>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
            {/* Report content */}
            <div className="p-6 max-w-4xl">
              <Markdown
                components={{
                  h1: ({ children }) => (
                    <h1 className="text-xl font-bold text-white mb-3 mt-5 pb-2 border-b border-dark-700">
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 className="text-lg font-semibold text-white mb-2 mt-4 pb-1.5 border-b border-dark-700/50">
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 className="text-sm font-semibold text-dark-100 mb-1.5 mt-3">
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p className="text-sm text-dark-200 leading-relaxed mb-2.5">
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul className="space-y-1.5 mb-3 ml-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="space-y-1.5 mb-3 ml-1 list-decimal list-inside">
                      {children}
                    </ol>
                  ),
                  li: ({ children }) => (
                    <li className="flex gap-2 text-sm text-dark-200">
                      <span className="text-oracle-red mt-1.5 shrink-0">•</span>
                      <span className="leading-relaxed">{children}</span>
                    </li>
                  ),
                  strong: ({ children }) => (
                    <strong className="text-white font-semibold">{children}</strong>
                  ),
                  em: ({ children }) => (
                    <em className="text-dark-300 italic">{children}</em>
                  ),
                  code: ({ children }) => (
                    <code className="bg-dark-700 px-1.5 py-0.5 rounded text-oracle-red text-xs font-mono">
                      {children}
                    </code>
                  ),
                  table: ({ children }) => (
                    <div className="my-3 border border-dark-700 rounded-lg overflow-hidden">
                      <table className="w-full text-sm">{children}</table>
                    </div>
                  ),
                  thead: ({ children }) => (
                    <thead className="bg-dark-800">{children}</thead>
                  ),
                  th: ({ children }) => (
                    <th className="px-3 py-2 text-left text-xs font-semibold text-dark-200 border-b border-dark-700">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="px-3 py-2 text-xs text-dark-300 border-b border-dark-700/30">
                      {children}
                    </td>
                  ),
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-2 border-oracle-red pl-3 my-2 text-sm text-dark-300 italic">
                      {children}
                    </blockquote>
                  ),
                  hr: () => <hr className="border-dark-700 my-4" />,
                }}
              >
                {report}
              </Markdown>
            </div>

            {/* Timeline (if available) */}
            {timeline.length > 0 && (
              <div className="border-t border-dark-700">
                <button
                  onClick={() => setShowTimeline(!showTimeline)}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-dark-200 hover:bg-dark-800"
                >
                  {showTimeline ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <Clock className="h-4 w-4 text-amber-400" />
                  <span>Timeline</span>
                  <span className="ml-auto text-xs bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
                    {timeline.length}
                  </span>
                </button>
                {showTimeline && (
                  <div className="px-4 pb-4 space-y-2">
                    {timeline.map((evt, i) => (
                      <div key={i} className="flex gap-3 items-start">
                        <div className="w-2 h-2 rounded-full bg-oracle-red mt-1.5 shrink-0" />
                        <div className="flex-1 bg-dark-800 border border-dark-700 rounded-lg px-3 py-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-oracle-red font-medium">
                              {evt.date}
                            </span>
                            <span className="text-xs text-dark-400 px-1.5 py-0.5 bg-dark-700 rounded">
                              {evt.type}
                            </span>
                          </div>
                          <p className="text-xs text-dark-200 mt-0.5">
                            {evt.description}
                          </p>
                          {evt.page && (
                            <p className="text-xs text-dark-400 mt-0.5">
                              Page {evt.page}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Sources */}
            {sources.length > 0 && (
              <div className="border-t border-dark-700">
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="w-full flex items-center gap-2 px-4 py-3 text-sm text-dark-200 hover:bg-dark-800"
                >
                  {showSources ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                  <ExternalLink className="h-4 w-4 text-blue-400" />
                  <span>Sources</span>
                  <span className="ml-auto text-xs bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded">
                    {sources.length}
                  </span>
                </button>
                {showSources && (
                  <div className="px-4 pb-4 space-y-1.5">
                    {sources.map((s, i) => (
                      <div
                        key={i}
                        className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2"
                      >
                        <div className="flex items-center justify-between mb-0.5">
                          <div className="flex items-center gap-2 min-w-0">
                            <span className="text-xs text-white font-medium shrink-0">
                              Page {s.page}
                            </span>
                            {s.document_name && (
                              <span className="text-xs text-oracle-red bg-oracle-red/10 px-1.5 py-0.5 rounded truncate">
                                {s.document_name.replace('.pdf', '').slice(0, 30)}
                              </span>
                            )}
                          </div>
                          <span
                            className={`text-xs px-1.5 py-0.5 rounded shrink-0 ${
                              s.relevance >= 0.5
                                ? 'bg-emerald-500/20 text-emerald-400'
                                : s.relevance >= 0.2
                                ? 'bg-amber-500/20 text-amber-400'
                                : 'bg-dark-600 text-dark-300'
                            }`}
                          >
                            {Math.round(s.relevance * 100)}%
                          </span>
                        </div>
                        <p className="text-xs text-dark-300 leading-relaxed">
                          {s.snippet}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Research;
