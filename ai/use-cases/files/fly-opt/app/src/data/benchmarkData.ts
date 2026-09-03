// Benchmark data from actual performance tests
// Source: payload_optimization benchmark results
// Updated for UK Route Optimization

import type { BenchmarkScenario, PerformanceMetric } from '@/types';
import {
  ukPostcodeAreas,
  getNearestPostcodeArea,
  generateUKPostcode,
  generateUKStops,
  generateBelronStops,
  belronJobTypes,
  ukMajorCities,
} from './ukPostcodes';

// Re-export UK data for convenience
export { ukPostcodeAreas, getNearestPostcodeArea, generateUKPostcode, generateUKStops, generateBelronStops, belronJobTypes, ukMajorCities };

// ============================================================================
// SCENARIO BUSINESS METRICS
// Different scenarios have different baseline metrics for LLM context
// ============================================================================

export interface ScenarioMetrics {
  id: string;
  name: string;
  type: 'field_service' | 'delivery' | 'food_delivery' | 'logistics' | 'healthcare';
  jobType: string;
  baselineJobsPerTech: number;  // Industry baseline jobs per technician/driver per day
  avgRevenuePerJob: number;     // Average revenue per job in GBP
  fuelCostPerKm: number;        // Fuel cost per km in GBP
  avgServiceTime: number;       // Average service/dwell time in minutes
  description: string;
}

export const SCENARIO_METRICS: Record<string, ScenarioMetrics> = {
  belron: {
    id: 'belron',
    name: 'Belron Windscreen Services',
    type: 'field_service',
    jobType: 'windscreen repair/replacement',
    baselineJobsPerTech: 3.2,
    avgRevenuePerJob: 185,
    fuelCostPerKm: 0.15,
    avgServiceTime: 45,
    description: 'Field service technicians performing windscreen repairs and replacements'
  },
  generic_delivery: {
    id: 'generic_delivery',
    name: 'Generic Delivery',
    type: 'delivery',
    jobType: 'package delivery',
    baselineJobsPerTech: 25,
    avgRevenuePerJob: 8,
    fuelCostPerKm: 0.12,
    avgServiceTime: 5,
    description: 'Standard package delivery operations'
  },
  food_delivery: {
    id: 'food_delivery',
    name: 'Food Delivery',
    type: 'food_delivery',
    jobType: 'restaurant/food delivery',
    baselineJobsPerTech: 15,
    avgRevenuePerJob: 12,
    fuelCostPerKm: 0.10,
    avgServiceTime: 8,
    description: 'Restaurant and food delivery services'
  },
  logistics: {
    id: 'logistics',
    name: 'Logistics & Freight',
    type: 'logistics',
    jobType: 'freight/cargo delivery',
    baselineJobsPerTech: 8,
    avgRevenuePerJob: 150,
    fuelCostPerKm: 0.25,
    avgServiceTime: 30,
    description: 'Commercial logistics and freight delivery'
  },
  healthcare: {
    id: 'healthcare',
    name: 'Healthcare Services',
    type: 'healthcare',
    jobType: 'home healthcare visit',
    baselineJobsPerTech: 6,
    avgRevenuePerJob: 95,
    fuelCostPerKm: 0.14,
    avgServiceTime: 35,
    description: 'Home healthcare and medical service visits'
  },
  ev_charging: {
    id: 'ev_charging',
    name: 'EV Charging Network',
    type: 'field_service',
    jobType: 'EV charger maintenance',
    baselineJobsPerTech: 4,
    avgRevenuePerJob: 220,
    fuelCostPerKm: 0.08,
    avgServiceTime: 60,
    description: 'Electric vehicle charging station maintenance and installation'
  }
};

// Get scenario metrics by ID with fallback to generic delivery
export function getScenarioMetrics(scenarioId: string): ScenarioMetrics {
  // Try exact match first
  if (SCENARIO_METRICS[scenarioId]) {
    return SCENARIO_METRICS[scenarioId];
  }

  // Try partial match (e.g., 'belron_london' should match 'belron')
  const partialMatch = Object.keys(SCENARIO_METRICS).find(key =>
    scenarioId.toLowerCase().includes(key) || key.includes(scenarioId.toLowerCase())
  );

  if (partialMatch) {
    return SCENARIO_METRICS[partialMatch];
  }

  // Default to generic delivery
  return SCENARIO_METRICS.generic_delivery;
}

// Detect scenario from user prompt
export function detectScenarioFromPrompt(prompt: string): ScenarioMetrics {
  const lowerPrompt = prompt.toLowerCase();

  if (lowerPrompt.includes('windscreen') || lowerPrompt.includes('belron') || lowerPrompt.includes('glass') || lowerPrompt.includes('autoglass')) {
    return SCENARIO_METRICS.belron;
  }
  if (lowerPrompt.includes('food') || lowerPrompt.includes('restaurant') || lowerPrompt.includes('meal') || lowerPrompt.includes('takeaway')) {
    return SCENARIO_METRICS.food_delivery;
  }
  if (lowerPrompt.includes('healthcare') || lowerPrompt.includes('medical') || lowerPrompt.includes('patient') || lowerPrompt.includes('nurse')) {
    return SCENARIO_METRICS.healthcare;
  }
  if (lowerPrompt.includes('freight') || lowerPrompt.includes('cargo') || lowerPrompt.includes('logistics') || lowerPrompt.includes('warehouse')) {
    return SCENARIO_METRICS.logistics;
  }
  if (lowerPrompt.includes('ev') || lowerPrompt.includes('charging') || lowerPrompt.includes('electric vehicle')) {
    return SCENARIO_METRICS.ev_charging;
  }

  // Default to generic delivery
  return SCENARIO_METRICS.generic_delivery;
}

