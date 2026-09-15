import type { EmotionInfo } from '../services/api';

interface EmotionsListProps {
  data: EmotionInfo[];
  loading: boolean;
}

const POSITIVE_EMOTIONS = [
  'joy', 'satisfaction', 'happiness', 'love', 'pride', 'gratitude',
  'excitement', 'delight', 'enthusiasm', 'trust', 'hope', 'admiration',
];

const NEGATIVE_EMOTIONS = [
  'anger', 'frustration', 'sadness', 'disappointment', 'fear', 'disgust',
  'annoyance', 'rage', 'resentment', 'regret', 'anxiety', 'contempt',
];

function getEmotionStyle(emotion: string) {
  const e = emotion.toLowerCase();
  if (POSITIVE_EMOTIONS.some((p) => e.includes(p))) {
    return 'bg-green-50 text-green-700 border-green-200';
  }
  if (NEGATIVE_EMOTIONS.some((n) => e.includes(n))) {
    return 'bg-red-50 text-red-700 border-red-200';
  }
  return 'bg-blue-50 text-blue-700 border-blue-200';
}

function EmotionSkeleton() {
  return (
    <div className="flex flex-wrap gap-2">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="shimmer h-7 rounded-full"
          style={{ width: `${50 + Math.random() * 70}px` }}
        />
      ))}
    </div>
  );
}

export default function EmotionsList({ data, loading }: EmotionsListProps) {
  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Customer Emotions
        </h3>
        <EmotionSkeleton />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
          <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Customer Emotions
        </h3>
        <div className="flex items-center justify-center py-6 text-gray-400 text-sm">
          No emotions detected yet.
        </div>
      </div>
    );
  }

  const items = data.slice(0, 14);
  const max = Math.max(...items.map((e) => e.count), 1);

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4 flex items-center gap-2">
        <svg className="w-4 h-4 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Customer Emotions
        <span className="ml-auto text-xs font-normal text-gray-400">
          {items.length} detected
        </span>
      </h3>
      <div className="flex flex-wrap gap-2 items-center">
        {items.map((em, i) => {
          const ratio = em.count / max;
          const fontSize = 0.7 + ratio * 0.35;
          return (
            <span
              key={`${em.emotion}-${i}`}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full font-medium border transition-all hover:shadow-sm ${getEmotionStyle(em.emotion)}`}
              style={{ fontSize: `${fontSize}rem` }}
              title={`${em.emotion} — ${em.count} mentions`}
            >
              <span>{em.emotion}</span>
              <span className="text-[10px] font-bold opacity-70">{em.count}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
