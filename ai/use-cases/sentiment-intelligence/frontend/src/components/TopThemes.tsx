import type { AspectInfo } from '../services/api';

interface TopThemesProps {
  data: AspectInfo[];
  loading: boolean;
}

function getThemeStyle(sentiment: string) {
  switch (sentiment) {
    case 'Positive':
      return 'bg-green-50 text-green-700 border-green-200';
    case 'Negative':
      return 'bg-red-50 text-red-700 border-red-200';
    default:
      return 'bg-yellow-50 text-yellow-700 border-yellow-200';
  }
}

function ThemeSkeleton() {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="shimmer h-7 rounded-full"
          style={{ width: `${60 + Math.random() * 60}px` }}
        />
      ))}
    </div>
  );
}

export default function TopThemes({ data, loading }: TopThemesProps) {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          Top Themes
        </h3>
        <ThemeSkeleton />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
          </svg>
          Top Themes
        </h3>
        <div className="flex items-center justify-center py-6 text-gray-400 text-sm">
          No themes detected yet.
        </div>
      </div>
    );
  }

  const items = data.slice(0, 14);
  const negativeCount = data.filter((a) => a.sentiment === 'Negative').length;
  const positiveCount = data.filter((a) => a.sentiment === 'Positive').length;

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
        </svg>
        Top Themes
        <span className="ml-auto text-xs font-normal text-gray-400">
          <span className="text-green-600">{positiveCount}+</span>
          <span className="mx-1">/</span>
          <span className="text-red-600">{negativeCount}-</span>
        </span>
      </h3>
      <div className="flex flex-wrap gap-2">
        {items.map((aspect, i) => (
          <span
            key={`${aspect.aspect}-${i}`}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all hover:shadow-sm ${getThemeStyle(aspect.sentiment)}`}
            title={`${aspect.aspect} — avg score ${aspect.avg_score.toFixed(2)}`}
          >
            <span>{aspect.aspect}</span>
            <span className="text-[10px] font-bold opacity-70">{aspect.count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}