// Performance baselines from Phase 1-3 testing
// Note: These baselines reflect CONSTRAINED field service scenarios (time windows, service durations, capacity)
// which are more realistic for enterprise use cases like Belron windscreen services
export const performanceBaselines: PerformanceMetric[] = [
  // Small datasets - field service with constraints
  { stopCount: 25, payloadSizeMB: 0.03, solveTimeSeconds: 18, throughputStopsPerSec: 1.4, status: 'success' },
  { stopCount: 50, payloadSizeMB: 0.11, solveTimeSeconds: 42, throughputStopsPerSec: 1.2, status: 'success' },
  { stopCount: 100, payloadSizeMB: 0.43, solveTimeSeconds: 65, throughputStopsPerSec: 1.5, status: 'success' },
  { stopCount: 250, payloadSizeMB: 2.7, solveTimeSeconds: 95, throughputStopsPerSec: 2.6, status: 'success' },
  { stopCount: 500, payloadSizeMB: 10.8, solveTimeSeconds: 140, throughputStopsPerSec: 3.6, status: 'success' },
  // Medium to large datasets
  { stopCount: 1000, payloadSizeMB: 36.85, solveTimeSeconds: 200, throughputStopsPerSec: 5.0, status: 'success' },
  { stopCount: 2500, payloadSizeMB: 230.43, solveTimeSeconds: 320, throughputStopsPerSec: 7.8, status: 'success' },
  { stopCount: 5000, payloadSizeMB: 921.96, solveTimeSeconds: 480, throughputStopsPerSec: 10.4, status: 'success' },
  { stopCount: 7500, payloadSizeMB: 1989.97, solveTimeSeconds: 600, throughputStopsPerSec: 12.5, status: 'success' },
  { stopCount: 10000, payloadSizeMB: 1004.8, solveTimeSeconds: 720, throughputStopsPerSec: 13.9, status: 'success' }, // Clustered
];

// Benchmark scenarios with real data - UK focused
export const benchmarkScenarios: BenchmarkScenario[] = [
  {
    id: 'ev_network',
    name: 'EV Network',
    description: 'EV charging stations across UK',
    stops: 15,
    vehicles: 5,
    expectedSolveTime: 15,
    payloadSizeMB: 0.12,
    category: 'field_service',
    centerLat: 54.5,
    centerLng: -2.0,
    radiusKm: 400,
  },
  {
    id: 'belron_london',
    name: 'Belron London',
    description: '50 windscreen jobs across Greater London (75% replacements, 25% repairs)',
    stops: 50,
    vehicles: 12,
    expectedSolveTime: 25,
    payloadSizeMB: 0.11,
    category: 'field_service',
    centerLat: 51.5074,
    centerLng: -0.1278,
    radiusKm: 40,
  },
  {
    id: 'london_central',
    name: 'London Central',
    description: '100 deliveries in Central London postcodes',
    stops: 100,
    vehicles: 10,
    expectedSolveTime: 30,
    payloadSizeMB: 0.43,
    category: 'field_service',
    centerLat: 51.5074,
    centerLng: -0.1278,
    radiusKm: 15,
  },
  {
    id: 'manchester_region',
    name: 'Manchester Region',
    description: '200 stops across Greater Manchester',
    stops: 200,
    vehicles: 20,
    expectedSolveTime: 60,
    payloadSizeMB: 1.73,
    category: 'field_service',
    centerLat: 53.4808,
    centerLng: -2.2426,
    radiusKm: 25,
  },
  {
    id: 'midlands_mixed',
    name: 'Midlands Mixed',
    description: '500 stops across Birmingham & Midlands',
    stops: 500,
    vehicles: 30,
    expectedSolveTime: 90,
    payloadSizeMB: 10.80,
    category: 'mixed_density',
    centerLat: 52.4862,
    centerLng: -1.8904,
    radiusKm: 60,
  },
  {
    id: 'scotland_wide',
    name: 'Scotland Wide',
    description: '300 stops across Scotland major cities',
    stops: 300,
    vehicles: 25,
    expectedSolveTime: 75,
    payloadSizeMB: 3.89,
    category: 'mixed_density',
    centerLat: 56.0,
    centerLng: -4.0,
    radiusKm: 150,
  },
  {
    id: 'uk_national',
    name: 'UK National',
    description: '1,000 stops nationwide UK delivery',
    stops: 1000,
    vehicles: 50,
    expectedSolveTime: 135,
    payloadSizeMB: 43.20,
    category: 'high_density_parcel',
    centerLat: 54.5,
    centerLng: -2.0,
    radiusKm: 400,
  },
  {
    id: 'uk_enterprise',
    name: 'UK Enterprise',
    description: '2,500 stops - full UK coverage',
    stops: 2500,
    vehicles: 100,
    expectedSolveTime: 180,
    payloadSizeMB: 270.00,
    category: 'high_density_parcel',
    centerLat: 54.5,
    centerLng: -2.0,
    radiusKm: 400,
  },
];

