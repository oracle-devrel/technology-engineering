import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, HelpCircle, Clock, Zap } from 'lucide-react';
import { performanceBaselines, parallelExecutionData } from '@/data/benchmarkData';
import { useOptimizationStore, useConfigStore } from '@/store';
import { getCountryByCode } from '@/data/locationData';

export function PerformanceChart() {
  const { stops, solveTime } = useOptimizationStore();
  const { config: appConfig } = useConfigStore();
  const [showBaselineInfo, setShowBaselineInfo] = useState(false);

  // Get currency info from config
  const country = getCountryByCode(appConfig.countryCode);
  const currencySymbol = country?.currency.symbol || '£';
  const hourlyRate = appConfig.dispatcherHourlyRate || 25;

  // Format stop count for display
  const formatStopCount = (count: number) => {
    if (count < 1000) return count.toString();
    if (count % 1000 === 0) return `${count / 1000}K`;
    return `${(count / 1000).toFixed(1)}K`;
  };

  // Add current result to chart data
  const chartData = performanceBaselines.map((baseline) => ({
    stops: baseline.stopCount,
    baseline: baseline.solveTimeSeconds,
    label: formatStopCount(baseline.stopCount),
  }));

  // Add current solve if available
  const currentData =
    solveTime > 0 && stops.length > 0
      ? {
          stops: stops.length,
          current: solveTime,
          label: 'Current',
        }
      : null;

  // Calculate performance vs baseline
  const getBaselineForStops = (numStops: number) => {
    // Linear interpolation between baseline points
    const sorted = [...performanceBaselines].sort((a, b) => a.stopCount - b.stopCount);
    if (numStops <= sorted[0].stopCount) return sorted[0].solveTimeSeconds;
    if (numStops >= sorted[sorted.length - 1].stopCount) return sorted[sorted.length - 1].solveTimeSeconds;

    for (let i = 0; i < sorted.length - 1; i++) {
      if (numStops >= sorted[i].stopCount && numStops <= sorted[i + 1].stopCount) {
        const ratio = (numStops - sorted[i].stopCount) / (sorted[i + 1].stopCount - sorted[i].stopCount);
        return sorted[i].solveTimeSeconds + ratio * (sorted[i + 1].solveTimeSeconds - sorted[i].solveTimeSeconds);
      }
    }
    return sorted[0].solveTimeSeconds;
  };

  const expectedBaseline = stops.length > 0 ? getBaselineForStops(stops.length) : 0;
  const performanceVsBaseline = solveTime > 0 && expectedBaseline > 0
    ? ((expectedBaseline - solveTime) / expectedBaseline) * 100
    : 0;
  const isBetterThanBaseline = performanceVsBaseline > 0;

  // Business value calculations
  // Manual planning: ~1.5 min per stop for experienced dispatcher
  const manualPlanningMinutes = stops.length * 1.5;
  const timeSavingsMinutes = manualPlanningMinutes - (solveTime / 60);
  const productivityMultiplier = solveTime > 0 ? Math.round(manualPlanningMinutes / (solveTime / 60)) : 0;
  // Annual savings: assume 250 working days, 4 planning sessions/day, configurable hourly dispatcher cost
  const annualHoursSaved = (timeSavingsMinutes / 60) * 4 * 250;
  const annualCostSavings = Math.round(annualHoursSaved * hourlyRate);

  return (
    <div className="h-full flex flex-col overflow-y-auto">
      {/* Planning Efficiency Summary - Solver speed vs manual planning */}
      {solveTime > 0 && stops.length > 0 && (
        <div className="mb-3 p-3 rounded-lg border bg-oracle-red/10 border-oracle-red/30">
          <div className="flex items-center gap-2 mb-2">
            <Zap className="w-4 h-4 text-oracle-red" />
            <span className="text-sm font-semibold text-oracle-red">Planning Efficiency</span>
            <span className="text-xs text-gray-500">(AI vs Manual)</span>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-lg font-bold text-white">{productivityMultiplier}x</div>
              <div className="text-xs text-gray-400">Faster than manual</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">{Math.round(timeSavingsMinutes)} min</div>
              <div className="text-xs text-gray-400">Saved per run</div>
            </div>
            <div>
              <div className="text-lg font-bold text-white">{currencySymbol}{annualCostSavings.toLocaleString()}</div>
              <div className="text-xs text-gray-400">Dispatcher savings*</div>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-2 text-center">*Based on 4 optimizations/day, 250 days/year, {currencySymbol}{hourlyRate}/hr dispatcher cost</p>
        </div>
      )}

      {/* Technical Performance */}
      {solveTime > 0 && (
        <div className="mb-3 p-2 rounded-lg border" style={{
          backgroundColor: isBetterThanBaseline ? 'rgba(199, 70, 52, 0.1)' : 'rgba(59, 130, 246, 0.1)',
          borderColor: isBetterThanBaseline ? 'rgba(199, 70, 52, 0.3)' : 'rgba(59, 130, 246, 0.3)'
        }}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isBetterThanBaseline ? (
                <TrendingUp className="w-4 h-4" style={{ color: '#C74634' }} />
              ) : (
                <Clock className="w-4 h-4 text-blue-400" />
              )}
              <span className="text-sm font-medium" style={{ color: isBetterThanBaseline ? '#C74634' : '#60A5FA' }}>
                {isBetterThanBaseline
                  ? `${Math.abs(performanceVsBaseline).toFixed(1)}% faster than baseline`
                  : `${solveTime.toFixed(1)}s solve time (within expected range)`
                }
              </span>
            </div>
            <button
              onClick={() => setShowBaselineInfo(!showBaselineInfo)}
              className="text-gray-400 hover:text-white transition-colors"
              title="What is the baseline?"
            >
              <HelpCircle className="w-4 h-4" />
            </button>
          </div>
          {showBaselineInfo && (
            <div className="mt-2 pt-2 border-t border-gray-700 text-xs text-gray-400 space-y-1">
              <p><strong className="text-gray-300">Baseline:</strong> cuOPT constrained field service solve (time windows, service durations, capacity).</p>
              <p><strong className="text-gray-300">Hardware:</strong> NVIDIA A10G GPU (24GB VRAM) via NIM microservice.</p>
              <p><strong className="text-gray-300">Note:</strong> Complex constraints (tight time windows, high utilization) naturally require more solve time.</p>
            </div>
          )}
        </div>
      )}

      <div className="flex-1" style={{ minHeight: '200px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={chartData}
            margin={{ top: 25, right: 30, left: 10, bottom: 25 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
            <XAxis
              dataKey="label"
              stroke="#6B7280"
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
              tickMargin={8}
            />
            <YAxis
              stroke="#6B7280"
              tick={{ fill: '#9CA3AF', fontSize: 11 }}
              domain={[0, 'auto']}
              tickCount={6}
              label={{
                value: 'Solve Time (s)',
                angle: -90,
                position: 'insideLeft',
                fill: '#9CA3AF',
                fontSize: 11,
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1B1F2E',
                border: '1px solid #2D3748',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#9CA3AF' }}
              itemStyle={{ color: '#FFFFFF' }}
              cursor={{ stroke: '#FFFFFF', strokeWidth: 1 }}
            />
            <Legend
              wrapperStyle={{ paddingTop: '10px' }}
              formatter={(value) => (
                <span style={{ color: '#9CA3AF' }}>{value}</span>
              )}
            />
            <Line
              type="monotone"
              dataKey="baseline"
              stroke="#C74634"
              strokeWidth={2}
              dot={{ fill: '#C74634', r: 4 }}
              name="Benchmark Baseline"
            />
            {currentData && (
              <ReferenceLine
                x={currentData.label}
                stroke="#006BBF"
                strokeDasharray="5 5"
                label={{
                  value: `${currentData.current.toFixed(1)}s`,
                  fill: '#006BBF',
                  fontSize: 12,
                }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Geographic Clustering - Throughput mini chart */}
      <div className="mt-4 pt-4 border-t border-dark-border flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs text-gray-400">Geographic Clustering Throughput</p>
          <span className="text-xs text-oracle-red font-medium">72% payload reduction</span>
        </div>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={parallelExecutionData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" />
            <XAxis
              dataKey="parallelJobs"
              stroke="#6B7280"
              tick={{ fill: '#9CA3AF', fontSize: 10 }}
              label={{
                value: 'Jobs',
                position: 'bottom',
                fill: '#9CA3AF',
                fontSize: 10,
              }}
            />
            <YAxis
              stroke="#6B7280"
              tick={{ fill: '#9CA3AF', fontSize: 10 }}
              width={40}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1B1F2E',
                border: '1px solid #2D3748',
                borderRadius: '6px',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#9CA3AF' }}
              itemStyle={{ color: '#FFFFFF' }}
              cursor={{ fill: 'rgba(255, 255, 255, 0.1)' }}
            />
            <Bar
              dataKey="throughputJobsPerHour"
              fill="#C74634"
              radius={[4, 4, 0, 0]}
              name="Throughput"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
