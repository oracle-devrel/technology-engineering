import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import type { TrendPoint } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface TrendChartProps {
  data: TrendPoint[];
  loading: boolean;
}

export default function TrendChart({ data, loading }: TrendChartProps) {
  const chartData = useMemo(() => ({
    labels: data.map((d) => d.week_label),
    datasets: [
      {
        label: 'Positive',
        data: data.map((d) => d.positive_pct),
        backgroundColor: 'rgba(19, 129, 28, 0.8)',
        borderColor: 'rgba(19, 129, 28, 1)',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: 'Neutral',
        data: data.map((d) => d.neutral_pct),
        backgroundColor: 'rgba(217, 123, 11, 0.8)',
        borderColor: 'rgba(217, 123, 11, 1)',
        borderWidth: 1,
        borderRadius: 3,
      },
      {
        label: 'Negative',
        data: data.map((d) => d.negative_pct),
        backgroundColor: 'rgba(199, 70, 52, 0.8)',
        borderColor: 'rgba(199, 70, 52, 1)',
        borderWidth: 1,
        borderRadius: 3,
      },
    ],
  }), [data]);

  const options = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#6B6B6B',
          usePointStyle: true,
          pointStyle: 'roundRect',
          padding: 20,
          font: {
            family: 'Inter, system-ui, sans-serif',
            size: 12,
          },
        },
      },
      tooltip: {
        backgroundColor: '#FFFFFF',
        titleColor: '#161513',
        bodyColor: '#6B6B6B',
        borderColor: '#E2E2E2',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 12,
        titleFont: {
          family: 'Inter, system-ui, sans-serif',
          size: 13,
          weight: 600 as const,
        },
        bodyFont: {
          family: 'Inter, system-ui, sans-serif',
          size: 12,
        },
        callbacks: {
          afterBody: function (context: { dataIndex: number }[]) {
            if (context.length > 0) {
              const idx = context[0].dataIndex;
              const point = data[idx];
              if (point) {
                return `\nTotal Reviews: ${point.total_reviews.toLocaleString()}`;
              }
            }
            return '';
          },
        },
      },
    },
    scales: {
      x: {
        stacked: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.06)',
        },
        ticks: {
          color: '#6B6B6B',
          font: {
            family: 'Inter, system-ui, sans-serif',
            size: 11,
          },
        },
      },
      y: {
        stacked: true,
        max: 100,
        grid: {
          color: 'rgba(0, 0, 0, 0.06)',
        },
        ticks: {
          color: '#6B6B6B',
          callback: function (value: string | number) {
            return value + '%';
          },
          font: {
            family: 'Inter, system-ui, sans-serif',
            size: 11,
          },
        },
      },
    },
  }), [data]);

  if (loading) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
          Sentiment Trend (12 Weeks)
        </h3>
        <div className="h-[300px] shimmer rounded-lg" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="glass-card p-6">
        <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
          Sentiment Trend (12 Weeks)
        </h3>
        <div className="h-[300px] flex items-center justify-center text-gray-400">
          <div className="text-center">
            <svg className="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="text-sm">Run an analysis to populate trend data</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card p-6 animate-fade-in">
      <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-4">
        Sentiment Trend ({data.length} Weeks)
      </h3>
      <div className="h-[300px]">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
}
