import { useState, useMemo } from 'react';
import {
  Route,
  Clock,
  Truck,
  MapPin,
  Zap,
  Download,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  ChevronUp,
  Lightbulb,
  Plus,
  Package,
  Timer,
  Car,
  Wrench,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/shared/Card';
import { Button } from '@/components/shared/Button';
import { Badge } from '@/components/shared/Badge';
import { MetricCard } from '@/components/shared/MetricCard';
import { useOptimizationStore, useConfigStore } from '@/store';
import { performanceBaselines } from '@/data/benchmarkData';
import {
  formatDistance,
  formatDuration,
  formatSolveTime,
  getVehicleColor,
  formatVehicleName,
  getVehiclePlate,
  setVehicleCountry,
} from '@/utils';
import { JOB_TYPE_CONFIGS } from '@/types/cuopt';

// Recovery suggestion interface
interface RecoverySuggestion {
  icon: React.ReactNode;
  title: string;
  description: string;
  impact: string;
  action?: string;
}

// Route segment detail for drive time vs job duration breakdown
interface RouteSegment {
  type: 'drive' | 'job';
  duration: number;
  label: string;
  stopId?: number;
  jobType?: string;
  color?: string;
}

/**
 * Calculate route segments showing drive time vs job duration
 */
function calculateRouteSegments(
  route: number[],
  arrivalTimes: number[],
  stops: { id: number; serviceDuration?: number; jobType?: string; label?: string; metadata?: Record<string, unknown> }[]
): RouteSegment[] {
  const segments: RouteSegment[] = [];

  if (route.length < 2 || arrivalTimes.length < 2) {
    return segments;
  }

  for (let i = 0; i < route.length; i++) {
    const stopIdx = route[i];
    const isDepot = i === 0 || i === route.length - 1;

    // Calculate drive time from previous stop
    if (i > 0) {
      const prevArrival = arrivalTimes[i - 1] || 0;
      const prevServiceTime = i === 1 ? 0 : (stops[route[i - 1] - 1]?.serviceDuration || 0);
      const driveTime = (arrivalTimes[i] || 0) - prevArrival - prevServiceTime;

      if (driveTime > 0) {
        const toLabel = isDepot && i === route.length - 1 ? 'Depot' : `Stop ${stopIdx}`;
        segments.push({
          type: 'drive',
          duration: Math.max(0, driveTime),
          label: `Drive to ${toLabel}`,
        });
      }
    }

    // Add job duration for non-depot stops
    if (!isDepot && stopIdx > 0) {
      const stop = stops[stopIdx - 1];
      const serviceDuration = stop?.serviceDuration || 0;

      if (serviceDuration > 0) {
        // Get job type from stop metadata or jobType field
        const jobType = stop?.metadata?.jobType as string || stop?.jobType || 'service';
        const jobConfig = JOB_TYPE_CONFIGS[jobType as keyof typeof JOB_TYPE_CONFIGS];
        const jobLabel = jobConfig?.label || stop?.metadata?.jobLabel as string || stop?.label || `Stop ${stopIdx}`;

        segments.push({
          type: 'job',
          duration: serviceDuration,
          label: jobLabel,
          stopId: stopIdx,
          jobType: jobType,
          color: jobConfig?.color || '#C74634',
        });
      }
    }
  }

  return segments;
}

export function ResultsPanel() {
  const {
    result,
    routes,
    totalDistance,
    totalDuration,
    vehiclesUsed,
    stopsServed,
    solveTime,
    stops,
    parallelJobs,
    config,
  } = useOptimizationStore();

  const { config: appConfig } = useConfigStore();

  // Set vehicle country based on config
  setVehicleCountry(appConfig.countryCode);

  const [expandedRoutes, setExpandedRoutes] = useState<Set<number>>(new Set());
  const [visibleRoutesCount, setVisibleRoutesCount] = useState(20);

  // Calculate baseline for current stop count using interpolation
  const getBaselineForStops = (numStops: number) => {
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

  // Route warnings for unrealistic durations/distances
  // Use 8h (480 min) if time windows enabled, otherwise 12h (720 min) as warning threshold
  const shiftLimitMinutes = config.enableTimeWindows ? 480 : 720;
  const shiftLimitLabel = config.enableTimeWindows ? '8h' : '12h';

  const routeWarnings = useMemo(() => {
    const warnings: Map<number, string[]> = new Map();
    routes.forEach((route) => {
      const routeWarns: string[] = [];
      // Warning if route exceeds shift limit
      if (route.route_duration > shiftLimitMinutes) {
        routeWarns.push(`Duration ${formatDuration(route.route_duration)} exceeds ${shiftLimitLabel} shift limit (PARTIAL solution)`);
      }
      // Warning if route is over 500km
      if (route.route_distance > 500) {
        routeWarns.push(`Distance ${formatDistance(route.route_distance)} exceeds 500km threshold`);
      }
      // Warning if more than 30 stops
      if (route.route.length - 2 > 30) {
        routeWarns.push(`${route.route.length - 2} stops may be operationally challenging`);
      }
      if (routeWarns.length > 0) {
        warnings.set(route.vehicle_id, routeWarns);
      }
    });
    return warnings;
  }, [routes, shiftLimitMinutes, shiftLimitLabel]);

  // Paginated routes
  const visibleRoutes = useMemo(() => {
    return routes.slice(0, visibleRoutesCount);
  }, [routes, visibleRoutesCount]);

  const hasMoreRoutes = routes.length > visibleRoutesCount;
  const remainingRoutes = routes.length - visibleRoutesCount;

  // Calculate dropped stops and generate recovery suggestions
  const droppedStopsCount = stops.length - stopsServed;
  const hasDroppedStops = result && droppedStopsCount > 0;

  const recoverySuggestions = useMemo((): RecoverySuggestion[] => {
    if (!hasDroppedStops) return [];

    const suggestions: RecoverySuggestion[] = [];
    const totalDemand = stops.reduce((sum, s) => sum + s.demand, 0);
    const avgDemandPerStop = totalDemand / stops.length;
    const totalCapacity = config.numVehicles * config.vehicleCapacity;
    const capacityUtilization = (totalDemand / totalCapacity) * 100;

    // Suggestion 1: Add more vehicles if capacity is the issue
    if (capacityUtilization > 90) {
      const additionalVehiclesNeeded = Math.ceil(
        (droppedStopsCount * avgDemandPerStop) / config.vehicleCapacity
      );
      suggestions.push({
        icon: <Plus className="w-4 h-4 text-green-400" />,
        title: 'Add More Vehicles',
        description: `Adding ${additionalVehiclesNeeded} vehicle${additionalVehiclesNeeded > 1 ? 's' : ''} could serve the dropped stops.`,
        impact: `+${droppedStopsCount} stops recovered`,
        action: `Increase fleet to ${config.numVehicles + additionalVehiclesNeeded} vehicles`,
      });
    }

    // Suggestion 2: Increase vehicle capacity
    if (capacityUtilization > 80) {
      const requiredCapacity = Math.ceil(totalDemand / config.numVehicles);
      suggestions.push({
        icon: <Package className="w-4 h-4 text-blue-400" />,
        title: 'Increase Vehicle Capacity',
        description: `Current capacity is ${config.vehicleCapacity} units. Consider larger vehicles.`,
        impact: `Capacity utilization: ${capacityUtilization.toFixed(0)}%`,
        action: `Increase capacity to ${requiredCapacity} units/vehicle`,
      });
    }

    // Suggestion 3: Extend time windows if enabled
    if (config.enableTimeWindows) {
      suggestions.push({
        icon: <Timer className="w-4 h-4 text-yellow-400" />,
        title: 'Extend Time Windows',
        description: 'Some stops may be outside their time windows.',
        impact: `${droppedStopsCount} stops missed windows`,
        action: 'Extend shift hours or adjust stop time windows',
      });
    }

    // Suggestion 4: Reduce service time if configured
    if (config.defaultServiceTime && config.defaultServiceTime > 30) {
      suggestions.push({
        icon: <Clock className="w-4 h-4 text-purple-400" />,
        title: 'Reduce Service Time',
        description: `Current dwell time: ${config.defaultServiceTime} min/stop.`,
        impact: 'More stops per route possible',
        action: 'Consider shorter service durations',
      });
    }

    // Default suggestion if no specific ones
    if (suggestions.length === 0) {
      suggestions.push({
        icon: <Lightbulb className="w-4 h-4 text-[#C74634]" />,
        title: 'Review Constraints',
        description: 'Check vehicle capacity, time windows, and fleet size.',
        impact: `${droppedStopsCount} stops need attention`,
      });
    }

    return suggestions;
  }, [hasDroppedStops, droppedStopsCount, stops, config, stopsServed]);

  const handleShowMore = () => {
    setVisibleRoutesCount((prev) => Math.min(prev + 20, routes.length));
  };

  const handleShowLess = () => {
    setVisibleRoutesCount(20);
  };

  const toggleRoute = (vehicleId: number) => {
    const newExpanded = new Set(expandedRoutes);
    if (newExpanded.has(vehicleId)) {
      newExpanded.delete(vehicleId);
    } else {
      newExpanded.add(vehicleId);
    }
    setExpandedRoutes(newExpanded);
  };

  const handleExport = (format: 'json' | 'csv') => {
    let data: string;

    if (format === 'json') {
      data = JSON.stringify({
        routes,
        metrics: { totalDistance, totalDuration, vehiclesUsed, stopsServed, solveTime },
        status: result?.status || 'SUCCESS'
      }, null, 2);
    } else {
      // CSV with proper formatting - each field quoted to handle special characters
      const headers = ['Vehicle ID', 'Plate', 'Name', 'Stops Count', 'Route Sequence', 'Distance (km)', 'Duration (min)', 'Duration (formatted)', 'Status'];
      const rows = routes.map((r) => {
        const vehicle = getVehiclePlate(r.vehicle_id);
        const stopsCount = r.route.length - 2; // Exclude depot start/end
        const routeSequence = r.route.join(' → ');
        const durationFormatted = formatDuration(r.route_duration);
        const status = r.route_duration > shiftLimitMinutes ? 'SHIFT VIOLATION' : 'OK';
        return [
          r.vehicle_id,
          vehicle.plate,
          vehicle.name,
          stopsCount,
          `"${routeSequence}"`,
          r.route_distance.toFixed(2),
          r.route_duration,
          durationFormatted,
          status
        ].join(',');
      });

      // Add summary row at the end
      const summary = [
        '',
        '',
        'TOTAL',
        stopsServed,
        '',
        totalDistance.toFixed(2),
        totalDuration,
        formatDuration(totalDuration),
        result?.status || 'SUCCESS'
      ].join(',');

      data = [headers.join(','), ...rows, '', summary].join('\n');
    }

    const blob = new Blob([data], {
      type: format === 'json' ? 'application/json' : 'text/csv',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `routes_${new Date().toISOString().slice(0,10)}.${format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="h-full p-4 space-y-4 overflow-y-auto">
      {/* Metrics Strip */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Distance"
          value={formatDistance(totalDistance)}
          icon={Route}
          variant={result ? 'highlight' : 'default'}
        />
        <MetricCard
          title="Total Duration"
          value={formatDuration(totalDuration)}
          icon={Clock}
          variant={result ? 'highlight' : 'default'}
        />
        <MetricCard
          title="Vehicles Used"
          value={`${vehiclesUsed} / ${config.numVehicles}`}
          icon={Truck}
          variant={result ? 'highlight' : 'default'}
          trend={
            vehiclesUsed > 0 && config.numVehicles > 0
              ? {
                  value: Math.round((vehiclesUsed / config.numVehicles) * 100),
                  isPositive: vehiclesUsed < config.numVehicles,
                }
              : undefined
          }
        />
        <MetricCard
          title="Stops Served"
          value={`${stopsServed} / ${stops.length}`}
          icon={MapPin}
          variant={result ? 'highlight' : 'default'}
        />
        <MetricCard
          title="Solve Time"
          value={formatSolveTime(solveTime * 1000)}
          icon={Zap}
          variant="highlight"
          trend={
            solveTime > 0 && expectedBaseline > 0
              ? {
                  value: Math.round(Math.abs(performanceVsBaseline)),
                  isPositive: isBetterThanBaseline,
                }
              : undefined
          }
        />
      </div>

      {/* Route Warnings Summary - Show when many routes have violations */}
      {routeWarnings.size > 0 && (
        <Card variant="bordered" className={`${
          routeWarnings.size >= routes.length * 0.5
            ? 'border-red-500/50 bg-red-500/5'
            : 'border-orange-500/50 bg-orange-500/5'
        }`}>
          <CardContent className="py-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${
                routeWarnings.size >= routes.length * 0.5 ? 'text-red-400' : 'text-orange-400'
              }`} />
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <h4 className={`font-medium ${
                    routeWarnings.size >= routes.length * 0.5 ? 'text-red-400' : 'text-orange-400'
                  }`}>
                    {routeWarnings.size} of {routes.length} Routes Have Constraint Violations
                  </h4>
                  <Badge variant={routeWarnings.size >= routes.length * 0.5 ? 'error' : 'warning'}>
                    {Math.round((routeWarnings.size / routes.length) * 100)}% affected
                  </Badge>
                </div>
                <p className="text-sm text-gray-400 mb-2">
                  These routes exceed the {shiftLimitLabel} shift limit. Stops are assigned but <strong>cannot be practically served</strong> within working hours.
                </p>
                <div className="text-xs text-gray-500 space-y-1">
                  <p><strong>Problem:</strong> Total service time + travel time = {formatDuration(totalDuration)} across {vehiclesUsed} vehicles (avg {formatDuration(Math.round(totalDuration / vehiclesUsed))}/vehicle)</p>
                  <p><strong>Available:</strong> {vehiclesUsed} vehicles × {shiftLimitLabel} shift = {formatDuration(vehiclesUsed * shiftLimitMinutes)} total vehicle-hours</p>
                  <p><strong>Required:</strong> ~{Math.ceil(totalDuration / shiftLimitMinutes)} vehicles needed for {shiftLimitLabel} shifts</p>
                  {vehiclesUsed < config.numVehicles && (
                    <p className="text-yellow-400"><strong>Note:</strong> Only {vehiclesUsed} of {config.numVehicles} configured vehicles used. {parallelJobs.length > 0 ? 'Parallel clustering may limit vehicle distribution - try single optimization for better utilization.' : 'Some vehicles may be unused due to constraint satisfaction.'}</p>
                  )}
                  <p><strong>Fix:</strong> {vehiclesUsed < config.numVehicles
                    ? 'Try single optimization (not parallel) to use all vehicles, or reduce service times'
                    : 'Add more vehicles, reduce service times, or increase shift duration'}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Partial Solution Warning - Time window constraints violated */}
      {result?.status === 'PARTIAL' && routeWarnings.size === 0 && (
        <Card variant="bordered" className="border-orange-500/50 bg-orange-500/5">
          <CardContent className="py-3">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-orange-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-medium text-orange-400 mb-1">
                  Partial Solution - Some Constraints Relaxed
                </h4>
                <p className="text-sm text-gray-400 mb-2">
                  cuOPT couldn't find a fully feasible solution. Time window or capacity constraints may be violated.
                  This typically means the workload exceeds available vehicle-hours.
                </p>
                <div className="text-xs text-gray-500 space-y-1">
                  <p><strong>Why this happens:</strong> Total service time + travel time exceeds combined vehicle shift limits</p>
                  <p><strong>To fix:</strong> Add more vehicles, extend shift hours, reduce service times, or accept dropped stops</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Dropped Stops Recovery Guidance */}
      {hasDroppedStops && (
        <Card variant="bordered" className="border-yellow-500/50 bg-yellow-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-400">
              <AlertTriangle className="w-5 h-5" />
              {droppedStopsCount} Stop{droppedStopsCount > 1 ? 's' : ''} Not Served
            </CardTitle>
            <Badge variant="warning">
              {((droppedStopsCount / stops.length) * 100).toFixed(1)}% dropped
            </Badge>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-400 mb-3">
              Some stops couldn't be served due to constraints. Here are suggestions to recover them:
            </p>
            <div className="space-y-2">
              {recoverySuggestions.map((suggestion, idx) => (
                <div
                  key={idx}
                  className="bg-dark-bg rounded-lg p-3 border border-dark-border"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">{suggestion.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-white text-sm">
                          {suggestion.title}
                        </span>
                        <span className="text-xs text-[#C74634]">
                          {suggestion.impact}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {suggestion.description}
                      </p>
                      {suggestion.action && (
                        <p className="text-xs text-blue-400 mt-1 font-medium">
                          → {suggestion.action}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Parallel Jobs Monitor */}
      {parallelJobs.length > 0 && (
        <Card variant="bordered">
          <CardHeader>
            <CardTitle>Parallel Jobs</CardTitle>
            <Badge variant="nvidia" pulse>
              {parallelJobs.filter((j) => j.status === 'running').length} running
            </Badge>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {parallelJobs.map((job) => (
                <div
                  key={job.jobId}
                  className="bg-dark-bg rounded-lg p-3 border border-dark-border"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">
                      Cluster {job.clusterId}
                    </span>
                    <Badge
                      variant={
                        job.status === 'completed'
                          ? 'success'
                          : job.status === 'running'
                          ? 'info'
                          : job.status === 'failed'
                          ? 'error'
                          : 'default'
                      }
                      pulse={job.status === 'running'}
                    >
                      {job.status}
                    </Badge>
                  </div>
                  <div className="text-xs text-gray-400">
                    {job.stops} stops
                    {job.solveTime && (
                      <span className="ml-2 text-[#C74634]">
                        {formatSolveTime(job.solveTime * 1000)}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Route Table */}
      <Card variant="bordered">
        <CardHeader>
          <CardTitle>Routes</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Download className="w-4 h-4" />}
              onClick={() => handleExport('json')}
              disabled={routes.length === 0}
            >
              JSON
            </Button>
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<Download className="w-4 h-4" />}
              onClick={() => handleExport('csv')}
              disabled={routes.length === 0}
            >
              CSV
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {routes.length === 0 ? (
            <div className="text-center py-12 text-gray-400">
              <Route className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No routes generated yet</p>
              <p className="text-sm mt-1">
                Configure your fleet and stops, then run optimization
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Route count summary */}
              <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                <span>Showing {visibleRoutes.length} of {routes.length} routes</span>
                {routeWarnings.size > 0 && (
                  <span className="flex items-center gap-1 text-yellow-400">
                    <AlertTriangle className="w-3 h-3" />
                    {routeWarnings.size} routes with warnings
                  </span>
                )}
              </div>

              {visibleRoutes.map((route) => {
                const color = getVehicleColor(route.vehicle_id);
                const isExpanded = expandedRoutes.has(route.vehicle_id);
                const warnings = routeWarnings.get(route.vehicle_id);

                return (
                  <div
                    key={route.vehicle_id}
                    className={`bg-dark-bg rounded-lg border overflow-hidden ${
                      warnings ? 'border-yellow-500/50' : 'border-dark-border'
                    }`}
                  >
                    <button
                      onClick={() => toggleRoute(route.vehicle_id)}
                      className="w-full p-3 flex items-center gap-4 hover:bg-dark-hover transition-colors"
                    >
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: color.color }}
                      />
                      <div className="flex-1 text-left">
                        <span className="font-medium text-white font-mono">
                          {formatVehicleName(route.vehicle_id)}
                        </span>
                        <span className="text-gray-500 ml-2 text-xs">
                          {getVehiclePlate(route.vehicle_id).name}
                        </span>
                        <span className="text-gray-400 ml-3 text-sm">
                          {route.route.length - 2} stops
                        </span>
                        {warnings && (
                          <AlertTriangle className="w-3 h-3 text-yellow-400 inline ml-2" />
                        )}
                      </div>
                      <div className="text-sm text-gray-400 space-x-4">
                        <span className={route.route_distance > 500 ? 'text-yellow-400' : ''}>
                          {formatDistance(route.route_distance)}
                        </span>
                        <span className={route.route_duration > shiftLimitMinutes ? 'text-yellow-400' : ''}>
                          {formatDuration(route.route_duration)}
                        </span>
                      </div>
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-gray-400" />
                      )}
                    </button>

                    {isExpanded && (
                      <div className="px-4 pb-3 border-t border-dark-border">
                        {/* Warnings */}
                        {warnings && (
                          <div className="mt-2 mb-3 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs text-yellow-400">
                            <div className="flex items-center gap-1 font-medium mb-1">
                              <AlertTriangle className="w-3 h-3" />
                              Route Warnings
                            </div>
                            <ul className="list-disc list-inside space-y-0.5">
                              {warnings.map((w, i) => (
                                <li key={i}>{w}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Route Segments - Drive time vs Job duration breakdown */}
                        {(() => {
                          const segments = calculateRouteSegments(route.route, route.arrival_times || [], stops);
                          const totalDriveTime = segments.filter(s => s.type === 'drive').reduce((sum, s) => sum + s.duration, 0);
                          const totalJobTime = segments.filter(s => s.type === 'job').reduce((sum, s) => sum + s.duration, 0);

                          return segments.length > 0 ? (
                            <div className="mt-3 space-y-2">
                              {/* Time breakdown summary */}
                              <div className="flex items-center gap-4 text-xs">
                                <div className="flex items-center gap-1">
                                  <Car className="w-3 h-3 text-blue-400" />
                                  <span className="text-gray-400">Drive:</span>
                                  <span className="text-blue-400 font-medium">{formatDuration(totalDriveTime)}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <Wrench className="w-3 h-3 text-[#C74634]" />
                                  <span className="text-gray-400">Jobs:</span>
                                  <span className="text-[#C74634] font-medium">{formatDuration(totalJobTime)}</span>
                                </div>
                                <div className="text-gray-500">
                                  ({Math.round(totalJobTime / (totalDriveTime + totalJobTime) * 100) || 0}% productive)
                                </div>
                              </div>

                              {/* Detailed segment breakdown */}
                              <div className="flex flex-wrap items-center gap-1 text-xs">
                                <span className="px-2 py-1 rounded bg-[#C74634]/20 text-[#C74634]">
                                  Depot
                                </span>
                                {segments.map((segment, idx) => (
                                  <div key={idx} className="flex items-center gap-1">
                                    <span className="text-gray-500">→</span>
                                    {segment.type === 'drive' ? (
                                      <span className="px-2 py-1 rounded bg-blue-500/10 text-blue-400 whitespace-nowrap">
                                        <Car className="w-3 h-3 inline mr-1" />
                                        {formatDuration(segment.duration)}
                                      </span>
                                    ) : (
                                      <span
                                        className="px-2 py-1 rounded whitespace-nowrap"
                                        style={{
                                          backgroundColor: `${segment.color}20`,
                                          color: segment.color,
                                        }}
                                      >
                                        <Wrench className="w-3 h-3 inline mr-1" />
                                        {segment.label} ({formatDuration(segment.duration)})
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : (
                            // Fallback to simple route display if no service durations
                            <div className="flex flex-wrap gap-2 mt-3">
                              {route.route.map((stopId, idx) => (
                                <div
                                  key={idx}
                                  className="flex items-center gap-1 text-xs"
                                >
                                  <span
                                    className={`px-2 py-1 rounded ${
                                      idx === 0 || idx === route.route.length - 1
                                        ? 'bg-[#C74634]/20 text-[#C74634]'
                                        : 'bg-dark-card text-gray-300'
                                    }`}
                                  >
                                    {idx === 0
                                      ? 'Depot'
                                      : idx === route.route.length - 1
                                      ? 'Return'
                                      : `Stop ${stopId}`}
                                  </span>
                                  {idx < route.route.length - 1 && (
                                    <span className="text-gray-500">→</span>
                                  )}
                                </div>
                              ))}
                            </div>
                          );
                        })()}

                        {/* Arrival times (if available and no segment breakdown) */}
                        {route.arrival_times && route.arrival_times.length > 0 && (
                          <div className="mt-2 text-xs text-gray-500">
                            Arrival times:{' '}
                            {route.arrival_times.map((t) => formatDuration(t)).join(', ')}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}

              {/* Pagination controls */}
              <div className="flex justify-center gap-2 pt-2">
                {hasMoreRoutes && (
                  <button
                    onClick={handleShowMore}
                    className="px-4 py-2 text-sm text-[#C74634] hover:bg-[#C74634]/10 rounded-lg transition-colors"
                  >
                    Load More ({remainingRoutes} remaining)
                  </button>
                )}
                {visibleRoutesCount > 20 && (
                  <button
                    onClick={handleShowLess}
                    className="px-4 py-2 text-sm text-gray-400 hover:bg-dark-hover rounded-lg transition-colors flex items-center gap-1"
                  >
                    <ChevronUp className="w-4 h-4" />
                    Show Less
                  </button>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
