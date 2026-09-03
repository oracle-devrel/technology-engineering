import axios, { AxiosInstance } from 'axios';
import type { CuOptRequest, CuOptResponse, Stop, Vehicle, OptimizationConfig } from '@/types';

class CuOptClient {
  private client: AxiosInstance;
  private pollInterval = 3000; // 3 seconds between polls
  private maxPollAttempts = 120; // 120 attempts = 6 minutes max wait per job

  constructor() {
    this.client = axios.create({
      baseURL: '/api/cuopt',
      timeout: 300000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  }

  async solveVRP(payload: CuOptRequest): Promise<CuOptResponse> {
    try {
      // Submit request
      const submitResponse = await this.client.post('/request', payload);
      const reqId = submitResponse.data.reqId;

      if (!reqId) {
        throw new Error('No request ID returned from cuOPT');
      }

      // Poll for solution
      return await this.pollForSolution(reqId);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`cuOPT API Error: ${error.response?.data?.error || error.message}`);
      }
      throw error;
    }
  }

  private async pollForSolution(reqId: string): Promise<CuOptResponse> {
    let attempts = 0;

    while (attempts < this.maxPollAttempts) {
      attempts++;
      await this.delay(this.pollInterval);

      const response = await this.client.get(`/solution/${reqId}`);
      const data = response.data;

      if (data.error) {
        throw new Error(`cuOPT Solve Error: ${data.error}`);
      }

      if (data.response) {
        // cuOPT returns solver_response for feasible solutions and
        // solver_infeasible_response for partial/constrained solutions
        const solverResponse = data.response.solver_response || data.response.solver_infeasible_response;
        const isPartialSolution = !!data.response.solver_infeasible_response;

        // Only throw error for infeasible notes if we don't have a partial solution with vehicle data
        // When solver_infeasible_response is returned, it contains a valid partial solution
        if (data.notes && data.notes.length > 0 && !isPartialSolution) {
          const note = data.notes[0];
          if (note.includes('Feasible solutions could not be found')) {
            if (note.includes('Capacity dimension')) {
              throw new Error('Capacity constraint violated: Vehicle capacity is too low for stop demands. Try increasing vehicle capacity.');
            }
            throw new Error(`Optimization infeasible: ${note}`);
          }
        }

        // Transform vehicle_data from object to array
        // cuOPT returns: { "1": {...}, "2": {...} }
        // Frontend expects: [{ vehicle_id: 1, ... }, { vehicle_id: 2, ... }]
        let vehicleDataArray: any[] = [];
        if (solverResponse?.vehicle_data && typeof solverResponse.vehicle_data === 'object') {
          vehicleDataArray = Object.entries(solverResponse.vehicle_data).map(([vehicleId, vehicleInfo]: [string, any]) => ({
            vehicle_id: parseInt(vehicleId),
            route: vehicleInfo.route || [],
            arrival_times: vehicleInfo.arrival_stamp || [],
            route_distance: 0, // Not provided by cuOPT, would need to calculate
            route_duration: vehicleInfo.arrival_stamp ?
              vehicleInfo.arrival_stamp[vehicleInfo.arrival_stamp.length - 1] - vehicleInfo.arrival_stamp[0] : 0,
            load_at_stops: [],
          }));
        }

        // Calculate per-route distance estimate (distribute total proportionally by route length)
        const totalCost = solverResponse?.solution_cost || 0;
        const totalStopsInRoutes = vehicleDataArray.reduce((sum, v) => sum + (v.route?.length || 0), 0);
        if (totalStopsInRoutes > 0 && totalCost > 0) {
          vehicleDataArray = vehicleDataArray.map(v => ({
            ...v,
            route_distance: (v.route?.length || 0) / totalStopsInRoutes * totalCost
          }));
        }

        // Determine status: solver_response = SUCCESS, solver_infeasible_response = PARTIAL
        return {
          ...solverResponse,
          vehicle_data: vehicleDataArray,
          total_distance: totalCost, // Explicitly include total distance
          status: vehicleDataArray.length > 0 ? (isPartialSolution ? 'PARTIAL' : 'SUCCESS') : 'FAILED',
          solve_time: data.response.total_solve_time || data.response.solve_time || 0,
        };
      }
    }

    throw new Error('cuOPT solve timeout - max poll attempts reached');
  }

