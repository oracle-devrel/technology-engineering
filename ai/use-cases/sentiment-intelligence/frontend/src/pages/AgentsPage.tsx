import AgentFlowDiagram from '../components/AgentFlowDiagram';
import type { WorkflowStep } from '../components/WorkflowProgress';

interface AgentsPageProps {
  onNavigate: (page: 'home' | 'dashboard' | 'agents') => void;
  workflowSteps: WorkflowStep[];
  isAnalyzing: boolean;
}

export default function AgentsPage({ onNavigate, workflowSteps, isAnalyzing }: AgentsPageProps) {
  return (
    <div className="min-h-screen bg-primary">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => onNavigate('home')}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all"
                title="Home"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
              <button
                onClick={() => onNavigate('dashboard')}
                className="p-2 rounded-lg text-gray-400 hover:text-gray-900 hover:bg-gray-100 transition-all"
                title="Back to Dashboard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shadow-sm">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-lg font-bold text-gray-900 tracking-tight">
                    Agent Pipeline
                  </h1>
                  <p className="text-[10px] text-gray-400 font-medium uppercase tracking-widest">
                    Coordinated Analysis Workflow
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {isAnalyzing && (
                <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-accent/10 text-accent border border-accent/20 animate-pulse flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
                  Analysis Running
                </span>
              )}
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 hover:text-gray-900 transition-all shadow-sm"
              >
                Dashboard
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Description */}
        <div className="mb-8 text-center max-w-2xl mx-auto">
          <p className="text-sm text-gray-500 leading-relaxed">
            The analysis pipeline is a <span className="text-gray-900 font-medium">coordinated six-stage workflow</span> that
            searches, ingests, analyzes, and generates actionable insights from customer sentiment data.
            Each stage has a specific responsibility and passes its output to the next stage.
          </p>
        </div>

        <AgentFlowDiagram
          workflowSteps={workflowSteps}
          isAnalyzing={isAnalyzing}
        />

        {/* Footer */}
        <footer className="text-center py-8 mt-8 border-t border-gray-200">
          <p className="text-[10px] text-gray-400 uppercase tracking-widest">
            Sentiment Intelligence &mdash; Powered by Oracle Cloud AI &amp; Select AI
          </p>
        </footer>
      </main>
    </div>
  );
}