// UK Cities with postcodes and coordinates
export const ukCitiesData = [
  // London
  { city: 'London', postcode: 'EC1A', lat: 51.5074, lng: -0.1278, region: 'London' },
  { city: 'Westminster', postcode: 'SW1A', lat: 51.4995, lng: -0.1248, region: 'London' },
  { city: 'Camden', postcode: 'NW1', lat: 51.5390, lng: -0.1426, region: 'London' },
  { city: 'Greenwich', postcode: 'SE10', lat: 51.4826, lng: -0.0077, region: 'London' },
  { city: 'Stratford', postcode: 'E15', lat: 51.5430, lng: -0.0005, region: 'London' },
  { city: 'Heathrow', postcode: 'TW6', lat: 51.4700, lng: -0.4543, region: 'London' },

  // Major Cities
  { city: 'Manchester', postcode: 'M1', lat: 53.4808, lng: -2.2426, region: 'North West' },
  { city: 'Birmingham', postcode: 'B1', lat: 52.4862, lng: -1.8904, region: 'Midlands' },
  { city: 'Leeds', postcode: 'LS1', lat: 53.8008, lng: -1.5491, region: 'Yorkshire' },
  { city: 'Liverpool', postcode: 'L1', lat: 53.4084, lng: -2.9916, region: 'North West' },
  { city: 'Bristol', postcode: 'BS1', lat: 51.4545, lng: -2.5879, region: 'South West' },
  { city: 'Sheffield', postcode: 'S1', lat: 53.3811, lng: -1.4701, region: 'Yorkshire' },
  { city: 'Newcastle', postcode: 'NE1', lat: 54.9783, lng: -1.6178, region: 'North East' },
  { city: 'Nottingham', postcode: 'NG1', lat: 52.9548, lng: -1.1581, region: 'Midlands' },

  // Scotland
  { city: 'Edinburgh', postcode: 'EH1', lat: 55.9533, lng: -3.1883, region: 'Scotland' },
  { city: 'Glasgow', postcode: 'G1', lat: 55.8642, lng: -4.2518, region: 'Scotland' },
  { city: 'Aberdeen', postcode: 'AB10', lat: 57.1497, lng: -2.0943, region: 'Scotland' },
  { city: 'Dundee', postcode: 'DD1', lat: 56.4620, lng: -2.9707, region: 'Scotland' },
  { city: 'Inverness', postcode: 'IV1', lat: 57.4778, lng: -4.2247, region: 'Scotland' },

  // Wales
  { city: 'Cardiff', postcode: 'CF10', lat: 51.4816, lng: -3.1791, region: 'Wales' },
  { city: 'Swansea', postcode: 'SA1', lat: 51.6214, lng: -3.9436, region: 'Wales' },

  // Northern Ireland
  { city: 'Belfast', postcode: 'BT1', lat: 54.5973, lng: -5.9301, region: 'Northern Ireland' },

  // Other Major Towns
  { city: 'Southampton', postcode: 'SO14', lat: 50.9097, lng: -1.4044, region: 'South' },
  { city: 'Portsmouth', postcode: 'PO1', lat: 50.8198, lng: -1.0880, region: 'South' },
  { city: 'Brighton', postcode: 'BN1', lat: 50.8225, lng: -0.1372, region: 'South' },
  { city: 'Plymouth', postcode: 'PL1', lat: 50.3755, lng: -4.1427, region: 'South West' },
  { city: 'Leicester', postcode: 'LE1', lat: 52.6369, lng: -1.1398, region: 'Midlands' },
  { city: 'Coventry', postcode: 'CV1', lat: 52.4068, lng: -1.5197, region: 'Midlands' },
  { city: 'Bradford', postcode: 'BD1', lat: 53.7960, lng: -1.7594, region: 'Yorkshire' },
  { city: 'Hull', postcode: 'HU1', lat: 53.7676, lng: -0.3274, region: 'Yorkshire' },
  { city: 'Stoke-on-Trent', postcode: 'ST1', lat: 53.0027, lng: -2.1794, region: 'Midlands' },
  { city: 'Derby', postcode: 'DE1', lat: 52.9225, lng: -1.4746, region: 'Midlands' },
  { city: 'Reading', postcode: 'RG1', lat: 51.4543, lng: -0.9781, region: 'South' },
  { city: 'Oxford', postcode: 'OX1', lat: 51.7520, lng: -1.2577, region: 'South' },
  { city: 'Cambridge', postcode: 'CB1', lat: 52.2053, lng: 0.1218, region: 'East' },
  { city: 'Norwich', postcode: 'NR1', lat: 52.6309, lng: 1.2974, region: 'East' },
  { city: 'Milton Keynes', postcode: 'MK9', lat: 52.0406, lng: -0.7594, region: 'South East' },
  { city: 'Luton', postcode: 'LU1', lat: 51.8787, lng: -0.4200, region: 'South East' },
  { city: 'York', postcode: 'YO1', lat: 53.9600, lng: -1.0873, region: 'Yorkshire' },
  { city: 'Exeter', postcode: 'EX1', lat: 50.7184, lng: -3.5339, region: 'South West' },
  { city: 'Bath', postcode: 'BA1', lat: 51.3758, lng: -2.3599, region: 'South West' },
];

