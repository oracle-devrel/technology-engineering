import { useEffect } from 'react';
import AgentFlowDiagram from './AgentFlowDiagram';
import type { WorkflowStep } from './WorkflowProgress';

interface AgentPipelineModalProps {
  open: boolean;
  onClose: () => void;
  workflowSteps: WorkflowStep[];
  isAnalyzing: boolean;
}

export default function AgentPipelineModal({
  open,
  onClose,
  workflowSteps,
  isAnalyzing,
}: AgentPipelineModalProps) {
  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [open, onClose]);

  if (!open) return null;

  const allComplete =
    workflowSteps.length > 0 &&
    workflowSteps.every((s) => s.status === 'complete');
  const hasError = workflowSteps.some((s) => s.status === 'error');

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative w-full max-w-6xl bg-white rounded-xl border border-gray-200 p-6 animate-fade-in shadow-xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-accent flex items-center justify-center shadow-sm">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider">
                Agent Pipeline
              </h3>
              <p className="text-[10px] text-gray-400 font-medium uppercase tracking-widest">
                Coordinated Analysis Workflow
              </p>
            </div>

            {/* Status badge */}
            {isAnalyzing && (
              <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-accent/10 text-accent border border-accent/20 animate-pulse flex items-center gap-2 ml-3">
                <span className="w-2 h-2 rounded-full bg-accent animate-ping" />
                Analysis Running
              </span>
            )}
            {allComplete && !isAnalyzing && (
              <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-green-50 text-green-600 border border-green-200 flex items-center gap-2 ml-3">
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                Analysis Complete
              </span>
            )}
            {hasError && !isAnalyzing && !allComplete && (
              <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-red-50 text-red-600 border border-red-200 flex items-center gap-2 ml-3">
                Error Occurred
              </span>
            )}
          </div>

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

        {/* Description */}
        <div className="mb-6 text-center max-w-2xl mx-auto">
          <p className="text-sm text-gray-500 leading-relaxed">
            The analysis pipeline is a{' '}
            <span className="text-gray-900 font-medium">coordinated six-stage workflow</span>{' '}
            that searches, ingests, analyzes, and generates actionable insights
            from customer sentiment data.
          </p>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <AgentFlowDiagram
            workflowSteps={workflowSteps}
            isAnalyzing={isAnalyzing}
          />
        </div>
      </div>
    </div>
  );
}