  async solveParallel(
    payloads: CuOptRequest[],
    concurrency: number = 4,
    onProgress?: (completed: number, total: number, results: (CuOptResponse | null)[]) => void,
    onJobStart?: (index: number) => void,
    onJobError?: (index: number, error: Error) => void
  ): Promise<(CuOptResponse | null)[]> {
    // Initialize results array with nulls to avoid sparse array issues
    const results: (CuOptResponse | null)[] = new Array(payloads.length).fill(null);
    const semaphore = new Semaphore(concurrency);

    const tasks = payloads.map(async (payload, index) => {
      await semaphore.acquire();
      try {
        // Notify that this job is now running
        onJobStart?.(index);
        const result = await this.solveVRP(payload);
        results[index] = result;
        onProgress?.(results.filter(Boolean).length, payloads.length, results);
        return result;
      } catch (error) {
        // Mark this job as failed in results (null indicates failure)
        results[index] = null;
        onJobError?.(index, error instanceof Error ? error : new Error(String(error)));
        onProgress?.(results.filter(Boolean).length, payloads.length, results);
        return null;
      } finally {
        semaphore.release();
      }
    });

    await Promise.allSettled(tasks);
    return results;
  }

  buildPayload(
    stops: Stop[],
    vehicles: Vehicle[],
    config: OptimizationConfig
  ): CuOptRequest {
    // For home-start routing, include vehicle home locations in the matrix
    // Only use home-start if explicitly enabled AND vehicles have non-zero home locations
    const useHomeStart = config.enableHomeStart === true && vehicles.some(v =>
      v.startLat !== undefined && v.startLng !== undefined &&
      (v.startLat !== 0 || v.startLng !== 0)
    );
    const returnToDepot = config.returnToDepot ?? true;

    // Build location list: [depot, ...stops, ...vehicleHomes (if home-start)]
    // Index 0 = depot (first stop or center)
    // Indices 1..N = stops
    // Indices N+1..N+V = vehicle home locations (if home-start enabled)

    // Build distance matrix - include vehicle homes if home-start enabled
    const costMatrix = this.buildDistanceMatrixWithHomes(stops, vehicles, useHomeStart);
    const timeMatrix = this.buildTimeMatrix(costMatrix);

    // Build task data with service times (dwell times) if available
    const taskData: any = {
      task_locations: stops.map((_, i) => i + 1), // 0 is depot, tasks start at 1
      demand: [stops.map((s) => s.demand)],
    };

    // Add service times (dwell/job duration) - use per-stop or default
    const defaultServiceTime = config.defaultServiceTime || 0;
    const serviceTimes = stops.map((s) => s.serviceDuration ?? defaultServiceTime);
    const hasServiceTimes = serviceTimes.some((t) => t > 0);
    if (hasServiceTimes) {
      taskData.service_times = serviceTimes;
    }

    // Calculate required vehicles based on total service time + estimated drive time
    // This forces cuOPT to distribute work across enough vehicles for shift limits
    const totalServiceTime = serviceTimes.reduce((sum, t) => sum + t, 0);
    // Use realistic drive times for field service (~15 min avg between stops + depot travel)
    const avgDriveTimeBetweenStops = 15;
    const depotTravelTime = 30;
    const estimatedDriveTime = (stops.length * avgDriveTimeBetweenStops) + depotTravelTime;
    const totalWorkTime = totalServiceTime + estimatedDriveTime;

    // Use configured shift hours or default to 8
    const shiftHours = config.shiftHours ?? 8;
    const shiftMinutes = config.maxRouteDuration ?? (shiftHours * 60); // Use maxRouteDuration if set
    // Account for 30 min buffer (breaks, delays) when calculating required vehicles
    const effectiveShiftMinutes = shiftMinutes - 30;
    const minVehiclesRequired = Math.ceil(totalWorkTime / effectiveShiftMinutes);

    // Enforce shift limits when enabled (default: true)
    const enforceShiftLimits = config.enforceShiftLimits !== false;

    // Adjust capacity to force vehicle distribution when needed
    // If we have enough vehicles but cuOPT isn't using them, limit capacity per vehicle
    let effectiveCapacity = vehicles[0]?.capacity ?? config.vehicleCapacity ?? 100;

    // When enforcing shift limits, be VERY aggressive about capacity adjustment
    // The goal is to force cuOPT to use ALL configured vehicles
    if (enforceShiftLimits || hasServiceTimes) {
      const totalDemand = stops.reduce((sum, s) => sum + s.demand, 0);
      const maxDemand = Math.max(...stops.map(s => s.demand));
      const avgDemand = totalDemand / stops.length || 1;

      // Calculate EXACT capacity to FORCE all vehicles to be used
      // Formula: capacity = ceiling(totalDemand / numVehicles)
      // This ensures cuOPT MUST use all vehicles to satisfy total demand
      const capacityToForceAllVehicles = Math.ceil(totalDemand / vehicles.length);

      // Also calculate based on stops per vehicle (for low demand scenarios)
      const exactStopsPerVehicle = Math.ceil(stops.length / vehicles.length);
      const capacityByStops = Math.ceil(exactStopsPerVehicle * avgDemand);

      // Calculate max stops per vehicle based on time constraints
      const avgServiceTime = totalServiceTime / stops.length || 30;
      const timePerStop = avgServiceTime + avgDriveTimeBetweenStops;
      const maxStopsPerVehicleByTime = Math.floor(effectiveShiftMinutes / timePerStop);
      const capacityByTime = Math.ceil(maxStopsPerVehicleByTime * avgDemand);

      // Use the SMALLEST capacity that still allows feasibility
      // This FORCES cuOPT to use the maximum number of vehicles
      const minCapacity = Math.max(maxDemand, 1); // Must handle largest single stop
      const targetCapacity = Math.max(
        minCapacity,
        Math.min(capacityToForceAllVehicles, capacityByStops, capacityByTime)
      );

      console.log(`[cuOPT] === Vehicle Distribution Enforcement ===`);
      console.log(`[cuOPT] Stops: ${stops.length}, Vehicles: ${vehicles.length}, Total Demand: ${totalDemand}`);
      console.log(`[cuOPT] Capacity to force ALL vehicles: ${capacityToForceAllVehicles} (${totalDemand}/${vehicles.length})`);
      console.log(`[cuOPT] Capacity by stops: ${capacityByStops} (${exactStopsPerVehicle} stops × ${avgDemand.toFixed(1)} avg demand)`);
      console.log(`[cuOPT] Capacity by time: ${capacityByTime} (${maxStopsPerVehicleByTime} stops max in ${effectiveShiftMinutes}min)`);
      console.log(`[cuOPT] Final capacity: ${effectiveCapacity} → ${targetCapacity}`);

      effectiveCapacity = targetCapacity;

      // Warn if not enough vehicles for shift limits
      if (vehicles.length < minVehiclesRequired) {
        console.warn(`[cuOPT] Warning: ${minVehiclesRequired} vehicles needed for ${shiftHours}h shifts, only ${vehicles.length} configured.`);
      }
    }

    // Auto-enable time windows when enforcing shift limits or when service times exist
    const shouldEnableTimeWindows = config.enableTimeWindows || hasServiceTimes || enforceShiftLimits;

    // Add time windows if enabled (or if shift limits require enforcement)
    // Default: configured shift duration from vehicle start time
    if (shouldEnableTimeWindows) {
      // Get vehicle time window defaults - use configured shift duration
      const defaultStart = vehicles[0]?.timeWindowStart ?? 480;  // 8am
      const defaultEnd = vehicles[0]?.timeWindowEnd ?? (defaultStart + shiftMinutes);

      taskData.task_time_windows = stops.map((s) => [
        s.timeWindowStart ?? defaultStart,
        s.timeWindowEnd ?? defaultEnd,
      ]);
    }

    // Note: priorities field is NOT supported in cuOPT v25.10 API
    // Revenue-based prioritization is stored client-side but not sent to solver
    // Future versions may support this - for now we use service times and time windows
    // to influence route optimization

    // Build fleet data with vehicle locations
    let vehicleLocations: number[][];
    if (useHomeStart) {
      // Home-start: each vehicle starts from its home location index
      // Home indices start at stops.length + 1 (after depot + all stops)
      const homeStartIndex = stops.length + 1;
      vehicleLocations = vehicles.map((_, idx) => {
        const startIdx = homeStartIndex + idx;
        const endIdx = returnToDepot ? 0 : startIdx; // Return to depot or home
        return [startIdx, endIdx];
      });
    } else {
      // Traditional: all vehicles start/end at depot (index 0)
      vehicleLocations = vehicles.map(() => [0, 0]);
    }

    const fleetData: any = {
      vehicle_locations: vehicleLocations,
      capacities: [vehicles.map(() => effectiveCapacity)],
    };

    // Add vehicle time windows if enabled or if shift limits require enforcement
    // Default: configured shift duration
    if (shouldEnableTimeWindows) {
      fleetData.vehicle_time_windows = vehicles.map((v) => {
        const start = v.timeWindowStart ?? 480;  // Default 8am
        const end = v.timeWindowEnd ?? (start + shiftMinutes);
        return [start, end];
      });
    }

    // Build solver config with mode-based objectives
    const solverConfig = this.buildSolverConfig(config);

    return {
      cost_matrix_data: { data: { '0': costMatrix } },
      travel_time_matrix_data: { data: { '0': timeMatrix } },
      task_data: taskData,
      fleet_data: fleetData,
      solver_config: solverConfig,
    };
  }