// Sample stops for UK with postcodes
export const sampleStopsUK = [
  { id: 1, lat: 51.5074, lng: -0.1278, demand: 5, label: 'London EC1A', postcode: 'EC1A 1BB' },
  { id: 2, lat: 53.4808, lng: -2.2426, demand: 3, label: 'Manchester M1', postcode: 'M1 1AD' },
  { id: 3, lat: 52.4862, lng: -1.8904, demand: 4, label: 'Birmingham B1', postcode: 'B1 1AA' },
  { id: 4, lat: 53.8008, lng: -1.5491, demand: 6, label: 'Leeds LS1', postcode: 'LS1 1AA' },
  { id: 5, lat: 55.9533, lng: -3.1883, demand: 2, label: 'Edinburgh EH1', postcode: 'EH1 1AA' },
  { id: 6, lat: 55.8642, lng: -4.2518, demand: 5, label: 'Glasgow G1', postcode: 'G1 1AA' },
  { id: 7, lat: 51.4545, lng: -2.5879, demand: 3, label: 'Bristol BS1', postcode: 'BS1 1AA' },
  { id: 8, lat: 53.4084, lng: -2.9916, demand: 4, label: 'Liverpool L1', postcode: 'L1 1AA' },
  { id: 9, lat: 54.9783, lng: -1.6178, demand: 7, label: 'Newcastle NE1', postcode: 'NE1 1AA' },
  { id: 10, lat: 51.4816, lng: -3.1791, demand: 2, label: 'Cardiff CF10', postcode: 'CF10 1AA' },
];

// Note: generateUKPostcode is now imported from ukPostcodes.ts

// Generate random stops within a specific region
// Global land zones for coastal cities (multiple zones to avoid water bodies)
// Structure: city_id -> array of land zone bounding boxes

// New York land zones
const NEW_YORK_LAND_ZONES = [
  // Manhattan
  { minLat: 40.70, maxLat: 40.88, minLng: -74.02, maxLng: -73.93 },
  // Brooklyn (north/central - avoid Jamaica Bay)
  { minLat: 40.63, maxLat: 40.74, minLng: -74.03, maxLng: -73.86 },
  // Queens (avoid Jamaica Bay)
  { minLat: 40.72, maxLat: 40.82, minLng: -73.96, maxLng: -73.70 },
  // Bronx
  { minLat: 40.79, maxLat: 40.92, minLng: -73.93, maxLng: -73.75 },
  // New Jersey (Newark, Jersey City area)
  { minLat: 40.65, maxLat: 40.80, minLng: -74.25, maxLng: -74.03 },
  // Staten Island (only the main land mass)
  { minLat: 40.56, maxLat: 40.65, minLng: -74.22, maxLng: -74.05 },
  // Westchester/Yonkers
  { minLat: 40.88, maxLat: 41.05, minLng: -73.95, maxLng: -73.75 },
];

// Mumbai land zones (Arabian Sea is to the WEST, so we need eastern land areas)
// IMPORTANT: Keep zones compact to avoid routes spreading too far
const MUMBAI_LAND_ZONES = [
  // South Mumbai (Colaba, Fort, Marine Drive, Churchgate) - avoid coast
  { minLat: 18.92, maxLat: 18.98, minLng: 72.825, maxLng: 72.845 },
  // Lower Parel, Dadar, Mahim - central business
  { minLat: 18.98, maxLat: 19.03, minLng: 72.835, maxLng: 72.855 },
  // Bandra, Khar, Santacruz - western suburbs
  { minLat: 19.03, maxLat: 19.08, minLng: 72.835, maxLng: 72.855 },
  // Andheri, Jogeshwari - major hub
  { minLat: 19.08, maxLat: 19.14, minLng: 72.84, maxLng: 72.875 },
  // Kurla, Ghatkopar, Chembur - eastern suburbs (away from creek)
  { minLat: 19.03, maxLat: 19.10, minLng: 72.875, maxLng: 72.92 },
  // Powai, Vikhroli - tech hub area
  { minLat: 19.10, maxLat: 19.14, minLng: 72.89, maxLng: 72.93 },
  // Mulund - northern limit (don't go beyond to avoid Thane Creek)
  { minLat: 19.14, maxLat: 19.18, minLng: 72.94, maxLng: 72.97 },
];

