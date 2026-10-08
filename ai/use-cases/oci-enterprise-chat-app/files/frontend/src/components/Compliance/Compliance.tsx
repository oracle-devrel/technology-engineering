import React, { useEffect, useState } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Search,
  Shield,
  X,
  ChevronDown,
  Factory,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../services/api';
import {
  Document,
  DocumentComplianceResult,
  ComplianceFinding,
  IndustryOption,
} from '../../types';

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  return (
    <div className="w-full bg-dark-700 rounded-full h-1.5">
      <div
        className="h-1.5 rounded-full transition-all"
        style={{
          width: `${(value / Math.max(max, 1)) * 100}%`,
          backgroundColor: color,
        }}
      />
    </div>
  );
}

const Compliance: React.FC = () => {
  const [data, setData] = useState<DocumentComplianceResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDoc, setSelectedDoc] = useState<DocumentComplianceResult | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Industry selection
  const [industries, setIndustries] = useState<IndustryOption[]>([]);
  const [selectedIndustry, setSelectedIndustry] = useState<string>('generic');
  const [showIndustryDropdown, setShowIndustryDropdown] = useState(false);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [hasRun, setHasRun] = useState(false);
  const [reviewer, setReviewer] = useState('');
  const [reviewNotes, setReviewNotes] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState('');

  // Load industries and documents on mount
  useEffect(() => {
    api.listIndustries().then(setIndustries).catch(() => {});
    api.listDocuments().then((docs) => {
      const completed = docs.filter((d) => d.status === 'completed');
      setDocuments(completed);
    });
  }, []);

  // Auto-run compliance checks when documents are loaded or industry changes
  useEffect(() => {
    if (documents.length === 0) return;
    setLoading(true);
    setSelectedDoc(null);
    const docIds = documents.map((d) => d.id);
    api.checkCompliance(docIds, selectedIndustry)
      .then((response) => {
        setData(response.results);
        setHasRun(true);
      })
      .catch(() => {
        setData([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [documents, selectedIndustry]);

  const runComplianceCheck = async () => {
    if (documents.length === 0) return;
    setLoading(true);
    setSelectedDoc(null);
    try {
      const docIds = documents.map((d) => d.id);
      const response = await api.checkCompliance(docIds, selectedIndustry);
      setData(response.results);
      setHasRun(true);
    } catch {
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const recordReview = async (decision: 'approved' | 'changes_requested') => {
    if (!selectedDoc) return;
    if (!reviewer.trim()) {
      setReviewError('Enter the accountable reviewer before recording a decision.');
      return;
    }
    setReviewSubmitting(true);
    setReviewError('');
    try {
      const updated = await api.reviewCompliance(
        selectedDoc.document_id,
        reviewer.trim(),
        decision,
        reviewNotes.trim() || undefined,
      );
      setData(current => current.map(doc => doc.document_id === updated.document_id ? updated : doc));
      setSelectedDoc(updated);
    } catch {
      setReviewError('Could not record the human review. Please try again.');
    } finally {
      setReviewSubmitting(false);
    }
  };

  const filtered = data.filter((d) =>
    d.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalChecks = data.reduce((s, d) => s + d.total, 0);
  const totalPasses = data.reduce((s, d) => s + d.passes, 0);
  const totalWarnings = data.reduce((s, d) => s + d.warnings, 0);
  const totalFails = data.reduce((s, d) => s + d.fails, 0);
  const totalCritical = data.reduce((s, d) => s + d.critical_count, 0);

  const filteredFindings =
    selectedDoc?.findings.filter((f) => {
      if (severityFilter !== 'all' && f.severity !== severityFilter) return false;
      if (statusFilter !== 'all' && f.status !== statusFilter) return false;
      return true;
    }) || [];

  const currentIndustry = industries.find((i) => i.id === selectedIndustry);

  return (
    <div className="h-full flex flex-col overflow-hidden p-6">
      {/* Header with industry selector */}
      <div className="flex items-center justify-between mb-4 shrink-0">
        <div>
          <h2 className="text-lg font-semibold text-white">Compliance</h2>
          <p className="text-xs text-dark-300">
            {hasRun
              ? `${data.length} documents analyzed · ${currentIndustry?.name || 'Generic'} rules`
              : `${documents.length} documents available`}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Industry selector */}
          <div className="relative">
            <button
              onClick={() => setShowIndustryDropdown(!showIndustryDropdown)}
              className="flex items-center gap-2 px-3 py-2 bg-dark-800 border border-dark-700 rounded-lg text-sm text-white hover:border-dark-600 transition-colors min-w-[180px]"
            >
              <Factory className="h-4 w-4 text-oracle-red" />
              <span className="flex-1 text-left">{currentIndustry?.name || 'Select Industry'}</span>
              <ChevronDown className="h-4 w-4 text-dark-400" />
            </button>

            {showIndustryDropdown && (
              <div className="absolute right-0 top-full mt-1 w-72 bg-dark-800 border border-dark-700 rounded-lg shadow-xl z-50 overflow-hidden">
                {industries.map((ind) => (
                  <button
                    key={ind.id}
                    onClick={() => {
                      setSelectedIndustry(ind.id);
                      setShowIndustryDropdown(false);
                    }}
                    className={`w-full text-left px-4 py-3 text-sm hover:bg-dark-700 transition-colors border-b border-dark-700/30 last:border-0 ${
                      selectedIndustry === ind.id
                        ? 'bg-oracle-red/10 text-oracle-red'
                        : 'text-white'
                    }`}
                  >
                    <div className="font-medium">{ind.name}</div>
                    <div className="text-xs text-dark-400 mt-0.5">
                      {ind.description} · {ind.rules_count} rules
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Refresh button */}
          <button
            onClick={runComplianceCheck}
            disabled={loading || documents.length === 0}
            className="flex items-center gap-2 px-3 py-2 bg-dark-800 border border-dark-700 text-white rounded-lg text-sm hover:border-dark-600 disabled:opacity-40 transition-colors"
            title="Refresh compliance checks"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4" />
            )}
          </button>
        </div>
      </div>

      {/* Summary cards */}
      {hasRun && (
        <div className="grid grid-cols-2 lg:grid-cols-6 gap-2 mb-3 shrink-0">
          {[
            { label: 'Total Checks', value: totalChecks, color: 'text-white' },
            { label: 'Pass', value: totalPasses, color: 'text-emerald-400' },
            { label: 'Warnings', value: totalWarnings, color: 'text-amber-400' },
            { label: 'Failures', value: totalFails, color: 'text-red-400' },
            { label: 'Critical', value: totalCritical, color: 'text-red-400' },
            {
              label: 'Avg Pass Rate',
              value: `${
                data.length > 0
                  ? Math.round(data.reduce((s, d) => s + d.pass_rate, 0) / data.length)
                  : 0
              }%`,
              color: 'text-emerald-400',
            },
          ].map(({ label, value, color }) => (
            <div
              key={label}
              className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-center"
            >
              <p className={`text-lg font-bold ${color}`}>{value}</p>
              <p className="text-xs text-dark-400">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Main content */}
      {!hasRun && !loading ? (
        <div className="flex-1 flex flex-col items-center justify-center text-dark-400">
          <Shield className="h-12 w-12 mb-4" />
          <p className="text-sm mb-2">
            {documents.length === 0 ? 'No completed documents available' : 'Loading compliance data...'}
          </p>
          <p className="text-xs">
            {documents.length} document{documents.length !== 1 ? 's' : ''} available for analysis
          </p>
        </div>
      ) : loading ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Loader2 className="h-8 w-8 text-oracle-red animate-spin" />
          <p className="text-dark-300 text-sm">
            Running {currentIndustry?.name || 'Generic'} compliance checks...
          </p>
        </div>
      ) : (
        <div className="flex-1 flex gap-3 overflow-hidden" style={{ minHeight: 0 }}>
          {/* Left: Document list */}
          <div className="w-80 shrink-0 bg-dark-800 border border-dark-700 rounded-lg flex flex-col overflow-hidden">
            {/* Search */}
            <div className="p-2 border-b border-dark-700">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-dark-400 h-3.5 w-3.5" />
                <input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search documents..."
                  className="w-full bg-dark-900 border border-dark-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-dark-400 focus:outline-none focus:border-oracle-red/50"
                />
              </div>
            </div>

            {/* Document list */}
            <div className="flex-1 overflow-y-auto" style={{ minHeight: 0 }}>
              {filtered.length === 0 ? (
                <p className="text-center text-dark-400 text-xs py-8">No documents found</p>
              ) : (
                filtered.map((doc) => (
                  <button
                    key={doc.document_id}
                      onClick={() => {
                        setSelectedDoc(doc);
                        setSeverityFilter('all');
                        setStatusFilter('all');
                        setReviewError('');
                      }}
                    className={`w-full text-left px-3 py-2.5 border-b border-dark-700/30 transition-colors ${
                      selectedDoc?.document_id === doc.document_id
                        ? 'bg-oracle-red/10 border-l-2 border-l-oracle-red'
                        : 'hover:bg-dark-700/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className="text-xs text-white truncate pr-2"
                        title={doc.filename}
                      >
                        {doc.filename.replace('.pdf', '')}
                      </span>
                      <span
                        className={`text-xs font-bold shrink-0 ${
                          doc.pass_rate >= 80
                            ? 'text-emerald-400'
                            : doc.pass_rate >= 50
                            ? 'text-amber-400'
                            : 'text-red-400'
                        }`}
                      >
                        {doc.pass_rate}%
                      </span>
                    </div>
                    <MiniBar
                      value={doc.passes}
                      max={doc.total}
                      color={
                        doc.pass_rate >= 80
                          ? '#34d399'
                          : doc.pass_rate >= 50
                          ? '#fbbf24'
                          : '#ef4444'
                      }
                    />
                    <div className="flex gap-2 mt-1 text-xs">
                      <span className="text-emerald-400">{doc.passes} pass</span>
                      <span className="text-amber-400">{doc.warnings} warn</span>
                      {doc.fails > 0 && <span className="text-red-400">{doc.fails} fail</span>}
                      {doc.critical_count > 0 && (
                        <span className="text-red-400">{doc.critical_count} critical</span>
                      )}
                    </div>
                    {doc.assessment_status !== 'completed' && (
                      <p className="mt-1 text-xs text-red-300 truncate" title={doc.error_message || undefined}>
                        {doc.error_message || 'Assessment could not be completed'}
                      </p>
                    )}
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Right: Selected document findings */}
          <div className="flex-1 bg-dark-800 border border-dark-700 rounded-lg flex flex-col overflow-hidden">
            {!selectedDoc ? (
              <div className="flex-1 flex flex-col items-center justify-center text-dark-400">
                <Shield className="h-8 w-8 mb-3" />
                <p className="text-sm">Select a document to view compliance details</p>
                <p className="text-xs mt-1">Documents are sorted by pass rate (lowest first)</p>
              </div>
            ) : (
              <>
                {/* Header */}
                <div className="px-4 py-3 border-b border-dark-700 shrink-0">
                  <div className="flex items-center justify-between mb-2">
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-white truncate">
                        {selectedDoc.filename}
                      </h3>
                      <p className="text-xs text-dark-400">
                        {selectedDoc.industry} · {selectedDoc.total} checks
                      </p>
                      <p className="text-xs text-dark-500 mt-0.5" title={selectedDoc.document_sha256 || undefined}>
                        Ruleset {selectedDoc.ruleset_version || 'legacy'}
                        {selectedDoc.assessed_at ? ` · assessed ${new Date(selectedDoc.assessed_at).toLocaleString()}` : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => setSelectedDoc(null)}
                      className="p-1 rounded hover:bg-dark-700 text-dark-400"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  {selectedDoc.assessment_status === 'completed' && (
                    <div className="mb-3 rounded-lg border border-dark-700 bg-dark-900/50 p-2.5">
                      <div className="flex items-center justify-between gap-3 mb-2">
                        <span className="text-xs font-medium text-white">Human review</span>
                        <span className={`text-xs capitalize ${
                          selectedDoc.review_status === 'approved'
                            ? 'text-emerald-400'
                            : selectedDoc.review_status === 'changes_requested'
                            ? 'text-amber-400'
                            : 'text-blue-300'
                        }`}>
                          {selectedDoc.review_status.replace('_', ' ')}
                        </span>
                      </div>
                      {selectedDoc.reviewed_by ? (
                        <p className="text-xs text-dark-300">
                          {selectedDoc.review_status.replace('_', ' ')} by {selectedDoc.reviewed_by}
                          {selectedDoc.reviewed_at ? ` · ${new Date(selectedDoc.reviewed_at).toLocaleString()}` : ''}
                          {selectedDoc.review_notes ? ` · ${selectedDoc.review_notes}` : ''}
                        </p>
                      ) : (
                        <div className="flex flex-col gap-2 sm:flex-row">
                          <input
                            value={reviewer}
                            onChange={(event) => setReviewer(event.target.value)}
                            placeholder="Accountable reviewer"
                            className="min-w-0 flex-1 rounded border border-dark-600 bg-dark-800 px-2 py-1.5 text-xs text-white placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-oracle-red/50"
                          />
                          <input
                            value={reviewNotes}
                            onChange={(event) => setReviewNotes(event.target.value)}
                            placeholder="Optional review note"
                            className="min-w-0 flex-1 rounded border border-dark-600 bg-dark-800 px-2 py-1.5 text-xs text-white placeholder-dark-500 focus:outline-none focus:ring-1 focus:ring-oracle-red/50"
                          />
                          <button onClick={() => recordReview('approved')} disabled={reviewSubmitting} className="rounded bg-emerald-500/20 px-2 py-1.5 text-xs text-emerald-300 hover:bg-emerald-500/30 disabled:opacity-50">Approve</button>
                          <button onClick={() => recordReview('changes_requested')} disabled={reviewSubmitting} className="rounded bg-amber-500/20 px-2 py-1.5 text-xs text-amber-300 hover:bg-amber-500/30 disabled:opacity-50">Request changes</button>
                        </div>
                      )}
                      {reviewError && <p className="mt-2 text-xs text-red-300">{reviewError}</p>}
                    </div>
                  )}

                  {/* Stats + Filters */}
                  <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex gap-1.5">
                      {[
                        { label: 'Pass', value: selectedDoc.passes, statusKey: 'pass', bgActive: 'bg-emerald-500/30 text-emerald-400 border border-emerald-500/30', bgInactive: 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20' },
                        { label: 'Warn', value: selectedDoc.warnings, statusKey: 'warning', bgActive: 'bg-amber-500/30 text-amber-400 border border-amber-500/30', bgInactive: 'bg-amber-500/10 text-amber-400 hover:bg-amber-500/20' },
                        { label: 'Review', value: selectedDoc.reviews, statusKey: 'review', bgActive: 'bg-blue-500/30 text-blue-400 border border-blue-500/30', bgInactive: 'bg-blue-500/10 text-blue-400 hover:bg-blue-500/20' },
                        { label: 'Fail', value: selectedDoc.fails, statusKey: 'fail', bgActive: 'bg-red-500/30 text-red-400 border border-red-500/30', bgInactive: 'bg-red-500/10 text-red-400 hover:bg-red-500/20' },
                      ].map(({ label, value, statusKey, bgActive, bgInactive }) => (
                        <button
                          key={label}
                          onClick={() =>
                            setStatusFilter(statusFilter === statusKey ? 'all' : statusKey)
                          }
                          className={`px-2 py-0.5 rounded text-xs font-medium transition-colors ${
                            statusFilter === statusKey ? bgActive : bgInactive
                          }`}
                        >
                          {value} {label}
                        </button>
                      ))}
                    </div>
                    <div className="w-px h-4 bg-dark-700" />
                    <div className="flex gap-1">
                      {['all', 'critical', 'high', 'medium', 'low'].map((sev) => (
                        <button
                          key={sev}
                          onClick={() => setSeverityFilter(sev)}
                          className={`px-1.5 py-0.5 rounded text-xs capitalize transition-colors ${
                            severityFilter === sev
                              ? 'bg-oracle-red/20 text-oracle-red border border-oracle-red/30'
                              : 'text-dark-400 hover:text-dark-200 hover:bg-dark-700'
                          }`}
                        >
                          {sev}
                        </button>
                      ))}
                    </div>
                    <span className="text-xs text-dark-400 ml-auto">
                      {filteredFindings.length} shown
                    </span>
                  </div>
                </div>

                {/* Findings list */}
                <div className="flex-1 overflow-y-auto p-2" style={{ minHeight: 0 }}>
                  <div className="space-y-1">
                    {filteredFindings.map((f, i) => (
                      <div
                        key={i}
                        className={`flex items-start gap-2 px-3 py-2 rounded-lg text-xs ${
                          f.status === 'pass'
                            ? 'bg-emerald-500/5'
                            : f.status === 'warning'
                            ? 'bg-amber-500/5'
                            : f.status === 'fail'
                            ? 'bg-red-500/10'
                            : 'bg-blue-500/5'
                        }`}
                      >
                        {f.status === 'pass' ? (
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-500 mt-0.5 shrink-0" />
                        ) : f.status === 'warning' ? (
                          <AlertTriangle className="h-3.5 w-3.5 text-amber-500 mt-0.5 shrink-0" />
                        ) : f.status === 'fail' ? (
                          <AlertTriangle className="h-3.5 w-3.5 text-red-500 mt-0.5 shrink-0" />
                        ) : (
                          <Search className="h-3.5 w-3.5 text-blue-500 mt-0.5 shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-dark-100 leading-relaxed">{f.message}</p>
                          {f.extracted_value && (
                            <p className="text-xs text-emerald-300 mt-1">Extracted: {f.extracted_value}</p>
                          )}
                          {f.evidence[0] && (
                            <div className="mt-1.5 rounded bg-dark-900/60 border border-dark-700 px-2 py-1.5 text-dark-300">
                              <p className="text-xs leading-relaxed">“{f.evidence[0].quote}”</p>
                              <p className="mt-1 text-[10px] text-dark-500">
                                {f.evidence[0].page ? `Page ${f.evidence[0].page}` : 'Text location unavailable'}
                                {f.evidence[0].section ? ` · ${f.evidence[0].section}` : ''}
                                {` · matched ${f.evidence[0].matched_text}`}
                              </p>
                            </div>
                          )}
                          <div className="flex gap-2 mt-0.5">
                            <span className="text-xs text-dark-400">{f.category}</span>
                            <span
                              className={`text-xs px-1 py-0.5 rounded ${
                                f.severity === 'critical'
                                  ? 'bg-red-500/20 text-red-400'
                                  : f.severity === 'high'
                                  ? 'bg-amber-500/20 text-amber-400'
                                  : f.severity === 'medium'
                                  ? 'bg-blue-500/20 text-blue-400'
                                  : 'bg-dark-600 text-dark-300'
                              }`}
                            >
                              {f.severity}
                            </span>
                            {f.rule_id && (
                              <span className="text-xs text-dark-500">{f.rule_id}</span>
                            )}
                            {f.requires_human_review && (
                              <span className="text-xs text-blue-300">human review</span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                    {filteredFindings.length === 0 && (
                      <p className="text-center text-dark-400 text-xs py-8">
                        No findings match the current filters
                      </p>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Compliance;