  private buildSolverConfig(config: OptimizationConfig): any {
    // cuOPT v25.10 solver_config only supports time_limit and objectives
    // Note: number_of_climbers, min_vehicles are NOT supported in this API version
    const solverConfig: any = {
      time_limit: config.timeLimit,
    };

    // Adjust time limit based on solver mode
    // Quality mode: use full time limit
    // Speed mode: use reduced time limit for faster results
    switch (config.solverMode) {
      case 'quality':
        // Use full time limit for best solution quality
        break;
      case 'speed':
        // Reduce effective time limit for faster results
        solverConfig.time_limit = Math.max(10, Math.floor(config.timeLimit * 0.5));
        break;
      case 'balanced':
      default:
        // Use 75% of time limit for balance
        solverConfig.time_limit = Math.max(10, Math.floor(config.timeLimit * 0.75));
        break;
    }

    // Map objective to solver objectives (weighted)
    // Note: Only cost and travel_time are reliably supported
    switch (config.objective) {
      case 'minimize_distance':
        solverConfig.objectives = {
          cost: 1,           // Primary: minimize distance/cost
          travel_time: 0,    // Secondary: time not prioritized
        };
        break;
      case 'minimize_time':
        solverConfig.objectives = {
          cost: 0,           // Distance not prioritized
          travel_time: 1,    // Primary: minimize travel time
        };
        break;
      case 'minimize_vehicles':
        // Balance cost and time for vehicle minimization
        solverConfig.objectives = {
          cost: 0.5,
          travel_time: 0.5,
        };
        break;
    }

    return solverConfig;
  }