// Chennai land zones (Bay of Bengal is to the EAST, so we need western land areas)
const CHENNAI_LAND_ZONES = [
  // Central Chennai (Marina to T.Nagar)
  { minLat: 13.00, maxLat: 13.10, minLng: 80.22, maxLng: 80.28 },
  // North Chennai
  { minLat: 13.08, maxLat: 13.20, minLng: 80.18, maxLng: 80.28 },
  // West Chennai (Anna Nagar, Vadapalani)
  { minLat: 13.02, maxLat: 13.12, minLng: 80.18, maxLng: 80.24 },
  // South Chennai (Adyar, Velachery)
  { minLat: 12.92, maxLat: 13.02, minLng: 80.20, maxLng: 80.26 },
  // Tambaram-Chromepet
  { minLat: 12.85, maxLat: 12.95, minLng: 80.10, maxLng: 80.18 },
];

// Sydney land zones (Pacific Ocean is to the EAST)
const SYDNEY_LAND_ZONES = [
  // CBD & Inner West
  { minLat: -33.92, maxLat: -33.85, minLng: 151.15, maxLng: 151.22 },
  // Western Sydney (Parramatta area)
  { minLat: -33.88, maxLat: -33.78, minLng: 150.95, maxLng: 151.10 },
  // South Sydney (Bankstown, Hurstville)
  { minLat: -34.00, maxLat: -33.90, minLng: 151.00, maxLng: 151.15 },
  // Northern Suburbs
  { minLat: -33.82, maxLat: -33.70, minLng: 151.12, maxLng: 151.25 },
  // Hills District
  { minLat: -33.75, maxLat: -33.65, minLng: 150.95, maxLng: 151.10 },
];

// Miami land zones (Atlantic Ocean is to the EAST, Everglades to WEST)
const MIAMI_LAND_ZONES = [
  // Miami Beach (narrow strip)
  { minLat: 25.76, maxLat: 25.88, minLng: -80.14, maxLng: -80.12 },
  // Downtown Miami
  { minLat: 25.75, maxLat: 25.82, minLng: -80.22, maxLng: -80.18 },
  // Coral Gables, Coconut Grove
  { minLat: 25.68, maxLat: 25.76, minLng: -80.28, maxLng: -80.22 },
  // North Miami, Hialeah
  { minLat: 25.82, maxLat: 25.95, minLng: -80.28, maxLng: -80.18 },
  // Kendall, South Miami
  { minLat: 25.65, maxLat: 25.72, minLng: -80.38, maxLng: -80.28 },
];

// San Francisco land zones (Pacific Ocean is to the WEST)
const SAN_FRANCISCO_LAND_ZONES = [
  // SF Peninsula
  { minLat: 37.70, maxLat: 37.82, minLng: -122.48, maxLng: -122.38 },
  // Oakland, Berkeley
  { minLat: 37.78, maxLat: 37.90, minLng: -122.30, maxLng: -122.18 },
  // South Bay (San Jose)
  { minLat: 37.28, maxLat: 37.45, minLng: -122.05, maxLng: -121.85 },
  // Peninsula (Palo Alto, Menlo Park)
  { minLat: 37.40, maxLat: 37.55, minLng: -122.20, maxLng: -122.05 },
  // Fremont, Newark
  { minLat: 37.48, maxLat: 37.58, minLng: -122.08, maxLng: -121.92 },
];

// Los Angeles land zones (Pacific Ocean is to the WEST)
const LOS_ANGELES_LAND_ZONES = [
  // Downtown LA
  { minLat: 33.98, maxLat: 34.08, minLng: -118.30, maxLng: -118.18 },
  // Hollywood, West Hollywood
  { minLat: 34.08, maxLat: 34.15, minLng: -118.40, maxLng: -118.28 },
  // Pasadena, Glendale
  { minLat: 34.12, maxLat: 34.22, minLng: -118.20, maxLng: -118.05 },
  // Long Beach (inland part)
  { minLat: 33.78, maxLat: 33.88, minLng: -118.22, maxLng: -118.12 },
  // San Fernando Valley
  { minLat: 34.15, maxLat: 34.28, minLng: -118.55, maxLng: -118.35 },
  // Inland Empire
  { minLat: 33.90, maxLat: 34.05, minLng: -117.95, maxLng: -117.75 },
];

// Global registry of all land zones
const GLOBAL_LAND_ZONES: Record<string, Array<{ minLat: number; maxLat: number; minLng: number; maxLng: number }>> = {
  'new_york': NEW_YORK_LAND_ZONES,
  'mumbai': MUMBAI_LAND_ZONES,
  'chennai': CHENNAI_LAND_ZONES,
  'sydney': SYDNEY_LAND_ZONES,
  'miami': MIAMI_LAND_ZONES,
  'san_francisco': SAN_FRANCISCO_LAND_ZONES,
  'los_angeles': LOS_ANGELES_LAND_ZONES,
};

