import type { Alert } from '../services/api';

interface AlertFeedProps {
  alerts: Alert[];
  loading: boolean;
}

function getAlertConfig(alertType: string) {
  switch (alertType) {
    case 'spike_negative':
      return {
        icon: (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        ),
        badgeColor: 'bg-red-50 text-red-700 border-red-200',
        accentColor: 'border-l-red-500',
        label: 'Spike Detected',
      };
    case 'trending_positive':
      return {
        icon: (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clipRule="evenodd" />
          </svg>
        ),
        badgeColor: 'bg-green-50 text-green-700 border-green-200',
        accentColor: 'border-l-green-500',
        label: 'Trending Positive',
      };
    case 'emerging_topic':
      return {
        icon: (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path d="M11 3a1 1 0 10-2 0v1a1 1 0 102 0V3zM15.657 5.757a1 1 0 00-1.414-1.414l-.707.707a1 1 0 001.414 1.414l.707-.707zM18 10a1 1 0 01-1 1h-1a1 1 0 110-2h1a1 1 0 011 1zM5.05 6.464A1 1 0 106.464 5.05l-.707-.707a1 1 0 00-1.414 1.414l.707.707zM5 10a1 1 0 01-1 1H3a1 1 0 110-2h1a1 1 0 011 1zM8 16v-1h4v1a2 2 0 11-4 0zM12 14c.015-.34.208-.646.477-.859a4 4 0 10-4.954 0c.27.213.462.519.476.859h4.002z" />
          </svg>
        ),
        badgeColor: 'bg-blue-50 text-blue-700 border-blue-200',
        accentColor: 'border-l-blue-500',
        label: 'Emerging Topic',
      };
    default:
      return {
        icon: (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        ),
        badgeColor: 'bg-gray-50 text-gray-600 border-gray-200',
        accentColor: 'border-l-gray-400',
        label: alertType.replace(/_/g, ' '),
      };
  }
}

function getSeverityTileClass(severity?: string, alertType?: string): string {
  const sev = (severity || '').toLowerCase();
  if (sev === 'critical') return 'tile-critical';
  if (sev === 'warning') return 'tile-warning';
  if (sev === 'info') return 'tile-info';
  if (alertType === 'trending_positive') return 'tile-positive';
  return 'tile-neutral';
}

function formatTimeAgo(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  } catch {
    return dateStr;
  }
}

function AlertSkeleton() {
  return (
    <div className="p-4 border-l-4 border-l-gray-200 rounded-r-lg bg-gray-50">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-24 h-5 rounded shimmer" />
        <div className="w-16 h-4 rounded shimmer" />
      </div>
      <div className="w-3/4 h-4 rounded shimmer mb-2" />
      <div className="w-full h-3 rounded shimmer" />
    </div>
  );
}

export default function AlertFeed({ alerts, loading }: AlertFeedProps) {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
          </svg>
          AI Alert Feed
        </h3>
        <div className="space-y-3">
          <AlertSkeleton />
          <AlertSkeleton />
          <AlertSkeleton />
        </div>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
          </svg>
          AI Alert Feed
        </h3>
        <div className="flex items-center justify-center py-8 text-gray-400">
          <div className="text-center">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <p className="text-sm">No alerts yet. Run an analysis to detect trends.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10 2a6 6 0 00-6 6v3.586l-.707.707A1 1 0 004 14h12a1 1 0 00.707-1.707L16 11.586V8a6 6 0 00-6-6zM10 18a3 3 0 01-3-3h6a3 3 0 01-3 3z" />
        </svg>
        AI Alert Feed
        <span className="ml-auto text-xs font-normal text-gray-400">
          {alerts.length} alert{alerts.length !== 1 ? 's' : ''}
        </span>
      </h3>
      <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
        {alerts.map((alert, index) => {
          const config = getAlertConfig(alert.alert_type);
          const tileClass = getSeverityTileClass(alert.severity, alert.alert_type);
          return (
            <div
              key={alert.id}
              className={`p-4 ${tileClass} rounded-r-lg hover:brightness-[0.98] transition-all animate-slide-in-right`}
              style={{ animationDelay: `${index * 80}ms` }}
            >
              <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${config.badgeColor}`}>
                  {config.icon}
                  {config.label}
                </span>
                {alert.brand && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-accent/8 text-accent border border-accent/15">
                    {alert.brand}
                  </span>
                )}
                {alert.severity && (
                  <span className="text-[10px] font-medium uppercase tracking-wider text-gray-400">
                    {alert.severity}
                  </span>
                )}
                <span className="text-[10px] text-gray-400 ml-auto">
                  {formatTimeAgo(alert.detected_at)}
                </span>
              </div>
              <h4 className="text-sm font-semibold text-gray-900 mb-1">{alert.title}</h4>
              {alert.description && alert.description !== alert.title && (
                <p className="text-xs text-gray-500 leading-relaxed">{alert.description}</p>
              )}
              <div className="mt-2 flex items-center gap-3 text-[10px] text-gray-400">
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  {alert.source_count} source{alert.source_count !== 1 ? 's' : ''}
                </span>
                {alert.sources && (
                  <span className="text-gray-400 truncate max-w-[60%]">{alert.sources}</span>
                )}
              </div>
              {alert.sources_data && alert.sources_data.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-200">
                  <p className="text-[10px] uppercase tracking-wider text-gray-400 mb-1.5">
                    Contributing reviews
                  </p>
                  <ul className="space-y-1">
                    {alert.sources_data.slice(0, 5).map((src, i) => (
                      <li key={`${alert.id}-${i}`} className="text-xs">
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-accent2 hover:underline flex items-center gap-1.5 group"
                          title={src.url}
                        >
                          <svg className="w-3 h-3 flex-shrink-0 opacity-60 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                          <span className="font-medium text-gray-700 group-hover:text-accent2">{src.domain}</span>
                          <span className="text-gray-400 truncate flex-1 min-w-0">— {src.title}</span>
                          {typeof src.score === 'number' && (
                            <span className="text-[10px] text-red-600 font-medium flex-shrink-0">
                              {src.score.toFixed(2)}
                            </span>
                          )}
                        </a>
                      </li>
                    ))}
                    {alert.sources_data.length > 5 && (
                      <li className="text-[10px] text-gray-400 pl-[18px]">
                        +{alert.sources_data.length - 5} more
                      </li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
