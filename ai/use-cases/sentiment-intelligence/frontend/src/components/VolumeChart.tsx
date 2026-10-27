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
import type { VolumePoint } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

interface VolumeChartProps {
  data: VolumePoint[];
  loading: boolean;
}

export default function VolumeChart({ data, loading }: VolumeChartProps) {
  const chartData = useMemo(() => {
    const labels = data.map((d) => {
      const date = new Date(d.date);
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    return {
      labels,
      datasets: [
        {
          label: 'Reviews',
          data: data.map((d) => d.count),
          borderColor: 'rgba(5, 114, 206, 0.9)',
          backgroundColor: 'rgba(5, 114, 206, 0.08)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgba(5, 114, 206, 1)',
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
        },
      },
      scales: {
        x: {
          grid: { color: 'rgba(0, 0, 0, 0.06)' },
          ticks: { color: '#6B6B6B', font: { size: 10 } },
        },
        y: {
          beginAtZero: true,
          grid: { color: 'rgba(0, 0, 0, 0.06)' },
          ticks: { color: '#6B6B6B', font: { size: 10 }, precision: 0 },
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
          Review Volume Over Time
        </h3>
        <div className="h-[200px] flex items-center justify-center text-gray-400 border border-dashed border-gray-200 rounded-lg">
          <div className="text-center px-6">
            <svg className="w-10 h-10 mx-auto mb-2 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
            </svg>
            {isEmpty ? (
              <p className="text-xs">No volume data yet</p>
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
        Review Volume Over Time
      </h3>
      <div className="h-[200px]">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
}
