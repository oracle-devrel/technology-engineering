import { useState, useCallback, useRef, useMemo } from 'react';
import {
  Sparkles,
  Send,
  Loader2,
  ChevronDown,
  ChevronRight,
  Settings,
  Bug,
  Copy,
  Check,
  Truck,
  MapPin,
  Play,
  RotateCcw,
  Upload,
  Shuffle,
  Battery,
  Briefcase,
} from 'lucide-react';
import { Button } from '@/components/shared/Button';
import { Slider } from '@/components/shared/Slider';
import { Select } from '@/components/shared/Select';
import { Toggle } from '@/components/shared/Toggle';
import { useOptimizationStore, useAppStore, useConfigStore, useWeatherStore } from '@/store';
import { genaiClient, cuoptClient } from '@/api';
import { COUNTRIES, generateDynamicScenarios, formatCurrency } from '@/data/locationData';
import { evStationsToStops, filterEVStationsByLocation } from '@/data/evChargingData';
import { generateRandomStops } from '@/data/benchmarkData';
import type { Stop, JobType } from '@/types';
import { JOB_TYPE_CONFIGS, DEFAULT_JOB_TYPE_MIX } from '@/types/cuopt';

// Convert "HH:MM" time string to minutes from midnight
function timeToMinutes(timeStr: string): number {
  const [hours, minutes] = timeStr.split(':').map(Number);
  return hours * 60 + (minutes || 0);
}

interface AIAssistantProps {
  onRunOptimization: () => void;
}

