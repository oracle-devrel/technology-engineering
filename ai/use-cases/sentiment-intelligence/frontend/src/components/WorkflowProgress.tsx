import React, { useEffect, useState } from 'react';

export interface WorkflowStep {
  step: string;
  status: 'pending' | 'running' | 'complete' | 'error';
  duration?: number;
  message?: string;
}

interface WorkflowProgressProps {
  steps: WorkflowStep[];
  visible: boolean;
}

const COLLAPSE_DELAY_MS = 1500;

const STEP_ICONS: Record<string, React.ReactNode> = {
  'Web Scout': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
    </svg>
  ),
  'Ingestion': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  ),
  'Sentiment Analysis': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  ),
  'Analytics': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  'Alert Detection': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  ),
  'Actions': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  ),
  'Complete': (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
};

function getStepIcon(stepName: string): React.ReactNode {
  for (const [key, icon] of Object.entries(STEP_ICONS)) {
    if (stepName.toLowerCase().includes(key.toLowerCase())) {
      return icon;
    }
  }
  return STEP_ICONS['Complete'];
}

export default function WorkflowProgress({ steps, visible }: WorkflowProgressProps) {
  const [expanded, setExpanded] = useState(true);

  const isAnalyzing = steps.some((s) => s.status === 'running');
  const allComplete =
    steps.length > 0 && steps.every((s) => s.status === 'complete');
  const hasError = steps.some((s) => s.status === 'error');
  const totalDuration = steps.reduce((acc, s) => acc + (s.duration ?? 0), 0);

  // Re-expand whenever a new run starts
  useEffect(() => {
    if (isAnalyzing) setExpanded(true);
  }, [isAnalyzing]);

  // Auto-collapse shortly after completion
  useEffect(() => {
    if (allComplete && !isAnalyzing) {
      const t = setTimeout(() => setExpanded(false), COLLAPSE_DELAY_MS);
      return () => clearTimeout(t);
    }
  }, [allComplete, isAnalyzing]);

  if (!visible || steps.length === 0) return null;

  // Collapsed pill once everything is done
  if (allComplete && !isAnalyzing && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="w-full glass-card px-4 py-2.5 flex items-center justify-between hover:bg-gray-50 transition-all animate-fade-in group"
      >
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-full bg-green-50 text-green-600 flex items-center justify-center ring-1 ring-green-200">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="text-left">
            <p className="text-xs font-semibold text-gray-900">Analysis complete</p>
            <p className="text-[10px] text-gray-400">
              All {steps.length} steps finished
              {totalDuration > 0 ? ` in ${totalDuration.toFixed(1)}s` : ''}
            </p>
          </div>
        </div>
        <span className="text-[10px] text-gray-400 group-hover:text-gray-700 flex items-center gap-1 uppercase tracking-wider">
          Show details
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </span>
      </button>
    );
  }

  return (
    <div className="glass-card p-6 animate-slide-in-up">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clipRule="evenodd" />
          </svg>
          Workflow Progress
        </h3>
        {allComplete && !isAnalyzing && !hasError && (
          <button
            onClick={() => setExpanded(false)}
            className="text-[10px] uppercase tracking-wider text-gray-400 hover:text-gray-700 flex items-center gap-1"
          >
            Collapse
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z" clipRule="evenodd" />
            </svg>
          </button>
        )}
      </div>

      {/* Horizontal Step Progress */}
      <div className="flex items-center justify-between overflow-x-auto pb-2">
        {steps.map((step, index) => (
          <div key={step.step} className="flex items-center flex-shrink-0">
            {/* Step Node */}
            <div className="flex flex-col items-center min-w-[80px]">
              {/* Circle */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300 ${
                  step.status === 'complete'
                    ? 'bg-green-50 text-green-600 ring-2 ring-green-200'
                    : step.status === 'running'
                    ? 'bg-accent/10 text-accent ring-2 ring-accent/30 animate-pulse-ring'
                    : step.status === 'error'
                    ? 'bg-red-50 text-red-600 ring-2 ring-red-200'
                    : 'bg-gray-100 text-gray-400 ring-1 ring-gray-200'
                }`}
              >
                {step.status === 'complete' ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : step.status === 'running' ? (
                  <svg className="w-5 h-5 animate-spin-slow" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                ) : step.status === 'error' ? (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                ) : (
                  getStepIcon(step.step)
                )}
              </div>

              {/* Label */}
              <span
                className={`text-[10px] font-medium mt-2 text-center leading-tight ${
                  step.status === 'complete'
                    ? 'text-green-600'
                    : step.status === 'running'
                    ? 'text-accent'
                    : step.status === 'error'
                    ? 'text-red-600'
                    : 'text-gray-400'
                }`}
              >
                {step.step}
              </span>

              {/* Duration / Message */}
              {step.status === 'complete' && step.duration !== undefined && (
                <span className="text-[9px] text-gray-400 mt-0.5">
                  {step.duration.toFixed(1)}s
                </span>
              )}
              {step.status === 'running' && step.message && (
                <span className="text-[9px] text-accent/70 mt-0.5 max-w-[80px] truncate text-center">
                  {step.message}
                </span>
              )}
              {step.status === 'error' && (
                <span className="text-[9px] text-red-500 mt-0.5">
                  Failed
                </span>
              )}
            </div>

            {/* Connector */}
            {index < steps.length - 1 && (
              <div
                className={`step-connector mx-1 ${
                  step.status === 'complete'
                    ? 'complete'
                    : step.status === 'running'
                    ? 'active'
                    : ''
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* Live Message Feed */}
      {steps.some((s) => s.status === 'running') && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          {steps
            .filter((s) => s.status === 'running' && s.message)
            .map((s) => (
              <p key={s.step} className="text-xs text-gray-500 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
                {s.message}
              </p>
            ))}
        </div>
      )}
    </div>
  );
}
