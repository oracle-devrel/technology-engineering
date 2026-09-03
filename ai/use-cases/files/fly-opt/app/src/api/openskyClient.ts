import axios, { AxiosInstance } from 'axios';
import type {
  StatesResponse,
  ParsedStatesResponse,
  Flight,
  BoundingBox,
  OpenSkyHealthResponse,
  StateVector,
} from '@/types/opensky';
import { parseStateVector } from '@/types/opensky';

class OpenSkyClient {
  private client: AxiosInstance;
  private cacheTimeout = 10000; // 10 seconds cache
  private cache: Map<string, { data: any; timestamp: number }> = new Map();

  constructor() {
    this.client = axios.create({
      baseURL: '/api/opensky',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Health check for OpenSky API
   */
  async healthCheck(): Promise<OpenSkyHealthResponse> {
    try {
      const response = await this.client.get<OpenSkyHealthResponse>('/health');
      return response.data;
    } catch (error) {
      return {
        status: 'disconnected',
        endpoint: '',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get all aircraft states, optionally filtered by bounding box
   */
  async getStates(bbox?: BoundingBox): Promise<StatesResponse> {
    const cacheKey = bbox
      ? `states-${bbox.lamin}-${bbox.lomin}-${bbox.lamax}-${bbox.lomax}`
      : 'states-all';

    // Check cache
    const cached = this.getFromCache(cacheKey);
    if (cached) {
      console.log('[OpenSky] Returning cached data for:', cacheKey);
      return cached;
    }

    try {
      const params = bbox ? {
        lamin: bbox.lamin,
        lomin: bbox.lomin,
        lamax: bbox.lamax,
        lomax: bbox.lomax,
      } : {};

      const response = await this.client.get<StatesResponse>('/states/all', { params });

      // Cache the response
      this.setCache(cacheKey, response.data);

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError = error.response?.data?.error;
        const apiMessage = error.response?.data?.message;
        throw new Error(`OpenSky API Error: ${apiError || apiMessage || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Get parsed state vectors (easier to use than raw arrays)
   */
  async getParsedStates(bbox?: BoundingBox): Promise<ParsedStatesResponse> {
    const response = await this.getStates(bbox);

    if (!response.states || response.states.length === 0) {
      return {
        states: [],
        dataSource: response.dataSource || 'api',
        fallbackReason: response.fallbackReason,
        fallbackActive: response.fallbackActive || response.dataSource === 'fallback',
        time: response.time,
      };
    }

    return {
      states: response.states.map(parseStateVector),
      dataSource: response.dataSource || 'api',
      fallbackReason: response.fallbackReason,
      fallbackActive: response.fallbackActive || response.dataSource === 'fallback',
      time: response.time,
    };
  }

  /**
   * Get flights for a time interval
   */
  async getFlights(begin: number, end: number): Promise<Flight[]> {
    const cacheKey = `flights-${begin}-${end}`;

    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await this.client.get<Flight[]>('/flights/all', {
        params: { begin, end },
      });

      this.setCache(cacheKey, response.data);
      return response.data || [];
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError = error.response?.data?.error;
        const apiMessage = error.response?.data?.message;
        throw new Error(`OpenSky Flights Error: ${apiError || apiMessage || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Get flights for a specific airport
   */
  async getAirportFlights(
    airport: string,
    begin: number,
    end: number,
    type: 'departure' | 'arrival'
  ): Promise<Flight[]> {
    const cacheKey = `airport-${airport}-${type}-${begin}-${end}`;

    const cached = this.getFromCache(cacheKey);
    if (cached) {
      return cached;
    }

    try {
      const response = await this.client.get<Flight[]>('/flights/airport', {
        params: { airport, begin, end, type },
      });

      this.setCache(cacheKey, response.data);
      return response.data || [];
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const apiError = error.response?.data?.error;
        const apiMessage = error.response?.data?.message;
        throw new Error(`OpenSky Airport Flights Error: ${apiError || apiMessage || error.message}`);
      }
      throw error;
    }
  }

  /**
   * Get bounding box for a city/region
   */
  getBoundingBoxForRegion(region: string): BoundingBox | null {
    const regions: Record<string, BoundingBox> = {
      'london': { lamin: 51.3, lomin: -0.5, lamax: 51.7, lomax: 0.3 },
      'new york': { lamin: 40.5, lomin: -74.5, lamax: 41.0, lomax: -73.5 },
      'europe': { lamin: 35, lomin: -10, lamax: 70, lomax: 40 },
      'north america': { lamin: 25, lomin: -130, lamax: 50, lomax: -60 },
      'united states': { lamin: 25, lomin: -125, lamax: 50, lomax: -65 },
      'uk': { lamin: 49.9, lomin: -8.2, lamax: 60.9, lomax: 2.0 },
    };

    return regions[region.toLowerCase()] || null;
  }

  /**
   * Filter aircraft by altitude range
   */
  filterByAltitude(
    states: StateVector[],
    minAltitude: number,
    maxAltitude: number
  ): StateVector[] {
    return states.filter(s => {
      const altitude = s.baro_altitude || s.geo_altitude || 0;
      return altitude >= minAltitude && altitude <= maxAltitude;
    });
  }

  /**
   * Filter aircraft by country
   */
  filterByCountry(states: StateVector[], country: string): StateVector[] {
    return states.filter(s =>
      s.origin_country.toLowerCase().includes(country.toLowerCase())
    );
  }

  /**
   * Find aircraft by callsign
   */
  findByCallsign(states: StateVector[], callsign: string): StateVector | null {
    return states.find(s =>
      s.callsign.toLowerCase().includes(callsign.toLowerCase())
    ) || null;
  }

  /**
   * Cache helpers
   */
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    return null;
  }

  private setCache(key: string, data: any): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  /**
   * Clear cache (useful for manual refresh)
   */
  clearCache(): void {
    this.cache.clear();
  }
}

export const openskyClient = new OpenSkyClient();
export default openskyClient;
