// OpenSky Network API Types
// Based on: https://openskynetwork.github.io/opensky-api/rest.html

/**
 * State vector representing a single aircraft's state at a given time
 * Array format: [icao24, callsign, origin_country, time_position, last_contact,
 *                longitude, latitude, baro_altitude, on_ground, velocity,
 *                true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
 */
export type StateVectorArray = [
  string,      // 0: icao24 - Unique ICAO 24-bit address (hex string)
  string,      // 1: callsign - Flight callsign (8 chars, padded)
  string,      // 2: origin_country - Country name
  number,      // 3: time_position - Unix timestamp of position update
  number,      // 4: last_contact - Unix timestamp of last update
  number,      // 5: longitude - WGS-84 longitude in degrees
  number,      // 6: latitude - WGS-84 latitude in degrees
  number | null, // 7: baro_altitude - Barometric altitude in meters
  boolean,     // 8: on_ground - True if aircraft is on ground
  number,      // 9: velocity - Ground speed in m/s
  number,      // 10: true_track - Track angle in degrees (0=north, clockwise)
  number | null, // 11: vertical_rate - Vertical rate in m/s (positive = climbing)
  number[] | null, // 12: sensors - Sensor serial numbers
  number | null, // 13: geo_altitude - Geometric altitude in meters
  string,      // 14: squawk - Transponder code (4 digits)
  boolean,     // 15: spi - Special position indicator
  number       // 16: position_source - 0=ADS-B, 1=ASTERIX, 2=MLAT
];

/**
 * Parsed state vector with named properties (easier to use)
 */
export interface StateVector {
  icao24: string;
  callsign: string;
  origin_country: string;
  time_position: number;
  last_contact: number;
  longitude: number;
  latitude: number;
  baro_altitude: number | null;
  on_ground: boolean;
  velocity: number;
  true_track: number;
  vertical_rate: number | null;
  sensors: number[] | null;
  geo_altitude: number | null;
  squawk: string;
  spi: boolean;
  position_source: number;
}

/**
 * Response from /states/all endpoint
 */
export interface StatesResponse {
  time: number;           // Unix timestamp of the response
  states: StateVectorArray[] | null; // Array of state vectors, null if no data
  dataSource?: 'api' | 'fallback';
  fallbackReason?: string;
  fallbackActive?: boolean;
}

export interface ParsedStatesResponse {
  states: StateVector[];
  dataSource: 'api' | 'fallback';
  fallbackReason?: string;
  fallbackActive: boolean;
  time: number;
}

/**
 * Flight information from /flights endpoints
 */
export interface Flight {
  icao24: string;           // Unique ICAO 24-bit address
  firstSeen: number;        // Unix timestamp of first position
  estDepartureAirport: string | null; // ICAO code of departure airport
  lastSeen: number;         // Unix timestamp of last position
  estArrivalAirport: string | null;   // ICAO code of arrival airport
  callsign: string;         // Flight callsign
  estDepartureAirportHorizDistance: number | null;
  estDepartureAirportVertDistance: number | null;
  estArrivalAirportHorizDistance: number | null;
  estArrivalAirportVertDistance: number | null;
  departureAirportCandidatesCount: number | null;
  arrivalAirportCandidatesCount: number | null;
}

/**
 * Bounding box for geographic queries
 */
export interface BoundingBox {
  lamin: number;  // Lower latitude bound
  lomin: number;  // Lower longitude bound
  lamax: number;  // Upper latitude bound
  lomax: number;  // Upper longitude bound
}

/**
 * Health check response
 */
export interface OpenSkyHealthResponse {
  status: 'connected' | 'disconnected' | 'unavailable';
  endpoint: string;
  aircraftCount?: number;
  authenticated?: boolean;
  error?: string;
}

/**
 * Helper function to parse state vector array into object
 */
export function parseStateVector(sv: StateVectorArray): StateVector {
  return {
    icao24: sv[0],
    callsign: sv[1].trim(),
    origin_country: sv[2],
    time_position: sv[3],
    last_contact: sv[4],
    longitude: sv[5],
    latitude: sv[6],
    baro_altitude: sv[7],
    on_ground: sv[8],
    velocity: sv[9],
    true_track: sv[10],
    vertical_rate: sv[11],
    sensors: sv[12],
    geo_altitude: sv[13],
    squawk: sv[14],
    spi: sv[15],
    position_source: sv[16],
  };
}

/**
 * Aircraft categories for UI filtering
 */
export enum AircraftCategory {
  ALL = 'all',
  COMMERCIAL = 'commercial',
  CARGO = 'cargo',
  PRIVATE = 'private',
  MILITARY = 'military',
}

/**
 * Altitude ranges for filtering
 */
export interface AltitudeRange {
  min: number; // meters
  max: number; // meters
  label: string;
  color: string;
}

export const ALTITUDE_RANGES: AltitudeRange[] = [
  { min: 0, max: 1000, label: 'Ground - 1km', color: '#22c55e' },
  { min: 1000, max: 5000, label: '1km - 5km', color: '#3b82f6' },
  { min: 5000, max: 10000, label: '5km - 10km', color: '#f59e0b' },
  { min: 10000, max: 15000, label: '10km - 15km', color: '#ef4444' },
  { min: 15000, max: 50000, label: 'Above 15km', color: '#8b5cf6' },
];

/**
 * Query parameters for natural language processing
 */
export interface AirTrafficQuery {
  intent: 'live_traffic_region' | 'airport_departures' | 'airport_arrivals' |
          'track_flight' | 'airline_filter' | 'altitude_filter' | 'traffic_density';
  region?: string;
  bbox?: BoundingBox;
  airport?: string;
  callsign?: string;
  airline?: string;
  country?: string;
  altitude_min?: number;
  altitude_max?: number;
  time_range_hours?: number;
}
