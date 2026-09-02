import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  Stop,
  Vehicle,
  OptimizationConfig,
  CuOptResponse,
  ParallelJobResult,
  ClusterInfo,
  VehicleRoute,
} from '@/types';

// Haversine distance calculation
function haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Calculate route distance from stop coordinates
function calculateRouteDistance(route: number[], stops: Stop[]): number {
  if (route.length < 2) return 0;

  let totalDistance = 0;

  // Build a map from stop ID to stop object for efficient lookup
  // This handles both indexed routes (1,2,3...) and ID-based routes (actual stop IDs)
  const stopMap = new Map<number, Stop>();
  stops.forEach((stop, idx) => {
    stopMap.set(stop.id, stop);
    // Also map by index+1 for backward compatibility with non-remapped routes
    stopMap.set(idx + 1, stop);
  });

  // Use first stop as depot (index 0 in route means depot)
  const depot = stops[0];

  for (let i = 0; i < route.length - 1; i++) {
    const fromIdx = route[i];
    const toIdx = route[i + 1];

    // Get coordinates - 0 is depot, otherwise look up by ID
    const fromStop = fromIdx === 0 ? depot : (stopMap.get(fromIdx) || depot);
    const toStop = toIdx === 0 ? depot : (stopMap.get(toIdx) || depot);

    if (fromStop && toStop) {
      totalDistance += haversineDistance(fromStop.lat, fromStop.lng, toStop.lat, toStop.lng);
    }
  }

  return totalDistance;
}

interface OptimizationState {
  // Input data
  stops: Stop[];
  vehicles: Vehicle[];
  config: OptimizationConfig;

  // Results
  result: CuOptResponse | null;
  routes: VehicleRoute[];
  unservedStops: number[];

  // Parallel execution
  clusters: ClusterInfo[];
  parallelJobs: ParallelJobResult[];

  // Performance metrics
  solveTime: number;
  totalDistance: number;
  totalDuration: number;
  vehiclesUsed: number;
  stopsServed: number;

  // Debug data for cuOPT request/response inspection
  debugData: {
    request: object | null;
    response: object | null;
    prompt: string | null;
    source: 'ai' | 'manual' | null;
  };

  // Actions - Input
  setStops: (stops: Stop[]) => void;
  addStop: (stop: Stop) => void;
  removeStop: (id: number) => void;
  clearStops: () => void;

  setVehicles: (vehicles: Vehicle[]) => void;
  setConfig: (config: Partial<OptimizationConfig>) => void;

  // Actions - Results
  setResult: (result: CuOptResponse) => void;
  clearResult: () => void;

  // Actions - Parallel
  setClusters: (clusters: ClusterInfo[]) => void;
  updateParallelJob: (job: ParallelJobResult) => void;
  clearParallelJobs: () => void;

  // Actions - Metrics
  updateMetrics: (metrics: Partial<{
    solveTime: number;
    totalDistance: number;
    totalDuration: number;
    vehiclesUsed: number;
    stopsServed: number;
  }>) => void;

  // Actions - Debug
  setDebugData: (data: Partial<{
    request: object | null;
    response: object | null;
    prompt: string | null;
    source: 'ai' | 'manual' | null;
  }>) => void;
  clearDebugData: () => void;

  // Reset
  reset: () => void;
}

const defaultConfig: OptimizationConfig = {
  numVehicles: 10,
  vehicleCapacity: 100,
  timeLimit: 30,
  objective: 'minimize_distance',
  enableTimeWindows: false,
  enableCapacity: true,
  parallelJobs: 4,
  parallelMode: 'auto', // System decides single vs parallel based on best practices
  solverMode: 'balanced',
  defaultServiceTime: 0, // No default service time
  enforceShiftLimits: true, // Enforce 8h shift limits by default
  maxRouteDuration: 480,    // 8 hours in minutes
  shiftHours: 8,            // 8 hour shifts
};

