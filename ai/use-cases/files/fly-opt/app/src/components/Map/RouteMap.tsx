import { useEffect, useState, useCallback, useMemo, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Map as MapIcon, Layers, Navigation, Info } from 'lucide-react';
import { useOptimizationStore, useAppStore, useConfigStore } from '@/store';
import { getVehicleColor, formatVehicleName } from '@/utils';
import 'leaflet/dist/leaflet.css';

// OSRM routing for road-following polylines
interface RouteGeometry {
  vehicleId: number;
  positions: [number, number][];
  color: { color: string; stroke: string };
}

async function fetchOSRMRoute(waypoints: [number, number][]): Promise<[number, number][]> {
  if (waypoints.length < 2) return waypoints;

  // OSRM expects lng,lat format
  const coordinates = waypoints.map(([lat, lng]) => `${lng},${lat}`).join(';');
  const url = `https://router.project-osrm.org/route/v1/driving/${coordinates}?overview=full&geometries=geojson`;

  try {
    const response = await fetch(url);
    if (!response.ok) return waypoints;

    const data = await response.json();
    if (data.code !== 'Ok' || !data.routes?.[0]?.geometry?.coordinates) {
      return waypoints;
    }

    // Convert GeoJSON coordinates [lng, lat] to [lat, lng] for Leaflet
    return data.routes[0].geometry.coordinates.map(([lng, lat]: [number, number]) => [lat, lng] as [number, number]);
  } catch (error) {
    console.warn('OSRM routing failed, using straight lines:', error);
    return waypoints;
  }
}

// Map style options - user-friendly tile providers
type MapStyle = 'streets' | 'voyager' | 'satellite' | 'terrain' | 'dark';

interface MapStyleOption {
  id: MapStyle;
  name: string;
  url: string;
  attribution: string;
  preview: string;
}

const MAP_STYLES: MapStyleOption[] = [
  {
    id: 'streets',
    name: 'Streets',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    preview: 'Classic road map with traffic-relevant details',
  },
  {
    id: 'voyager',
    name: 'Voyager',
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    preview: 'Colorful modern style with clear labels',
  },
  {
    id: 'terrain',
    name: 'Terrain',
    url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
    preview: 'Topographic map with elevation contours',
  },
  {
    id: 'satellite',
    name: 'Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri',
    preview: 'Satellite imagery view',
  },
  {
    id: 'dark',
    name: 'Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
    preview: 'Dark theme for night viewing',
  },
];

// Legacy map theme mapping for backward compatibility
const LEGACY_THEME_MAP: Record<string, MapStyle> = {
  dark: 'dark',
  light: 'voyager',
};

// Fix Leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons - smaller for cleaner map appearance
const createMarkerIcon = (color: string, isDepot: boolean = false, isEV: boolean = false, isUnassigned: boolean = false) => {
  if (isUnassigned) {
    // Smaller, faded marker with red border for unassigned stops
    return L.divIcon({
      className: 'custom-marker unassigned-marker',
      html: `
        <div style="
          width: 6px;
          height: 6px;
          background: ${color};
          border: 1px solid #EF4444;
          border-radius: 50%;
          box-shadow: 0 1px 2px rgba(0,0,0,0.3);
          opacity: 0.6;
        "></div>
      `,
      iconSize: [6, 6],
      iconAnchor: [3, 3],
    });
  }

  if (isEV) {
    // EV charging station marker with lightning bolt
    return L.divIcon({
      className: 'custom-marker ev-marker',
      html: `
        <div style="
          width: 12px;
          height: 12px;
          background: linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -20)} 100%);
          border: 1px solid white;
          border-radius: 3px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <svg width="7" height="7" viewBox="0 0 24 24" fill="white" stroke="none">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
          </svg>
        </div>
      `,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });
  }

  if (isDepot) {
    // Special depot marker with building icon
    return L.divIcon({
      className: 'custom-marker depot-marker',
      html: `
        <div style="
          width: 16px;
          height: 16px;
          background: linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -30)} 100%);
          border: 2px solid white;
          border-radius: 4px;
          box-shadow: 0 2px 6px rgba(0,0,0,0.35);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <svg width="9" height="9" viewBox="0 0 24 24" fill="white" stroke="none">
            <path d="M12 2L2 7v15h20V7L12 2zm0 2.3L18 8v11H6V8l6-3.7zM8 11v2h2v-2H8zm3 0v2h2v-2h-2zm3 0v2h2v-2h-2zM8 14v2h2v-2H8zm3 0v2h2v-2h-2zm3 0v2h2v-2h-2z"/>
          </svg>
        </div>
      `,
      iconSize: [16, 16],
      iconAnchor: [8, 8],
    });
  }

  // Regular stop marker - small circle
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: 10px;
        height: 10px;
        background: linear-gradient(135deg, ${color} 0%, ${adjustColor(color, -20)} 100%);
        border: 1px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
      "></div>
    `,
    iconSize: [10, 10],
    iconAnchor: [5, 5],
  });
};

// Helper to darken/lighten colors for gradients
function adjustColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace('#', ''), 16);
  const r = Math.min(255, Math.max(0, (num >> 16) + amount));
  const g = Math.min(255, Math.max(0, ((num >> 8) & 0x00ff) + amount));
  const b = Math.min(255, Math.max(0, (num & 0x0000ff) + amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, '0')}`;
}

