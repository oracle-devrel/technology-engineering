import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  FolderOpen,
  FileText,
  Link2,
  TrendingUp,
  ArrowRight,
  Upload,
  CheckCircle,
  Clock,
  AlertCircle,
  Activity,
  Zap,
  MessageSquare,
  Database,
  GitBranch,
  Cloud,
  Brain,
  Layers,
  Server,
  Cpu,
  ChevronRight,
  Shield,
  Settings,
} from 'lucide-react';
import { api } from '../../services/api';
import { User, Project, Document, RAGHealthResponse, BatchJob, Workflow } from '../../types';

interface DashboardProps {
  user: User;
  projects: Project[];
  onProjectSelect: (project: Project) => void;
  onNavigateProjects: () => void;
  showWelcome?: boolean;
  onWelcomeDismissed?: () => void;
}

// --- Mini Progress Bar ---
function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  return (
    <div className="w-full bg-dark-500 rounded-full h-1">
      <div
        className="h-1 rounded-full transition-all"
        style={{ width: `${(value / Math.max(max, 1)) * 100}%`, backgroundColor: color }}
      />
    </div>
  );
}

// --- Helpers ---
function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// --- Welcome Toast ---
const WelcomeToast: React.FC<{ userName: string; onClose: () => void }> = ({ userName, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 animate-fade-in">
      <div className="flex items-center gap-3 px-6 py-3.5 bg-dark-700 border border-oracle-red/40 rounded-xl shadow-lg">
        <div className="w-8 h-8 rounded-full bg-oracle-red/20 flex items-center justify-center flex-shrink-0">
          <CheckCircle className="w-4 h-4 text-oracle-red" />
        </div>
        <span className="text-white text-sm font-medium">Welcome back, {userName}!</span>
        <button onClick={onClose} className="ml-2 text-dark-400 hover:text-white transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

// === Main Dashboard ===
const Dashboard: React.FC<DashboardProps> = ({
  user,
  projects,
  onProjectSelect,
  onNavigateProjects,
  showWelcome,
  onWelcomeDismissed,
}) => {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(true);
  const [ragHealth, setRagHealth] = useState<RAGHealthResponse | null>(null);
  const [batchJobs, setBatchJobs] = useState<BatchJob[]>([]);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  useEffect(() => {
    setIsLoadingDocs(true);
    Promise.all([
      api.listDocuments().catch(() => []),
      api.checkRAGHealth().catch(() => null),
      api.listBatchJobs().catch(() => []),
      api.listWorkflows().catch(() => []),
    ]).then(([docs, health, jobs, wfs]) => {
      setDocuments(docs as Document[]);
      setRagHealth(health as RAGHealthResponse | null);
      setBatchJobs(jobs as BatchJob[]);
      setWorkflows(wfs as Workflow[]);
      setIsLoadingDocs(false);
    });
  }, []);

  // Compute stats
  const totalDocs = projects.reduce((sum, p) => sum + p.document_ids.length, 0);
  const totalUrls = projects.reduce((sum, p) => sum + p.web_sources.length, 0);
  const completedDocs = documents.filter((d) => d.status === 'completed').length;
  const processingDocs = documents.filter((d) => d.status === 'processing').length;

  const inferenceModel = localStorage.getItem('selectedInferenceModel') || 'Not configured';
  const shortModelName = inferenceModel.includes('/')
    ? inferenceModel.split('/').pop() || inferenceModel
    : inferenceModel;

  // Activity feed
  const activityFeed = documents
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 5);

  const recentProjects = projects.slice(0, 4);

  // Quick nav items
  const navItems = [
    { icon: FolderOpen, label: 'Projects', desc: `${projects.length} active`, detail: 'View and manage your projects, upload documents, and organize web sources for RAG-powered chat.', color: '#C74634', to: '/projects' },
    { icon: FileText, label: 'Documents', desc: `${totalDocs} indexed`, detail: 'Browse, search, and manage all uploaded documents. View extraction results and edit fields inline.', color: '#0066CC', to: '/documents' },
    { icon: MessageSquare, label: 'Chat', desc: 'RAG-powered Q&A', detail: 'Ask natural language questions about your documents. AI retrieves relevant chunks and generates cited answers.', color: '#4CB848', to: '/chat' },
    { icon: Database, label: 'Batch', desc: `${batchJobs.length} jobs`, detail: 'Connect OCI Object Storage buckets for bulk document sync. Set up triggers for automated batch processing.', color: '#06B6D4', to: '/batch' },
    { icon: GitBranch, label: 'Workflows', desc: `${workflows.length} saved`, detail: 'Build and execute multi-step AI workflows with drag-and-drop nodes. Chain data sources, agents, and outputs.', color: '#8B5CF6', to: '/workflows' },
  ];

  return (
    <div className="flex-1 overflow-auto bg-dark-900">
      {/* Welcome toast */}
      {showWelcome && onWelcomeDismissed && (
        <WelcomeToast userName={user.full_name} onClose={onWelcomeDismissed} />
      )}

      <div className="h-full overflow-y-auto space-y-4 w-full p-6">

        {/* Welcome + API Status Row */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white">Welcome back, {user.full_name}</h2>
            <p className="text-xs text-dark-400 mt-0.5">
              AI-powered document intelligence across {projects.length} project{projects.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="flex gap-2 shrink-0">
            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
              <div className={`w-1.5 h-1.5 rounded-full ${ragHealth?.status === 'healthy' ? 'bg-emerald-400 animate-pulse' : ragHealth ? 'bg-red-400' : 'bg-dark-400 animate-pulse'}`} />
              <span className={`text-[11px] ${ragHealth?.status === 'healthy' ? 'text-emerald-400' : ragHealth ? 'text-red-400' : 'text-dark-400'}`}>
                {ragHealth?.status === 'healthy' ? 'API Connected' : ragHealth ? 'API Offline' : 'Checking...'}
              </span>
            </div>
          </div>
        </div>

        {/* Platform Overview + Infrastructure */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {/* Platform Overview */}
          <div className="bg-dark-card border border-dark-border rounded-lg p-5">
            <div className="flex items-center gap-2.5 mb-3">
              <Cloud size={18} className="text-oracle-red" />
              <span className="text-sm font-semibold text-white">Platform Overview</span>
            </div>
            <p className="text-sm text-dark-300 leading-relaxed mb-3">
              AI-Q Enterprise Chat — AI-powered document intelligence with RAG-powered conversational search.
              Upload documents, build a vector index, and get cited answers.
            </p>
            <div className="space-y-2">
              {[
                { label: 'Document Extraction', desc: 'PDF text, tables, images with AI field detection' },
                { label: 'RAG Chat', desc: 'Document-grounded Q&A with cited sources' },
                { label: 'Batch Processing', desc: 'OCI Object Storage sync with automated triggers' },
                { label: 'Workflows', desc: 'Multi-step AI pipelines with drag-and-drop builder' },
              ].map(({ label, desc }) => (
                <div key={label} className="flex gap-2 items-start">
                  <ChevronRight size={11} className="text-oracle-red mt-0.5 shrink-0" />
                  <span className="text-xs text-dark-200">{label} <span className="text-dark-400">— {desc}</span></span>
                </div>
              ))}
            </div>
          </div>

          {/* Infrastructure & Models */}
          <div className="bg-dark-card border border-dark-border rounded-lg p-5">
            <div className="flex items-center gap-2.5 mb-3">
              <Server size={18} className="text-oci-blue" />
              <span className="text-sm font-semibold text-white">Infrastructure & Models</span>
            </div>
            <div className="space-y-2">
              {[
                { icon: Brain, label: 'LLM', value: shortModelName || 'Not configured', color: '#76B900' },
                { icon: Cloud, label: 'Hosting', value: 'OCI GenAI Service (PaaS)', color: '#C74634' },
                { icon: Layers, label: 'Embeddings', value: 'Cohere embed-multilingual-v3.0', color: '#0066CC' },
                { icon: Database, label: 'Database', value: 'Oracle Autonomous DB + Vector Search', color: '#F0AB00' },
                { icon: Server, label: 'Compute', value: 'OKE (Oracle Kubernetes Engine)', color: '#8B5CF6' },
                { icon: Shield, label: 'Status', value: ragHealth?.status === 'healthy' ? 'All systems operational' : 'Checking...', color: '#4CB848' },
              ].map(({ icon: Icon, label, value, color }) => (
                <div key={label} className="flex items-center gap-3 py-1.5 border-b border-dark-border/20 last:border-0">
                  <Icon size={14} style={{ color }} />
                  <span className="text-xs text-dark-400 w-20 shrink-0">{label}</span>
                  <span className="text-xs text-dark-200">{value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-3 lg:grid-cols-6 gap-2">
          {[
            { label: 'Projects', value: projects.length, icon: FolderOpen, color: '#C74634', sub: `${projects.length} active` },
            { label: 'Documents', value: totalDocs, icon: FileText, color: '#0066CC', sub: `${completedDocs} completed` },
            { label: 'Web Sources', value: totalUrls, icon: Link2, color: '#F0AB00', sub: 'indexed urls' },
            { label: 'AI Service', value: ragHealth?.status === 'healthy' ? 'Online' : '...', icon: Zap, color: ragHealth?.status === 'healthy' ? '#4CB848' : '#F0AB00', sub: ragHealth?.status === 'healthy' ? 'Operational' : 'Checking' },
            { label: 'Batch Jobs', value: batchJobs.length, icon: Database, color: '#06B6D4', sub: `${batchJobs.filter(j => j.status === 'completed').length} completed` },
            { label: 'Workflows', value: workflows.length, icon: GitBranch, color: '#8B5CF6', sub: 'saved' },
          ].map(({ label, value, icon: Icon, color, sub }) => (
            <div key={label} className="bg-dark-card border border-dark-border rounded-lg p-2.5">
              <div className="flex items-center gap-1.5 mb-1">
                <Icon size={12} style={{ color }} />
                <span className="text-[11px] text-dark-400 uppercase tracking-wider">{label}</span>
              </div>
              <p className="text-lg font-bold text-white leading-none">{value}</p>
              <p className="text-[11px] text-dark-400 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>

        {/* Quick Navigation */}
        <div className="grid grid-cols-3 lg:grid-cols-5 gap-2">
          {navItems.map(({ icon: Icon, label, desc, detail, color, to }) => (
            <div key={label} className="relative">
              <button
                onClick={() => navigate(to)}
                onMouseEnter={() => setActiveTooltip(label)}
                onMouseLeave={() => setActiveTooltip(null)}
                className="w-full bg-dark-card border border-dark-border rounded-lg p-3 text-center hover:border-oracle-red/30 transition-colors group"
              >
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center mx-auto mb-1.5 group-hover:scale-110 transition-transform"
                  style={{ backgroundColor: color + '1A' }}
                >
                  <Icon size={16} style={{ color }} />
                </div>
                <p className="text-xs text-white font-medium">{label}</p>
                <p className="text-[11px] text-dark-400">{desc}</p>
              </button>
              {activeTooltip === label && (
                <div className="absolute z-30 top-full mt-1 left-1/2 -translate-x-1/2 w-56 bg-dark-card border border-dark-border rounded-lg shadow-xl p-3 pointer-events-none">
                  <div className="flex items-center gap-2 mb-1.5">
                    <Icon size={12} style={{ color }} />
                    <span className="text-[11px] text-white font-semibold">{label}</span>
                  </div>
                  <p className="text-[11px] text-dark-300 leading-relaxed">{detail}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Two Columns: Recent Projects + Activity / System Health */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">

          {/* Recent Projects */}
          <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
            <div className="px-4 py-2.5 border-b border-dark-border flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock size={13} className="text-dark-300" />
                <span className="text-xs font-semibold text-white">Recent Projects</span>
              </div>
              <button onClick={onNavigateProjects} className="text-[11px] text-oracle-red hover:underline flex items-center gap-0.5">
                View all <ChevronRight size={10} />
              </button>
            </div>
            <div>
              {recentProjects.length === 0 ? (
                <div className="text-center py-8">
                  <FolderOpen className="h-8 w-8 text-dark-500 mx-auto mb-2" />
                  <p className="text-dark-400 text-xs mb-3">No projects yet</p>
                  <Link
                    to="/projects"
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-oracle-red hover:bg-oracle-red-dark text-white text-xs font-medium rounded-lg transition-colors"
                  >
                    <FolderOpen size={12} />
                    Create Project
                  </Link>
                </div>
              ) : (
                recentProjects.map((project) => (
                  <button
                    key={project.id}
                    onClick={() => onProjectSelect(project)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-dark-hover/50 transition-colors border-b border-dark-border/30 last:border-0 text-left"
                  >
                    <div className="w-8 h-8 rounded-lg bg-oracle-red/10 flex items-center justify-center shrink-0">
                      <FolderOpen size={14} className="text-oracle-red" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-white font-medium truncate">{project.name}</p>
                      <p className="text-[11px] text-dark-400">
                        {project.document_ids.length} doc{project.document_ids.length !== 1 ? 's' : ''} · {project.web_sources.length} url{project.web_sources.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <span className="text-[11px] text-dark-400">{getTimeAgo(new Date(project.updated_at))}</span>
                      <ArrowRight size={10} className="text-dark-500" />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>

          {/* Activity + System Health */}
          <div className="space-y-3">
            {/* Recent Activity */}
            <div className="bg-dark-card border border-dark-border rounded-lg overflow-hidden">
              <div className="px-4 py-2.5 border-b border-dark-border flex items-center gap-2">
                <Activity size={13} className="text-dark-300" />
                <span className="text-xs font-semibold text-white">Recent Activity</span>
              </div>
              <div className="px-4 py-2">
                {isLoadingDocs ? (
                  <div className="flex items-center gap-2 text-xs text-dark-400 py-3">
                    <svg className="animate-spin h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Loading...
                  </div>
                ) : activityFeed.length === 0 ? (
                  <p className="text-center text-dark-400 text-xs py-4">No recent activity</p>
                ) : (
                  activityFeed.map((doc) => {
                    const statusIcon = doc.status === 'completed'
                      ? <CheckCircle size={11} className="text-emerald-500" />
                      : doc.status === 'processing'
                      ? <Clock size={11} className="text-amber-400 animate-spin" />
                      : doc.status === 'failed'
                      ? <AlertCircle size={11} className="text-red-400" />
                      : <Upload size={11} className="text-oracle-red" />;

                    return (
                      <div key={doc.id} className="flex items-center gap-2.5 py-1.5 border-b border-dark-border/20 last:border-0">
                        <div className="w-6 h-6 rounded-full bg-dark-600 flex items-center justify-center shrink-0">
                          {statusIcon}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] text-white truncate">{doc.metadata.filename}</p>
                        </div>
                        <span className="text-[11px] text-dark-400 shrink-0">{getTimeAgo(new Date(doc.updated_at))}</span>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* System Health */}
            <div className="bg-dark-card border border-dark-border rounded-lg p-4">
              <h3 className="text-[11px] text-dark-400 uppercase tracking-wider font-medium mb-3">System Health</h3>
              <div className="space-y-3">
                {/* Processing Queue */}
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-dark-300">Processing Queue</span>
                    <span className="text-white font-medium">{processingDocs} doc{processingDocs !== 1 ? 's' : ''}</span>
                  </div>
                  <MiniBar value={processingDocs} max={Math.max(documents.length, 1)} color="#C74634" />
                </div>

                {/* AI Service */}
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-dark-300">AI Service</span>
                    <span className={`font-medium ${
                      ragHealth?.status === 'healthy' ? 'text-emerald-400'
                      : ragHealth ? 'text-red-400'
                      : 'text-dark-400'
                    }`}>
                      {ragHealth?.status === 'healthy' ? 'Operational' : ragHealth ? 'Unavailable' : 'Checking...'}
                    </span>
                  </div>
                  <MiniBar
                    value={ragHealth?.status === 'healthy' ? 100 : ragHealth ? 0 : 50}
                    max={100}
                    color={ragHealth?.status === 'healthy' ? '#4CB848' : ragHealth ? '#EF4444' : '#4A5568'}
                  />
                </div>

                {/* Inference Model */}
                <div>
                  <div className="text-[11px] text-dark-300 mb-1">Inference Model</div>
                  <p className="text-[11px] text-dark-300 bg-dark-600 rounded-md px-2 py-1 font-mono truncate">
                    {shortModelName}
                  </p>
                </div>

                {/* Extraction Success */}
                <div>
                  <div className="flex items-center justify-between text-[11px] mb-1">
                    <span className="text-dark-300">Extraction Success</span>
                    <span className="text-white font-medium">
                      {documents.length > 0 ? `${Math.round((completedDocs / documents.length) * 100)}%` : 'N/A'}
                    </span>
                  </div>
                  <MiniBar value={completedDocs} max={Math.max(documents.length, 1)} color="#0066CC" />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Infrastructure Bar */}
        <div className="bg-dark-card border border-dark-border rounded-lg px-4 py-2.5 flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Cpu size={13} className="text-dark-400" />
            <span className="text-[11px] text-dark-400">Infrastructure</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-dark-400">
            <span>LLM: <span className="text-dark-200">{shortModelName}</span></span>
            <span>Embeddings: <span className="text-dark-200">Cohere v3.0</span></span>
            <span>Service: <span className="text-dark-200">{ragHealth?.status === 'healthy' ? 'Operational' : '...'}</span></span>
            <span>Projects: <span className="text-dark-200">{projects.length}</span></span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