  // Build distance matrix including vehicle home locations for home-start routing
  private buildDistanceMatrixWithHomes(stops: Stop[], vehicles: Vehicle[], includeHomes: boolean): number[][] {
    // Build location list: [depot, ...stops, ...vehicleHomes]
    const allPoints: { lat: number; lng: number }[] = [
      // Index 0: Depot (use center of stops or first stop)
      {
        lat: stops.length > 0 ? stops[0].lat : 0,
        lng: stops.length > 0 ? stops[0].lng : 0
      },
      // Indices 1..N: Stops
      ...stops.map(s => ({ lat: s.lat, lng: s.lng })),
    ];

    // Add vehicle home locations if home-start is enabled
    if (includeHomes) {
      vehicles.forEach(v => {
        // Use vehicle's start location, or generate random location near depot
        const homeLat = v.startLat || allPoints[0].lat + (Math.random() - 0.5) * 0.1;
        const homeLng = v.startLng || allPoints[0].lng + (Math.random() - 0.5) * 0.1;
        allPoints.push({ lat: homeLat, lng: homeLng });
      });
    }

    const n = allPoints.length;
    const matrix: number[][] = [];

    for (let i = 0; i < n; i++) {
      const row: number[] = [];
      for (let j = 0; j < n; j++) {
        if (i === j) {
          row.push(0);
        } else {
          row.push(this.haversineDistance(
            allPoints[i].lat,
            allPoints[i].lng,
            allPoints[j].lat,
            allPoints[j].lng
          ));
        }
      }
      matrix.push(row);
    }

    return matrix;
  }

  private buildTimeMatrix(distanceMatrix: number[][]): number[][] {
    // Assume average speed of 50 km/h = 0.833 km/min
    const avgSpeed = 0.833;
    return distanceMatrix.map((row) =>
      row.map((dist) => Math.round(dist / avgSpeed))
    );
  }

