import { useState, useCallback } from 'react';
import { MessageSquare, Send, Sparkles, Loader2, ChevronUp, ChevronDown } from 'lucide-react';
import { Button } from '@/components/shared/Button';
import { useOptimizationStore, useAppStore, useConfigStore } from '@/store';
import { genaiClient, cuoptClient } from '@/api';

// Convert "HH:MM" time string to minutes from midnight
function timeToMinutes(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + (minutes || 0);
}

interface MiniChatProps {
  onOptimizationComplete?: () => void;
}

export function MiniChat({ onOptimizationComplete }: MiniChatProps) {
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const { setStops, setResult, config, setConfig, updateParallelJob, clearParallelJobs } = useOptimizationStore();
  const { addToast, setIsOptimizing } = useAppStore();
  const { config: appConfig } = useConfigStore();

  const handleSend = useCallback(async () => {
    if (!prompt.trim() || isProcessing) return;

    setIsProcessing(true);
    setIsOptimizing(true);
    setLastResponse(null);

    try {
      // Step 1: Classify intent
      const intentResult = await genaiClient.classifyIntent(prompt);

      if (intentResult.intent === 'greeting' || intentResult.intent === 'question') {
        setLastResponse(intentResult.answer || "I can help you optimize routes! Try: 'Optimize 50 deliveries with 5 vehicles'");
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Step 2: Convert prompt to cuOPT request
      const { request, interpretation, error, numVehicles, stops: generatedStops } =
        await genaiClient.convertPromptToCuOpt(prompt);

      if (error || !request) {
        setLastResponse(`Could not understand request. ${interpretation || error || 'Please try rephrasing.'}`);
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Use generated stops
      const stops = generatedStops || [];
      if (stops.length === 0) {
        setLastResponse('No stops generated. Please specify location and number of stops.');
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Update config based on extracted parameters
      const vehicleCount = numVehicles || config.numVehicles;
      if (numVehicles) {
        setConfig({ numVehicles });
      }

      // Get working hours for vehicles
      const workingStart = timeToMinutes(appConfig.workingHoursStart || '08:00');
      const workingEnd = timeToMinutes(appConfig.workingHoursEnd || '18:00');

      // Use parallel clustering for large datasets (200+ stops) to avoid payload size issues
      const useParallel = stops.length >= 200;
      const numClusters = useParallel ? Math.min(Math.ceil(stops.length / 150), 8) : 1;

      setLastResponse(`${interpretation}\n\n${useParallel ? `Using parallel processing (${numClusters} clusters)...` : 'Optimizing...'}`);

      let result;

      if (useParallel) {
        // Clear previous parallel jobs and cluster stops for parallel processing
        clearParallelJobs();
        const clusters = cuoptClient.clusterStops(stops, numClusters);
        const vehiclesPerCluster = Math.max(1, Math.ceil(vehicleCount / numClusters));

        // Initialize parallel jobs in dashboard (1-indexed for user display)
        clusters.forEach((cluster, idx) => {
          updateParallelJob({
            jobId: `job-${idx + 1}`,
            clusterId: idx + 1,
            status: 'queued',
            stops: cluster.length,
          });
        });

        // Calculate total vehicles actually used in parallel mode
        const totalVehiclesInParallel = vehiclesPerCluster * numClusters;

        // Update config to reflect actual vehicles being used
        if (totalVehiclesInParallel !== vehicleCount) {
          setConfig({ numVehicles: totalVehiclesInParallel });
        }

        const payloads = clusters.map((cluster) => {
          const vehicles = Array.from({ length: vehiclesPerCluster }, (_, i) => ({
            id: i,
            capacity: config.vehicleCapacity,
            startLat: cluster[0]?.lat || 51.5,
            startLng: cluster[0]?.lng || -0.1,
            timeWindowStart: workingStart,
            timeWindowEnd: workingEnd,
          }));
          return cuoptClient.buildPayload(cluster, vehicles, {
            ...config,
            numVehicles: vehiclesPerCluster,
            enableTimeWindows: true,
          });
        });

        // Run parallel optimization with progress tracking
        const results = await cuoptClient.solveParallel(
          payloads,
          numClusters,
          // Progress callback - update completed jobs
          (_completed, _total, partialResults) => {
            for (let idx = 0; idx < partialResults.length; idx++) {
              const partialResult = partialResults[idx];
              if (partialResult) {
                updateParallelJob({
                  jobId: `job-${idx + 1}`,
                  clusterId: idx + 1,
                  status: 'completed',
                  stops: clusters[idx].length,
                  solveTime: partialResult.solve_time,
                  result: partialResult,
                });
              }
            }
          },
          // Job start callback
          (jobIndex) => {
            updateParallelJob({
              jobId: `job-${jobIndex + 1}`,
              clusterId: jobIndex + 1,
              status: 'running',
              stops: clusters[jobIndex].length,
            });
          },
          // Job error callback
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
        // cuOPT returns: 0 = depot, 1 = first stop in cluster, 2 = second stop, etc.
        // We need to convert these to original stop IDs
        let globalVehicleId = 0;
        const mergedVehicleData = results.flatMap((r, clusterIdx) => {
          if (!r) return [];
          const clusterStops = clusters[clusterIdx];

          return (r.vehicle_data || []).map((v: any) => {
            // Remap route indices to original stop IDs
            const remappedRoute = (v.route || []).map((idx: number) => {
              if (idx === 0) return 0; // Depot stays 0
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

        result = {
          status: 'SUCCESS' as const,
          num_vehicles: mergedVehicleData.length,
          solution_cost: results.reduce((sum, r) => sum + (r?.solution_cost || 0), 0),
          solve_time: Math.max(...results.map(r => r?.solve_time || 0)),
          vehicle_data: mergedVehicleData,
        };
      } else {
        // Single optimization for smaller datasets
        const vehicles = Array.from({ length: vehicleCount }, (_, i) => ({
          id: i,
          capacity: config.vehicleCapacity,
          startLat: stops[0]?.lat || 51.5,
          startLng: stops[0]?.lng || -0.1,
          timeWindowStart: workingStart,
          timeWindowEnd: workingEnd,
        }));

        const payload = cuoptClient.buildPayload(stops, vehicles, {
          ...config,
          numVehicles: vehicleCount,
          enableTimeWindows: true,
        });

        result = await cuoptClient.solveVRP(payload);
      }

      // Sync to Route Optimizer
      setStops(stops);
      setResult(result);

      // Generate summary
      const totalDistance = result.vehicle_data?.reduce((sum: number, v: any) => sum + (v.route_distance || 0), 0) || 0;
      const stopsServed = result.vehicle_data?.reduce((sum: number, v: any) => sum + Math.max(0, (v.route?.length || 0) - 2), 0) || 0;

      setLastResponse(
        `Optimization complete!\n` +
        `${result.num_vehicles || 0} vehicles assigned\n` +
        `${stopsServed}/${stops.length} stops served\n` +
        `${totalDistance.toFixed(1)} km total distance\n` +
        `Solve time: ${(result.solve_time || 0).toFixed(2)}s` +
        (useParallel ? `\n(${numClusters} parallel clusters)` : '')
      );

      addToast({
        type: 'success',
        title: 'AI Optimization Complete',
        message: `${stopsServed} stops served with ${result.num_vehicles || 0} vehicles`,
      });

      onOptimizationComplete?.();
      setPrompt('');
    } catch (error) {
      setLastResponse(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      addToast({
        type: 'error',
        title: 'Optimization Failed',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
    } finally {
      setIsProcessing(false);
      setIsOptimizing(false);
    }
  }, [prompt, isProcessing, config, appConfig, setStops, setResult, setConfig, setIsOptimizing, addToast, onOptimizationComplete, updateParallelJob, clearParallelJobs]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickPrompts = [
    '50 deliveries in London',
    '100 stops with 10 vehicles',
    '200 parcels across UK',
  ];

  return (
    <div className="border-t border-dark-border bg-dark-card/50">
      {/* Header - Collapsible */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 hover:bg-dark-hover transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#C74634]" />
          <span className="text-sm font-medium text-white">AI Assistant</span>
          {isProcessing && <Loader2 className="w-3 h-3 animate-spin text-[#C74634]" />}
        </div>
        {isExpanded ? (
          <ChevronDown className="w-4 h-4 text-gray-400" />
        ) : (
          <ChevronUp className="w-4 h-4 text-gray-400" />
        )}
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          {/* Quick Prompts */}
          <div className="flex flex-wrap gap-1">
            {quickPrompts.map((qp, idx) => (
              <button
                key={idx}
                onClick={() => setPrompt(qp)}
                className="px-2 py-1 text-xs bg-dark-bg border border-dark-border rounded-full text-gray-400 hover:text-[#C74634] hover:border-[#C74634]/50 transition-colors"
              >
                {qp}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="flex gap-2">
            <div className="flex-1 relative">
              <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Describe your routing problem..."
                disabled={isProcessing}
                className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#C74634] disabled:opacity-50"
              />
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSend}
              disabled={!prompt.trim() || isProcessing}
              className="px-3"
            >
              {isProcessing ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>

          {/* Response */}
          {lastResponse && (
            <div className="p-3 bg-dark-bg border border-dark-border rounded-lg">
              <p className="text-xs text-gray-300 whitespace-pre-line">{lastResponse}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
