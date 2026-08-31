import { useMemo } from 'react';
import {
  TrendingUp,
  Car,
  Wrench,
  DollarSign,
  Users,
  Clock,
  Target,
  Home,
  Route,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { Tooltip } from '@/components/shared/Tooltip';
import { useOptimizationStore, useConfigStore } from '@/store';
import { formatDistance, formatDuration } from '@/utils';
import { formatCurrency } from '@/data/locationData';

// Business Impact baseline values (Belron UK case study)
const BUSINESS_IMPACT_BASELINES = {
  // Per-job efficiency improvement targets
  avgJobsPerTechPerDay: { before: 3.2, after: 4.0 },
  // Fuel savings per km reduction
  fuelCostPerKm: 0.15, // GBP (diesel van ~7p/km fuel + wear)
  // Revenue per additional job served
  avgRevenuePerJob: 185, // GBP average across job types
  // Working days per year
  workingDaysPerYear: 250,
};

export function OperationalImpactPanel() {
  const {
    result,
    routes,
    totalDistance,
    totalDuration,
    vehiclesUsed,
    stopsServed,
    stops,
    config,
  } = useOptimizationStore();

  const { config: appConfig } = useConfigStore();

  // Calculate operational metrics
  const metrics = useMemo(() => {
    if (!result || stopsServed === 0 || vehiclesUsed === 0) {
      return null;
    }

    const totalJobTime = stops.reduce((sum, s) => sum + (s.serviceDuration || 0), 0);
    const totalDriveTime = Math.max(0, totalDuration - totalJobTime);
    const productiveRatio = totalDuration > 0 ? totalJobTime / totalDuration : 0;
    const jobsPerTechPerDay = stopsServed / vehiclesUsed;

    // Calculate efficiency vs baseline
    const efficiencyImprovement = BUSINESS_IMPACT_BASELINES.avgJobsPerTechPerDay.before > 0
      ? ((jobsPerTechPerDay - BUSINESS_IMPACT_BASELINES.avgJobsPerTechPerDay.before) /
         BUSINESS_IMPACT_BASELINES.avgJobsPerTechPerDay.before) * 100
      : 0;

    // Calculate potential savings
    const distanceReduction = totalDistance * 0.15; // Assume 15% reduction from optimization
    const fuelSavingsDaily = distanceReduction * BUSINESS_IMPACT_BASELINES.fuelCostPerKm;
    const additionalJobsPerDay = Math.max(0, jobsPerTechPerDay - BUSINESS_IMPACT_BASELINES.avgJobsPerTechPerDay.before) * vehiclesUsed;
    const additionalRevenueDaily = additionalJobsPerDay * BUSINESS_IMPACT_BASELINES.avgRevenuePerJob;

    const totalDailySavings = fuelSavingsDaily + additionalRevenueDaily;
    const annualSavings = totalDailySavings * BUSINESS_IMPACT_BASELINES.workingDaysPerYear;

    // Return-to-depot estimates (when disabled)
    const estimatedReturnDistance = routes.reduce((sum, r) => sum + (r.route_distance * 0.3), 0);
    const estimatedReturnTime = (estimatedReturnDistance / 30) * 60; // 30 km/h avg speed

    return {
      jobsPerTechPerDay,
      efficiencyImprovement,
      productiveRatio,
      totalJobTime,
      totalDriveTime,
      fuelSavingsDaily,
      additionalRevenueDaily,
      totalDailySavings,
      annualSavings,
      estimatedReturnDistance,
      estimatedReturnTime,
    };
  }, [result, stops, stopsServed, vehiclesUsed, totalDistance, totalDuration, routes]);

  if (!result || !metrics) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <Target className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>Run optimization to see operational impact</p>
          <p className="text-sm mt-1 text-gray-500">
            Metrics include jobs/tech/day, productive time, and savings
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto space-y-4 p-1">
      {/* Main Metrics Card */}
      <Card variant="bordered" className="border-green-500/30 bg-green-500/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-green-400">
            <TrendingUp className="w-5 h-5" />
            Field Service Efficiency
          </CardTitle>
          <span className="text-xs text-gray-500">Belron Calibrated</span>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            {/* Jobs per Tech per Day */}
            <div className="bg-dark-bg rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <Users className="w-4 h-4 text-green-400" />
                <Tooltip
                  content={
                    <div className="max-w-xs">
                      <p className="font-medium">Jobs per Technician per Day</p>
                      <p className="text-gray-400 mt-1">Number of jobs assigned to each technician in this solution.</p>
                      <p className="text-gray-400 mt-1">Industry baseline: 3.2 jobs/tech/day</p>
                      <p className="text-green-400 mt-1">Target: 4.0+ jobs/tech/day</p>
                    </div>
                  }
                  position="left"
                />
              </div>
              <div className="text-2xl font-bold text-white">
                {metrics.jobsPerTechPerDay.toFixed(1)}
              </div>
              <div className="text-xs text-gray-400">Jobs/Tech/Day</div>
              <div className={`text-xs mt-1 font-medium ${metrics.efficiencyImprovement >= 0 ? 'text-green-400' : 'text-yellow-400'}`}>
                {metrics.efficiencyImprovement >= 0 ? '+' : ''}{metrics.efficiencyImprovement.toFixed(0)}% vs baseline
              </div>
            </div>

            {/* Productive Time */}
            <div className="bg-dark-bg rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <Wrench className="w-4 h-4 text-green-400" />
                <Tooltip
                  content={
                    <div className="max-w-xs">
                      <p className="font-medium">Productive Time Ratio</p>
                      <p className="text-gray-400 mt-1">Percentage of time spent on actual jobs vs driving between locations.</p>
                      <p className="text-gray-400 mt-1">Higher = more efficient routes with less wasted drive time.</p>
                    </div>
                  }
                  position="left"
                />
              </div>
              <div className="text-2xl font-bold text-white">
                {Math.round(metrics.productiveRatio * 100)}%
              </div>
              <div className="text-xs text-gray-400">On Jobs</div>
              <div className="text-xs text-gray-500 mt-1">
                {formatDuration(metrics.totalDriveTime)} driving
              </div>
            </div>

            {/* Daily Savings */}
            <div className="bg-dark-bg rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <DollarSign className="w-4 h-4 text-green-400" />
                <Tooltip
                  content={
                    <div className="max-w-xs">
                      <p className="font-medium">Daily Operational Savings</p>
                      <p className="text-gray-400 mt-1">Estimated daily savings from:</p>
                      <ul className="text-gray-400 mt-1 list-disc list-inside text-xs">
                        <li>Fuel savings from shorter routes (~15% reduction)</li>
                        <li>Additional revenue from more jobs served</li>
                      </ul>
                      <div className="border-t border-dark-border pt-2 mt-2 text-xs">
                        <p>Fuel: {formatCurrency(Math.round(metrics.fuelSavingsDaily), appConfig.currency)}</p>
                        <p>Revenue: {formatCurrency(Math.round(metrics.additionalRevenueDaily), appConfig.currency)}</p>
                      </div>
                    </div>
                  }
                  position="left"
                />
              </div>
              <div className="text-2xl font-bold text-white">
                {formatCurrency(Math.round(metrics.totalDailySavings), appConfig.currency)}
              </div>
              <div className="text-xs text-gray-400">Daily Savings</div>
              <div className="text-xs text-gray-500 mt-1">
                fuel + productivity
              </div>
            </div>

            {/* Annual Potential */}
            <div className="bg-dark-bg rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <TrendingUp className="w-4 h-4 text-green-400" />
                <Tooltip
                  content={
                    <div className="max-w-xs">
                      <p className="font-medium">Annual Savings Potential</p>
                      <p className="text-gray-400 mt-1">Daily savings scaled to 250 working days per year.</p>
                      <p className="text-gray-400 mt-1">This represents the potential ROI from route optimization.</p>
                      <div className="border-t border-dark-border pt-2 mt-2 text-xs text-gray-500">
                        Calculation: {formatCurrency(Math.round(metrics.totalDailySavings), appConfig.currency)}/day × 250 days
                      </div>
                    </div>
                  }
                  position="left"
                />
              </div>
              <div className="text-2xl font-bold text-white">
                {formatCurrency(Math.round(metrics.annualSavings), appConfig.currency)}
              </div>
              <div className="text-xs text-gray-400">Annual Potential</div>
              <div className="text-xs text-gray-500 mt-1">
                250 working days
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Time Breakdown Card */}
      <Card variant="bordered">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-400" />
            Time Breakdown
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Visual bar */}
            <div className="h-6 rounded-full overflow-hidden flex bg-dark-bg">
              <div
                className="bg-[#C74634] flex items-center justify-center text-xs text-white font-medium"
                style={{ width: `${metrics.productiveRatio * 100}%` }}
              >
                {Math.round(metrics.productiveRatio * 100)}% Jobs
              </div>
              <div
                className="bg-blue-500 flex items-center justify-center text-xs text-white font-medium"
                style={{ width: `${(1 - metrics.productiveRatio) * 100}%` }}
              >
                {Math.round((1 - metrics.productiveRatio) * 100)}% Drive
              </div>
            </div>

            {/* Breakdown details */}
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="flex items-center gap-2">
                <Wrench className="w-4 h-4 text-[#C74634]" />
                <span className="text-gray-400">Job Time:</span>
                <span className="text-white font-medium">{formatDuration(metrics.totalJobTime)}</span>
              </div>
              <div className="flex items-center gap-2">
                <Car className="w-4 h-4 text-blue-400" />
                <span className="text-gray-400">Drive Time:</span>
                <span className="text-white font-medium">{formatDuration(metrics.totalDriveTime)}</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Return-to-Depot Estimate (when disabled) */}
      {config.enableHomeStart && config.returnToDepot === false && (
        <Card variant="bordered" className="border-blue-500/30 bg-blue-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-400">
              <Home className="w-5 h-5" />
              Return-to-Depot Estimate
            </CardTitle>
            <Badge variant="info">Home-End Mode</Badge>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-300 mb-3">
              Vehicles end at last job (no depot return). If depot return is needed:
            </p>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-dark-bg rounded-lg p-3 text-center">
                <Route className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                <div className="text-lg font-bold text-blue-400">
                  +{formatDistance(metrics.estimatedReturnDistance)}
                </div>
                <div className="text-xs text-gray-400">Additional Distance</div>
              </div>
              <div className="bg-dark-bg rounded-lg p-3 text-center">
                <Clock className="w-4 h-4 text-blue-400 mx-auto mb-1" />
                <div className="text-lg font-bold text-blue-400">
                  +{formatDuration(metrics.estimatedReturnTime)}
                </div>
                <div className="text-xs text-gray-400">Additional Time</div>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-3">
              <span className="text-yellow-400">Tip:</span> Enable "Return to Depot" in Fleet settings to include return trips.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Calibration Note */}
      <div className="text-xs text-gray-500 px-2">
        <span className="text-gray-400">Calibration:</span> Based on Belron UK field service benchmarks (3.2 → 4.0 jobs/tech/day target, £7.7M p.a. potential across 2,500 technicians).
      </div>
    </div>
  );
}