  private haversineDistance(lat1: number, lon1: number, lat2: number, lon2: number): number {
    const R = 6371; // Earth's radius in km
    const dLat = this.toRad(lat2 - lat1);
    const dLon = this.toRad(lon2 - lon1);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.toRad(lat1)) *
        Math.cos(this.toRad(lat2)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  private toRad(deg: number): number {
    return deg * (Math.PI / 180);
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  // K-means clustering for geographic partitioning
  clusterStops(stops: Stop[], numClusters: number): Stop[][] {
    if (stops.length <= numClusters) {
      return [stops];
    }

    // Simple k-means implementation
    const clusters: Stop[][] = Array.from({ length: numClusters }, () => []);

    // Initialize centroids
    const centroids: { lat: number; lng: number }[] = [];
    for (let i = 0; i < numClusters; i++) {
      const idx = Math.floor((i * stops.length) / numClusters);
      centroids.push({ lat: stops[idx].lat, lng: stops[idx].lng });
    }

    // Run k-means iterations
    for (let iter = 0; iter < 10; iter++) {
      // Clear clusters
      clusters.forEach((c) => (c.length = 0));

      // Assign stops to nearest centroid
      stops.forEach((stop) => {
        let minDist = Infinity;
        let nearest = 0;
        centroids.forEach((centroid, i) => {
          const dist = this.haversineDistance(stop.lat, stop.lng, centroid.lat, centroid.lng);
          if (dist < minDist) {
            minDist = dist;
            nearest = i;
          }
        });
        clusters[nearest].push(stop);
      });

      // Update centroids
      clusters.forEach((cluster, i) => {
        if (cluster.length > 0) {
          centroids[i] = {
            lat: cluster.reduce((sum, s) => sum + s.lat, 0) / cluster.length,
            lng: cluster.reduce((sum, s) => sum + s.lng, 0) / cluster.length,
          };
        }
      });
    }

    return clusters.filter((c) => c.length > 0);
  }

  // Estimate payload size for a given number of stops
  estimatePayloadSize(numStops: number): number {
    // Formula: ~43.2 * N^2 bytes (from benchmark data)
    const n = numStops + 1; // +1 for depot
    return (43.2 * n * n) / (1024 * 1024); // MB
  }

  // Estimate required vehicles based on workload and shift limits
  estimateRequiredVehicles(
    stops: Stop[],
    shiftHours: number = 8,
    defaultServiceTime: number = 30
  ): { minVehicles: number; totalWorkTime: number; avgTimePerVehicle: number } {
    // Calculate total service time
    const totalServiceTime = stops.reduce(
      (sum, s) => sum + (s.serviceDuration ?? defaultServiceTime),
      0
    );

    // Estimate drive time more realistically for field service
    // ~15-20 min average between stops in urban areas (not 3 min)
    // Also add ~30 min for start/end of day travel to/from depot
    const avgDriveTimeBetweenStops = 15; // More realistic for field service
    const depotTravelTime = 30; // Travel to first stop + return from last
    const estimatedDriveTime = (stops.length * avgDriveTimeBetweenStops) + depotTravelTime;

    // Total work time in minutes
    const totalWorkTime = totalServiceTime + estimatedDriveTime;

    // Shift duration in minutes (with 30 min buffer for breaks/delays)
    const effectiveShiftMinutes = (shiftHours * 60) - 30;

    // Minimum vehicles needed (add 1 buffer for uneven distribution)
    const rawMinVehicles = Math.ceil(totalWorkTime / effectiveShiftMinutes);
    const minVehicles = Math.ceil(rawMinVehicles * 1.1); // 10% buffer for route inefficiency

    // Average time per vehicle if using minimum
    const avgTimePerVehicle = totalWorkTime / minVehicles;

    return {
      minVehicles,
      totalWorkTime,
      avgTimePerVehicle,
    };
  }
}

// Simple semaphore for concurrency control
class Semaphore {
  private permits: number;
  private waiting: (() => void)[] = [];

  constructor(permits: number) {
    this.permits = permits;
  }

  async acquire(): Promise<void> {
    if (this.permits > 0) {
      this.permits--;
      return;
    }
    return new Promise((resolve) => {
      this.waiting.push(resolve);
    });
  }

  release(): void {
    if (this.waiting.length > 0) {
      const next = this.waiting.shift();
      next?.();
    } else {
      this.permits++;
    }
  }
}

export const cuoptClient = new CuOptClient();
export default cuoptClient;
