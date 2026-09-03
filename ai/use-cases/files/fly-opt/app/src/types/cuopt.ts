// cuOPT API Types - Based on v25.10 API specification

export interface CostMatrixData {
  data: {
    '0': number[][];
  };
}

export interface TravelTimeMatrixData {
  data: {
    '0': number[][];
  };
}

export interface TaskData {
  task_locations: number[];
  demand: number[][];
  task_time_windows?: number[][];
  service_times?: number[];
  // Note: priorities field is NOT supported in cuOPT v25.10
  // priorities?: number[];
  pickup_indices?: number[];
  delivery_indices?: number[];
}

export interface FleetData {
  vehicle_locations: number[][];
  capacities: number[][];
  vehicle_time_windows?: number[][];
  vehicle_ids?: string[];
}

export interface SolverConfig {
  time_limit: number;
  objectives?: {
    cost?: number;
    travel_time?: number;
    variance_route_size?: number;
    variance_route_service_time?: number;
  };
  verbose_mode?: boolean;
  error_logging?: boolean;
}

export interface CuOptRequest {
  cost_matrix_data: CostMatrixData;
  travel_time_matrix_data: TravelTimeMatrixData;
  task_data: TaskData;
  fleet_data: FleetData;
  solver_config: SolverConfig;
}

export interface VehicleRoute {
  vehicle_id: number;
  route: number[];
  arrival_times: number[];
  route_distance: number;
  route_duration: number;
  load_at_stops: number[];
}

export interface SolutionStatus {
  num_vehicles: number;
  solution_cost: number;
  total_distance: number;
  total_duration: number;
  num_stops_served: number;
  num_stops_unserved: number;
  unserved_stops: number[];
  solve_time_ms: number;
}

export interface CuOptResponse {
  vehicle_data: VehicleRoute[];
  solution_cost: number;
  num_vehicles: number;
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED' | 'INFEASIBLE' | 'TIMEOUT' | 'ERROR';
  solve_time: number;
  solver_response?: {
    solution_cost: number;
    num_vehicles: number;
    vehicle_data: VehicleRoute[];
  };
}

export interface CuOptJobStatus {
  reqId: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  response?: CuOptResponse;
  error?: string;
}

// Job types for Belron and similar field service scenarios
export type JobType = 'delivery' | 'chip_repair' | 'replacement' | 'recalibration' | 'maintenance' | 'installation';

export interface JobTypeConfig {
  type: JobType;
  label: string;
  minDuration: number; // minutes
  maxDuration: number; // minutes
  defaultDuration: number; // minutes
  color: string;
  revenue: number;         // Average revenue in GBP
  requiresEquipment?: boolean;
}

export const JOB_TYPE_CONFIGS: Record<JobType, JobTypeConfig> = {
  delivery: { type: 'delivery', label: 'Delivery', minDuration: 5, maxDuration: 30, defaultDuration: 15, color: '#3B82F6', revenue: 25 },
  chip_repair: { type: 'chip_repair', label: 'Chip Repair', minDuration: 30, maxDuration: 60, defaultDuration: 45, color: '#10B981', revenue: 85 },
  replacement: { type: 'replacement', label: 'Windshield Replacement', minDuration: 60, maxDuration: 120, defaultDuration: 90, color: '#F59E0B', revenue: 350 },
  recalibration: { type: 'recalibration', label: 'ADAS Recalibration', minDuration: 60, maxDuration: 90, defaultDuration: 75, color: '#8B5CF6', revenue: 180, requiresEquipment: true },
  maintenance: { type: 'maintenance', label: 'Maintenance', minDuration: 30, maxDuration: 120, defaultDuration: 60, color: '#EC4899', revenue: 150 },
  installation: { type: 'installation', label: 'Installation', minDuration: 60, maxDuration: 180, defaultDuration: 120, color: '#06B6D4', revenue: 450 },
};

export interface Stop {
  id: number;
  lat: number;
  lng: number;
  demand: number;
  timeWindowStart?: number;
  timeWindowEnd?: number;
  serviceDuration?: number;
  priority?: number;
  revenue?: number;           // Revenue/value for this job (used for prioritization)
  label?: string;
  postcode?: string;
  jobType?: JobType;
  requiresEquipment?: boolean;
  metadata?: Record<string, unknown>;
}

export interface Vehicle {
  id: number;
  capacity: number;
  startLat: number;
  startLng: number;
  endLat?: number;
  endLng?: number;
  timeWindowStart?: number;
  timeWindowEnd?: number;
  label?: string;
}

// Job type mix configuration for stop generation
export interface JobTypeMix {
  delivery: number;       // Percentage 0-100
  chip_repair: number;
  replacement: number;
  recalibration: number;
  maintenance: number;
  installation: number;
}

export const DEFAULT_JOB_TYPE_MIX: JobTypeMix = {
  delivery: 0,
  chip_repair: 25,
  replacement: 50,
  recalibration: 10,
  maintenance: 10,
  installation: 5,
};

// Parallel optimization mode
export type ParallelMode = 'auto' | 'single' | 'parallel';

export interface OptimizationConfig {
  numVehicles: number;
  vehicleCapacity: number;
  timeLimit: number;
  objective: 'minimize_distance' | 'minimize_time' | 'minimize_vehicles';
  enableTimeWindows: boolean;
  enableCapacity: boolean;
  maxRouteDistance?: number;
  maxStopsPerVehicle?: number;
  parallelJobs: number;
  parallelMode: ParallelMode;   // auto = system decides, single = always single, parallel = always parallel
  solverMode: 'quality' | 'speed' | 'balanced';
  defaultServiceTime?: number; // Default dwell/service time in minutes per stop
  jobTypeMix?: JobTypeMix;     // Mix of job types for stop generation
  useJobTypes?: boolean;       // Enable job type differentiation
  enableHomeStart?: boolean;   // Enable home-start routing (vehicles start from home locations)
  returnToDepot?: boolean;     // Should vehicles return to depot at end of day
  prioritizeByRevenue?: boolean; // Prioritize higher-revenue jobs when capacity is limited
  enforceShiftLimits?: boolean; // Enforce max route duration (8h shift limit)
  maxRouteDuration?: number;    // Maximum route duration in minutes (default: 480 = 8 hours)
  shiftHours?: number;          // Working hours per shift (default: 8)
}

export interface ClusterInfo {
  clusterId: number;
  stops: number[];
  centroid: { lat: number; lng: number };
  stopCount: number;
  payloadSizeMB: number;
}

export interface ParallelJobResult {
  jobId: string;
  clusterId: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  stops: number;
  solveTime?: number;
  result?: CuOptResponse;
  error?: string;
}

// Benchmark data types
export interface BenchmarkScenario {
  id: string;
  name: string;
  description: string;
  stops: number;
  vehicles: number;
  expectedSolveTime: number;
  payloadSizeMB: number;
  category: 'field_service' | 'mixed_density' | 'high_density_parcel';
  centerLat: number;
  centerLng: number;
  radiusKm: number;
}

export interface PerformanceMetric {
  stopCount: number;
  payloadSizeMB: number;
  solveTimeSeconds: number;
  throughputStopsPerSec: number;
  status: 'success' | 'failed';
}