// Land boundary boxes for coastal cities to avoid generating stops in water
// Format: { minLat, maxLat, minLng, maxLng } for valid land areas
const COASTAL_CITY_BOUNDS: Record<string, { minLat: number; maxLat: number; minLng: number; maxLng: number; biasLng?: 'west' | 'east'; biasLat?: 'north' | 'south' }> = {
  // New York: Use special multi-zone handling (this is fallback)
  'new_york': { minLat: 40.56, maxLat: 41.05, minLng: -74.25, maxLng: -73.70, biasLng: 'west' },
  // Los Angeles: Bias eastward to avoid Pacific
  'los_angeles': { minLat: 33.70, maxLat: 34.35, minLng: -118.70, maxLng: -117.70, biasLng: 'east' },
  // San Francisco: Bias eastward
  'san_francisco': { minLat: 37.35, maxLat: 38.00, minLng: -122.55, maxLng: -121.80, biasLng: 'east' },
  // Miami: Bias westward and northward
  'miami': { minLat: 25.60, maxLat: 26.30, minLng: -80.50, maxLng: -80.05, biasLng: 'west', biasLat: 'north' },
  // Seattle: Bias eastward
  'seattle': { minLat: 47.35, maxLat: 47.85, minLng: -122.50, maxLng: -121.90, biasLng: 'east' },
  // Sydney: Bias westward
  'sydney': { minLat: -34.15, maxLat: -33.55, minLng: 150.60, maxLng: 151.35, biasLng: 'west' },
  // Mumbai: Tighter bounds to keep stops in urban core (avoid Thane Creek, Navi Mumbai)
  'mumbai': { minLat: 18.92, maxLat: 19.18, minLng: 72.82, maxLng: 72.97, biasLng: 'east' },
  // Chennai: Bias westward
  'chennai': { minLat: 12.85, maxLat: 13.30, minLng: 80.05, maxLng: 80.35, biasLng: 'west' },
  // London: No major water issues but has Thames
  'london': { minLat: 51.28, maxLat: 51.70, minLng: -0.55, maxLng: 0.30 },
};

// Check if a point might be in water (simple heuristic for coastal areas)
function isLikelyOnLand(lat: number, lng: number, cityId?: string): boolean {
  if (!cityId) return true;

  // Check if this city has specific land zones defined
  const landZones = GLOBAL_LAND_ZONES[cityId];
  if (landZones) {
    // Point must be within at least one of the land zones
    return landZones.some(zone =>
      lat >= zone.minLat && lat <= zone.maxLat &&
      lng >= zone.minLng && lng <= zone.maxLng
    );
  }

  // Fallback to simple bounds check for cities without detailed land zones
  const bounds = COASTAL_CITY_BOUNDS[cityId];
  if (!bounds) return true;

  // Check if within city bounds
  return lat >= bounds.minLat && lat <= bounds.maxLat &&
         lng >= bounds.minLng && lng <= bounds.maxLng;
}

// Generate a random point biased toward land for coastal cities
function generateBiasedPoint(
  centerLat: number,
  centerLng: number,
  radiusDeg: number,
  cityId?: string
): { lat: number; lng: number } {
  // Check if this city has specific land zones defined (priority over simple bounds)
  const landZones = cityId ? GLOBAL_LAND_ZONES[cityId] : null;
  if (landZones && landZones.length > 0) {
    // Pick a random land zone (weighted by area for more even distribution)
    const zone = landZones[Math.floor(Math.random() * landZones.length)];
    // Generate point within that zone
    const lat = zone.minLat + Math.random() * (zone.maxLat - zone.minLat);
    const lng = zone.minLng + Math.random() * (zone.maxLng - zone.minLng);
    return { lat, lng };
  }

  const bounds = cityId ? COASTAL_CITY_BOUNDS[cityId] : null;

  // If we have bounds for this city, generate within bounds
  if (bounds) {
    const latRange = bounds.maxLat - bounds.minLat;
    const lngRange = bounds.maxLng - bounds.minLng;

    // Generate point within bounds, biased away from water if specified
    let lat = bounds.minLat + Math.random() * latRange;
    let lng = bounds.minLng + Math.random() * lngRange;

    // Apply bias toward land
    if (bounds.biasLng === 'west') {
      // Bias toward lower longitude (west)
      lng = bounds.minLng + Math.pow(Math.random(), 1.5) * lngRange;
    } else if (bounds.biasLng === 'east') {
      // Bias toward higher longitude (east)
      lng = bounds.maxLng - Math.pow(Math.random(), 1.5) * lngRange;
    }

    if (bounds.biasLat === 'north') {
      lat = bounds.maxLat - Math.pow(Math.random(), 1.5) * latRange;
    } else if (bounds.biasLat === 'south') {
      lat = bounds.minLat + Math.pow(Math.random(), 1.5) * latRange;
    }

    return { lat, lng };
  }

  // Default: generate in circle but bias toward land side for coastal areas
  const angle = Math.random() * 2 * Math.PI;
  const distance = Math.sqrt(Math.random()) * radiusDeg;

  return {
    lat: centerLat + distance * Math.cos(angle),
    lng: centerLng + distance * Math.sin(angle) / Math.cos(centerLat * Math.PI / 180)
  };
}

// Detect city ID from center coordinates
function detectCityFromCoords(centerLat: number, centerLng: number): string | undefined {
  // Check each coastal city to see if the center is near it
  for (const [cityId, bounds] of Object.entries(COASTAL_CITY_BOUNDS)) {
    const cityLat = (bounds.minLat + bounds.maxLat) / 2;
    const cityLng = (bounds.minLng + bounds.maxLng) / 2;
    const latDiff = Math.abs(centerLat - cityLat);
    const lngDiff = Math.abs(centerLng - cityLng);

    if (latDiff < 0.5 && lngDiff < 0.5) {
      return cityId;
    }
  }
  return undefined;
}

