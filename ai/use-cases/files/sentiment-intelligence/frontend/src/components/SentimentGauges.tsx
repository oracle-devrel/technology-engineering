import { useMemo } from 'react';
import type { GaugeData } from '../services/api';

export interface GaugeSummary {
  totalReviews?: number;
  avgScore?: number | null;
  topNegativeAspect?: string | null;
  topEmotion?: string | null;
}

interface SentimentGaugesProps {
  data: GaugeData | null;
  loading: boolean;
  summary?: GaugeSummary;
}

interface GaugeProps {
  value: number;
  label: string;
  color: string;
  bgColor: string;
  change?: number;
  delay?: number;
}

function Gauge({ value, label, color, bgColor, change, delay = 0 }: GaugeProps) {
  const clampedValue = Math.min(100, Math.max(0, value));
  const gradientStyle = useMemo(() => ({
    background: `conic-gradient(${color} ${clampedValue * 3.6}deg, ${bgColor} ${clampedValue * 3.6}deg)`,
  }), [clampedValue, color, bgColor]);

  return (
    <div
      className="flex flex-col items-center animate-slide-in-up"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="gauge-ring" style={gradientStyle}>
        <div className="flex flex-col items-center">
          <span className="gauge-value" style={{ color }}>
            {clampedValue.toFixed(1)}%
          </span>
          <span className="gauge-label text-gray-500">{label}</span>
        </div>
      </div>
      {change !== undefined && (
        <div className="mt-2 flex items-center gap-1 text-xs">
          {change >= 0 ? (
            <svg className="w-3 h-3" style={{ color }} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-3 h-3" style={{ color }} fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )}
          <span style={{ color }}>
            {change >= 0 ? '+' : ''}{change.toFixed(1)}%
          </span>
          <span className="text-gray-400">vs last period</span>
        </div>
      )}
    </div>
  );
}

function GaugeSkeleton() {
  return (
    <div className="flex flex-col items-center">
      <div className="w-[120px] h-[120px] rounded-full shimmer" />
      <div className="mt-2 w-20 h-3 rounded shimmer" />
    </div>
  );
}

interface StatProps {
  label: string;
  value: string;
  hint?: string;
  valueColor?: string;
  icon: React.ReactNode;
  compact?: boolean;
}

function Stat({ label, value, hint, valueColor = 'text-gray-900', icon, compact = false }: StatProps) {
  const valueClass = compact
    ? 'text-sm font-bold leading-snug'
    : 'text-xl font-extrabold leading-tight truncate';
  return (
    <div className="flex items-start gap-3">
      <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-gray-100 to-gray-50 text-gray-600 flex items-center justify-center flex-shrink-0 ring-1 ring-gray-200">
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">{label}</p>
        <p className={`${valueClass} ${valueColor}`} title={value}>
          {value}
        </p>
        {hint && <p className="text-[10px] text-gray-400 mt-0.5 truncate">{hint}</p>}
      </div>
    </div>
  );
}

export default function SentimentGauges({ data, loading, summary }: SentimentGaugesProps) {
  if (loading || !data) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
          Overall Sentiment
        </h3>
        <div className="flex justify-around items-center">
          <GaugeSkeleton />
          <GaugeSkeleton />
          <GaugeSkeleton />
        </div>
      </div>
    );
  }

  const totalReviews = summary?.totalReviews ?? data.total ?? 0;
  const avgScore = summary?.avgScore ?? null;
  const topNeg = summary?.topNegativeAspect ?? null;
  const topEmotion = summary?.topEmotion ?? null;

  const hasSummary =
    totalReviews > 0 || avgScore !== null || topNeg || topEmotion;

  const scoreColor =
    avgScore === null
      ? 'text-gray-900'
      : avgScore >= 0.1
      ? 'text-green-600'
      : avgScore <= -0.1
      ? 'text-red-600'
      : 'text-yellow-600';

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
        Overall Sentiment
      </h3>
      <div className="flex justify-around items-center flex-wrap gap-4">
        <Gauge
          value={data.positive_pct}
          label="Positive"
          color="var(--green)"
          bgColor="rgba(19, 129, 28, 0.12)"
          change={2.3}
          delay={0}
        />
        <Gauge
          value={data.neutral_pct}
          label="Neutral"
          color="var(--orange)"
          bgColor="rgba(217, 123, 11, 0.12)"
          change={-1.1}
          delay={100}
        />
        <Gauge
          value={data.negative_pct}
          label="Negative"
          color="var(--accent)"
          bgColor="rgba(199, 70, 52, 0.12)"
          change={-1.2}
          delay={200}
        />
      </div>

      {hasSummary && (
        <div className="mt-6 pt-5 border-t border-gray-200 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Stat
            label="Total Reviews"
            value={totalReviews > 0 ? totalReviews.toLocaleString() : '—'}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
          <Stat
            label="Avg Score"
            value={avgScore !== null ? avgScore.toFixed(2) : '—'}
            hint="−1.0 to +1.0 scale"
            valueColor={scoreColor}
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            }
          />
          <Stat
            label="Top Complaint"
            value={topNeg ?? '—'}
            valueColor={topNeg ? 'text-red-600' : 'text-gray-900'}
            compact
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            }
          />
          <Stat
            label="Top Emotion"
            value={topEmotion ?? '—'}
            compact
            icon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      )}
    </div>
  );
}
