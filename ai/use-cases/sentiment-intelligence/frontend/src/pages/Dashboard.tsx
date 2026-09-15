import { useState, useEffect, useCallback, useRef } from 'react';
import { fetchDashboard, fetchHistory, runAnalysis } from '../services/api';
import type { DashboardData, HistoryData, ProgressEvent } from '../services/api';
import SentimentGauges from '../components/SentimentGauges';
import AlertFeed from '../components/AlertFeed';
import ActionPanel from '../components/ActionPanel';
import ChatPanel from '../components/ChatPanel';
import WorkflowProgress from '../components/WorkflowProgress';
import type { WorkflowStep } from '../components/WorkflowProgress';
import SourcesList from '../components/SourcesList';
import VolumeChart from '../components/VolumeChart';
import ScoreHistoryChart from '../components/ScoreHistoryChart';
import TopThemes from '../components/TopThemes';
import EmotionsList from '../components/EmotionsList';
import CampaignModal from '../components/CampaignModal';
import type { CampaignContext } from '../components/CampaignModal';
import AgentPipelineModal from '../components/AgentPipelineModal';

const DEFAULT_STEPS: WorkflowStep[] = [
  { step: 'Web Scout', status: 'pending' },
  { step: 'Ingestion', status: 'pending' },
  { step: 'Sentiment Analysis', status: 'pending' },
  { step: 'Analytics', status: 'pending' },
  { step: 'Actions', status: 'pending' },
  { step: 'Complete', status: 'pending' },
];

const QUICK_ANALYSES = [
  { label: 'Customer satisfaction', topic: 'customer satisfaction and experience', icon: 'heart' },
  { label: 'Product quality', topic: 'product quality and reliability', icon: 'star' },
  { label: 'Brand reputation', topic: 'overall brand reputation and perception', icon: 'shield' },
];

interface DashboardProps {
  onNavigate: (page: 'home' | 'dashboard' | 'agents') => void;
  onWorkflowUpdate: (steps: WorkflowStep[], isAnalyzing: boolean) => void;
}