interface MapUpdaterProps {
  isActive?: boolean;
}

function MapUpdater({ isActive = true }: MapUpdaterProps) {
  const map = useMap();
  const { stops, routes } = useOptimizationStore();
  const { config: appConfig } = useConfigStore();

  // Invalidate size when map becomes visible (fixes white background issue)
  useEffect(() => {
    if (isActive) {
      setTimeout(() => {
        map.invalidateSize();
      }, 100);
    }
  }, [isActive, map]);

  // Re-fit bounds when stops change
  useEffect(() => {
    if (stops.length > 0) {
      const bounds = L.latLngBounds(stops.map((s) => [s.lat, s.lng]));
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [stops, map]);

  // Force invalidate when routes change (fixes AI-generated results not displaying)
  useEffect(() => {
    if (routes.length > 0) {
      setTimeout(() => {
        map.invalidateSize();
      }, 50);
    }
  }, [routes, map]);

  // Pan to new location when country/city changes (when no stops loaded)
  useEffect(() => {
    if (stops.length === 0) {
      map.setView(
        [appConfig.defaultCenter.lat, appConfig.defaultCenter.lng],
        appConfig.defaultZoom || 11
      );
    }
  }, [appConfig.defaultCenter.lat, appConfig.defaultCenter.lng, appConfig.defaultZoom, stops.length, map]);

  return null;
}

interface RouteMapProps {
  isActive?: boolean;
}

export function RouteMap({ isActive = true }: RouteMapProps) {
  const { stops, routes } = useOptimizationStore();
  const { mapTheme } = useAppStore();
  const { config: appConfig } = useConfigStore();
  const [mapStyle, setMapStyle] = useState<MapStyle>(() => LEGACY_THEME_MAP[mapTheme] || 'voyager');
  const [showStyleSelector, setShowStyleSelector] = useState(false);
  const [showTrafficInfo, setShowTrafficInfo] = useState(false);
  const [routeGeometries, setRouteGeometries] = useState<RouteGeometry[]>([]);
  const [isLoadingRoutes, setIsLoadingRoutes] = useState(false);

  // Update map style when theme changes
  useEffect(() => {
    setMapStyle(LEGACY_THEME_MAP[mapTheme] || 'voyager');
  }, [mapTheme]);

  const currentStyle = MAP_STYLES.find((s) => s.id === mapStyle) || MAP_STYLES[1];

  // Default center - use config store or calculate from stops (memoized)
  const center: [number, number] = useMemo(() =>
    stops.length > 0
      ? [
          stops.reduce((sum, s) => sum + s.lat, 0) / stops.length,
          stops.reduce((sum, s) => sum + s.lng, 0) / stops.length,
        ]
      : [appConfig.defaultCenter.lat, appConfig.defaultCenter.lng],
    [stops, appConfig.defaultCenter.lat, appConfig.defaultCenter.lng]
  );

  // Build stop lookup map for O(1) access (fixes AI-generated route rendering)
  // Memoize to prevent infinite loop in useEffect
  const stopMap = useMemo(() => new Map(stops.map((s) => [s.id, s])), [stops]);

  // Get depot location (first stop or center) - memoized
  const depotLocation: [number, number] = useMemo(() =>
    stops.length > 0
      ? [stops[0].lat, stops[0].lng]
      : center,
    [stops, center]
  );

  // Build waypoints for each route (used for OSRM fetching)
  const getRouteWaypoints = useCallback((route: typeof routes[0]): [number, number][] => {
    return route.route
      .map((stopIdx) => {
        if (stopIdx === 0) {
          return depotLocation;
        }
        const stop = stopMap.get(stopIdx);
        if (stop) {
          return [stop.lat, stop.lng] as [number, number];
        }
        const stopByIndex = stops[stopIdx];
        if (stopByIndex) {
          return [stopByIndex.lat, stopByIndex.lng] as [number, number];
        }
        return null;
      })
      .filter((pos): pos is [number, number] => pos !== null);
  }, [depotLocation, stopMap, stops]);

  // Create a stable key for routes to prevent unnecessary re-fetching
  const routesKey = useMemo(() => {
    if (routes.length === 0) return '';
    return routes.map(r => `${r.vehicle_id}:${r.route.join(',')}`).join('|');
  }, [routes]);

  // Track last fetched routes to prevent re-fetching
  const lastFetchedRoutesKey = useRef<string>('');

  // Fetch OSRM routes for road-following polylines
  useEffect(() => {
    if (routes.length === 0) {
      setRouteGeometries([]);
      lastFetchedRoutesKey.current = '';
      return;
    }

    // Skip if we've already fetched these routes
    if (lastFetchedRoutesKey.current === routesKey) {
      return;
    }

    const fetchAllRoutes = async () => {
      setIsLoadingRoutes(true);
      lastFetchedRoutesKey.current = routesKey;
      const geometries: RouteGeometry[] = [];

      for (const route of routes) {
        const color = getVehicleColor(route.vehicle_id);
        const waypoints = getRouteWaypoints(route);

        if (waypoints.length >= 2) {
          // Fetch OSRM route for this vehicle
          const positions = await fetchOSRMRoute(waypoints);
          geometries.push({ vehicleId: route.vehicle_id, positions, color });
        }

        // Small delay between requests to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 100));
      }

      setRouteGeometries(geometries);
      setIsLoadingRoutes(false);
    };

    fetchAllRoutes();
  }, [routesKey, getRouteWaypoints]);

  // Build route polylines with robust stop lookup (fallback for straight lines)
  const routeLines = routes.map((route) => {
    const color = getVehicleColor(route.vehicle_id);
    const positions: [number, number][] = route.route
      .map((stopIdx) => {
        if (stopIdx === 0) {
          return depotLocation;
        }
        // Use Map lookup for O(1) access
        const stop = stopMap.get(stopIdx);
        if (stop) {
          return [stop.lat, stop.lng] as [number, number];
        }
        // For AI-generated routes, stopIdx might be 1-indexed matching stop array position
        // Try array index lookup as fallback (stopIdx - 1 since depot is at 0)
        const stopByIndex = stops[stopIdx];
        if (stopByIndex) {
          return [stopByIndex.lat, stopByIndex.lng] as [number, number];
        }
        // Skip invalid stop indices
        return null;
      })
      .filter((pos): pos is [number, number] => pos !== null);

    return { vehicleId: route.vehicle_id, positions, color };
  });

  const isDarkStyle = mapStyle === 'dark';

  return (
    <div className="relative h-full w-full">
      {/* Map Style Selector */}
      <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-2">
        {/* Style Toggle Button */}
        <button
          onClick={() => setShowStyleSelector(!showStyleSelector)}
          className={`p-2 rounded-lg shadow-lg transition-colors flex items-center gap-2 ${
            isDarkStyle
              ? 'bg-dark-card border border-dark-border hover:bg-dark-hover text-white'
              : 'bg-white border border-gray-200 hover:bg-gray-50 text-gray-700'
          }`}
          title="Change map style"
        >
          <Layers className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">{currentStyle.name}</span>
        </button>

        {/* Style Dropdown */}
        {showStyleSelector && (
          <div className={`absolute top-12 right-0 rounded-lg shadow-xl border overflow-hidden min-w-[180px] ${
            isDarkStyle ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
          }`}>
            <div className={`px-3 py-2 text-xs font-semibold border-b ${
              isDarkStyle ? 'text-gray-400 border-dark-border' : 'text-gray-500 border-gray-100'
            }`}>
              Map Style
            </div>
            {MAP_STYLES.map((style) => (
              <button
                key={style.id}
                onClick={() => {
                  setMapStyle(style.id);
                  setShowStyleSelector(false);
                }}
                className={`w-full px-3 py-2 text-left flex items-center gap-2 transition-colors ${
                  mapStyle === style.id
                    ? isDarkStyle ? 'bg-[#C74634]/20 text-[#C74634]' : 'bg-red-50 text-red-700'
                    : isDarkStyle ? 'text-gray-300 hover:bg-dark-hover' : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <MapIcon className="w-4 h-4" />
                <div>
                  <div className="text-sm font-medium">{style.name}</div>
                  <div className={`text-xs ${isDarkStyle ? 'text-gray-500' : 'text-gray-400'}`}>
                    {style.preview}
                  </div>
                </div>
              </button>
            ))}

            {/* Traffic Info Section */}
            <div className={`border-t px-3 py-2 ${isDarkStyle ? 'border-dark-border' : 'border-gray-100'}`}>
              <button
                onClick={() => setShowTrafficInfo(!showTrafficInfo)}
                className={`flex items-center gap-2 text-xs ${
                  isDarkStyle ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                <Info className="w-3 h-3" />
                Traffic Information
              </button>
              {showTrafficInfo && (
                <div className={`mt-2 p-2 rounded text-xs ${
                  isDarkStyle ? 'bg-dark-bg text-gray-400' : 'bg-gray-50 text-gray-600'
                }`}>
                  Real-time traffic data requires API integration (e.g., TomTom, HERE, Google).
                  The Streets map shows road types and importance for planning purposes.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Route Legend */}
      {routes.length > 0 && (
        <div className={`absolute bottom-4 left-4 z-[1000] rounded-lg shadow-lg p-3 max-w-[200px] ${
          isDarkStyle ? 'bg-dark-card border border-dark-border' : 'bg-white border border-gray-200'
        }`}>
          <div className={`text-xs font-semibold mb-2 flex items-center gap-1 ${
            isDarkStyle ? 'text-gray-300' : 'text-gray-700'
          }`}>
            <Navigation className="w-3 h-3" />
            Routes ({routes.length})
            {isLoadingRoutes && (
              <span className="ml-1 text-[10px] text-orange-400">Loading roads...</span>
            )}
          </div>
          <div className="space-y-1 max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-500 scrollbar-track-transparent pr-1">
            {routes.map((route) => {
              const color = getVehicleColor(route.vehicle_id);
              return (
                <div key={route.vehicle_id} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-3 h-3 rounded-full border border-white flex-shrink-0"
                    style={{ backgroundColor: color.color }}
                  />
                  <span className={isDarkStyle ? 'text-gray-400' : 'text-gray-600'}>
                    {formatVehicleName(route.vehicle_id)} ({route.route.length - 2} stops)
                  </span>
                </div>
              );
            })}
          </div>
          {/* Unassigned Stops Warning */}
          {(() => {
            const assignedStopIds = new Set<number>();
            routes.forEach(r => r.route.forEach(id => { if (id !== 0) assignedStopIds.add(id); }));
            const unassignedCount = stops.slice(1).filter(s => !assignedStopIds.has(s.id)).length;
            if (unassignedCount > 0) {
              return (
                <div className={`mt-2 pt-2 border-t ${isDarkStyle ? 'border-dark-border' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-gray-400 opacity-50 border-2 border-red-500" style={{ width: '12px', height: '12px' }} />
                    <span className={`text-[10px] ${isDarkStyle ? 'text-red-400' : 'text-red-500'}`}>
                      {unassignedCount} unassigned
                    </span>
                  </div>
                </div>
              );
            }
            return null;
          })()}
        </div>
      )}

      <MapContainer
        center={center}
        zoom={stops.length > 0 ? 11 : 6}
        className="h-full w-full rounded-xl"
        style={{ background: isDarkStyle ? '#1B1F2E' : '#f8fafc' }}
      >
        <TileLayer
          key={currentStyle.id}
          url={currentStyle.url}
          attribution={currentStyle.attribution}
        />

      <MapUpdater isActive={isActive} />

      {/* Route polylines - use OSRM road-following routes when available */}
      {/* Shadow/border for polylines */}
      {(routeGeometries.length > 0 ? routeGeometries : routeLines).map((line) => (
        <Polyline
          key={`shadow-${line.vehicleId}`}
          positions={line.positions}
          pathOptions={{
            color: isDarkStyle ? '#000000' : '#ffffff',
            weight: 7,
            opacity: 0.5,
          }}
        />
      ))}
      {/* Main colored polylines */}
      {(routeGeometries.length > 0 ? routeGeometries : routeLines).map((line) => (
        <Polyline
          key={line.vehicleId}
          positions={line.positions}
          pathOptions={{
            color: line.color.color,
            weight: 4,
            opacity: 0.9,
            lineCap: 'round',
            lineJoin: 'round',
          }}
        />
      ))}

      {/* Depot marker */}
      {stops.length > 0 && (
        <Marker
          position={[stops[0].lat, stops[0].lng]}
          icon={createMarkerIcon('#76B900', true)}
        >
          <Popup>
            <div style={{ fontFamily: 'system-ui, sans-serif', minWidth: '160px' }}>
              <div style={{ fontWeight: 600, fontSize: '14px', color: '#1a1a1a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ background: '#76B900', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' }}>DEPOT</span>
                Fleet Base
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Latitude:</span>
                  <span style={{ fontFamily: 'monospace', color: '#333' }}>{stops[0].lat.toFixed(5)}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Longitude:</span>
                  <span style={{ fontFamily: 'monospace', color: '#333' }}>{stops[0].lng.toFixed(5)}</span>
                </div>
              </div>
            </div>
          </Popup>
        </Marker>
      )}

      {/* Stop markers */}
      {stops.slice(1).map((stop) => {
        // Find which route this stop belongs to (check both by ID and by index)
        const assignedRoute = routes.find((r) =>
          r.route.includes(stop.id) || r.route.includes(stops.indexOf(stop))
        );
        const isAssigned = !!assignedRoute;
        const color = assignedRoute
          ? getVehicleColor(assignedRoute.vehicle_id).color
          : '#9CA3AF'; // Gray for unassigned

        // Check if this is an EV charging station (has metadata with networkName)
        const isEVStation = !!(stop as any).metadata?.networkName;
        const metadata = (stop as any).metadata;

        // Use different marker for unassigned stops when routes exist
        const isUnassigned = !isAssigned && routes.length > 0;

        return (
          <Marker
            key={stop.id}
            position={[stop.lat, stop.lng]}
            icon={createMarkerIcon(isEVStation ? '#22C55E' : color, false, isEVStation, isUnassigned)}
            opacity={isUnassigned ? 0.5 : 1}
          >
            <Popup>
              <div style={{ fontFamily: 'system-ui, sans-serif', minWidth: '200px' }}>
                <div style={{ fontWeight: 600, fontSize: '14px', color: '#1a1a1a', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {isUnassigned && (
                    <span style={{ background: '#EF4444', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '10px' }}>UNASSIGNED</span>
                  )}
                  {isEVStation && (
                    <span style={{ background: '#22C55E', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '10px' }}>EV</span>
                  )}
                  {stop.label || `Stop ${stop.id}`}
                </div>
                <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.6' }}>
                  {stop.postcode && (
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Postcode:</span>
                      <span style={{ fontFamily: 'monospace', color: '#333', fontWeight: 500 }}>{stop.postcode}</span>
                    </div>
                  )}
                  {isEVStation && metadata && (
                    <>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Network:</span>
                        <span style={{ color: '#333' }}>{metadata.networkName}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Power:</span>
                        <span style={{ color: '#333' }}>{metadata.powerGroup}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>Type:</span>
                        <span style={{ color: '#333' }}>{metadata.connectorType}</span>
                      </div>
                    </>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Demand:</span>
                    <span style={{ color: '#333', fontWeight: 500 }}>{stop.demand} units</span>
                  </div>
                  {assignedRoute && (
                    <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #eee', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: color }} />
                      <span style={{ fontFamily: 'monospace', fontWeight: 600, color: color }}>
                        {formatVehicleName(assignedRoute.vehicle_id)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </Popup>
          </Marker>
        );
      })}
    </MapContainer>
    </div>
  );
}
