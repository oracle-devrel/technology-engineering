import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { ScorePoint } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface ScoreHistoryChartProps {
  data: ScorePoint[];
  loading: boolean;
}

export default function ScoreHistoryChart({ data, loading }: ScoreHistoryChartProps) {
  const chartData = useMemo(() => {
    const labels = data.map((d) => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const scores = data.map((d) => d.avg_score);

    return {
      labels,
      datasets: [
        {
          label: 'Avg Score',
          data: scores,
          borderColor: scores.map((s) => (s >= 0 ? 'rgba(19, 129, 28, 0.9)' : 'rgba(199, 70, 52, 0.9)')),
          backgroundColor: 'transparent',
          segment: {
            borderColor: ((ctx: any) => {
              const avg = ((ctx.p0.parsed.y ?? 0) + (ctx.p1.parsed.y ?? 0)) / 2;
              return avg >= 0 ? 'rgba(19, 129, 28, 0.9)' : 'rgba(199, 70, 52, 0.9)';
            }) as any,
          },
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 7,
          pointBackgroundColor: scores.map((s) =>
            s >= 0 ? 'rgba(19, 129, 28, 1)' : 'rgba(199, 70, 52, 1)'
          ),
          pointBorderColor: 'transparent',
        },
      ],
    };
  }, [data]);

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          backgroundColor: '#FFFFFF',
          borderColor: '#E2E2E2',
          borderWidth: 1,
          cornerRadius: 8,
          titleColor: '#161513',
          bodyColor: '#6B6B6B',
          padding: 12,
          callbacks: {
            label: (context: { parsed: { y: number } }) => {
              const score = context.parsed.y;
              const label = score >= 0 ? 'Positive' : 'Negative';
              return `Score: ${score.toFixed(3)} (${label})`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(0, 0, 0, 0.06)' },
          ticks: { color: '#6B6B6B', font: { size: 10 } },
        },
        y: {
          min: -1,
          max: 1,
          grid: {
            color: (context: { tick: { value: number } }) =>
              context.tick.value === 0
                ? 'rgba(0, 0, 0, 0.15)'
                : 'rgba(0, 0, 0, 0.06)',
          },
          ticks: {
            color: '#6B6B6B',
            font: { size: 10 },
            stepSize: 0.5,
          },
        },
      },
    }),
    []
  );

  if (loading) {
    return (
      <div className="glass-card p-6">
        <div className="shimmer h-4 w-40 rounded mb-4" />
        <div className="shimmer h-[200px] rounded" />
      </div>
    );
  }

  if (data.length < 3) {
    const isEmpty = data.length === 0;
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
          Sentiment Score History
        </h3>
        <div className="h-[200px] flex items-center justify-center text-gray-400 border border-dashed border-gray-200 rounded-lg">
          <div className="text-center px-6">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
            {isEmpty ? (
              <p className="text-xs">No score history yet</p>
            ) : (
              <>
                <p className="text-xs font-medium text-gray-500">
                  {data.length} day{data.length !== 1 ? 's' : ''} of data so far
                </p>
                <p className="text-[10px] text-gray-400 mt-1">
                  Run analyses across more days to build a trend.
                </p>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
        Sentiment Score History
      </h3>
      <div className="h-[200px]">
        <Line data={chartData} options={options as any} />
      </div>
    </div>
  );
}
