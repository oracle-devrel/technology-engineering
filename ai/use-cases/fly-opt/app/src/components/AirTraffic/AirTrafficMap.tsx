import { useState, useEffect, useCallback, useRef } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { AircraftMarker } from './AircraftMarker';
import { openskyClient } from '@/api';
import type { StateVector, BoundingBox } from '@/types/opensky';
import 'leaflet/dist/leaflet.css';

export interface AirTrafficSnapshot {
  states: StateVector[];
  dataSource: 'api' | 'fallback';
  fallbackReason?: string;
  fetchedAt: number;
}

interface AirTrafficMapProps {
  bbox?: BoundingBox;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onAircraftCountChange?: (count: number) => void;
  onDataSourceChange?: (source: 'api' | 'fallback', reason?: string) => void;
  onAircraftSnapshotChange?: (snapshot: AirTrafficSnapshot) => void;
}

function MapViewController({ bbox }: { bbox?: BoundingBox }) {
  const map = useMap();

  useEffect(() => {
    if (!bbox) return;
    map.fitBounds([
      [bbox.lamin, bbox.lomin],
      [bbox.lamax, bbox.lomax],
    ]);
  }, [bbox, map]);

  return null;
}

export function AirTrafficMap({
  bbox,
  autoRefresh = true,
  refreshInterval = 15,
  onAircraftCountChange,
  onDataSourceChange,
  onAircraftSnapshotChange,
}: AirTrafficMapProps) {
  const [aircraft, setAircraft] = useState<StateVector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [nextUpdate, setNextUpdate] = useState(refreshInterval);
  const [dataSource, setDataSource] = useState<'api' | 'fallback'>('api');
  const [fallbackReason, setFallbackReason] = useState<string | null>(null);

  // Read callbacks through a ref so fetchAircraft stays stable even when the
  // parent passes inline functions; otherwise the fetch effect refires on
  // every parent render and the map refreshes in a loop.
  const callbacksRef = useRef({ onAircraftCountChange, onDataSourceChange, onAircraftSnapshotChange });
  useEffect(() => {
    callbacksRef.current = { onAircraftCountChange, onDataSourceChange, onAircraftSnapshotChange };
  });

  const fetchAircraft = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await openskyClient.getParsedStates(bbox);
      setAircraft(result.states);
      setDataSource(result.dataSource);
      setFallbackReason(result.fallbackReason || null);
      const callbacks = callbacksRef.current;
      callbacks.onAircraftCountChange?.(result.states.length);
      callbacks.onDataSourceChange?.(result.dataSource, result.fallbackReason);
      callbacks.onAircraftSnapshotChange?.({
        states: result.states,
        dataSource: result.dataSource,
        fallbackReason: result.fallbackReason,
        fetchedAt: result.time,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch aircraft';
      setError(message);
      console.error('[AirTrafficMap] Error:', message);
    } finally {
      setLoading(false);
    }
  }, [bbox]);

  useEffect(() => {
    setNextUpdate(refreshInterval);
  }, [refreshInterval, bbox]);

  useEffect(() => {
    fetchAircraft();
  }, [fetchAircraft]);

  useEffect(() => {
    if (!autoRefresh) return;

    const countdownInterval = setInterval(() => {
      setNextUpdate((prev) => {
        if (prev <= 1) {
          fetchAircraft();
          return refreshInterval;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(countdownInterval);
  }, [autoRefresh, refreshInterval, fetchAircraft]);

  const defaultCenter: [number, number] = bbox
    ? [(bbox.lamin + bbox.lamax) / 2, (bbox.lomin + bbox.lomax) / 2]
    : [50.0, 10.0];

  return (
    <div className="relative h-full w-full">
      <div className="absolute left-4 top-4 z-[1000] rounded-lg bg-gray-900/90 px-4 py-2 text-white shadow-lg backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div
              className={`h-2 w-2 rounded-full ${
                loading ? 'animate-pulse bg-yellow-400' : 'bg-green-400'
              }`}
            />
            <span className="font-semibold">{aircraft.length} Aircraft</span>
            <span
              title={dataSource === 'fallback' && fallbackReason ? fallbackReason : 'Live OpenSky API data'}
              className={`rounded px-2 py-0.5 text-xs font-semibold ${
                dataSource === 'fallback'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
              }`}
            >
              {dataSource === 'fallback' ? 'FALLBACK' : 'API'}
            </span>
          </div>
          {autoRefresh && !loading && (
            <div className="text-sm text-gray-300">Next update: {nextUpdate}s</div>
          )}
          {dataSource === 'fallback' && fallbackReason && (
            <div className="text-sm text-amber-300">Reason: {fallbackReason}</div>
          )}
          {error && <div className="text-sm text-red-400">Error: {error}</div>}
        </div>
      </div>

      <button
        type="button"
        onClick={() => {
          openskyClient.clearCache();
          setNextUpdate(refreshInterval);
          fetchAircraft();
        }}
        disabled={loading}
        className="absolute right-4 top-4 z-[1000] rounded-lg bg-green-600 px-4 py-2 text-white shadow-lg transition-colors hover:bg-green-700 disabled:bg-gray-600"
      >
        {loading ? 'Refreshing...' : 'Refresh Now'}
      </button>

      <MapContainer
        center={defaultCenter}
        zoom={6}
        style={{ width: '100%', height: '100%' }}
        className="rounded-lg"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        <MapViewController bbox={bbox} />
        {aircraft.map((ac, index) => (
          <AircraftMarker key={`${ac.icao24}-${ac.time_position}-${index}`} aircraft={ac} />
        ))}
      </MapContainer>
    </div>
  );
}
