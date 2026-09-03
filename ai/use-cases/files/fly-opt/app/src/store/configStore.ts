import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
  SCENARIO_PRESETS,
  getCountryByCode,
  getCityById,
  type CurrencyConfig,
  type BelronJobType,
} from '@/data/locationData';

// Application configuration interface
export interface AppConfig {
  // Region settings
  countryCode: string;
  cityId: string;

  // AI Model settings
  aiModel: string;

  // Display preferences
  currency: CurrencyConfig;
  distanceUnit: 'km' | 'miles';
  dateFormat: string;
  timeFormat: '12h' | '24h';

  // Map defaults
  defaultCenter: { lat: number; lng: number };
  defaultZoom: number;
  serviceRadius: number;

  // Business defaults
  defaultVehicles: number;
  defaultShiftHours: number;
  workingHoursStart: string;
  workingHoursEnd: string;
  vehicleLabelType: 'generic' | 'license_plate';
  dispatcherHourlyRate: number;

  // Scenario settings
  activeScenario: string;
  scenarioJobTypes: BelronJobType[];
  useScenarioJobTypes: boolean;
  useScenarioRevenue: boolean;
  useScenarioMetrics: boolean;
}

// Typical dispatcher hourly rates by country (in local currency)
const HOURLY_RATES_BY_COUNTRY: Record<string, number> = {
  'GB': 25,    // £25/hr
  'US': 30,    // $30/hr
  'DE': 28,    // €28/hr
  'FR': 26,    // €26/hr
  'AU': 35,    // A$35/hr
  'IN': 500,   // ₹500/hr
  'NL': 27,    // €27/hr
  'ES': 22,    // €22/hr
  'IT': 24,    // €24/hr
  'CA': 32,    // C$32/hr
};

// Default configuration (UK - London - Belron)
const DEFAULT_CONFIG: AppConfig = {
  countryCode: 'GB',
  cityId: 'london',
  aiModel: 'openai.gpt-4o-mini',
  currency: { code: 'GBP', symbol: '£', position: 'before' },
  distanceUnit: 'miles',
  dateFormat: 'DD/MM/YYYY',
  timeFormat: '24h',
  defaultCenter: { lat: 51.5074, lng: -0.1278 },
  defaultZoom: 11,
  serviceRadius: 40,
  defaultVehicles: 12,
  defaultShiftHours: 8,
  workingHoursStart: '08:00',
  workingHoursEnd: '18:00',
  vehicleLabelType: 'license_plate',
  dispatcherHourlyRate: 25,
  activeScenario: 'belron',
  scenarioJobTypes: SCENARIO_PRESETS.find(s => s.id === 'belron')?.jobTypes || [],
  useScenarioJobTypes: true,
  useScenarioRevenue: true,
  useScenarioMetrics: true,
};

interface ConfigStore {
  config: AppConfig;

  // Country/City setters
  setCountry: (countryCode: string) => void;
  setCity: (cityId: string) => void;

  // AI Model setter
  setAiModel: (modelId: string) => void;

  // Preference setters
  setDistanceUnit: (unit: 'km' | 'miles') => void;
  setTimeFormat: (format: '12h' | '24h') => void;
  setVehicleLabelType: (type: 'generic' | 'license_plate') => void;

  // Business defaults setters
  setDefaultVehicles: (count: number) => void;
  setDefaultShiftHours: (hours: number) => void;
  setWorkingHours: (start: string, end: string) => void;

  // Map setters
  setDefaultCenter: (lat: number, lng: number) => void;
  setDefaultZoom: (zoom: number) => void;
  setServiceRadius: (radius: number) => void;

  // Scenario setters
  setActiveScenario: (scenarioId: string) => void;
  setUseScenarioJobTypes: (use: boolean) => void;
  setUseScenarioRevenue: (use: boolean) => void;
  setUseScenarioMetrics: (use: boolean) => void;

  // General update
  updateConfig: (partial: Partial<AppConfig>) => void;

  // Reset
  resetToDefaults: () => void;