export function generateRandomStops(
  count: number,
  centerLat: number = 54.5, // Center of UK
  centerLng: number = -2.0,
  radiusKm: number = 400 // Cover most of UK
): { id: number; lat: number; lng: number; demand: number; label: string; postcode?: string }[] {
  const stops = [];

  // Convert radius to degrees (approx 111km per degree)
  const radiusDeg = radiusKm / 111;

  // Detect if this is a known coastal city
  const detectedCity = detectCityFromCoords(centerLat, centerLng);

  // Filter postcode areas within the specified radius
  const areasInRegion = ukPostcodeAreas.filter((area) => {
    const latDiff = area.lat - centerLat;
    const lngDiff = area.lng - centerLng;
    const distance = Math.sqrt(latDiff * latDiff + lngDiff * lngDiff);
    return distance <= radiusDeg;
  });

  // Also filter legacy cities for backward compatibility
  const citiesInRegion = ukCitiesData.filter((city) => {
    const latDiff = city.lat - centerLat;
    const lngDiff = city.lng - centerLng;
    const distance = Math.sqrt(latDiff * latDiff + lngDiff * lngDiff);
    return distance <= radiusDeg;
  });

  // Use postcode areas if available, otherwise fall back to cities
  const locationsToUse = areasInRegion.length > 0 ? areasInRegion : citiesInRegion;

  // If we have locations in region and count is manageable
  if (locationsToUse.length > 0) {
    for (let i = 0; i < count; i++) {
      // Pick a location from the region (cycle through if needed)
      const loc = locationsToUse[i % locationsToUse.length];

      // Add variation around the location center
      const localRadius = Math.min(radiusDeg * 0.3, 0.08); // Max ~8km variation
      const angle = Math.random() * 2 * Math.PI;
      const distance = Math.random() * localRadius;

      const lat = loc.lat + distance * Math.cos(angle);
      const lng = loc.lng + distance * Math.sin(angle);

      // Get proper postcode from nearest area
      const nearestArea = getNearestPostcodeArea(lat, lng);

      stops.push({
        id: i + 1,
        lat,
        lng,
        demand: Math.floor(Math.random() * 10) + 1,
        label: `${nearestArea.name} Stop ${i + 1}`,
        postcode: generateUKPostcode(nearestArea.code),
      });
    }
    return stops;
  }

  // Fallback: generate random points within radius (land-aware for coastal cities)
  for (let i = 0; i < count; i++) {
    // Use biased generation for coastal cities
    const point = generateBiasedPoint(centerLat, centerLng, radiusDeg, detectedCity);

    // Retry if point is likely in water (max 5 attempts)
    let attempts = 0;
    while (!isLikelyOnLand(point.lat, point.lng, detectedCity) && attempts < 5) {
      const newPoint = generateBiasedPoint(centerLat, centerLng, radiusDeg, detectedCity);
      point.lat = newPoint.lat;
      point.lng = newPoint.lng;
      attempts++;
    }

    stops.push({
      id: i + 1,
      lat: point.lat,
      lng: point.lng,
      demand: Math.floor(Math.random() * 10) + 1,
      label: `Stop ${i + 1}`,
    });
  }

  return stops;
}

// Parallel execution baseline data
export const parallelExecutionData = [
  { parallelJobs: 1, throughputJobsPerHour: 60, avgSolveTimeSeconds: 60 },
  { parallelJobs: 2, throughputJobsPerHour: 100, avgSolveTimeSeconds: 72 },
  { parallelJobs: 4, throughputJobsPerHour: 180, avgSolveTimeSeconds: 80 },
  { parallelJobs: 8, throughputJobsPerHour: 320, avgSolveTimeSeconds: 90 },
];

// Cluster performance data (10,000 stops)
export const clusterPerformanceData = [
  { clusterId: 0, stops: 2562, payloadMB: 237.58, solveTimeSeconds: 109.1 },
  { clusterId: 1, stops: 2652, payloadMB: 254.56, solveTimeSeconds: 127.0 },
  { clusterId: 2, stops: 2641, payloadMB: 252.54, solveTimeSeconds: 110.5 },
  { clusterId: 3, stops: 2681, payloadMB: 260.10, solveTimeSeconds: 111.3 },
];

// Example prompts for chat interface - UK focused
export const examplePrompts = [
  // Basic Route Optimization
  "Optimize 50 deliveries across London with 5 vehicles available 8am-6pm",
  "Plan routes for 200 stops in Manchester area with 20 vans",
  "I have 500 parcels to deliver across the Midlands, minimize fuel costs",
  "Schedule 100 engineer visits in Scotland with priority levels",
  "What's the best route for 1000 UK-wide deliveries?",
  "Plan delivery routes from Birmingham depot to cover Yorkshire postcodes",
];

