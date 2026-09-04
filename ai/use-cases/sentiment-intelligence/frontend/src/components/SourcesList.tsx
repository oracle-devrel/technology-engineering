import type { SourceInfo } from '../services/api';

interface SourcesListProps {
  sources: SourceInfo[];
  loading: boolean;
}

function getSourceConfig(source: string) {
  const s = source.toLowerCase();
  if (s.includes('amazon') || s.includes('product') || s.includes('review')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
        </svg>
      ),
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
    };
  }
  if (s.includes('twitter') || s.includes('social') || s.includes('x.com')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      ),
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    };
  }
  if (s.includes('forum') || s.includes('reddit')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
        </svg>
      ),
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    };
  }
  if (s.includes('news') || s.includes('press')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      ),
      color: 'text-gray-600',
      bgColor: 'bg-gray-50',
    };
  }
  if (s.includes('google') || s.includes('play')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      ),
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
    };
  }
  if (s.includes('trustpilot')) {
    return {
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    };
  }
  return {
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50',
  };
}

function SourceSkeleton() {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-gray-50">
      <div className="w-10 h-10 rounded-lg shimmer" />
      <div className="flex-1">
        <div className="w-24 h-4 rounded shimmer mb-1" />
        <div className="w-16 h-3 rounded shimmer" />
      </div>
    </div>
  );
}

export default function SourcesList({ sources, loading }: SourcesListProps) {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          Monitored Sources
        </h3>
        <div className="space-y-2">
          <SourceSkeleton />
          <SourceSkeleton />
          <SourceSkeleton />
          <SourceSkeleton />
        </div>
      </div>
    );
  }

  if (sources.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
            <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
          </svg>
          Monitored Sources
        </h3>
        <div className="flex items-center justify-center py-6 text-gray-400 text-sm">
          No sources available
        </div>
      </div>
    );
  }

  const totalCount = sources.reduce((sum, s) => sum + s.count, 0);

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent2" fill="currentColor" viewBox="0 0 20 20">
          <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
        Monitored Sources
        <span className="ml-auto text-xs font-normal text-gray-400">
          {totalCount.toLocaleString()} total
        </span>
      </h3>
      <div className="space-y-1.5 max-h-[280px] overflow-y-auto pr-1">
        {sources.map((source, index) => {
          const config = getSourceConfig(source.source);
          return (
            <div
              key={source.source}
              className="flex items-center gap-2.5 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors animate-slide-in-right"
              style={{ animationDelay: `${index * 60}ms` }}
            >
              <div className={`w-8 h-8 rounded-lg ${config.bgColor} flex items-center justify-center ${config.color}`}>
                {config.icon}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{source.source}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs text-gray-500">
                    {source.count.toLocaleString()} reviews
                  </span>
                  {source.avg_score !== null && (
                    <>
                      <span className="text-gray-300">|</span>
                      <span className={`text-xs font-medium ${source.avg_score > 0.2 ? 'text-green-600' : source.avg_score < -0.2 ? 'text-red-600' : 'text-yellow-600'}`}>
                        {source.avg_score > 0 ? '+' : ''}{source.avg_score.toFixed(2)}
                      </span>
                    </>
                  )}
                </div>
              </div>
              {/* Percentage bar */}
              <div className="w-16 flex-shrink-0">
                <div className="text-right text-[10px] text-gray-400 mb-0.5">
                  {totalCount > 0 ? ((source.count / totalCount) * 100).toFixed(0) : 0}%
                </div>
                <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{
                      width: `${totalCount > 0 ? (source.count / totalCount) * 100 : 0}%`,
                      backgroundColor: config.color.includes('orange')
                        ? '#D97B0B'
                        : config.color.includes('blue')
                        ? '#0572CE'
                        : config.color.includes('purple')
                        ? '#7B4BC4'
                        : config.color.includes('green')
                        ? '#13811C'
                        : config.color.includes('yellow')
                        ? '#D97B0B'
                        : '#0891b2',
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