  // Helper to check if using Belron scenario
  isBelronScenario: () => boolean;
}

export const useConfigStore = create<ConfigStore>()(
  persist(
    (set, get) => ({
      config: DEFAULT_CONFIG,

      setCountry: (countryCode: string) => {
        const country = getCountryByCode(countryCode);
        if (country) {
          const firstCity = country.cities[0];
          const hourlyRate = HOURLY_RATES_BY_COUNTRY[countryCode] || 25;
          set({
            config: {
              ...get().config,
              countryCode,
              cityId: firstCity.id,
              currency: country.currency,
              distanceUnit: country.units.distance,
              dateFormat: country.units.dateFormat,
              timeFormat: country.units.timeFormat,
              defaultCenter: firstCity.coordinates,
              defaultZoom: firstCity.defaultZoom,
              serviceRadius: firstCity.serviceRadius,
              dispatcherHourlyRate: hourlyRate,
            },
          });
        }
      },

      setCity: (cityId: string) => {
        const city = getCityById(get().config.countryCode, cityId);
        if (city) {
          set({
            config: {
              ...get().config,
              cityId,
              defaultCenter: city.coordinates,
              defaultZoom: city.defaultZoom,
              serviceRadius: city.serviceRadius,
            },
          });
        }
      },

      setAiModel: (modelId: string) => {
        set({ config: { ...get().config, aiModel: modelId } });
      },

      setDistanceUnit: (unit: 'km' | 'miles') => {
        set({ config: { ...get().config, distanceUnit: unit } });
      },

      setTimeFormat: (format: '12h' | '24h') => {
        set({ config: { ...get().config, timeFormat: format } });
      },

      setVehicleLabelType: (type: 'generic' | 'license_plate') => {
        set({ config: { ...get().config, vehicleLabelType: type } });
      },

      setDefaultVehicles: (count: number) => {
        set({ config: { ...get().config, defaultVehicles: count } });
      },

      setDefaultShiftHours: (hours: number) => {
        set({ config: { ...get().config, defaultShiftHours: hours } });
      },

      setWorkingHours: (start: string, end: string) => {
        set({ config: { ...get().config, workingHoursStart: start, workingHoursEnd: end } });
      },

      setDefaultCenter: (lat: number, lng: number) => {
        set({ config: { ...get().config, defaultCenter: { lat, lng } } });
      },

      setDefaultZoom: (zoom: number) => {
        set({ config: { ...get().config, defaultZoom: zoom } });
      },

      setServiceRadius: (radius: number) => {
        set({ config: { ...get().config, serviceRadius: radius } });
      },

      setActiveScenario: (scenarioId: string) => {
        const scenario = SCENARIO_PRESETS.find(s => s.id === scenarioId);
        if (scenario) {
          set({
            config: {
              ...get().config,
              activeScenario: scenarioId,
              scenarioJobTypes: scenario.jobTypes,
              defaultVehicles: scenario.defaultVehicles,
              defaultShiftHours: scenario.defaultShiftHours,
            },
          });
        }
      },

      setUseScenarioJobTypes: (use: boolean) => {
        set({ config: { ...get().config, useScenarioJobTypes: use } });
      },

      setUseScenarioRevenue: (use: boolean) => {
        set({ config: { ...get().config, useScenarioRevenue: use } });
      },

      setUseScenarioMetrics: (use: boolean) => {
        set({ config: { ...get().config, useScenarioMetrics: use } });
      },

      updateConfig: (partial: Partial<AppConfig>) => {
        set({ config: { ...get().config, ...partial } });
      },

      resetToDefaults: () => {
        set({ config: DEFAULT_CONFIG });
      },

      isBelronScenario: () => {
        return get().config.activeScenario === 'belron' && get().config.useScenarioJobTypes;
      },
    }),
    {
      name: 'cuopt-config', // localStorage key
      version: 1,
    }
  )
);

// Export helper to get current config outside of React components
export const getConfig = () => useConfigStore.getState().config;