// Comprehensive AI Assistant Test Prompts
export const aiTestPrompts = {
  // Category 1: EV Network - Charging Station Routes
  evNetwork: [
    "Plan maintenance routes for 15 EV charging stations with 5 service vehicles",
    "Optimize technician visits to all EV chargers, prioritizing rapid chargers first",
    "Schedule emergency repair routes for 10 faulty EV charging points across the UK",
    "Create efficient routes to inspect BP Pulse and Pod Point stations in South East England",
    "Route 3 maintenance vans to service Ultra-rapid chargers before Fast chargers",
  ],

  // Category 2: London Central - High Density Urban
  londonCentral: [
    "Deliver 100 packages across Central London postcodes EC1, WC1, SW1 with 10 electric vans",
    "Optimize same-day delivery routes for 80 parcels in Westminster and Camden areas",
    "Plan rush hour delivery avoiding congestion zones, 50 stops in Greater London",
    "Schedule 120 deliveries in London with time windows between 9am-5pm",
    "Route optimization for 75 business deliveries in the City of London financial district",
  ],

  // Category 3: Manchester Region - Regional Coverage
  manchesterRegion: [
    "Plan routes for 200 deliveries across Greater Manchester with 20 vehicles",
    "Optimize parcel delivery from Manchester depot covering Salford, Stockport, and Bolton",
    "Schedule 150 engineer visits across North West England, minimize total travel time",
    "Route planning for 180 stops in Manchester, Liverpool, and surrounding areas",
    "Create efficient delivery routes for 250 packages across Lancashire postcodes",
  ],

  // Category 4: Midlands Mixed - Mixed Urban/Rural
  midlandsMixed: [
    "Optimize 500 deliveries across Birmingham and the Midlands region with 30 vans",
    "Plan mixed density routes covering Nottingham, Leicester, and Derby",
    "Schedule field service visits to 400 locations across the West Midlands",
    "Route optimization for 350 parcels spanning urban Birmingham and rural Shropshire",
    "Create delivery routes from Coventry depot to cover Warwickshire and Worcestershire",
  ],

  // Category 5: Scotland Wide - Long Distance
  scotlandWide: [
    "Plan routes for 300 deliveries across Scotland from Edinburgh depot",
    "Optimize delivery network covering Glasgow, Aberdeen, Dundee, and Inverness",
    "Schedule 250 service calls across Scottish Highlands with 25 vehicles",
    "Route planning for nationwide Scotland coverage, minimize total distance",
    "Create efficient routes for 200 parcels spanning Edinburgh to Inverness",
  ],

  // Category 6: UK National - Enterprise Scale
  ukNational: [
    "Optimize 1000 nationwide UK deliveries with 50 vehicles from multiple depots",
    "Plan enterprise-scale routing for 2000 stops across England, Scotland, and Wales",
    "Schedule UK-wide field service with 100 engineers, prioritize urgent calls",
    "Create national delivery network covering all major UK cities",
    "Route optimization for 1500 parcels with regional clustering",
  ],

  // Category 7: Parallel Processing Tests
  parallelProcessing: [
    "Run parallel optimization for 800 stops using 4 clusters",
    "Optimize 1200 deliveries using parallel processing with 6 job clusters",
    "Large scale route planning: 2000 stops across UK, use parallel execution",
    "Process 500 stops per cluster for 4 regions simultaneously",
    "Enterprise routing with parallel clusters: London, Manchester, Birmingham, Edinburgh",
  ],

  // Category 8: Constraint-Based Scenarios
  constraints: [
    "Deliver 100 packages with vehicle capacity of 50 units each, 3 vehicles available",
    "Route 80 deliveries with strict time windows: morning (8-12) and afternoon (14-18)",
    "Plan routes with maximum 20 stops per vehicle, total 150 deliveries",
    "Optimize with priority levels: 30 urgent, 50 standard, 20 low priority deliveries",
    "Schedule deliveries avoiding school zones during 8-9am and 3-4pm",
  ],

  // Category 9: Objective-Specific
  objectives: [
    "Minimize total distance for 100 deliveries across Yorkshire",
    "Reduce number of vehicles needed for 200 Manchester deliveries",
    "Optimize for fastest completion time: 150 urgent London deliveries",
    "Balance workload evenly across 10 vehicles for 180 stops",
    "Minimize fuel consumption for 300 deliveries with diesel vans",
  ],

  // Category 10: Real-World Scenarios
  realWorld: [
    "Black Friday sale: handle 500 extra deliveries in London with existing 20 vehicle fleet",
    "Storm damage response: route 50 emergency repair crews across flooded areas in Yorkshire",
    "Christmas peak: optimize 2500 parcels UK-wide with temporary additional vehicles",
    "New depot opening in Bristol: plan optimal routes for 200 deliveries in South West",
    "Vehicle breakdown: re-route remaining 80 deliveries among 4 available vans",
  ],

  // Category 11: Weather-Aware Routing
  weatherAware: [
    "Plan 50 deliveries in London considering current weather conditions and safety",
    "Optimize routes for 100 stops in Manchester with weather impact assessment",
    "Route 30 EV charging station visits with weather-adjusted travel times",
    "Schedule 80 deliveries across Scotland checking for adverse weather conditions",
    "Plan safe routes for 60 stops in Yorkshire considering rain and wind forecasts",
    "Optimize 40 field service visits in Birmingham with weather safety scoring",
    "Route 120 parcels in North West England with storm warning consideration",
    "Plan weather-safe routes for 25 technician visits across Wales",
  ],
};
