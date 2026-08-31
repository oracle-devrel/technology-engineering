import { useCallback, useState } from 'react';
import { InputPanel } from './InputPanel';
import { ResultsPanel } from './ResultsPanel';
import { RouteMap } from '@/components/Map/RouteMap';
import { GoogleRouteMap } from '@/components/Map/GoogleRouteMap';
import { PerformanceChart } from '@/components/Metrics/PerformanceChart';
import { OperationalImpactPanel } from '@/components/Metrics/OperationalImpactPanel';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/shared/Card';
import { useOptimizationStore, useAppStore } from '@/store';
import { useConfigStore } from '@/store/configStore';
import { BarChart3, MapPin, Target } from 'lucide-react';
import { cuoptClient } from '@/api';

// Convert "HH:MM" time string to minutes from midnight
function timeToMinutes(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + (minutes || 0);
}

export function Dashboard() {
  const {
    setResult,
    updateParallelJob,
    clearParallelJobs,
    setDebugData,
  } = useOptimizationStore();

  const { setIsOptimizing, addToast, mapProvider, setMapProvider } = useAppStore();
  const { config: appConfig } = useConfigStore();
  const [rightPanelView, setRightPanelView] = useState<'impact' | 'performance'>('impact');

  const handleRunOptimization = useCallback(async () => {
    // Always get the LATEST config from store to ensure user's manual changes are respected
    const currentState = useOptimizationStore.getState();
    const currentConfig = currentState.config;
    const currentStops = currentState.stops;

    if (currentStops.length === 0) {
      addToast({
        type: 'warning',
        title: 'No stops configured',
        message: 'Please add stops before running optimization',
      });
      return;
    }

    // Validate capacity is sufficient for max demand
    const maxDemand = Math.max(...currentStops.map((s) => s.demand));
    if (currentConfig.vehicleCapacity < maxDemand) {
      addToast({
        type: 'error',
        title: 'Invalid Configuration',
        message: `Vehicle capacity (${currentConfig.vehicleCapacity}) must be at least ${maxDemand} to handle largest stop demand`,
      });
      return;
    }

    // Log current config for debugging
    console.log(`[Optimization] Using config: ${currentConfig.numVehicles} vehicles, ${currentConfig.vehicleCapacity} capacity`);

    // Smart auto-selection based on parallel mode and stop count
    const parallelMode = currentConfig.parallelMode || 'auto';
    let useParallel = false;
    let numClusters = 1;

    if (parallelMode === 'single') {
      useParallel = false;
      numClusters = 1;
    } else if (parallelMode === 'parallel') {
      useParallel = true;
      numClusters = Math.min(Math.max(currentConfig.parallelJobs || 2, 2), 8);
    } else {
      // Auto mode: System decides based on best practices
      // - < 300 stops: Single optimization (better vehicle distribution)
      // - 300-500 stops: Parallel with 2-3 clusters
      // - 500+ stops: Parallel with 4-8 clusters
      if (currentStops.length < 300) {
        useParallel = false;
        numClusters = 1;
      } else if (currentStops.length < 500) {
        useParallel = true;
        numClusters = Math.min(Math.ceil(currentStops.length / 200), 3);
      } else {
        useParallel = true;
        numClusters = Math.min(Math.ceil(currentStops.length / 150), 8);
      }
    }

    console.log(`[Optimization] Mode: ${parallelMode}, Stops: ${currentStops.length}, Using: ${useParallel ? `parallel (${numClusters} clusters)` : 'single'}`);

    setIsOptimizing(true);
    const startTime = Date.now();

    try {
      const workingStart = timeToMinutes(appConfig.workingHoursStart || '08:00');
      const workingEnd = timeToMinutes(appConfig.workingHoursEnd || '18:00');

      if (!useParallel) {
        // Single optimization - best for smaller datasets
        const vehicles = Array.from({ length: currentConfig.numVehicles }, (_, i) => ({
          id: i,
          capacity: currentConfig.vehicleCapacity,
          startLat: currentConfig.enableHomeStart ? currentStops[0]?.lat + (Math.random() - 0.5) * 0.05 : currentStops[0]?.lat || 54.5,
          startLng: currentConfig.enableHomeStart ? currentStops[0]?.lng + (Math.random() - 0.5) * 0.05 : currentStops[0]?.lng || -2.0,
          timeWindowStart: workingStart,
          timeWindowEnd: workingEnd,
        }));

        const payload = cuoptClient.buildPayload(currentStops, vehicles, currentConfig);

        // Set debug data - request (before optimization)
        setDebugData({
          request: payload,
          prompt: `Manual optimization: ${currentStops.length} stops, ${currentConfig.numVehicles} vehicles`,
          source: 'manual',
        });

        const result = await cuoptClient.solveVRP(payload);

        // Set debug data - response (after optimization)
        setDebugData({ response: result });

        const solveTime = (Date.now() - startTime) / 1000;
        setResult({ ...result, solve_time: solveTime });

        addToast({
          type: 'success',
          title: 'Optimization Complete',
          message: `Found solution with ${result.num_vehicles} vehicles in ${solveTime.toFixed(2)}s`,
        });
      } else {
        // Parallel optimization - for larger datasets
        clearParallelJobs();
        const clusters = cuoptClient.clusterStops(currentStops, numClusters);
        const vehiclesPerCluster = Math.ceil(currentConfig.numVehicles / clusters.length);

        // Initialize parallel jobs
        clusters.forEach((cluster, idx) => {
          updateParallelJob({
            jobId: `job-${idx + 1}`,
            clusterId: idx + 1,
            status: 'queued',
            stops: cluster.length,
          });
        });

        const payloads = clusters.map((cluster) => {
          const clusterCenterLat = cluster.reduce((sum, s) => sum + s.lat, 0) / cluster.length;
          const clusterCenterLng = cluster.reduce((sum, s) => sum + s.lng, 0) / cluster.length;

          const vehicles = Array.from({ length: vehiclesPerCluster }, (_, i) => ({
            id: i,
            capacity: currentConfig.vehicleCapacity,
            startLat: currentConfig.enableHomeStart ? clusterCenterLat + (Math.random() - 0.5) * 0.1 : 0,
            startLng: currentConfig.enableHomeStart ? clusterCenterLng + (Math.random() - 0.5) * 0.1 : 0,
            timeWindowStart: workingStart,
            timeWindowEnd: workingEnd,
          }));
          return cuoptClient.buildPayload(cluster, vehicles, currentConfig);
        });

        // Set debug data - request (first payload for parallel)
        setDebugData({
          request: { parallel: true, clusters: numClusters, payloads },
          prompt: `Parallel optimization: ${currentStops.length} stops, ${currentConfig.numVehicles} vehicles, ${numClusters} clusters`,
          source: 'manual',
        });

        const results = await cuoptClient.solveParallel(
          payloads,
          numClusters,
          (_completed, _total, partialResults) => {
            for (let idx = 0; idx < partialResults.length; idx++) {
              const result = partialResults[idx];
              if (result) {
                updateParallelJob({
                  jobId: `job-${idx + 1}`,
                  clusterId: idx + 1,
                  status: 'completed',
                  stops: clusters[idx].length,
                  solveTime: result.solve_time,
                  result,
                });
              }
            }
          },
          (jobIndex) => {
            updateParallelJob({
              jobId: `job-${jobIndex + 1}`,
              clusterId: jobIndex + 1,
              status: 'running',
              stops: clusters[jobIndex].length,
            });
          },
          (jobIndex, error) => {
            updateParallelJob({
              jobId: `job-${jobIndex + 1}`,
              clusterId: jobIndex + 1,
              status: 'failed',
              stops: clusters[jobIndex].length,
              error: error.message,
            });
          }
        );

        // Merge results with proper route remapping
        let globalVehicleId = 0;
        const mergedVehicleData = results.flatMap((r, clusterIdx) => {
          if (!r) return [];
          const clusterStops = clusters[clusterIdx];

          return (r.vehicle_data || []).map((v: any) => {
            const remappedRoute = (v.route || []).map((idx: number) => {
              if (idx === 0) return 0;
              const clusterStopIndex = idx - 1;
              if (clusterStopIndex >= 0 && clusterStopIndex < clusterStops.length) {
                return clusterStops[clusterStopIndex].id;
              }
              return idx;
            });

            return {
              ...v,
              route: remappedRoute,
              vehicle_id: globalVehicleId++,
              cluster_id: clusterIdx,
            };
          });
        });

        const mergedResult = {
          status: 'SUCCESS' as const,
          num_vehicles: mergedVehicleData.length,
          solution_cost: results.reduce((sum, r) => sum + (r?.solution_cost || 0), 0),
          solve_time: Math.max(...results.map(r => r?.solve_time || 0)),
          vehicle_data: mergedVehicleData,
        };

        setResult(mergedResult);

        // Set debug data - response (merged result for parallel)
        setDebugData({ response: mergedResult });

        addToast({
          type: 'success',
          title: 'Parallel Optimization Complete',
          message: `${numClusters} clusters, ${mergedVehicleData.length} vehicles in ${mergedResult.solve_time.toFixed(2)}s`,
        });
      }
    } catch (error) {
      addToast({
        type: 'error',
        title: 'Optimization Failed',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      });
    } finally {
      setIsOptimizing(false);
    }
  }, [appConfig, setResult, setIsOptimizing, addToast, clearParallelJobs, updateParallelJob, setDebugData]);

  return (
    <div className="flex h-full">
      {/* Left Panel - Input */}
      <InputPanel
        onRunOptimization={handleRunOptimization}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Top - Map */}
        <div className="h-1/2 p-4 pb-2">
          <Card variant="bordered" padding="none" className="h-full overflow-hidden relative">
            {/* Map Provider Toggle - z-[1001] to be above Leaflet controls */}
            <div className="absolute top-3 left-3 z-[1001] flex bg-dark-card border border-dark-border rounded-lg overflow-hidden shadow-lg">
              <button
                onClick={() => setMapProvider('google')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                  mapProvider === 'google'
                    ? 'bg-[#C74634] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-dark-hover'
                }`}
                title="Google Maps with Traffic & Directions"
              >
                <MapPin className="w-3.5 h-3.5" />
                Google
              </button>
              <button
                onClick={() => setMapProvider('leaflet')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                  mapProvider === 'leaflet'
                    ? 'bg-[#C74634] text-white'
                    : 'text-gray-400 hover:text-white hover:bg-dark-hover'
                }`}
                title="OpenStreetMap (Free)"
              >
                <MapPin className="w-3.5 h-3.5" />
                Leaflet
              </button>
            </div>

            {/* Render both maps but only show active one */}
            <div className={`h-full w-full ${mapProvider === 'google' ? 'block' : 'hidden'}`}>
              <GoogleRouteMap />
            </div>
            <div className={`h-full w-full ${mapProvider === 'leaflet' ? 'block' : 'hidden'}`}>
              <RouteMap isActive={mapProvider === 'leaflet'} />
            </div>
          </Card>
        </div>

        {/* Bottom - Results and Charts */}
        <div className="h-1/2 flex overflow-hidden">
          <div className="w-1/2 h-full overflow-hidden">
            <ResultsPanel />
          </div>
          <div className="w-1/2 p-4 pl-2">
            <div className="h-full flex flex-col">
              {/* Tab Buttons */}
              <div className="flex border-b border-dark-border mb-2">
                <button
                  onClick={() => setRightPanelView('impact')}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
                    rightPanelView === 'impact'
                      ? 'text-green-400 border-b-2 border-green-400'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  title="Field service efficiency metrics"
                >
                  <Target className="w-4 h-4" />
                  Impact
                </button>
                <button
                  onClick={() => setRightPanelView('performance')}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors ${
                    rightPanelView === 'performance'
                      ? 'text-[#C74634] border-b-2 border-[#C74634]'
                      : 'text-gray-400 hover:text-white'
                  }`}
                  title="Solver speed & planning efficiency"
                >
                  <BarChart3 className="w-4 h-4" />
                  Performance
                </button>
              </div>

              {/* Panel Content */}
              <div className="flex-1 overflow-hidden">
                {rightPanelView === 'impact' && (
                  <Card variant="bordered" className="h-full">
                    <CardHeader>
                      <CardTitle>Operational Impact</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[calc(100%-60px)] overflow-hidden">
                      <OperationalImpactPanel />
                    </CardContent>
                  </Card>
                )}
                {rightPanelView === 'performance' && (
                  <Card variant="bordered" className="h-full">
                    <CardHeader>
                      <CardTitle>Performance</CardTitle>
                    </CardHeader>
                    <CardContent className="h-[calc(100%-60px)]">
                      <PerformanceChart />
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