export function AIAssistant({ onRunOptimization }: AIAssistantProps) {
  // Local state
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [detailedResponse, setDetailedResponse] = useState<string | null>(null);
  const [isGeneratingResponse, setIsGeneratingResponse] = useState(false);
  const [showDebug, setShowDebug] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // Collapsible sections
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    fleet: false,
    stops: false,
    solver: false,
    jobTypes: false,
    debug: false,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Store hooks
  const {
    stops,
    config,
    setConfig,
    setStops,
    setResult,
    updateParallelJob,
    clearParallelJobs,
    reset,
    debugData,
    setDebugData,
    clearDebugData,
  } = useOptimizationStore();
  const { setIsOptimizing, addToast, isOptimizing } = useAppStore();
  const { config: appConfig, setCountry, setCity } = useConfigStore();
  const { fetchWeatherForStops, fetchRoutingImpacts, clearWeather } = useWeatherStore();

  // Get current country and city
  const currentCountry = COUNTRIES.find(c => c.code === appConfig.countryCode) || COUNTRIES[0];
  const currentCity = currentCountry.cities.find(c => c.id === appConfig.cityId) || currentCountry.cities[0];

  // Check if Belron scenario
  const { isBelronScenario } = useConfigStore();
  const isBelron = isBelronScenario();

  // Generate dynamic scenarios for current location
  const scenarios = generateDynamicScenarios(appConfig.countryCode, appConfig.cityId, 'generic');

  // Calculate required vehicles based on current stops and shift limits
  const vehicleEstimate = useMemo(() => {
    if (stops.length === 0) return null;

    const shiftHours = config.shiftHours ?? 8;
    const defaultServiceTime = config.defaultServiceTime ?? 30;

    return cuoptClient.estimateRequiredVehicles(stops, shiftHours, defaultServiceTime);
  }, [stops, config.shiftHours, config.defaultServiceTime]);

  // Check if configured vehicles are insufficient
  const vehicleShortage = useMemo(() => {
    if (!vehicleEstimate) return 0;
    return Math.max(0, vehicleEstimate.minVehicles - config.numVehicles);
  }, [vehicleEstimate, config.numVehicles]);

  // Toggle section
  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Copy to clipboard
  const copyToClipboard = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch {
      addToast({ type: 'error', title: 'Copy failed', message: 'Could not copy to clipboard' });
    }
  };

  // Handle AI optimization
  const handleSend = useCallback(async () => {
    if (!prompt.trim() || isProcessing) return;

    setIsProcessing(true);
    setIsOptimizing(true);
    setLastResponse(null);
    clearDebugData();

    try {
      // Set the AI model from configuration before making API calls
      genaiClient.setModel(appConfig.aiModel || 'openai.gpt-4o-mini');

      // Step 1: Classify intent
      const intentResult = await genaiClient.classifyIntent(prompt);

      if (intentResult.intent === 'greeting' || intentResult.intent === 'question') {
        setLastResponse(intentResult.answer || "I can help you optimize routes! Try: 'Optimize 50 deliveries in London with 5 vehicles'");
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Step 2: Convert prompt to cuOPT request with current location context
      const locationContext = {
        countryName: currentCountry?.name,
        cityName: currentCity?.name,
        centerLat: currentCity?.coordinates?.lat,
        centerLng: currentCity?.coordinates?.lng,
        radiusKm: currentCity?.serviceRadius,
      };

      const {
        request,
        interpretation,
        error,
        numVehicles,
        vehicleCapacity: extractedCapacity,
        stops: generatedStops,
        extractedConfig,
      } = await genaiClient.convertPromptToCuOpt(prompt, locationContext);

      setDebugData({ prompt: interpretation || prompt, source: 'ai' });

      if (error || !request) {
        setLastResponse(`Could not understand request. ${interpretation || error || 'Please try rephrasing.'}`);
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Smart stop selection logic:
      // Use loaded stops ONLY if user didn't explicitly request a specific number
      let stopsToUse: Stop[];
      let usingExistingStops = false;

      const promptLower = prompt.toLowerCase();

      // Check if user explicitly mentioned a NUMBER of stops/deliveries in their prompt
      const numberMatch = prompt.match(/(\d+)\s*(stop|deliver|location|point|job|order)/i);
      const userSpecifiedCount = numberMatch ? parseInt(numberMatch[1]) : null;

      // Check if user explicitly wants NEW/DIFFERENT stops
      const wantsNewStops = (promptLower.includes('generate') || promptLower.includes('create new')) &&
        !promptLower.includes('route');

      // Check if user mentioned "all", "loaded", "these", "EV stations" - wants existing stops
      const wantsExistingStops = (promptLower.includes('all ') && !userSpecifiedCount) ||
        promptLower.includes('loaded') ||
        promptLower.includes('these') ||
        promptLower.includes('ev station') ||
        promptLower.includes('charging station');

      // User explicitly requested a different number (50% difference threshold)
      const userRequestedDifferentCount = userSpecifiedCount && stops.length > 0 &&
        Math.abs(userSpecifiedCount - stops.length) > stops.length * 0.5; // >50% difference

      // Decision logic:
      // 1. If user wants existing (said "all", "loaded", "EV stations") → use loaded
      // 2. If user specified a number that's different from loaded → generate new
      // 3. If user wants new stops explicitly → generate new
      // 4. If stops loaded and user didn't specify a number → use loaded
      // 5. Otherwise → generate

      if (wantsExistingStops && stops.length > 0) {
        // User explicitly wants loaded stops
        stopsToUse = stops;
        usingExistingStops = true;
        console.log(`[AI Assistant] User wants existing stops, using ${stops.length} loaded stops`);
      } else if (userRequestedDifferentCount || wantsNewStops) {
        // User wants a different number or explicitly wants new stops
        if (generatedStops && generatedStops.length > 0) {
          stopsToUse = generatedStops;
          console.log(`[AI Assistant] User requested ${userSpecifiedCount || 'new'} stops (loaded: ${stops.length}), using ${generatedStops.length} generated stops`);
        } else {
          setLastResponse(`Cannot generate ${userSpecifiedCount} stops. Please try again.`);
          setIsProcessing(false);
          setIsOptimizing(false);
          return;
        }
      } else if (stops.length > 0 && !userSpecifiedCount) {
        // User has loaded stops and didn't specify a number → use loaded
        stopsToUse = stops;
        usingExistingStops = true;
        console.log(`[AI Assistant] No count specified, using ${stops.length} loaded stops`);
      } else if (generatedStops && generatedStops.length > 0) {
        // No loaded stops, use generated
        stopsToUse = generatedStops;
        console.log(`[AI Assistant] No loaded stops, using ${generatedStops.length} AI-generated stops`);
      } else {
        setLastResponse('No stops available. Please load stops via CSV, Quick Start, or describe a location with number of stops.');
        setIsProcessing(false);
        setIsOptimizing(false);
        return;
      }

      // Priority: AI-extracted values > Dashboard config
      // Only use config as fallback when AI doesn't extract a value
      const vehicleCount = numVehicles || config.numVehicles;
      const effectiveCapacity = extractedCapacity || config.vehicleCapacity;
      const effectiveTimeLimit = extractedConfig?.timeLimit || config.timeLimit;

      // Update dashboard to reflect AI-extracted values
      if (numVehicles) {
        setConfig({ numVehicles });
      }
      if (extractedCapacity) {
        setConfig({ vehicleCapacity: extractedCapacity });
      }

      // Get working hours for vehicles
      const workingStart = timeToMinutes(appConfig.workingHoursStart || '08:00');
      const workingEnd = timeToMinutes(appConfig.workingHoursEnd || '18:00');

      // Smart parallel mode selection based on config and best practices
      const parallelMode = config.parallelMode || 'auto';
      let useParallel = false;
      let numClusters = 1;
      let modeReason = '';

      if (parallelMode === 'single') {
        // Manual: Always single optimization
        useParallel = false;
        numClusters = 1;
        modeReason = 'Single mode (manual)';
      } else if (parallelMode === 'parallel') {
        // Manual: Always parallel optimization
        useParallel = true;
        numClusters = Math.min(Math.max(config.parallelJobs || 2, 2), 8);
        modeReason = `Parallel mode (manual, ${numClusters} clusters)`;
      } else {
        // Auto mode: System decides based on best practices
        // Best practice thresholds:
        // - < 300 stops: Single optimization (better vehicle distribution, constraint satisfaction)
        // - 300-500 stops: Parallel with 2-3 clusters (balance of performance and distribution)
        // - 500+ stops: Parallel with 4-8 clusters (performance priority)

        if (stopsToUse.length < 300) {
          // Single optimization for better vehicle utilization and constraint satisfaction
          useParallel = false;
          numClusters = 1;
          modeReason = 'Auto: Single (best vehicle distribution for <300 stops)';
        } else if (stopsToUse.length < 500) {
          // Moderate parallel for balance
          useParallel = true;
          numClusters = Math.min(Math.ceil(stopsToUse.length / 200), 3);
          modeReason = `Auto: Parallel (${numClusters} clusters for 300-500 stops)`;
        } else {
          // Higher parallel for large datasets
          useParallel = true;
          numClusters = Math.min(Math.ceil(stopsToUse.length / 150), 8);
          modeReason = `Auto: Parallel (${numClusters} clusters for ${stopsToUse.length}+ stops)`;
        }
      }

      console.log(`[Optimization] ${modeReason}, ${stopsToUse.length} stops, ${vehicleCount} vehicles`);

      // Create corrected interpretation with actual stop count (not AI default)
      const locationName = `${currentCity?.name || 'Selected Area'}, ${currentCountry?.name || 'Region'}`;
      const correctedInterpretation = usingExistingStops
        ? `Optimizing ${stopsToUse.length} loaded stops with ${vehicleCount} vehicles in ${locationName}. Vehicle capacity: ${effectiveCapacity} units. Solver time limit: ${effectiveTimeLimit}s.`
        : interpretation;

      setLastResponse(`${correctedInterpretation}\n\n${useParallel ? `Using parallel processing (${numClusters} clusters)...` : 'Using single optimization for best vehicle distribution...'}`);
      setDebugData({ prompt: correctedInterpretation, source: 'ai' });

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      let result: any;

      if (useParallel) {
        // Clear previous parallel jobs and cluster stops
        clearParallelJobs();
        const clusters = cuoptClient.clusterStops(stopsToUse, numClusters);
        const vehiclesPerCluster = Math.max(1, Math.ceil(vehicleCount / numClusters));

        // Initialize parallel jobs in dashboard
        clusters.forEach((cluster, idx) => {
          updateParallelJob({
            jobId: `job-${idx + 1}`,
            clusterId: idx + 1,
            status: 'queued',
            stops: cluster.length,
          });
        });

        const totalVehiclesInParallel = vehiclesPerCluster * numClusters;
        if (totalVehiclesInParallel !== vehicleCount) {
          setConfig({ numVehicles: totalVehiclesInParallel });
        }

        const payloads = clusters.map((cluster) => {
          const clusterDepotLat = cluster[0]?.lat || currentCity.coordinates.lat;
          const clusterDepotLng = cluster[0]?.lng || currentCity.coordinates.lng;

          const vehicles = Array.from({ length: vehiclesPerCluster }, (_, i) => ({
            id: i,
            capacity: effectiveCapacity,
            // If home-start enabled, generate home locations near cluster center
            startLat: config.enableHomeStart ? clusterDepotLat + (Math.random() - 0.5) * 0.05 : 0,
            startLng: config.enableHomeStart ? clusterDepotLng + (Math.random() - 0.5) * 0.05 : 0,
            timeWindowStart: workingStart,
            timeWindowEnd: workingEnd,
          }));
          return cuoptClient.buildPayload(cluster, vehicles, {
            ...config,
            numVehicles: vehiclesPerCluster,
            vehicleCapacity: effectiveCapacity,
            timeLimit: effectiveTimeLimit,
            enableTimeWindows: config.enableTimeWindows,
          });
        });

        // Store debug request
        setDebugData({ request: payloads[0], source: 'ai' });

        // Run parallel optimization with progress tracking
        const results = await cuoptClient.solveParallel(
          payloads,
          numClusters,
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
          (jobIndex) => {
            updateParallelJob({
              jobId: `job-${jobIndex + 1}`,
              clusterId: jobIndex + 1,
              status: 'running',
              stops: clusters[jobIndex].length,
            });
          },
          (jobIndex, err) => {
            updateParallelJob({
              jobId: `job-${jobIndex + 1}`,
              clusterId: jobIndex + 1,
              status: 'failed',
              stops: clusters[jobIndex].length,
              error: err.message,
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

        result = {
          status: 'SUCCESS' as const,
          num_vehicles: mergedVehicleData.length,
          solution_cost: results.reduce((sum, r) => sum + (r?.solution_cost || 0), 0),
          solve_time: Math.max(...results.map(r => r?.solve_time || 0)),
          vehicle_data: mergedVehicleData,
        };

        setDebugData({ response: result });
      } else {
        // Single optimization for smaller datasets
        // For home-start routing, generate random home locations near depot
        const depotLat = stopsToUse[0]?.lat || currentCity.coordinates.lat;
        const depotLng = stopsToUse[0]?.lng || currentCity.coordinates.lng;

        const vehicles = Array.from({ length: vehicleCount }, (_, i) => ({
          id: i,
          capacity: effectiveCapacity,
          // If home-start enabled, generate home locations within ~5km of depot
          startLat: config.enableHomeStart ? depotLat + (Math.random() - 0.5) * 0.05 : 0,
          startLng: config.enableHomeStart ? depotLng + (Math.random() - 0.5) * 0.05 : 0,
          timeWindowStart: workingStart,
          timeWindowEnd: workingEnd,
        }));

        const payload = cuoptClient.buildPayload(stopsToUse, vehicles, {
          ...config,
          numVehicles: vehicleCount,
          vehicleCapacity: effectiveCapacity,
          timeLimit: effectiveTimeLimit,
          enableTimeWindows: config.enableTimeWindows,
        });

        setDebugData({ request: payload, source: 'ai' });

        result = await cuoptClient.solveVRP(payload);
        setDebugData({ response: result });
      }

      // Sync to store
      setStops(stopsToUse);
      setResult(result);

      // Generate summary
      const totalDistance = result.vehicle_data?.reduce((sum: number, v: any) => sum + (v.route_distance || 0), 0) || 0;
      const stopsServed = result.vehicle_data?.reduce((sum: number, v: any) => sum + Math.max(0, (v.route?.length || 0) - 2), 0) || 0;

      // Fetch weather first for quick summary
      let weatherSummary = '';
      let weatherContext = '';
      try {
        await fetchWeatherForStops(stopsToUse);
        await fetchRoutingImpacts(stopsToUse);

        const weatherStore = useWeatherStore.getState();
        const weatherMap = weatherStore.weatherByStop;
        const assessment = weatherStore.overallAssessment;

        if (weatherMap.size > 0) {
          const sampleWeather = Array.from(weatherMap.values())[0];
          if (sampleWeather?.current && typeof sampleWeather.current.temperature === 'number') {
            const temp = sampleWeather.current.temperature.toFixed(0);
            const desc = sampleWeather.current.conditions?.[0]?.description || 'Unknown';
            weatherSummary = `\nWeather: ${desc}, ${temp}°C`;
          }
        }

        if (assessment) {
          const impactLevel = assessment.level || 'none';
          const travelImpact = typeof assessment.travelTimeMultiplier === 'number'
            ? Math.round((assessment.travelTimeMultiplier - 1) * 100)
            : 0;

          if (impactLevel !== 'none') {
            weatherSummary += `\nImpact: ${impactLevel}`;
            if (travelImpact > 0) {
              weatherSummary += ` (+${travelImpact}% travel time)`;
            }
          }
        }
      } catch (weatherErr) {
        console.warn('Weather fetch for summary failed:', weatherErr);
      }

      // Quick summary with weather
      const stopsSource = usingExistingStops ? '(using loaded stops)' : '(AI-generated)';
      const quickSummary = `Optimization complete! ${stopsSource}\n` +
        `${result.num_vehicles || 0} vehicles assigned\n` +
        `${stopsServed}/${stopsToUse.length} stops served\n` +
        `${totalDistance.toFixed(1)} km total distance\n` +
        `Solve time: ${(result.solve_time || 0).toFixed(2)}s` +
        (useParallel ? `\n(${numClusters} parallel clusters)` : '') +
        weatherSummary;

      setLastResponse(quickSummary);
      setDetailedResponse(null);

      addToast({
        type: 'success',
        title: 'AI Optimization Complete',
        message: `${stopsServed} stops served with ${result.num_vehicles || 0} vehicles`,
      });

      // Generate detailed AI response in background with weather
      setIsGeneratingResponse(true);
      const originalPrompt = prompt; // Save prompt before clearing
      try {
        // Build weather context from already-fetched data (no new fetch needed)
        try {
          const weatherStore = useWeatherStore.getState();
          const weatherMap = weatherStore.weatherByStop;
          const assessment = weatherStore.overallAssessment;

          if (weatherMap.size > 0) {
            // Get a sample of weather conditions (first few stops)
            const sampleWeather = Array.from(weatherMap.values()).slice(0, 3);
            const validWeather = sampleWeather.filter(w => w?.current && typeof w.current.temperature === 'number');

            if (validWeather.length > 0) {
              const conditions = validWeather.map(w =>
                `${w.current.conditions?.[0]?.description || 'Unknown'}, ${w.current.temperature.toFixed(0)}°C, ${w.current.humidity ?? 'N/A'}% humidity`
              ).join('; ');

              weatherContext = `Current Weather Conditions:\n`;
              weatherContext += `- Conditions: ${conditions}\n`;
            }

            if (assessment) {
              weatherContext += `- Overall Impact Level: ${assessment.level || 'unknown'}\n`;
              weatherContext += `- Safety Score: ${assessment.safetyScore ?? 'N/A'}/100\n`;
              weatherContext += `- Travel Time Adjustment: ${typeof assessment.travelTimeMultiplier === 'number' ? ((assessment.travelTimeMultiplier - 1) * 100).toFixed(0) : '0'}% increase\n`;

              if (assessment.factors && assessment.factors.length > 0) {
                weatherContext += `- Weather Factors: ${assessment.factors.map(f => `${f.type} (${f.severity})`).join(', ')}\n`;
              }

              if (assessment.recommendations && assessment.recommendations.length > 0) {
                weatherContext += `- Recommendations: ${assessment.recommendations.slice(0, 3).join('; ')}\n`;
              }
            }
          }
        } catch (weatherErr) {
          console.warn('Weather fetch failed, continuing without weather:', weatherErr);
        }

        const detailed = await genaiClient.convertResponseToNaturalLanguage(
          result,
          originalPrompt,
          weatherContext || undefined,
          stopsToUse,
          isBelron ? 'belron' : 'generic',
          currentCity.name
        );
        setDetailedResponse(detailed);
      } catch (err) {
        console.error('Failed to generate detailed response:', err);
        // Show error message as fallback
        setDetailedResponse(`Unable to generate detailed analysis: ${err instanceof Error ? err.message : 'Unknown error'}`);
      } finally {
        setIsGeneratingResponse(false);
      }

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
  }, [prompt, isProcessing, config, appConfig, currentCity, isBelron, setStops, setResult, setConfig, setIsOptimizing, addToast, updateParallelJob, clearParallelJobs, fetchWeatherForStops, fetchRoutingImpacts]);

  // Handle keyboard
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Load scenario - Ask AI version (loads stops on map + fills prompt)
  const handleAskAI = (scenario: any) => {
    const jobTypeMix = config.jobTypeMix || DEFAULT_JOB_TYPE_MIX;

    // Generate stops for scenario with service times (same as handleLoadDirect)
    const newStops: Stop[] = Array.from({ length: scenario.stops }, (_, i) => {
      const rand = Math.random() * 100;
      let cumulative = 0;
      let selectedJobType: JobType = 'delivery';
      let serviceDuration = 30;

      for (const [type, percentage] of Object.entries(jobTypeMix)) {
        cumulative += percentage;
        if (rand <= cumulative) {
          selectedJobType = type as JobType;
          const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];
          serviceDuration = jobConfig?.defaultDuration || 30;
          break;
        }
      }

      const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];

      return {
        id: i + 1,
        lat: currentCity.coordinates.lat + (Math.random() - 0.5) * 0.2,
        lng: currentCity.coordinates.lng + (Math.random() - 0.5) * 0.2,
        demand: Math.floor(Math.random() * 5) + 1,
        label: `${jobConfig?.label || 'Stop'} ${i + 1}`,
        jobType: selectedJobType,
        serviceDuration,
        revenue: jobConfig?.revenue || 0,
      };
    });

    // Load stops on map
    setStops(newStops);
    setConfig({ numVehicles: scenario.vehicles });

    // Fill the prompt for AI optimization
    const promptText = `Optimize ${scenario.stops} deliveries in ${currentCity.name} with ${scenario.vehicles} vehicles`;
    setPrompt(promptText);

    addToast({
      type: 'info',
      title: 'Scenario Ready',
      message: `${scenario.stops} stops loaded. Click Send or Run Optimization to optimize.`,
    });
  };

  // Load scenario - Direct load
  const handleLoadDirect = (scenario: any) => {
    const jobTypeMix = config.jobTypeMix || DEFAULT_JOB_TYPE_MIX;

    // Generate stops for scenario with service times
    const newStops: Stop[] = Array.from({ length: scenario.stops }, (_, i) => {
      // Randomly assign job type based on mix percentages
      const rand = Math.random() * 100;
      let cumulative = 0;
      let selectedJobType: JobType = 'delivery';
      let serviceDuration = 30; // Default 30 min

      for (const [type, percentage] of Object.entries(jobTypeMix)) {
        cumulative += percentage;
        if (rand <= cumulative) {
          selectedJobType = type as JobType;
          const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];
          serviceDuration = jobConfig?.defaultDuration || 30;
          break;
        }
      }

      const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];

      return {
        id: i + 1,
        lat: currentCity.coordinates.lat + (Math.random() - 0.5) * 0.2,
        lng: currentCity.coordinates.lng + (Math.random() - 0.5) * 0.2,
        demand: Math.floor(Math.random() * 5) + 1,
        label: `${jobConfig?.label || 'Stop'} ${i + 1}`,
        jobType: selectedJobType,
        serviceDuration,
        revenue: jobConfig?.revenue || 0,
      };
    });

    setStops(newStops);
    setConfig({ numVehicles: scenario.vehicles });
    addToast({
      type: 'success',
      title: 'Scenario Loaded',
      message: `${scenario.stops} stops loaded for ${currentCity.name} with service times`,
    });
  };

  // CSV upload handler - supports multiple column formats
  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string;
        const lines = text.trim().split('\n');
        if (lines.length < 2) {
          addToast({ type: 'error', title: 'CSV Error', message: 'CSV file is empty or has no data rows' });
          return;
        }

        // Parse header to determine column mapping
        const headerLine = lines[0].toLowerCase();
        const headers = headerLine.split(',').map(h => h.trim());

        // Find column indices (support various column names)
        const latIdx = headers.findIndex(h => h === 'lat' || h === 'latitude');
        const lngIdx = headers.findIndex(h => h === 'lng' || h === 'lon' || h === 'longitude');
        const demandIdx = headers.findIndex(h => h === 'demand' || h === 'quantity' || h === 'weight');
        const labelIdx = headers.findIndex(h => h === 'label' || h === 'name' || h === 'address' || h === 'location');
        const serviceTimeIdx = headers.findIndex(h => h === 'service_time' || h === 'servicetime' || h === 'duration');

        // Validate required columns
        if (latIdx === -1 || lngIdx === -1) {
          addToast({
            type: 'error',
            title: 'CSV Error',
            message: 'CSV must have lat/latitude and lng/lon/longitude columns'
          });
          return;
        }

        const newStops: Stop[] = [];
        let stopId = 1;

        // Parse data rows (skip header)
        for (let i = 1; i < lines.length; i++) {
          const line = lines[i].trim();
          if (!line) continue; // Skip empty lines

          const parts = line.split(',').map(p => p.trim());

          const lat = parseFloat(parts[latIdx]);
          const lng = parseFloat(parts[lngIdx]);

          // Validate coordinates
          if (isNaN(lat) || isNaN(lng)) {
            console.warn(`Skipping row ${i + 1}: Invalid coordinates`);
            continue;
          }

          const demand = demandIdx !== -1 && parts[demandIdx] ? parseInt(parts[demandIdx]) || 1 : 1;
          const label = labelIdx !== -1 && parts[labelIdx] ? parts[labelIdx] : `Stop ${stopId}`;
          const serviceDuration = serviceTimeIdx !== -1 && parts[serviceTimeIdx] ? parseInt(parts[serviceTimeIdx]) || 30 : 30;

          newStops.push({
            id: stopId++,
            lat,
            lng,
            demand,
            label,
            serviceDuration,
          });
        }

        if (newStops.length > 0) {
          setStops(newStops);
          // Update vehicle count suggestion based on stops
          const suggestedVehicles = Math.max(2, Math.ceil(newStops.length / 15));
          if (config.numVehicles < suggestedVehicles) {
            setConfig({ numVehicles: Math.min(suggestedVehicles, 50) });
          }
          addToast({
            type: 'success',
            title: 'CSV Loaded',
            message: `${newStops.length} stops imported. Click "Run Optimization" or use AI Assistant to optimize.`,
          });
        } else {
          addToast({ type: 'error', title: 'CSV Error', message: 'No valid stops found in CSV' });
        }
      } catch (err) {
        console.error('CSV parse error:', err);
        addToast({ type: 'error', title: 'CSV Error', message: 'Failed to parse CSV file. Check console for details.' });
      }
    };
    reader.readAsText(file);
    e.target.value = '';
  };

  // Generate random stops
  const handleGenerateStops = () => {
    const count = config.numVehicles * 10;
    const baseStops = generateRandomStops(
      count,
      currentCity.coordinates.lat,
      currentCity.coordinates.lng,
      appConfig.serviceRadius
    );

    // Get job type configs for service times
    const jobTypeMix = config.jobTypeMix || DEFAULT_JOB_TYPE_MIX;

    // Add service times based on job type mix
    const newStops = baseStops.map((stop, i) => {
      // Randomly assign job type based on mix percentages
      const rand = Math.random() * 100;
      let cumulative = 0;
      let selectedJobType: JobType = 'delivery';
      let serviceDuration = 30; // Default 30 min

      for (const [type, percentage] of Object.entries(jobTypeMix)) {
        cumulative += percentage;
        if (rand <= cumulative) {
          selectedJobType = type as JobType;
          const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];
          serviceDuration = jobConfig?.defaultDuration || 30;
          break;
        }
      }

      const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];

      return {
        ...stop,
        label: `${jobConfig?.label || 'Stop'} ${i + 1}`,
        jobType: selectedJobType,
        serviceDuration,
        revenue: jobConfig?.revenue || 0,
      };
    });

    setStops(newStops);
    addToast({
      type: 'success',
      title: 'Stops Generated',
      message: `${count} random stops created in ${currentCity.name} with service times`,
    });
  };

  // Handle full reset - clears everything including local state
  const handleReset = useCallback(() => {
    // Clear local state
    setPrompt('');
    setLastResponse(null);
    setDetailedResponse(null);
    setIsGeneratingResponse(false);
    clearDebugData();

    // Clear optimization store (stops, routes, results)
    reset();

    // Clear weather data
    clearWeather();

    addToast({
      type: 'info',
      title: 'Reset Complete',
      message: 'All data and results cleared',
    });
  }, [reset, clearWeather, addToast]);

  // Load EV stations - filtered by current city/location
  const handleLoadEVStations = () => {
    // Get current city coordinates
    const centerLat = currentCity?.coordinates?.lat || 51.5074;
    const centerLng = currentCity?.coordinates?.lng || -0.1278;
    const radiusKm = currentCity?.serviceRadius || 75;
    const isUK = appConfig.countryCode === 'GB';

    let evStops: Stop[];
    let locationInfo: string;

    if (isUK) {
      // UK: Use real EV charging station data with location filtering
      const { stations: filteredStations, actualRadius, region } = filterEVStationsByLocation(
        centerLat,
        centerLng,
        radiusKm,
        5 // Minimum 5 stations
      );
      evStops = evStationsToStops(filteredStations);
      locationInfo = actualRadius === -1 ? 'UK-Wide' : `${region} (${actualRadius}km)`;
    } else {
      // Other countries: Generate EV charging station stops
      const numStations = 25; // Reasonable number of EV stations
      const generatedStops = generateRandomStops(numStations, centerLat, centerLng, radiusKm);

      // Add EV-specific metadata to stops
      const evTypes = ['Rapid DC 50kW', 'Ultra-rapid 150kW', 'Fast AC 22kW', 'Standard 7kW'];
      const networks = ['ChargePoint', 'Electrify', 'EVgo', 'Tesla Supercharger', 'Shell Recharge'];

      evStops = generatedStops.map((stop, idx) => ({
        ...stop,
        label: `EV Station ${idx + 1} - ${evTypes[idx % evTypes.length]}`,
        demand: Math.floor(Math.random() * 3) + 1, // 1-3 service visits needed
        metadata: {
          networkName: networks[idx % networks.length],
          powerGroup: evTypes[idx % evTypes.length],
          locationClass: idx % 3 === 0 ? 'En-route' : 'Destination',
        },
      }));
      locationInfo = `${currentCity?.name || 'Selected Area'} (${radiusKm}km)`;
    }

    setStops(evStops);

    // Set appropriate vehicle config for EV service
    const totalDemand = evStops.reduce((sum, s) => sum + s.demand, 0);
    const numVehicles = Math.max(3, Math.ceil(evStops.length / 8));
    const capacityPerVehicle = Math.ceil(totalDemand / numVehicles) + 5;

    setConfig({
      numVehicles,
      vehicleCapacity: capacityPerVehicle,
    });

    addToast({
      type: 'success',
      title: `EV Stations - ${currentCountry?.name || 'Selected Region'}`,
      message: `${evStops.length} charging stations loaded (${locationInfo})`,
    });
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-dark-border bg-dark-card">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[#C74634]" />
          <span className="font-semibold text-white">AI Route Assistant</span>
          {isProcessing && <Loader2 className="w-4 h-4 animate-spin text-[#C74634]" />}
        </div>
        <button
          onClick={() => setShowDebug(!showDebug)}
          className={`p-1.5 rounded transition-colors ${showDebug ? 'bg-[#C74634]/20 text-[#C74634]' : 'text-gray-400 hover:text-white'}`}
          title="Toggle cuOPT Debug"
        >
          <Bug className="w-4 h-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Input Section */}
        <div className="space-y-2">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe your routing problem... e.g., 'Optimize 50 deliveries in London with 5 vehicles'"
            disabled={isProcessing}
            className="w-full h-20 px-3 py-2 bg-dark-bg border border-dark-border rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#C74634] resize-none disabled:opacity-50"
          />

          {/* Location & Send */}
          <div className="flex items-center gap-2">
            <select
              value={appConfig.countryCode}
              onChange={(e) => setCountry(e.target.value)}
              className="px-2 py-1.5 text-sm bg-dark-bg border border-dark-border rounded text-white"
            >
              {COUNTRIES.map(c => (
                <option key={c.code} value={c.code}>{c.flag} {c.name}</option>
              ))}
            </select>
            <select
              value={appConfig.cityId}
              onChange={(e) => setCity(e.target.value)}
              className="flex-1 px-2 py-1.5 text-sm bg-dark-bg border border-dark-border rounded text-white"
            >
              {currentCountry.cities.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
            <Button
              variant="primary"
              size="sm"
              onClick={handleSend}
              disabled={!prompt.trim() || isProcessing}
              className="px-4"
            >
              {isProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Quick Start Scenarios */}
        <div className="space-y-2">
          <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider">Quick Start</h3>
          <div className="space-y-2">
            {scenarios.slice(0, 3).map((scenario, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-dark-bg border border-dark-border rounded-lg">
                <div className="flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-[#C74634]" />
                  <span className="text-sm text-white">{scenario.name}</span>
                  <span className="text-xs text-gray-500">{scenario.stops} stops</span>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleAskAI(scenario)}
                    className="px-2 py-1 text-xs bg-[#C74634]/20 text-[#C74634] rounded hover:bg-[#C74634]/30 transition-colors"
                  >
                    Ask AI
                  </button>
                  <button
                    onClick={() => handleLoadDirect(scenario)}
                    className="px-2 py-1 text-xs bg-dark-hover text-gray-300 rounded hover:bg-dark-border transition-colors"
                  >
                    Load
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Load Data Section - Always Visible */}
        <div className="border border-dark-border rounded-lg p-3 bg-dark-card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#C74634]" />
              <span className="text-sm font-medium text-white">Load Data</span>
              {stops.length > 0 && (
                <span className="text-xs bg-[#C74634]/20 text-[#C74634] px-2 py-0.5 rounded-full font-medium">
                  {stops.length} stops
                </span>
              )}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              onChange={handleCSVUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm bg-dark-bg border border-dark-border rounded-lg text-gray-300 hover:bg-dark-hover hover:border-[#C74634]/50 transition-colors"
            >
              <Upload className="w-4 h-4" /> CSV
            </button>
            <button
              onClick={handleGenerateStops}
              className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm bg-dark-bg border border-dark-border rounded-lg text-gray-300 hover:bg-dark-hover hover:border-[#C74634]/50 transition-colors"
            >
              <Shuffle className="w-4 h-4" /> Random
            </button>
            <button
              onClick={handleLoadEVStations}
              className="flex items-center justify-center gap-1.5 px-3 py-2 text-sm bg-dark-bg border border-dark-border rounded-lg text-gray-300 hover:bg-dark-hover hover:border-[#C74634]/50 transition-colors"
            >
              <Battery className="w-4 h-4" /> EV
            </button>
          </div>
        </div>

        {/* Response Area */}
        {(lastResponse || isGeneratingResponse) && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            {/* Quick Summary Header */}
            {lastResponse && (
              <div className="p-3 bg-gradient-to-r from-[#C74634]/10 to-transparent border-b border-dark-border">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-[#C74634]" />
                  <span className="text-sm font-medium text-white">Optimization Result</span>
                </div>
                <p className="text-sm text-gray-300 whitespace-pre-line font-mono">{lastResponse}</p>
              </div>
            )}

            {/* Detailed AI Response */}
            {isGeneratingResponse && (
              <div className="p-3 bg-dark-bg flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-[#C74634]" />
                <span className="text-sm text-gray-400">Generating detailed analysis...</span>
              </div>
            )}

            {detailedResponse && !isGeneratingResponse && (
              <div className="p-3 bg-dark-bg max-h-64 overflow-y-auto">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-400 uppercase">AI Analysis</span>
                  <button
                    onClick={() => copyToClipboard(detailedResponse, 'detailed')}
                    className="flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 hover:text-white hover:bg-dark-hover rounded transition-colors"
                  >
                    {copiedField === 'detailed' ? (
                      <><Check className="w-3 h-3 text-green-500" /> Copied!</>
                    ) : (
                      <><Copy className="w-3 h-3" /> Copy</>
                    )}
                  </button>
                </div>
                <div className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed prose prose-invert prose-sm max-w-none">
                  {detailedResponse}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Fleet Settings */}
        <div className="border border-dark-border rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('fleet')}
            className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center gap-2">
              <Truck className="w-4 h-4 text-[#C74634]" />
              <span className="text-sm font-medium text-white">Fleet Settings</span>
              <span className="text-xs text-gray-500">({config.numVehicles} vehicles)</span>
            </div>
            {expandedSections.fleet ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
          {expandedSections.fleet && (
            <div className="p-3 space-y-3 border-t border-dark-border">
              <Slider
                min={1}
                max={200}
                value={config.numVehicles}
                onChange={(e) => setConfig({ numVehicles: parseInt(e.target.value) })}
                valueFormatter={(v) => `${v} vehicles`}
              />

              {/* Vehicle shortage warning */}
              {vehicleShortage > 0 && (config.enforceShiftLimits ?? true) && (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-2">
                  <div className="flex items-start gap-2">
                    <span className="text-yellow-500 text-sm">⚠️</span>
                    <div className="flex-1">
                      <p className="text-xs text-yellow-400 font-medium">
                        Need {vehicleEstimate?.minVehicles} vehicles for {config.shiftHours ?? 8}h shifts
                      </p>
                      <p className="text-[10px] text-yellow-500/70 mt-0.5">
                        {stops.length} stops × ~{Math.round((vehicleEstimate?.totalWorkTime || 0) / stops.length)}min avg = {Math.round((vehicleEstimate?.totalWorkTime || 0) / 60)}h total work
                      </p>
                      <button
                        onClick={() => setConfig({ numVehicles: vehicleEstimate?.minVehicles || config.numVehicles })}
                        className="mt-1.5 px-2 py-0.5 text-[10px] bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded transition-colors"
                      >
                        Use {vehicleEstimate?.minVehicles} vehicles
                      </button>
                    </div>
                  </div>
                </div>
              )}
              <Slider
                min={1}
                max={500}
                value={config.vehicleCapacity}
                onChange={(e) => setConfig({ vehicleCapacity: parseInt(e.target.value) })}
                valueFormatter={(v) => `${v} units capacity`}
              />
              <Slider
                min={0}
                max={120}
                step={5}
                value={config.defaultServiceTime || 0}
                onChange={(e) => setConfig({ defaultServiceTime: parseInt(e.target.value) })}
                valueFormatter={(v) => v === 0 ? 'No service time' : `${v} min service`}
              />

              {/* Home-Start Routing */}
              <div className="pt-2 border-t border-dark-border">
                <Toggle
                  label="Home-Start Routing"
                  checked={config.enableHomeStart ?? false}
                  onChange={(e) => setConfig({ enableHomeStart: e.target.checked })}
                />
                <p className="text-[10px] text-gray-500 mt-1 ml-6">Technicians start from home locations</p>
              </div>

              {config.enableHomeStart && (
                <div className="ml-4">
                  <Toggle
                    label="Return to Depot"
                    checked={config.returnToDepot ?? true}
                    onChange={(e) => setConfig({ returnToDepot: e.target.checked })}
                  />
                </div>
              )}

              {/* Revenue Priority */}
              {(config.useJobTypes || isBelron) && (
                <Toggle
                  label="Prioritize by Revenue"
                  checked={config.prioritizeByRevenue ?? false}
                  onChange={(e) => setConfig({ prioritizeByRevenue: e.target.checked })}
                />
              )}

              {/* Shift Limits */}
              <div className="pt-2 border-t border-dark-border">
                <Toggle
                  label="Enforce Shift Limits"
                  checked={config.enforceShiftLimits ?? true}
                  onChange={(e) => setConfig({ enforceShiftLimits: e.target.checked })}
                />
                <p className="text-[10px] text-gray-500 mt-1 ml-6">
                  Force routes to fit within working hours
                </p>
              </div>

              {(config.enforceShiftLimits ?? true) && (
                <div className="ml-4 space-y-2">
                  <div>
                    <label className="text-xs text-gray-400">Shift Duration: {config.shiftHours ?? 8}h</label>
                    <input
                      type="range"
                      min="4"
                      max="12"
                      value={config.shiftHours ?? 8}
                      onChange={(e) => {
                        const hours = parseInt(e.target.value);
                        setConfig({
                          shiftHours: hours,
                          maxRouteDuration: hours * 60,
                        });
                      }}
                      className="w-full"
                    />
                  </div>
                </div>
              )}

              {/* Objective */}
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Optimization Objective</label>
                <Select
                  options={[
                    { value: 'minimize_distance', label: 'Minimize Distance' },
                    { value: 'minimize_time', label: 'Minimize Time' },
                    { value: 'minimize_vehicles', label: 'Minimize Vehicles' },
                  ]}
                  value={config.objective}
                  onChange={(e) => setConfig({ objective: e.target.value as typeof config.objective })}
                />
              </div>
            </div>
          )}
        </div>

        {/* Job Types (Belron) */}
        {isBelron && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('jobTypes')}
              className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
            >
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-[#C74634]" />
                <span className="text-sm font-medium text-white">Job Types</span>
                <span className="text-xs bg-oracle-red/20 text-oracle-red px-1.5 py-0.5 rounded">Belron</span>
              </div>
              {expandedSections.jobTypes ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
            </button>
            {expandedSections.jobTypes && (
              <div className="p-3 space-y-2 border-t border-dark-border">
                {appConfig.scenarioJobTypes.map((jt) => (
                  <div
                    key={jt.id}
                    className="flex items-center justify-between p-2 rounded-lg border border-dark-border"
                    style={{ borderLeftColor: jt.color, borderLeftWidth: 3 }}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full shrink-0"
                        style={{ backgroundColor: jt.color }}
                      />
                      <span className="text-sm text-white">{jt.label}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-mono text-[#C74634]">
                        {formatCurrency(jt.revenue, appConfig.currency)}
                      </div>
                      <div className="text-xs text-gray-500">{jt.duration} min</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Job Type Mix (Generic) */}
        {!isBelron && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('jobTypes')}
              className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
            >
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-[#C74634]" />
                <span className="text-sm font-medium text-white">Job Type Mix</span>
              </div>
              {expandedSections.jobTypes ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
            </button>
            {expandedSections.jobTypes && (
              <div className="p-3 space-y-3 border-t border-dark-border">
                <Toggle
                  label="Enable Job Types"
                  checked={config.useJobTypes ?? false}
                  onChange={(e) => setConfig({
                    useJobTypes: e.target.checked,
                    jobTypeMix: e.target.checked ? DEFAULT_JOB_TYPE_MIX : undefined,
                  })}
                />
                {config.useJobTypes && config.jobTypeMix && (
                  <div className="space-y-2 bg-dark-bg rounded-lg p-2">
                    {(Object.keys(JOB_TYPE_CONFIGS) as JobType[]).map((type) => {
                      const typeConfig = JOB_TYPE_CONFIGS[type];
                      return (
                        <div key={type} className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full shrink-0"
                            style={{ backgroundColor: typeConfig.color }}
                          />
                          <div className="flex-1 min-w-0">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-gray-300 truncate">{typeConfig.label}</span>
                              <span className="text-[#C74634] font-mono">
                                {config.jobTypeMix![type]}%
                              </span>
                            </div>
                            <input
                              type="range"
                              min={0}
                              max={100}
                              step={5}
                              value={config.jobTypeMix![type]}
                              onChange={(e) => {
                                const newMix = {
                                  ...config.jobTypeMix!,
                                  [type]: parseInt(e.target.value),
                                };
                                setConfig({ jobTypeMix: newMix });
                              }}
                              className="w-full h-1 bg-dark-border rounded-lg appearance-none cursor-pointer accent-[#C74634]"
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Stops Constraints */}
        <div className="border border-dark-border rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('stops')}
            className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4 text-[#C74634]" />
              <span className="text-sm font-medium text-white">Constraints</span>
              <span className="text-xs text-gray-500">
                ({config.enableTimeWindows ? 'TW' : ''}{config.enableTimeWindows && config.enableCapacity ? ', ' : ''}{config.enableCapacity ? 'Cap' : ''}{!config.enableTimeWindows && !config.enableCapacity ? 'none' : ''})
              </span>
            </div>
            {expandedSections.stops ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
          {expandedSections.stops && (
            <div className="p-3 space-y-3 border-t border-dark-border">
              <Toggle
                label="Enable Time Windows"
                checked={config.enableTimeWindows}
                onChange={(e) => setConfig({ enableTimeWindows: e.target.checked })}
              />
              <Toggle
                label="Enable Capacity Constraints"
                checked={config.enableCapacity}
                onChange={(e) => setConfig({ enableCapacity: e.target.checked })}
              />
            </div>
          )}
        </div>

        {/* Solver Settings */}
        <div className="border border-dark-border rounded-lg overflow-hidden">
          <button
            onClick={() => toggleSection('solver')}
            className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
          >
            <div className="flex items-center gap-2">
              <Settings className="w-4 h-4 text-[#C74634]" />
              <span className="text-sm font-medium text-white">Solver Settings</span>
              <span className="text-xs text-gray-500">
                ({config.timeLimit}s, {config.parallelMode || 'auto'}, {config.solverMode})
              </span>
            </div>
            {expandedSections.solver ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
          </button>
          {expandedSections.solver && (
            <div className="p-3 space-y-3 border-t border-dark-border">
              <div>
                <label className="text-xs text-gray-400">Time Limit: {config.timeLimit}s</label>
                <input
                  type="range"
                  min="10"
                  max="120"
                  value={config.timeLimit}
                  onChange={(e) => setConfig({ timeLimit: parseInt(e.target.value) })}
                  className="w-full"
                />
              </div>

              {/* Parallel Mode Selection */}
              <div>
                <label className="text-xs text-gray-400">Optimization Mode</label>
                <select
                  value={config.parallelMode || 'auto'}
                  onChange={(e) => setConfig({ parallelMode: e.target.value as 'auto' | 'single' | 'parallel' })}
                  className="w-full px-2 py-1 text-sm bg-dark-bg border border-dark-border rounded text-white mt-1"
                >
                  <option value="auto">Auto (Recommended)</option>
                  <option value="single">Single - Best Vehicle Distribution</option>
                  <option value="parallel">Parallel - Faster for Large Datasets</option>
                </select>
                <p className="text-[10px] text-gray-500 mt-1">
                  {config.parallelMode === 'single' && 'Uses all vehicles optimally. Best for constraint satisfaction.'}
                  {config.parallelMode === 'parallel' && 'Splits into clusters. Faster but may underutilize vehicles.'}
                  {(config.parallelMode === 'auto' || !config.parallelMode) && 'Single for <300 stops, parallel for larger datasets.'}
                </p>
              </div>

              {/* Parallel Clusters - only show when parallel mode */}
              {config.parallelMode === 'parallel' && (
                <div>
                  <label className="text-xs text-gray-400">Parallel Clusters: {config.parallelJobs}</label>
                  <input
                    type="range"
                    min="2"
                    max="8"
                    value={config.parallelJobs}
                    onChange={(e) => setConfig({ parallelJobs: parseInt(e.target.value) })}
                    className="w-full"
                  />
                </div>
              )}

              <div>
                <label className="text-xs text-gray-400">Solver Mode</label>
                <select
                  value={config.solverMode}
                  onChange={(e) => setConfig({ solverMode: e.target.value as 'speed' | 'balanced' | 'quality' })}
                  className="w-full px-2 py-1 text-sm bg-dark-bg border border-dark-border rounded text-white mt-1"
                >
                  <option value="speed">Speed</option>
                  <option value="balanced">Balanced</option>
                  <option value="quality">Quality</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Debug Panel */}
        {showDebug && (
          <div className="border border-dark-border rounded-lg overflow-hidden">
            <button
              onClick={() => toggleSection('debug')}
              className="w-full flex items-center justify-between px-3 py-2 bg-dark-card hover:bg-dark-hover transition-colors"
            >
              <div className="flex items-center gap-2">
                <Bug className="w-4 h-4 text-[#C74634]" />
                <span className="text-sm font-medium text-white">Debug Panel</span>
              </div>
              {expandedSections.debug ? <ChevronDown className="w-4 h-4 text-gray-400" /> : <ChevronRight className="w-4 h-4 text-gray-400" />}
            </button>
            {expandedSections.debug && (
              <div className="p-3 space-y-3 border-t border-dark-border">
                {/* cuOPT Request */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-gray-400 font-medium">cuOPT Request</label>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(debugData.request, null, 2), 'request')}
                      className="flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 hover:text-white hover:bg-dark-hover rounded transition-colors"
                      disabled={!debugData.request}
                    >
                      {copiedField === 'request' ? (
                        <><Check className="w-3 h-3 text-green-500" /> Copied!</>
                      ) : (
                        <><Copy className="w-3 h-3" /> Copy</>
                      )}
                    </button>
                  </div>
                  <pre className="p-2 bg-dark-bg rounded text-xs text-gray-300 overflow-auto max-h-48 whitespace-pre-wrap break-words">
                    {debugData.request ? JSON.stringify(debugData.request, null, 2) : 'No request yet'}
                  </pre>
                </div>

                {/* cuOPT Response */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-gray-400 font-medium">cuOPT Response</label>
                    <button
                      onClick={() => copyToClipboard(JSON.stringify(debugData.response, null, 2), 'response')}
                      className="flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 hover:text-white hover:bg-dark-hover rounded transition-colors"
                      disabled={!debugData.response}
                    >
                      {copiedField === 'response' ? (
                        <><Check className="w-3 h-3 text-green-500" /> Copied!</>
                      ) : (
                        <><Copy className="w-3 h-3" /> Copy</>
                      )}
                    </button>
                  </div>
                  <pre className="p-2 bg-dark-bg rounded text-xs text-gray-300 overflow-auto max-h-48 whitespace-pre-wrap break-words">
                    {debugData.response ? JSON.stringify(debugData.response, null, 2) : 'No response yet'}
                  </pre>
                </div>

                {/* GenAI Prompt */}
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-xs text-gray-400 font-medium">AI Interpretation</label>
                    <button
                      onClick={() => copyToClipboard(debugData.prompt || '', 'prompt')}
                      className="flex items-center gap-1 px-2 py-0.5 text-xs text-gray-400 hover:text-white hover:bg-dark-hover rounded transition-colors"
                      disabled={!debugData.prompt}
                    >
                      {copiedField === 'prompt' ? (
                        <><Check className="w-3 h-3 text-green-500" /> Copied!</>
                      ) : (
                        <><Copy className="w-3 h-3" /> Copy</>
                      )}
                    </button>
                  </div>
                  <pre className="p-2 bg-dark-bg rounded text-xs text-gray-300 overflow-auto max-h-32 whitespace-pre-wrap break-words">
                    {debugData.prompt || 'No prompt yet'}
                  </pre>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="p-4 border-t border-dark-border bg-dark-card space-y-2">
        <Button
          variant="primary"
          size="lg"
          onClick={onRunOptimization}
          disabled={stops.length === 0 || isOptimizing}
          isLoading={isOptimizing}
          className="w-full"
        >
          {!isOptimizing && <Play className="w-5 h-5 mr-1" />}
          {isOptimizing ? 'Optimizing...' : 'Run Optimization'}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          disabled={isOptimizing}
          className="w-full"
        >
          <RotateCcw className="w-4 h-4 mr-1" />
          Reset
        </Button>
      </div>
    </div>
  );
}
