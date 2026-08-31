import { create } from 'zustand';
import type { ViewMode, ConnectionStatus, Toast } from '@/types';

export type MapTheme = 'dark' | 'light';
export type MapProvider = 'leaflet' | 'google';

interface AppState {
  // View state
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;

  // Map theme
  mapTheme: MapTheme;
  setMapTheme: (theme: MapTheme) => void;
  toggleMapTheme: () => void;

  // Map provider (Leaflet or Google Maps)
  mapProvider: MapProvider;
  setMapProvider: (provider: MapProvider) => void;

  // Connection status
  cuoptStatus: ConnectionStatus;
  genaiStatus: ConnectionStatus;
  setCuoptStatus: (status: ConnectionStatus) => void;
  setGenaiStatus: (status: ConnectionStatus) => void;

  // Optimization state
  isOptimizing: boolean;
  setIsOptimizing: (optimizing: boolean) => void;
  parallelJobsRunning: number;
  setParallelJobsRunning: (count: number) => void;
  currentSolveTime: number;
  setCurrentSolveTime: (time: number) => void;

  // Toast notifications
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;

  // Sidebar state
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Settings modal
  showSettings: boolean;
  setShowSettings: (show: boolean) => void;

  // Help modal
  showHelp: boolean;
  setShowHelp: (show: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // View state
  viewMode: 'dashboard',
  setViewMode: (mode) => set({ viewMode: mode }),

  // Map theme - default to light for better visibility
  mapTheme: 'light',
  setMapTheme: (theme) => set({ mapTheme: theme }),
  toggleMapTheme: () =>
    set((state) => ({ mapTheme: state.mapTheme === 'dark' ? 'light' : 'dark' })),

  // Map provider - default to Google Maps for traffic & directions
  mapProvider: 'google',
  setMapProvider: (provider) => set({ mapProvider: provider }),

  // Connection status
  cuoptStatus: 'disconnected',
  genaiStatus: 'disconnected',
  setCuoptStatus: (status) => set({ cuoptStatus: status }),
  setGenaiStatus: (status) => set({ genaiStatus: status }),

  // Optimization state
  isOptimizing: false,
  setIsOptimizing: (optimizing) => set({ isOptimizing: optimizing }),
  parallelJobsRunning: 0,
  setParallelJobsRunning: (count) => set({ parallelJobsRunning: count }),
  currentSolveTime: 0,
  setCurrentSolveTime: (time) => set({ currentSolveTime: time }),

  // Toast notifications
  toasts: [],
  addToast: (toast) =>
    set((state) => ({
      toasts: [
        ...state.toasts,
        { ...toast, id: `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}` },
      ],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),

  // Sidebar state
  isSidebarCollapsed: false,
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),

  // Settings modal
  showSettings: false,
  setShowSettings: (show) => set({ showSettings: show }),

  // Help modal
  showHelp: false,
  setShowHelp: (show) => set({ showHelp: show }),
}));
