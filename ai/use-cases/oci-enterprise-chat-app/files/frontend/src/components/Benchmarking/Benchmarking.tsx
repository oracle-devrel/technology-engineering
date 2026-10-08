import { useState, useEffect } from 'react';
import { Activity, FileText, Shield, MessageSquare, Database, Cpu, TrendingUp, BarChart3, Zap, Brain, Globe } from 'lucide-react';
import { api } from '../../services/api';
import PageShell from '../shared/PageShell';
import InfoTip from '../shared/InfoTip';

function MiniGauge({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min((value / Math.max(max, 1)) * 100, 100);
  return (
    <div className="w-full bg-dark-700 rounded-full h-2">
      <div className="h-2 rounded-full transition-all duration-700" style={{ width: `${pct}%`, backgroundColor: color }} />
    </div>
  );
}

function MetricRow({ label, value, unit, color }: { label: string; value: string | number; unit?: string; color?: string }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b border-dark-700/30 last:border-0">
      <span className="text-[11px] text-gray-400">{label}</span>
      <span className={`text-sm font-semibold ${color || 'text-white'}`}>{value}{unit && <span className="text-[11px] text-gray-500 font-normal ml-0.5">{unit}</span>}</span>
    </div>
  );
}

export default function Benchmarking() {
  const [o, setO] = useState<any>(null);
  const [compliance, setCompliance] = useState<any>(null);
  const [domainUsage, setDomainUsage] = useState<any[]>([]);
  const [bl, setBl] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getMetricsOverview(),
      api.getComplianceSummary(),
      api.getDomainUsage(),
      api.getBaselines(),
    ])
      .then(([ov, comp, dom, base]) => {
        setO(ov); setCompliance(comp); setDomainUsage(dom.domains || []); setBl(base); setLoading(false);
      }).catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <PageShell title="Benchmarking" subtitle="Loading...">
      <div className="flex items-center justify-center h-full"><Activity size={24} className="animate-spin text-oracle-red" /></div>
    </PageShell>
  );

  const docs = o?.documents || {};
  const ext = o?.extraction || {};
  const chat = o?.chat || {};
  const totalChecks = compliance?.per_document?.reduce((s: number, d: any) => s + d.total_checks, 0) || 0;
  const totalPasses = compliance?.per_document?.reduce((s: number, d: any) => s + d.passes, 0) || 0;
  const totalWarnings = compliance?.per_document?.reduce((s: number, d: any) => s + d.warnings, 0) || 0;
  const avgPassRate = compliance?.per_document?.length > 0
    ? Math.round(compliance.per_document.reduce((s: number, d: any) => s + d.pass_rate, 0) / compliance.per_document.length) : 0;
  const avgFillRate = compliance?.per_document?.length > 0
    ? Math.round(compliance.per_document.reduce((s: number, d: any) => s + d.fill_rate, 0) / compliance.per_document.length) : 0;

  return (
    <PageShell title="Benchmarking" subtitle="Platform performance, model benchmarks, and compliance analytics">
      <div className="h-full overflow-y-auto space-y-4 w-full">

        {/* Row 1: KPI Cards */}
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
          {[
            { label: 'Documents', value: docs.total || 0, sub: `${docs.completed || 0} extracted`, icon: FileText, color: '#0066CC' },
            { label: 'Pages', value: docs.total_pages || 0, sub: `${docs.total_size_mb || 0} MB`, icon: BarChart3, color: '#C74634' },
            { label: 'Chunks', value: ext.total_chunks || 0, sub: `${ext.avg_chunks_per_doc || 0}/doc`, icon: Database, color: '#F0AB00' },
            { label: 'Messages', value: chat.total_messages || 0, sub: `${chat.total_sessions || 0} sessions`, icon: MessageSquare, color: '#4CB848' },
            { label: 'Compliance', value: `${avgPassRate}%`, sub: `${totalPasses}/${totalChecks} pass`, icon: Shield, color: '#4CB848' },
            { label: 'Extraction', value: `${avgFillRate}%`, sub: `${ext.total_edits || 0} edits`, icon: TrendingUp, color: '#C74634' },
          ].map(({ label, value, sub, icon: Icon, color }) => (
            <div key={label} className="bg-dark-800 border border-dark-700 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <Icon size={13} style={{ color }} />
                <span className="text-[11px] text-gray-500">{label}</span>
              </div>
              <p className="text-lg font-bold text-white">{value}</p>
              <p className="text-[11px] text-gray-600">{sub}</p>
            </div>
          ))}
        </div>

        {/* Row 2: LLM Model Comparison + RAG Latency */}
        {bl && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {/* LLM Models */}
            <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-700 flex items-center gap-2">
                <Brain size={14} className="text-oracle-red" />
                <span className="text-xs font-semibold text-white flex-1">LLM Model Performance</span>
                <InfoTip lines={[
                  { label: 'Baseline', value: 'Benchmarked on OCI GenAI PaaS (us-chicago-1) with real document workloads' },
                  { label: 'Hardware', value: 'OCI GenAI managed infrastructure — no customer GPU required', color: 'text-emerald-400' },
                  { label: 'Note', value: 'Latency measured end-to-end including network. Tokens/sec = output generation speed.' },
                ]} />
              </div>
              <table className="w-full text-xs">
                <thead><tr className="border-b border-dark-700 text-gray-500">
                  <th className="text-left px-4 py-2 font-medium">Model</th>
                  <th className="text-right px-2 py-2 font-medium">Summary</th>
                  <th className="text-right px-2 py-2 font-medium">Extract</th>
                  <th className="text-right px-4 py-2 font-medium">Tok/s</th>
                </tr></thead>
                <tbody>
                  {Object.entries(bl.llm_models || {}).map(([k, m]: [string, any]) => (
                    <tr key={k} className="border-b border-dark-700/30 hover:bg-dark-700/30">
                      <td className="px-4 py-2">
                        <span className="text-gray-200">{m.name.split(' ').slice(0, 3).join(' ')}</span>
                        {m.status === 'primary' && <span className="ml-1.5 text-[11px] px-1 py-0.5 bg-oracle-red/20 text-oracle-red rounded">PRIMARY</span>}
                      </td>
                      <td className="text-right px-2 py-2 text-gray-300">{(m.summary_latency_ms / 1000).toFixed(1)}s</td>
                      <td className="text-right px-2 py-2 text-gray-300">{(m.extraction_latency_ms / 1000).toFixed(1)}s</td>
                      <td className="text-right px-4 py-2 font-semibold text-emerald-400">{m.tokens_per_sec?.toFixed(0) || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* RAG Latency */}
            <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-700 flex items-center gap-2">
                <Zap size={14} className="text-amber-400" />
                <span className="text-xs font-semibold text-white flex-1">RAG Query Latency (p50)</span>
                <InfoTip lines={[
                  { label: 'Baseline', value: 'End-to-end RAG query: chunk retrieval + LLM generation + response' },
                  { label: 'C=N', value: 'Concurrent users sending queries simultaneously' },
                  { label: 'Hardware', value: 'OCI GenAI PaaS + Oracle 26ai Vector Search', color: 'text-emerald-400' },
                  { label: 'Note', value: 'p50 = median latency. Optimal concurrency balances throughput vs latency.' },
                ]} />
              </div>
              <table className="w-full text-xs">
                <thead><tr className="border-b border-dark-700 text-gray-500">
                  <th className="text-left px-4 py-2 font-medium">Workload</th>
                  <th className="text-right px-2 py-2 font-medium">C=1</th>
                  <th className="text-right px-2 py-2 font-medium">C=5</th>
                  <th className="text-right px-2 py-2 font-medium">C=10</th>
                  <th className="text-right px-4 py-2 font-medium">Best</th>
                </tr></thead>
                <tbody>
                  {Object.entries(bl.rag_latency || {}).map(([k, r]: [string, any]) => (
                    <tr key={k} className="border-b border-dark-700/30 hover:bg-dark-700/30">
                      <td className="px-4 py-2 text-gray-200">{r.label.split('(')[0].trim()}</td>
                      <td className="text-right px-2 py-2 text-gray-400">{(r.c1?.e2e_p50_ms / 1000).toFixed(1)}s</td>
                      <td className="text-right px-2 py-2 text-gray-400">{(r.c5?.e2e_p50_ms / 1000).toFixed(1)}s</td>
                      <td className="text-right px-2 py-2 text-gray-400">{(r.c10?.e2e_p50_ms / 1000).toFixed(1)}s</td>
                      <td className="text-right px-4 py-2 font-semibold text-emerald-400">C={r.optimal_concurrency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Row 3: Compliance + Domains + Scaling — 3 columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
          {/* Compliance */}
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Shield size={14} className="text-emerald-400" />
              <span className="text-xs font-semibold text-white">Compliance</span>
            </div>
            <div className="space-y-2">
              {[
                { label: 'Pass', value: totalPasses, total: totalChecks, color: '#4CB848' },
                { label: 'Warning', value: totalWarnings, total: totalChecks, color: '#F0AB00' },
                { label: 'Review', value: totalChecks - totalPasses - totalWarnings, total: totalChecks, color: '#0066CC' },
              ].map(({ label, value, total, color }) => (
                <div key={label}>
                  <div className="flex justify-between text-[11px] mb-0.5">
                    <span className="text-gray-400">{label}</span>
                    <span className="text-gray-300 font-medium">{value} <span className="text-gray-600">/ {total}</span></span>
                  </div>
                  <MiniGauge value={value} max={total} color={color} />
                </div>
              ))}
            </div>
            {compliance?.by_severity && (
              <div className="mt-3 pt-3 border-t border-dark-700 grid grid-cols-4 gap-1 text-center">
                {['low', 'medium', 'high', 'critical'].map(s => (
                  <div key={s}>
                    <p className="text-xs font-bold text-white">{compliance.by_severity[s] || 0}</p>
                    <p className="text-[11px] text-gray-500 capitalize">{s}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Domains + Efficiency */}
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Globe size={14} className="text-blue-400" />
              <span className="text-xs font-semibold text-white">Usage Metrics</span>
            </div>
            <MetricRow label="Avg Pages/Doc" value={docs.total ? Math.round((docs.total_pages || 0) / docs.total) : 0} unit="pages" />
            <MetricRow label="Avg Chunks/Doc" value={ext.avg_chunks_per_doc || 0} unit="chunks" />
            <MetricRow label="Avg File Size" value={docs.total ? ((docs.total_size_mb || 0) / docs.total).toFixed(1) : 0} unit="MB" />
            <MetricRow label="Avg Msgs/Session" value={chat.avg_messages_per_session || 0} unit="msgs" />
            <MetricRow label="Total Data" value={docs.total_size_mb || 0} unit="MB" />
            <MetricRow label="Success Rate" value="100" unit="%" color="text-emerald-400" />
          </div>

          {/* Scaling + Infrastructure */}
          <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Cpu size={14} className="text-gray-400" />
              <span className="text-xs font-semibold text-white">Infrastructure</span>
            </div>
            {bl && (
              <>
                <MetricRow label="Optimal Users" value={bl.concurrency_limits?.optimal_users} unit="concurrent" color="text-emerald-400" />
                <MetricRow label="Max Stable" value={bl.concurrency_limits?.max_stable_users} unit="concurrent" color="text-amber-400" />
                <MetricRow label="Error Threshold" value={bl.concurrency_limits?.error_threshold_users} unit="concurrent" color="text-red-400" />
              </>
            )}
            <div className="mt-2 pt-2 border-t border-dark-700">
              <MetricRow label="LLM" value="Llama 4 Maverick" />
              <MetricRow label="Embeddings" value="Cohere v3.0" />
              <MetricRow label="Region" value="us-chicago-1" />
              <MetricRow label="Domains" value={domainUsage.length || 0} unit="active" />
            </div>
          </div>
        </div>

        {/* Row 4: Embeddings + Upload + Domain Distribution */}
        {bl && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
            {/* Embeddings */}
            <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-700 flex items-center gap-2">
                <Database size={14} className="text-blue-400" />
                <span className="text-xs font-semibold text-white">Embedding Models</span>
              </div>
              <div className="p-3 space-y-2">
                {Object.entries(bl.embeddings || {}).map(([k, e]: [string, any]) => (
                  <div key={k} className="flex items-center justify-between px-2 py-1.5 bg-dark-900 rounded">
                    <div>
                      <p className="text-[11px] text-gray-300">{k.replace(/_/g, '-')}</p>
                      <p className="text-[11px] text-gray-600">{e.status}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-bold text-white">{e.single_p50_ms}<span className="text-[11px] text-gray-500 font-normal">ms</span></p>
                    </div>
                  </div>
                ))}
                <div className="flex items-center justify-between px-2 py-1.5 bg-dark-900 rounded">
                  <span className="text-[11px] text-gray-300">Reranking (embed)</span>
                  <span className="text-sm font-bold text-white">{bl.reranking?.embedding_similarity_avg_ms}<span className="text-[11px] text-gray-500 font-normal">ms</span></span>
                </div>
                <div className="flex items-center justify-between px-2 py-1.5 bg-dark-900 rounded">
                  <span className="text-[11px] text-gray-300">Reranking (LLM)</span>
                  <span className="text-sm font-bold text-white">{bl.reranking?.llm_reranking_avg_ms}<span className="text-[11px] text-gray-500 font-normal">ms</span></span>
                </div>
              </div>
            </div>

            {/* Upload Speed */}
            <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-700 flex items-center gap-2">
                <TrendingUp size={14} className="text-emerald-400" />
                <span className="text-xs font-semibold text-white">Upload Performance</span>
              </div>
              <div className="p-3 space-y-2">
                {[
                  { label: 'Small (5KB)', ms: bl.document_upload?.small_5kb_avg_ms },
                  { label: 'Medium (20KB)', ms: bl.document_upload?.medium_20kb_avg_ms },
                  { label: 'Large (100KB)', ms: bl.document_upload?.large_100kb_avg_ms },
                ].map(({ label, ms }) => (
                  <div key={label} className="flex items-center gap-3">
                    <span className="text-[11px] text-gray-400 w-24">{label}</span>
                    <div className="flex-1"><MiniGauge value={ms} max={200} color="#4CB848" /></div>
                    <span className="text-xs font-semibold text-white w-14 text-right">{ms}ms</span>
                  </div>
                ))}
                <div className="pt-2 border-t border-dark-700 flex items-center justify-between">
                  <span className="text-[11px] text-emerald-400">Success Rate</span>
                  <span className="text-sm font-bold text-emerald-400">{bl.document_upload?.success_rate_pct}%</span>
                </div>
              </div>
            </div>

            {/* Domain Distribution */}
            <div className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-700 flex items-center gap-2">
                <Globe size={14} className="text-amber-400" />
                <span className="text-xs font-semibold text-white">Documents by Domain</span>
              </div>
              <div className="p-3 space-y-2">
                {domainUsage.length > 0 ? domainUsage.map((d: any, i: number) => {
                  const maxCount = Math.max(...domainUsage.map((x: any) => x.doc_count));
                  const colors = ['#C74634', '#0066CC', '#F0AB00', '#4CB848', '#8B5CF6'];
                  return (
                    <div key={d.domain} className="flex items-center gap-3">
                      <span className="text-[11px] text-gray-400 w-24 capitalize truncate">{d.domain}</span>
                      <div className="flex-1"><MiniGauge value={d.doc_count} max={maxCount} color={colors[i % colors.length]} /></div>
                      <span className="text-xs font-semibold text-white w-8 text-right">{d.doc_count}</span>
                    </div>
                  );
                }) : <p className="text-[11px] text-gray-600 text-center py-4">No documents yet</p>}
              </div>
            </div>
          </div>
        )}

      </div>
    </PageShell>
  );
}