export const useOptimizationStore = create<OptimizationState>()(
  persist(
    (set) => ({
      // Initial state
      stops: [],
      vehicles: [],
      config: defaultConfig,
      result: null,
      routes: [],
      unservedStops: [],
      clusters: [],
      parallelJobs: [],
      solveTime: 0,
      totalDistance: 0,
      totalDuration: 0,
      vehiclesUsed: 0,
      stopsServed: 0,
      debugData: {
        request: null,
        response: null,
        prompt: null,
        source: null,
      },

      // Input actions
      setStops: (stops) => set({ stops }),
      addStop: (stop) => set((state) => ({ stops: [...state.stops, stop] })),
      removeStop: (id) => set((state) => ({ stops: state.stops.filter((s) => s.id !== id) })),
      clearStops: () => set({ stops: [] }),

      setVehicles: (vehicles) => set({ vehicles }),
      setConfig: (config) =>
        set((state) => ({ config: { ...state.config, ...config } })),

      // Result actions
      setResult: (result) =>
        set((state) => {
          // Calculate distances for each route using stop coordinates
          // Only recalculate if route_distance is not already provided
          const routesWithDistance = (result.vehicle_data || []).map((vehicle) => {
            // Use existing route_distance if it's a valid positive number
            // Otherwise calculate from stop coordinates
            const existingDistance = vehicle.route_distance;
            const routeDistance = (typeof existingDistance === 'number' && existingDistance > 0)
              ? existingDistance
              : calculateRouteDistance(vehicle.route, state.stops);
            return {
              ...vehicle,
              route_distance: routeDistance,
            };
          });

          const totalDistance = routesWithDistance.reduce((acc, v) => acc + v.route_distance, 0);
          const totalDuration = routesWithDistance.reduce((acc, v) => acc + (v.route_duration || 0), 0);
          const stopsServed = routesWithDistance.reduce((acc, v) => acc + Math.max(0, v.route.length - 2), 0);

          return {
            result: { ...result, vehicle_data: routesWithDistance },
            routes: routesWithDistance,
            unservedStops: [],
            solveTime: result.solve_time || 0,
            vehiclesUsed: result.num_vehicles || routesWithDistance.length || 0,
            totalDistance,
            totalDuration,
            stopsServed,
          };
        }),
      clearResult: () =>
        set({
          result: null,
          routes: [],
          unservedStops: [],
          solveTime: 0,
          totalDistance: 0,
          totalDuration: 0,
          vehiclesUsed: 0,
          stopsServed: 0,
        }),

      // Parallel actions
      setClusters: (clusters) => set({ clusters }),
      updateParallelJob: (job) =>
        set((state) => {
          const existingIndex = state.parallelJobs.findIndex((j) => j.jobId === job.jobId);
          if (existingIndex >= 0) {
            const updated = [...state.parallelJobs];
            updated[existingIndex] = job;
            return { parallelJobs: updated };
          }
          return { parallelJobs: [...state.parallelJobs, job] };
        }),
      clearParallelJobs: () => set({ parallelJobs: [], clusters: [] }),

      // Metrics actions
      updateMetrics: (metrics) => set((state) => ({ ...state, ...metrics })),

      // Debug actions
      setDebugData: (data) =>
        set((state) => ({
          debugData: { ...state.debugData, ...data },
        })),
      clearDebugData: () =>
        set({
          debugData: {
            request: null,
            response: null,
            prompt: null,
            source: null,
          },
        }),

      // Reset
      reset: () =>
        set({
          stops: [],
          vehicles: [],
          config: defaultConfig,
          result: null,
          routes: [],
          unservedStops: [],
          clusters: [],
          parallelJobs: [],
          solveTime: 0,
          totalDistance: 0,
          totalDuration: 0,
          vehiclesUsed: 0,
          stopsServed: 0,
          debugData: {
            request: null,
            response: null,
            prompt: null,
            source: null,
          },
        }),
    }),
    {
      name: 'cuopt-optimization', // localStorage key
      version: 1,
      // Only persist the config portion - stops/results are transient
      partialize: (state) => ({
        config: state.config,
      }),
    }
  )
);
