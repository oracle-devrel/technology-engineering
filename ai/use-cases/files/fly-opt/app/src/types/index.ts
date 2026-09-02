export * from './cuopt';
export * from './genai';
export * from './weather';

// Common UI types
export type ViewMode = 'dashboard' | 'chat';
export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting';

export interface AppState {
  viewMode: ViewMode;
  cuoptStatus: ConnectionStatus;
  genaiStatus: ConnectionStatus;
  isOptimizing: boolean;
  parallelJobsRunning: number;
}

export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface RouteColor {
  vehicleId: number;
  color: string;
  stroke: string;
}

// Chart data types
export interface ChartDataPoint {
  name: string;
  value: number;
  label?: string;
}

export interface PerformanceChartData {
  stopCount: number;
  solveTime: number;
  benchmark: number;
  label: string;
}
