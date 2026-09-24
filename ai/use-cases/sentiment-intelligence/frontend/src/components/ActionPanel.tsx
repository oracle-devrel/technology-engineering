import { useState } from 'react';
import type { Action } from '../services/api';

interface ActionPanelProps {
  actions: Action[];
  loading: boolean;
  onGenerateCampaign?: (actionText: string, category: string) => void;
}

function getPriorityConfig(priority: string) {
  switch (priority.toLowerCase()) {
    case 'critical':
      return {
        color: 'bg-red-50 text-red-700 border-red-200',
        dot: 'bg-red-500',
        tile: 'tile-critical',
        sortOrder: 0,
      };
    case 'high':
      return {
        color: 'bg-orange-50 text-orange-700 border-orange-200',
        dot: 'bg-orange-500',
        tile: 'tile-high',
        sortOrder: 1,
      };
    case 'medium':
      return {
        color: 'bg-blue-50 text-blue-700 border-blue-200',
        dot: 'bg-blue-500',
        tile: 'tile-medium',
        sortOrder: 2,
      };
    case 'low':
    default:
      return {
        color: 'bg-gray-50 text-gray-600 border-gray-200',
        dot: 'bg-gray-400',
        tile: 'tile-low',
        sortOrder: 3,
      };
  }
}

function getCategoryIcon(category: string) {
  switch (category.toLowerCase()) {
    case 'communication':
    case 'pr':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      );
    case 'compensation':
    case 'promotion':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'operations':
    case 'logistics':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      );
    case 'product':
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      );
    default:
      return (
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      );
  }
}

function ActionSkeleton() {
  return (
    <div className="p-4 rounded-lg bg-gray-50">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-16 h-5 rounded shimmer" />
        <div className="w-20 h-4 rounded shimmer" />
      </div>
      <div className="w-full h-4 rounded shimmer mb-2" />
      <div className="w-2/3 h-3 rounded shimmer" />
    </div>
  );
}

export default function ActionPanel({ actions, loading, onGenerateCampaign }: ActionPanelProps) {
  const [approvedIds, setApprovedIds] = useState<Set<number>>(new Set());

  const handleApprove = (id: number) => {
    setApprovedIds((prev) => {
      const next = new Set(prev);
      next.add(id);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
          </svg>
          Recommended Actions
        </h3>
        <div className="space-y-3">
          <ActionSkeleton />
          <ActionSkeleton />
          <ActionSkeleton />
        </div>
      </div>
    );
  }

  if (actions.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
          </svg>
          Recommended Actions
        </h3>
        <div className="flex items-center justify-center py-8 text-gray-400">
          <div className="text-center">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <p className="text-sm">No actions yet. Run an analysis to get recommendations.</p>
          </div>
        </div>
      </div>
    );
  }

  const sortedActions = [...actions].sort(
    (a, b) => getPriorityConfig(a.priority).sortOrder - getPriorityConfig(b.priority).sortOrder
  );

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
        </svg>
        Recommended Actions
        <span className="ml-auto text-xs font-normal text-gray-400">
          {actions.length} action{actions.length !== 1 ? 's' : ''}
        </span>
      </h3>
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {sortedActions.map((action, index) => {
          const priorityConfig = getPriorityConfig(action.priority);
          const isApproved = approvedIds.has(action.id);

          return (
            <div
              key={action.id}
              className={`p-4 ${priorityConfig.tile} rounded-r-lg hover:brightness-[0.98] transition-all animate-slide-in-up ${
                isApproved ? 'opacity-60' : ''
              }`}
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${priorityConfig.color}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${priorityConfig.dot}`} />
                      {action.priority}
                    </span>
                    {action.brand && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-accent/8 text-accent border border-accent/15">
                        {action.brand}
                      </span>
                    )}
                    {action.category && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium text-gray-500 bg-gray-100 border border-gray-200">
                        {getCategoryIcon(action.category)}
                        {action.category}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 leading-relaxed">{action.action_text}</p>
                  {action.impact && (
                    <p className="text-xs text-gray-400 mt-1.5">
                      <span className="font-medium text-gray-500">Impact:</span> {action.impact}
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-1.5 flex-shrink-0">
                  <button
                    onClick={() => handleApprove(action.id)}
                    disabled={isApproved}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isApproved
                        ? 'bg-green-50 text-green-600 cursor-default'
                        : 'bg-white text-gray-600 border border-gray-200 hover:bg-accent/5 hover:text-accent hover:border-accent/20 cursor-pointer'
                    }`}
                  >
                    {isApproved ? (
                      <span className="flex items-center gap-1">
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                        Approved
                      </span>
                    ) : (
                      'Approve'
                    )}
                  </button>
                  {onGenerateCampaign && (action.category === 'campaign' || action.category === 'engagement') && (
                    <button
                      onClick={() => onGenerateCampaign(action.action_text, action.category)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-accent/5 text-accent border border-accent/20 hover:bg-accent/10 transition-all flex items-center gap-1"
                    >
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      Campaign
                    </button>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
