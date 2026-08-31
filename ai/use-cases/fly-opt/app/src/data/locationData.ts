// Location data for multi-region support
// Provides country and city configurations with defaults

export interface CurrencyConfig {
  code: string;         // ISO 4217
  symbol: string;
  position: 'before' | 'after';
}

export interface UnitsConfig {
  distance: 'km' | 'miles';
  dateFormat: string;
  timeFormat: '12h' | '24h';
}

export interface CityConfig {
  id: string;
  name: string;
  coordinates: {
    lat: number;
    lng: number;
  };
  defaultZoom: number;
  serviceRadius: number;  // km
  timezone: string;
}

export interface CountryConfig {
  code: string;           // ISO 3166-1 alpha-2
  name: string;
  flag: string;           // Emoji flag
  currency: CurrencyConfig;
  units: UnitsConfig;
  cities: CityConfig[];
  licensePlateFormat: string;  // Regex pattern
  licensePlateExample: string;
}

// Pre-configured countries
export const COUNTRIES: CountryConfig[] = [
  {
    code: 'GB',
    name: 'United Kingdom',
    flag: '🇬🇧',
    currency: { code: 'GBP', symbol: '£', position: 'before' },
    units: { distance: 'miles', dateFormat: 'DD/MM/YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[A-Z]{2}[0-9]{2}\\s?[A-Z]{3}$',
    licensePlateExample: 'YA23 YRK',
    cities: [
      { id: 'london', name: 'London', coordinates: { lat: 51.5074, lng: -0.1278 }, defaultZoom: 11, serviceRadius: 40, timezone: 'Europe/London' },
      { id: 'manchester', name: 'Manchester', coordinates: { lat: 53.4808, lng: -2.2426 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/London' },
      { id: 'birmingham', name: 'Birmingham', coordinates: { lat: 52.4862, lng: -1.8904 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/London' },
      { id: 'glasgow', name: 'Glasgow', coordinates: { lat: 55.8642, lng: -4.2518 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/London' },
      { id: 'edinburgh', name: 'Edinburgh', coordinates: { lat: 55.9533, lng: -3.1883 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/London' },
      { id: 'leeds', name: 'Leeds', coordinates: { lat: 53.8008, lng: -1.5491 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/London' },
      { id: 'liverpool', name: 'Liverpool', coordinates: { lat: 53.4084, lng: -2.9916 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/London' },
      { id: 'bristol', name: 'Bristol', coordinates: { lat: 51.4545, lng: -2.5879 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/London' },
    ],
  },
  {
    code: 'US',
    name: 'United States',
    flag: '🇺🇸',
    currency: { code: 'USD', symbol: '$', position: 'before' },
    units: { distance: 'miles', dateFormat: 'MM/DD/YYYY', timeFormat: '12h' },
    licensePlateFormat: '^[A-Z0-9]{5,7}$',
    licensePlateExample: 'ABC1234',
    cities: [
      { id: 'new_york', name: 'New York', coordinates: { lat: 40.7128, lng: -74.0060 }, defaultZoom: 11, serviceRadius: 50, timezone: 'America/New_York' },
      { id: 'los_angeles', name: 'Los Angeles', coordinates: { lat: 34.0522, lng: -118.2437 }, defaultZoom: 10, serviceRadius: 60, timezone: 'America/Los_Angeles' },
      { id: 'chicago', name: 'Chicago', coordinates: { lat: 41.8781, lng: -87.6298 }, defaultZoom: 11, serviceRadius: 45, timezone: 'America/Chicago' },
      { id: 'houston', name: 'Houston', coordinates: { lat: 29.7604, lng: -95.3698 }, defaultZoom: 10, serviceRadius: 50, timezone: 'America/Chicago' },
      { id: 'phoenix', name: 'Phoenix', coordinates: { lat: 33.4484, lng: -112.0740 }, defaultZoom: 11, serviceRadius: 45, timezone: 'America/Phoenix' },
      { id: 'san_francisco', name: 'San Francisco', coordinates: { lat: 37.7749, lng: -122.4194 }, defaultZoom: 12, serviceRadius: 35, timezone: 'America/Los_Angeles' },
      { id: 'seattle', name: 'Seattle', coordinates: { lat: 47.6062, lng: -122.3321 }, defaultZoom: 11, serviceRadius: 40, timezone: 'America/Los_Angeles' },
      { id: 'miami', name: 'Miami', coordinates: { lat: 25.7617, lng: -80.1918 }, defaultZoom: 11, serviceRadius: 40, timezone: 'America/New_York' },
    ],
  },
  {
    code: 'DE',
    name: 'Germany',
    flag: '🇩🇪',
    currency: { code: 'EUR', symbol: '€', position: 'after' },
    units: { distance: 'km', dateFormat: 'DD.MM.YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[A-ZÄÖÜ]{1,3}\\s?[A-Z]{1,2}\\s?[0-9]{1,4}$',
    licensePlateExample: 'B AB 1234',
    cities: [
      { id: 'berlin', name: 'Berlin', coordinates: { lat: 52.5200, lng: 13.4050 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Europe/Berlin' },
      { id: 'munich', name: 'Munich', coordinates: { lat: 48.1351, lng: 11.5820 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Berlin' },
      { id: 'frankfurt', name: 'Frankfurt', coordinates: { lat: 50.1109, lng: 8.6821 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Berlin' },
      { id: 'hamburg', name: 'Hamburg', coordinates: { lat: 53.5511, lng: 9.9937 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Berlin' },
      { id: 'cologne', name: 'Cologne', coordinates: { lat: 50.9375, lng: 6.9603 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Berlin' },
      { id: 'stuttgart', name: 'Stuttgart', coordinates: { lat: 48.7758, lng: 9.1829 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Berlin' },
    ],
  },
  {
    code: 'FR',
    name: 'France',
    flag: '🇫🇷',
    currency: { code: 'EUR', symbol: '€', position: 'after' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[A-Z]{2}-[0-9]{3}-[A-Z]{2}$',
    licensePlateExample: 'AB-123-CD',
    cities: [
      { id: 'paris', name: 'Paris', coordinates: { lat: 48.8566, lng: 2.3522 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Paris' },
      { id: 'lyon', name: 'Lyon', coordinates: { lat: 45.7640, lng: 4.8357 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Paris' },
      { id: 'marseille', name: 'Marseille', coordinates: { lat: 43.2965, lng: 5.3698 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Paris' },
      { id: 'toulouse', name: 'Toulouse', coordinates: { lat: 43.6047, lng: 1.4442 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Paris' },
      { id: 'nice', name: 'Nice', coordinates: { lat: 43.7102, lng: 7.2620 }, defaultZoom: 12, serviceRadius: 20, timezone: 'Europe/Paris' },
    ],
  },
  {
    code: 'AU',
    name: 'Australia',
    flag: '🇦🇺',
    currency: { code: 'AUD', symbol: '$', position: 'before' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '12h' },
    licensePlateFormat: '^[A-Z0-9]{6}$',
    licensePlateExample: 'ABC123',
    cities: [
      { id: 'sydney', name: 'Sydney', coordinates: { lat: -33.8688, lng: 151.2093 }, defaultZoom: 11, serviceRadius: 40, timezone: 'Australia/Sydney' },
      { id: 'melbourne', name: 'Melbourne', coordinates: { lat: -37.8136, lng: 144.9631 }, defaultZoom: 11, serviceRadius: 40, timezone: 'Australia/Melbourne' },
      { id: 'brisbane', name: 'Brisbane', coordinates: { lat: -27.4698, lng: 153.0251 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Australia/Brisbane' },
      { id: 'perth', name: 'Perth', coordinates: { lat: -31.9505, lng: 115.8605 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Australia/Perth' },
      { id: 'adelaide', name: 'Adelaide', coordinates: { lat: -34.9285, lng: 138.6007 }, defaultZoom: 11, serviceRadius: 30, timezone: 'Australia/Adelaide' },
    ],
  },
  {
    code: 'IN',
    name: 'India',
    flag: '🇮🇳',
    currency: { code: 'INR', symbol: '₹', position: 'before' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '12h' },
    licensePlateFormat: '^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$',
    licensePlateExample: 'MH12AB1234',
    cities: [
      { id: 'mumbai', name: 'Mumbai', coordinates: { lat: 19.05, lng: 72.88 }, defaultZoom: 12, serviceRadius: 15, timezone: 'Asia/Kolkata' },
      { id: 'delhi', name: 'Delhi', coordinates: { lat: 28.7041, lng: 77.1025 }, defaultZoom: 11, serviceRadius: 40, timezone: 'Asia/Kolkata' },
      { id: 'bangalore', name: 'Bangalore', coordinates: { lat: 12.9716, lng: 77.5946 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Asia/Kolkata' },
      { id: 'chennai', name: 'Chennai', coordinates: { lat: 13.0827, lng: 80.2707 }, defaultZoom: 11, serviceRadius: 30, timezone: 'Asia/Kolkata' },
      { id: 'hyderabad', name: 'Hyderabad', coordinates: { lat: 17.3850, lng: 78.4867 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Asia/Kolkata' },
      { id: 'pune', name: 'Pune', coordinates: { lat: 18.5204, lng: 73.8567 }, defaultZoom: 11, serviceRadius: 30, timezone: 'Asia/Kolkata' },
    ],
  },
  {
    code: 'NL',
    name: 'Netherlands',
    flag: '🇳🇱',
    currency: { code: 'EUR', symbol: '€', position: 'before' },
    units: { distance: 'km', dateFormat: 'DD-MM-YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[A-Z0-9]{2}-[A-Z0-9]{3}-[A-Z0-9]{1}$',
    licensePlateExample: 'AB-123-C',
    cities: [
      { id: 'amsterdam', name: 'Amsterdam', coordinates: { lat: 52.3676, lng: 4.9041 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Amsterdam' },
      { id: 'rotterdam', name: 'Rotterdam', coordinates: { lat: 51.9244, lng: 4.4777 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Amsterdam' },
      { id: 'the_hague', name: 'The Hague', coordinates: { lat: 52.0705, lng: 4.3007 }, defaultZoom: 12, serviceRadius: 20, timezone: 'Europe/Amsterdam' },
      { id: 'utrecht', name: 'Utrecht', coordinates: { lat: 52.0907, lng: 5.1214 }, defaultZoom: 12, serviceRadius: 20, timezone: 'Europe/Amsterdam' },
    ],
  },
  {
    code: 'ES',
    name: 'Spain',
    flag: '🇪🇸',
    currency: { code: 'EUR', symbol: '€', position: 'after' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[0-9]{4}[A-Z]{3}$',
    licensePlateExample: '1234ABC',
    cities: [
      { id: 'madrid', name: 'Madrid', coordinates: { lat: 40.4168, lng: -3.7038 }, defaultZoom: 11, serviceRadius: 35, timezone: 'Europe/Madrid' },
      { id: 'barcelona', name: 'Barcelona', coordinates: { lat: 41.3851, lng: 2.1734 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Madrid' },
      { id: 'valencia', name: 'Valencia', coordinates: { lat: 39.4699, lng: -0.3763 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Madrid' },
      { id: 'seville', name: 'Seville', coordinates: { lat: 37.3891, lng: -5.9845 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Madrid' },
    ],
  },
  {
    code: 'IT',
    name: 'Italy',
    flag: '🇮🇹',
    currency: { code: 'EUR', symbol: '€', position: 'after' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[A-Z]{2}[0-9]{3}[A-Z]{2}$',
    licensePlateExample: 'AB123CD',
    cities: [
      { id: 'rome', name: 'Rome', coordinates: { lat: 41.9028, lng: 12.4964 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Rome' },
      { id: 'milan', name: 'Milan', coordinates: { lat: 45.4642, lng: 9.1900 }, defaultZoom: 12, serviceRadius: 30, timezone: 'Europe/Rome' },
      { id: 'naples', name: 'Naples', coordinates: { lat: 40.8518, lng: 14.2681 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Rome' },
      { id: 'turin', name: 'Turin', coordinates: { lat: 45.0703, lng: 7.6869 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Rome' },
    ],
  },
  {
    code: 'BE',
    name: 'Belgium',
    flag: '🇧🇪',
    currency: { code: 'EUR', symbol: '€', position: 'before' },
    units: { distance: 'km', dateFormat: 'DD/MM/YYYY', timeFormat: '24h' },
    licensePlateFormat: '^[0-9]-[A-Z]{3}-[0-9]{3}$',
    licensePlateExample: '1-ABC-234',
    cities: [
      { id: 'brussels', name: 'Brussels', coordinates: { lat: 50.8503, lng: 4.3517 }, defaultZoom: 12, serviceRadius: 25, timezone: 'Europe/Brussels' },
      { id: 'antwerp', name: 'Antwerp', coordinates: { lat: 51.2194, lng: 4.4025 }, defaultZoom: 12, serviceRadius: 20, timezone: 'Europe/Brussels' },
      { id: 'ghent', name: 'Ghent', coordinates: { lat: 51.0543, lng: 3.7174 }, defaultZoom: 12, serviceRadius: 18, timezone: 'Europe/Brussels' },
    ],
  },
];

// Scenario presets for different industries
export interface ScenarioPreset {
  id: string;
  name: string;
  description: string;
  jobTypes: BelronJobType[];
  defaultVehicles: number;
  defaultShiftHours: number;
}

// Belron-specific job types
export interface BelronJobType {
  id: string;
  label: string;
  duration: number;       // minutes
  revenue: number;        // in local currency
  color: string;
  defaultPercentage: number;
}

export const BELRON_JOB_TYPES: BelronJobType[] = [
  {
    id: 'repair',
    label: 'Repair',
    duration: 30,
    revenue: 100,
    color: '#22C55E', // green
    defaultPercentage: 20,
  },
  {
    id: 'replace',
    label: 'Replace',
    duration: 90,
    revenue: 300,
    color: '#F97316', // orange
    defaultPercentage: 60,
  },
  {
    id: 'replace_recalibrate',
    label: 'Replace + Recalibrate',
    duration: 180,
    revenue: 450, // £300 + £150
    color: '#8B5CF6', // purple
    defaultPercentage: 20,
  },
];

export const SCENARIO_PRESETS: ScenarioPreset[] = [
  {
    id: 'belron',
    name: 'Belron - Windscreen Services',
    description: 'Windscreen repair and replacement services',
    jobTypes: BELRON_JOB_TYPES,
    defaultVehicles: 12,
    defaultShiftHours: 8,
  },
  {
    id: 'generic',
    name: 'Generic Field Service',
    description: 'General field service operations',
    jobTypes: [
      { id: 'standard', label: 'Standard Service', duration: 60, revenue: 150, color: '#3B82F6', defaultPercentage: 100 },
    ],
    defaultVehicles: 10,
    defaultShiftHours: 8,
  },
];

// Helper functions

/**
 * Get a country by its code
 */
export function getCountryByCode(code: string): CountryConfig | undefined {
  return COUNTRIES.find(c => c.code === code);
}

/**
 * Get a city from a country
 */
export function getCityById(countryCode: string, cityId: string): CityConfig | undefined {
  const country = getCountryByCode(countryCode);
  return country?.cities.find(c => c.id === cityId);
}

/**
 * Get scenario preset by ID
 */
export function getScenarioPreset(id: string): ScenarioPreset | undefined {
  return SCENARIO_PRESETS.find(s => s.id === id);
}

/**
 * Format currency based on configuration
 */
export function formatCurrency(amount: number, currency: CurrencyConfig): string {
  const formatted = amount.toLocaleString();
  if (currency.position === 'before') {
    return `${currency.symbol}${formatted}`;
  }
  return `${formatted}${currency.symbol}`;
}

/**
 * Convert distance based on unit preference
 */
export function convertDistance(km: number, unit: 'km' | 'miles'): number {
  if (unit === 'miles') {
    return km * 0.621371;
  }
  return km;
}

/**
 * Format distance with unit
 */
export function formatDistance(km: number, unit: 'km' | 'miles'): string {
  const converted = convertDistance(km, unit);
  return `${converted.toFixed(1)} ${unit}`;
}

// Country-specific regional centers for multi-city and national scenarios
// These are geographic centers that cover multiple cities properly
const REGIONAL_CENTERS: Record<string, { multiCity: { lat: number; lng: number; radiusKm: number; name: string }; national: { lat: number; lng: number; radiusKm: number } }> = {
  GB: {
    multiCity: { lat: 52.6369, lng: -1.5, radiusKm: 80, name: 'Manchester & Birmingham' }, // Midlands center
    national: { lat: 54.0, lng: -2.0, radiusKm: 300 }, // UK center
  },
  US: {
    multiCity: { lat: 39.8283, lng: -98.5795, radiusKm: 200, name: 'Central US' },
    national: { lat: 39.8283, lng: -98.5795, radiusKm: 1500 },
  },
  DE: {
    multiCity: { lat: 51.0, lng: 9.0, radiusKm: 150, name: 'Central Germany' },
    national: { lat: 51.0, lng: 9.0, radiusKm: 400 },
  },
  FR: {
    multiCity: { lat: 46.5, lng: 2.5, radiusKm: 200, name: 'Central France' },
    national: { lat: 46.5, lng: 2.5, radiusKm: 500 },
  },
  AU: {
    multiCity: { lat: -33.0, lng: 147.0, radiusKm: 300, name: 'Eastern Australia' },
    national: { lat: -25.0, lng: 135.0, radiusKm: 1500 },
  },
  IN: {
    multiCity: { lat: 20.0, lng: 78.0, radiusKm: 300, name: 'Central India' },
    national: { lat: 20.0, lng: 78.0, radiusKm: 1000 },
  },
  NL: {
    multiCity: { lat: 52.1, lng: 5.0, radiusKm: 60, name: 'Randstad' },
    national: { lat: 52.1, lng: 5.0, radiusKm: 150 },
  },
  ES: {
    multiCity: { lat: 40.0, lng: -3.5, radiusKm: 200, name: 'Central Spain' },
    national: { lat: 40.0, lng: -3.5, radiusKm: 500 },
  },
  IT: {
    multiCity: { lat: 43.0, lng: 12.0, radiusKm: 200, name: 'Central Italy' },
    national: { lat: 42.0, lng: 12.5, radiusKm: 500 },
  },
  BE: {
    multiCity: { lat: 50.8, lng: 4.5, radiusKm: 50, name: 'Belgium' },
    national: { lat: 50.8, lng: 4.5, radiusKm: 100 },
  },
};

/**
 * Generate dynamic benchmark scenarios based on selected location
 */
export function generateDynamicScenarios(
  countryCode: string,
  cityId: string,
  scenarioId: string = 'belron'
): DynamicBenchmarkScenario[] {
  const country = getCountryByCode(countryCode);
  const city = getCityById(countryCode, cityId);
  const scenario = getScenarioPreset(scenarioId);

  if (!country || !city) return [];

  const cityName = city.name;
  const countryName = country.name;
  // Currency available via: country.currency.symbol

  // Get regional centers for multi-city and national scenarios
  const regionalCenters = REGIONAL_CENTERS[countryCode] || {
    multiCity: { lat: city.coordinates.lat, lng: city.coordinates.lng, radiusKm: city.serviceRadius * 2, name: `${cityName} Region` },
    national: { lat: city.coordinates.lat, lng: city.coordinates.lng, radiusKm: city.serviceRadius * 4 },
  };

  const scenarios: DynamicBenchmarkScenario[] = [
    {
      id: `${scenarioId}_${cityId}`,
      name: `${scenario?.name?.split(' - ')[0] || 'Service'} ${cityName}`,
      description: `50 service jobs across ${cityName} area`,
      stops: 50,
      vehicles: 12,
      expectedSolveTime: 25,
      payloadSizeMB: 0.11,
      category: 'field_service',
      centerLat: city.coordinates.lat,
      centerLng: city.coordinates.lng,
      radiusKm: city.serviceRadius,
    },
    {
      id: `${cityId}_central`,
      name: `${cityName} Central`,
      description: `100 deliveries in Central ${cityName}`,
      stops: 100,
      vehicles: 10,
      expectedSolveTime: 30,
      payloadSizeMB: 0.43,
      category: 'field_service',
      centerLat: city.coordinates.lat,
      centerLng: city.coordinates.lng,
      radiusKm: city.serviceRadius * 0.4,
    },
    {
      id: `${cityId}_region`,
      name: `${cityName} Region`,
      description: `200 stops across Greater ${cityName}`,
      stops: 200,
      vehicles: 20,
      expectedSolveTime: 60,
      payloadSizeMB: 1.73,
      category: 'field_service',
      centerLat: city.coordinates.lat,
      centerLng: city.coordinates.lng,
      radiusKm: city.serviceRadius,
    },
    {
      id: `${countryCode.toLowerCase()}_multi_city`,
      name: regionalCenters.multiCity.name,
      description: `500 stops across multiple cities`,
      stops: 500,
      vehicles: 30,
      expectedSolveTime: 90,
      payloadSizeMB: 10.80,
      category: 'mixed_density',
      centerLat: regionalCenters.multiCity.lat,
      centerLng: regionalCenters.multiCity.lng,
      radiusKm: regionalCenters.multiCity.radiusKm,
    },
    {
      id: `${countryCode.toLowerCase()}_national`,
      name: `${countryName} National`,
      description: `1,000 stops nationwide delivery`,
      stops: 1000,
      vehicles: 50,
      expectedSolveTime: 135,
      payloadSizeMB: 43.20,
      category: 'high_density_parcel',
      centerLat: regionalCenters.national.lat,
      centerLng: regionalCenters.national.lng,
      radiusKm: regionalCenters.national.radiusKm,
    },
  ];

  return scenarios;
}

export interface DynamicBenchmarkScenario {
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

/**
 * Generate dynamic example prompts based on selected location
 */
export function generateDynamicPrompts(
  countryCode: string,
  cityId: string,
  scenarioId: string = 'belron'
): string[] {
  const country = getCountryByCode(countryCode);
  const city = getCityById(countryCode, cityId);
  const scenario = getScenarioPreset(scenarioId);

  if (!country || !city) return [];

  const cityName = city.name;
  const countryName = country.name;
  // Currency available via: country.currency.symbol

  // Find nearby cities
  const nearbyCities = country.cities
    .filter(c => c.id !== cityId)
    .slice(0, 2)
    .map(c => c.name);

  // Generate location-specific prompts
  const prompts = [
    `Optimize 50 deliveries across ${cityName} with 5 vehicles available 8am-6pm`,
    `Plan routes for 200 stops in ${cityName} area with 20 vans`,
    `I have 500 parcels to deliver across ${cityName} region, minimize fuel costs`,
    `Schedule 100 engineer visits in ${cityName} with priority levels`,
    `What's the best route for 1000 ${countryName}-wide deliveries?`,
    `Plan delivery routes from ${cityName} depot to cover ${nearbyCities[0] || 'nearby'} area`,
  ];

  // Add Belron-specific prompts if scenario is Belron
  if (scenarioId === 'belron' && scenario) {
    const jobTypes = scenario.jobTypes.map(jt => jt.label.toLowerCase()).join(', ');
    prompts.push(
      `Schedule 50 windscreen service jobs (${jobTypes}) across ${cityName} for 12 technicians`,
      `Optimize Belron routes for 30 urgent replacements in ${cityName} before 2pm`,
      `Plan technician routes for 40 jobs in ${cityName}: 20% repairs, 60% replacements, 20% recalibrations`
    );
  }

  return prompts;
}

/**
 * Generate a license plate based on country format
 */
export function generateLicensePlate(countryCode: string, index: number): string {
  const country = getCountryByCode(countryCode);
  if (!country) return `V${index + 1}`;

  // Generate realistic-looking plates based on country
  switch (countryCode) {
    case 'GB': {
      // UK format: AB12 CDE
      const letters1 = ['YA', 'LN', 'BA', 'MK', 'SW', 'NE', 'SE', 'WM', 'EM', 'WY'][index % 10];
      const year = 23 + Math.floor(index / 10);
      const letters2 = ['YRK', 'FLT', 'ABC', 'XYZ', 'JKL', 'MNO', 'PQR', 'STU', 'VWX', 'DEF'][index % 10];
      return `${letters1}${year} ${letters2}`;
    }
    case 'US': {
      // US format varies, using generic ABC1234
      const letters = String.fromCharCode(65 + (index % 26)) +
                      String.fromCharCode(65 + ((index + 1) % 26)) +
                      String.fromCharCode(65 + ((index + 2) % 26));
      const numbers = String(1000 + index).slice(-4);
      return `${letters}${numbers}`;
    }
    case 'DE': {
      // German format: B AB 1234
      const city = ['B', 'M', 'F', 'HH', 'K', 'S', 'D', 'N', 'L', 'DO'][index % 10];
      const letters = String.fromCharCode(65 + (index % 26)) + String.fromCharCode(65 + ((index + 1) % 26));
      const numbers = String(100 + index).slice(-4);
      return `${city} ${letters} ${numbers}`;
    }
    case 'FR': {
      // French format: AB-123-CD
      const l1 = String.fromCharCode(65 + (index % 26)) + String.fromCharCode(65 + ((index + 1) % 26));
      const num = String(100 + index).slice(-3);
      const l2 = String.fromCharCode(65 + ((index + 2) % 26)) + String.fromCharCode(65 + ((index + 3) % 26));
      return `${l1}-${num}-${l2}`;
    }
    case 'AU': {
      // Australian format: ABC123
      const letters = String.fromCharCode(65 + (index % 26)) +
                      String.fromCharCode(65 + ((index + 1) % 26)) +
                      String.fromCharCode(65 + ((index + 2) % 26));
      const numbers = String(100 + index).slice(-3);
      return `${letters}${numbers}`;
    }
    case 'IN': {
      // Indian format: MH12AB1234
      const states = ['MH', 'DL', 'KA', 'TN', 'AP', 'GJ', 'RJ', 'UP', 'WB', 'MP'][index % 10];
      const district = String(10 + (index % 90)).slice(-2);
      const series = String.fromCharCode(65 + (index % 26)) + String.fromCharCode(65 + ((index + 1) % 26));
      const numbers = String(1000 + index).slice(-4);
      return `${states}${district}${series}${numbers}`;
    }
    default: {
      // Generic format
      return `V${String(index + 1).padStart(3, '0')}`;
    }
  }
}