export default function Dashboard({ onNavigate, onWorkflowUpdate }: DashboardProps) {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [historyData, setHistoryData] = useState<HistoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  const [analysisTopic, setAnalysisTopic] = useState('');
  const [analysisBrand, setAnalysisBrand] = useState('');
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [showAnalysisForm, setShowAnalysisForm] = useState(false);
  const [selectedBrand, setSelectedBrand] = useState('');
  const [showChat, setShowChat] = useState(false);
  const [showCampaign, setShowCampaign] = useState(false);
  const [campaignContext, setCampaignContext] = useState<CampaignContext | undefined>();
  const [showPipeline, setShowPipeline] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);

  // Load dashboard data — always pass brand explicitly to avoid stale closures
  const loadDashboard = useCallback(async (brandFilter: string = '') => {
    try {
      setLoading(true);
      setError(null);
      const brandParam = brandFilter || undefined;
      const [data, history] = await Promise.all([
        fetchDashboard(brandParam),
        fetchHistory(brandParam),
      ]);
      setDashboardData(data);
      setHistoryData(history);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Propagate workflow state to parent (for Agents page)
  useEffect(() => {
    onWorkflowUpdate(workflowSteps, isAnalyzing);
  }, [workflowSteps, isAnalyzing, onWorkflowUpdate]);

  // Map SSE step names to our workflow steps
  const mapStepName = (step: string): string => {
    const s = step.toLowerCase();
    if (s.includes('scout') || s.includes('scrape') || s.includes('web') || s.includes('search')) return 'Web Scout';
    if (s.includes('ingest') || s.includes('store') || s.includes('save')) return 'Ingestion';
    if (s.includes('sentiment') || s.includes('score') || s.includes('analyz')) return 'Sentiment Analysis';
    if (s.includes('alert') || s.includes('detect') || s.includes('analytic')) return 'Analytics';
    if (s.includes('action') || s.includes('recommend') || s.includes('propos')) return 'Actions';
    if (s.includes('complete') || s.includes('done') || s.includes('finish')) return 'Complete';
    return step;
  };

  // Handle progress events from analysis SSE
  const handleProgress = useCallback((event: ProgressEvent) => {
    switch (event.type) {
      case 'step_start': {
        const stepName = mapStepName(event.step || '');
        setWorkflowSteps((prev) => {
          const targetIdx = prev.findIndex((s) => s.step === stepName);
          return prev.map((s, i) => {
            if (i === targetIdx) {
              // Mark the current step as running
              return { ...s, status: 'running', message: event.message };
            }
            if (i < targetIdx && s.status !== 'complete') {
              // Auto-complete all prior steps that aren't already complete
              return { ...s, status: 'complete' };
            }
            return s;
          });
        });
        break;
      }
      case 'step_complete': {
        const stepName = mapStepName(event.step || '');
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.step === stepName
              ? { ...s, status: 'complete', duration: event.duration, message: event.message }
              : s
          )
        );
        break;
      }
      case 'step_warning':
      case 'sentiment_progress': {
        // Update running step message
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.status === 'running'
              ? { ...s, message: event.message }
              : s
          )
        );
        break;
      }
      case 'complete': {
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.step === 'Complete'
              ? { ...s, status: 'complete', duration: event.duration }
              : s.status === 'running'
              ? { ...s, status: 'complete' }
              : s
          )
        );
        setIsAnalyzing(false);
        // Auto-select the analyzed brand and refresh
        if (analysisBrand.trim()) {
          setSelectedBrand(analysisBrand.trim());
          loadDashboard(analysisBrand.trim());
        } else {
          loadDashboard();
        }
        // Auto-close pipeline modal after a delay so user sees "Complete" state
        setTimeout(() => setShowPipeline(false), 2500);
        break;
      }
      case 'error': {
        setWorkflowSteps((prev) =>
          prev.map((s) =>
            s.status === 'running'
              ? { ...s, status: 'error', message: event.error }
              : s
          )
        );
        setIsAnalyzing(false);
        break;
      }
      case 'ping':
        // Keep-alive, ignore
        break;
    }
  }, [loadDashboard, analysisBrand]);

  // Start analysis
  const startAnalysis = (topic: string) => {
    if (isAnalyzing) return;
    if (!analysisBrand.trim()) {
      setShowAnalysisForm(true);
      return;
    }

    setIsAnalyzing(true);
    setWorkflowSteps(DEFAULT_STEPS.map((s, i) => ({
      ...s,
      status: i === 0 ? 'running' as const : 'pending' as const,
      message: i === 0 ? 'Initializing web search...' : undefined,
    })));
    setShowAnalysisForm(false);
    setShowPipeline(true);

    const { cancel } = runAnalysis(topic, analysisBrand, useWebSearch, handleProgress);
    cancelRef.current = cancel;
  };

  // Cancel analysis
  const cancelAnalysis = () => {
    if (cancelRef.current) {
      cancelRef.current();
      cancelRef.current = null;
    }
    setIsAnalyzing(false);
    setWorkflowSteps((prev) =>
      prev.map((s) =>
        s.status === 'running' ? { ...s, status: 'error', message: 'Cancelled' } : s
      )
    );
  };

  return (
    <div className="min-h-screen bg-primary">
      {/* ── Header ── */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-gray-300 shadow-sm">
        <div className="h-1 bg-gradient-to-r from-accent via-orange-500 to-accent2" />
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-3">
              {/* Home */}
              <button
                onClick={() => onNavigate('home')}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all"
                title="Home"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
              {/* Logo / Brand */}
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shadow-sm">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900 tracking-tight">
                    Sentiment Intelligence
                  </h1>
                  <p className="text-[10px] text-gray-400 font-medium uppercase tracking-widest">
                    AI-Powered Brand Monitoring
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* Brand Filter */}
              {historyData && historyData.brands.length > 0 && (
                <div className="flex items-center gap-2">
                  <label className="text-[10px] uppercase tracking-wider text-gray-400 hidden sm:block">Brand</label>
                  <select
                    value={selectedBrand}
                    onChange={(e) => {
                      setSelectedBrand(e.target.value);
                      loadDashboard(e.target.value);
                    }}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-white text-gray-700 border border-gray-300 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all cursor-pointer appearance-none pr-7"
                    style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236B6B6B' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 8px center' }}
                  >
                    <option value="">All Brands</option>
                    {historyData.brands.map((b) => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Quick action buttons */}
              <div className="hidden md:flex items-center gap-2">
                {QUICK_ANALYSES.map((qa) => (
                  <button
                    key={qa.label}
                    onClick={() => {
                      if (!analysisBrand.trim()) {
                        setShowAnalysisForm(true);
                        setAnalysisTopic(qa.topic);
                        return;
                      }
                      startAnalysis(qa.topic);
                    }}
                    disabled={isAnalyzing}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-gray-50 text-gray-600 border border-gray-200 hover:bg-gray-100 hover:text-gray-900 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {qa.label}
                  </button>
                ))}
              </div>

              {/* Run Analysis Button */}
              {isAnalyzing ? (
                <button
                  onClick={cancelAnalysis}
                  className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 transition-all flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8 7a1 1 0 00-1 1v4a1 1 0 001 1h4a1 1 0 001-1V8a1 1 0 00-1-1H8z" clipRule="evenodd" />
                  </svg>
                  Cancel
                </button>
              ) : (
                <button
                  onClick={() => setShowAnalysisForm(!showAnalysisForm)}
                  className="px-4 py-2 rounded-lg text-sm font-semibold bg-accent text-white hover:bg-accent/90 transition-all shadow-md shadow-accent/20 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
                  </svg>
                  Run Analysis
                </button>
              )}

              {/* Campaign Generator Button */}
              <button
                onClick={() => { setCampaignContext(undefined); setShowCampaign(true); }}
                className="p-2 rounded-lg text-gray-400 hover:text-accent hover:bg-accent/5 transition-all"
                title="AI Campaign Studio"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </button>

              {/* Ask AI Button */}
              <button
                onClick={() => setShowChat(true)}
                className="p-2 rounded-lg text-gray-400 hover:text-accent hover:bg-accent/5 transition-all"
                title="Ask AI"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" clipRule="evenodd" />
                </svg>
              </button>

              {/* Agents Pipeline Button */}
              <button
                onClick={() => setShowPipeline((prev) => !prev)}
                className={`p-2 rounded-lg transition-all ${
                  showPipeline
                    ? 'text-accent bg-accent/5'
                    : 'text-gray-400 hover:text-gray-900 hover:bg-gray-100'
                }`}
                title="View Agent Pipeline"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>

              {/* Refresh */}
              <button
                onClick={() => loadDashboard(selectedBrand)}
                disabled={loading}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all disabled:opacity-40"
                title="Refresh dashboard"
              >
                <svg
                  className={`w-5 h-5 ${loading ? 'animate-spin-slow' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            </div>
          </div>

          {/* Analysis Form (expandable) */}
          {showAnalysisForm && (
            <div className="mt-4 p-4 rounded-lg bg-gray-50 border border-gray-200 animate-slide-in-up">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="flex-1">
                  <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                    Brand Name <span className="text-accent">*</span>
                  </label>
                  <input
                    type="text"
                    value={analysisBrand}
                    onChange={(e) => setAnalysisBrand(e.target.value)}
                    placeholder="e.g., Nike, Coca Cola, Apple"
                    className="w-full px-3 py-2 rounded-lg bg-white border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                  />
                </div>
                <div className="flex-1">
                  <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                    Topic <span className="text-gray-300">(optional)</span>
                  </label>
                  <input
                    type="text"
                    value={analysisTopic}
                    onChange={(e) => setAnalysisTopic(e.target.value)}
                    placeholder="customer sentiment (default)"
                    className="w-full px-3 py-2 rounded-lg bg-white border border-gray-300 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                  />
                </div>
                <div className="flex items-end gap-3">
                  <label className="flex items-center gap-2 cursor-pointer pb-2">
                    <input
                      type="checkbox"
                      checked={useWebSearch}
                      onChange={(e) => setUseWebSearch(e.target.checked)}
                      className="w-4 h-4 rounded border-gray-300 bg-white text-accent focus:ring-accent/30"
                    />
                    <span className="text-xs text-gray-500">Web search</span>
                  </label>
                  <button
                    onClick={() => startAnalysis(analysisTopic || 'customer sentiment')}
                    disabled={isAnalyzing || !analysisBrand.trim()}
                    className="px-5 py-2 rounded-lg text-sm font-semibold bg-accent text-white hover:bg-accent/90 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Start
                  </button>
                </div>
              </div>
              {/* Quick topics */}
              <div className="flex flex-wrap gap-2 mt-3 md:hidden">
                {QUICK_ANALYSES.map((qa) => (
                  <button
                    key={qa.label}
                    onClick={() => {
                      setAnalysisTopic(qa.topic);
                      if (analysisBrand.trim()) {
                        startAnalysis(qa.topic);
                      }
                    }}
                    className="px-2.5 py-1 rounded-full text-[10px] font-medium bg-white text-gray-500 border border-gray-200 hover:bg-gray-50 hover:text-gray-700 transition-all"
                  >
                    {qa.label}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </header>

      {/* ── Main Content ── */}
      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Error Banner */}
        {error && (
          <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 flex items-center gap-3 animate-fade-in">
            <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium">Connection Error</p>
              <p className="text-xs text-red-500 mt-0.5">{error}</p>
            </div>
            <button
              onClick={() => loadDashboard(selectedBrand)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-red-100 text-red-700 hover:bg-red-200 transition-all"
            >
              Retry
            </button>
          </div>
        )}

        {/* Workflow Progress (collapses to a thin pill once complete) */}
        <WorkflowProgress steps={workflowSteps} visible={isAnalyzing || workflowSteps.some((s) => s.status !== 'pending')} />

        {/* Row 1: Gauges (with key stats) + Sources */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <SentimentGauges
              data={dashboardData?.gauges ?? null}
              loading={loading}
              summary={{
                totalReviews: dashboardData?.gauges?.total,
                avgScore: dashboardData?.avg_score ?? null,
                topNegativeAspect:
                  dashboardData?.top_aspects?.find((a) => a.sentiment === 'Negative')?.aspect ?? null,
                topEmotion: dashboardData?.emotion_distribution?.[0]?.emotion ?? null,
              }}
            />
          </div>
          <div className="lg:col-span-1">
            <SourcesList
              sources={dashboardData?.sources ?? []}
              loading={loading}
            />
          </div>
        </div>

        {/* Row 2: Alerts + Actions (side-by-side, both need horizontal room) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <AlertFeed
            alerts={dashboardData?.alerts ?? []}
            loading={loading}
          />
          <ActionPanel
            actions={dashboardData?.actions ?? []}
            loading={loading}
            onGenerateCampaign={(actionText, category) => {
              setCampaignContext({ actionText, category });
              setShowCampaign(true);
            }}
          />
        </div>

        {/* Row 3: Themes + Emotions (qualitative signal from in-DB AI) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopThemes
            data={dashboardData?.top_aspects ?? []}
            loading={loading}
          />
          <EmotionsList
            data={dashboardData?.emotion_distribution ?? []}
            loading={loading}
          />
        </div>

        {/* Row 4: Historical Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <VolumeChart
            data={historyData?.volume_over_time ?? []}
            loading={loading}
          />
          <ScoreHistoryChart
            data={historyData?.score_history ?? []}
            loading={loading}
          />
        </div>

        {/* Footer */}
        <footer className="text-center py-6 border-t border-gray-200">
          <p className="text-[10px] text-gray-400 uppercase tracking-widest">
            Sentiment Intelligence &mdash; Powered by Oracle Cloud AI &amp; Select AI
          </p>
        </footer>
      </main>

      {/* Ask AI Modal */}
      <ChatPanel open={showChat} onClose={() => setShowChat(false)} />

      {/* Campaign Studio Modal */}
      <CampaignModal
        open={showCampaign}
        onClose={() => setShowCampaign(false)}
        brand={selectedBrand || analysisBrand}
        context={campaignContext}
      />

      {/* Agent Pipeline Modal */}
      <AgentPipelineModal
        open={showPipeline}
        onClose={() => setShowPipeline(false)}
        workflowSteps={workflowSteps}
        isAnalyzing={isAnalyzing}
      />
    </div>
  );
}
