import { useState, useCallback, useEffect, useRef } from 'react';
import {
  GoogleMap,
  useJsApiLoader,
  Marker,
  DirectionsRenderer,
  TrafficLayer,
  InfoWindow,
} from '@react-google-maps/api';
import { Map as MapIcon, Navigation, Layers, AlertCircle, Car, Cloud, AlertTriangle } from 'lucide-react';
import { useOptimizationStore, useAppStore, useConfigStore } from '@/store';
import { getVehicleColor, formatVehicleName } from '@/utils';
import { weatherClient } from '@/api/weatherClient';
import type { LocationWeather, AdverseConditionAssessment, AdverseConditionLevel } from '@/types/weather';

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

// Libraries to load - Directions API doesn't need a library, it's always available
const libraries: ('places')[] = ['places'];

// Map container style
const containerStyle = {
  width: '100%',
  height: '100%',
};

// Map style options
type MapStyleId = 'roadmap' | 'satellite' | 'hybrid' | 'terrain';

interface MapStyleOption {
  id: MapStyleId;
  name: string;
  description: string;
}

const MAP_STYLES: MapStyleOption[] = [
  { id: 'roadmap', name: 'Roadmap', description: 'Standard road map with traffic' },
  { id: 'satellite', name: 'Satellite', description: 'Satellite imagery' },
  { id: 'hybrid', name: 'Hybrid', description: 'Satellite with labels' },
  { id: 'terrain', name: 'Terrain', description: 'Topographic map' },
];

// Custom dark mode styles for Google Maps
const darkModeStyles: google.maps.MapTypeStyle[] = [
  { elementType: 'geometry', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#242f3e' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#746855' }] },
  { featureType: 'administrative.locality', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
  { featureType: 'poi', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
  { featureType: 'poi.park', elementType: 'geometry', stylers: [{ color: '#263c3f' }] },
  { featureType: 'poi.park', elementType: 'labels.text.fill', stylers: [{ color: '#6b9a76' }] },
  { featureType: 'road', elementType: 'geometry', stylers: [{ color: '#38414e' }] },
  { featureType: 'road', elementType: 'geometry.stroke', stylers: [{ color: '#212a37' }] },
  { featureType: 'road', elementType: 'labels.text.fill', stylers: [{ color: '#9ca5b3' }] },
  { featureType: 'road.highway', elementType: 'geometry', stylers: [{ color: '#746855' }] },
  { featureType: 'road.highway', elementType: 'geometry.stroke', stylers: [{ color: '#1f2835' }] },
  { featureType: 'road.highway', elementType: 'labels.text.fill', stylers: [{ color: '#f3d19c' }] },
  { featureType: 'transit', elementType: 'geometry', stylers: [{ color: '#2f3948' }] },
  { featureType: 'transit.station', elementType: 'labels.text.fill', stylers: [{ color: '#d59563' }] },
  { featureType: 'water', elementType: 'geometry', stylers: [{ color: '#17263c' }] },
  { featureType: 'water', elementType: 'labels.text.fill', stylers: [{ color: '#515c6d' }] },
  { featureType: 'water', elementType: 'labels.text.stroke', stylers: [{ color: '#17263c' }] },
];

interface RouteDirections {
  vehicleId: number;
  directions: google.maps.DirectionsResult | null;
  color: string;
  additionalSegments?: google.maps.DirectionsResult[]; // For long routes split into segments
}

interface StopWeatherData {
  stopId: number;
  weather: LocationWeather;
  assessment: AdverseConditionAssessment;
}

// Weather severity colors
const WEATHER_SEVERITY_COLORS: Record<AdverseConditionLevel, string> = {
  none: '#22C55E',      // Green
  low: '#84CC16',       // Lime
  moderate: '#F59E0B',  // Amber
  high: '#EF4444',      // Red
  severe: '#7C3AED',    // Purple
};

// Get weather icon based on conditions
function getWeatherIcon(weather: LocationWeather): string {
  const condition = weather.current.conditions[0];
  if (!condition) return '☀️';

  const id = condition.id;
  if (id >= 200 && id < 300) return '⛈️'; // Thunderstorm
  if (id >= 300 && id < 400) return '🌧️'; // Drizzle
  if (id >= 500 && id < 600) return '🌧️'; // Rain
  if (id >= 600 && id < 700) return '❄️'; // Snow
  if (id >= 700 && id < 800) return '🌫️'; // Atmosphere (fog, mist)
  if (id === 800) return '☀️'; // Clear
  if (id > 800) return '☁️'; // Clouds
  return '☀️';
}

export function GoogleRouteMap() {
  const { stops, routes } = useOptimizationStore();
  const { mapTheme } = useAppStore();
  const { config: appConfig } = useConfigStore();
  const [mapStyle, setMapStyle] = useState<MapStyleId>('roadmap');
  const [showStyleSelector, setShowStyleSelector] = useState(false);
  const [showTraffic, setShowTraffic] = useState(true);
  const [showWeather, setShowWeather] = useState(true);
  const [routeDirections, setRouteDirections] = useState<RouteDirections[]>([]);
  const [selectedMarker, setSelectedMarker] = useState<number | null>(null);
  const [isLoadingDirections, setIsLoadingDirections] = useState(false);
  const [weatherData, setWeatherData] = useState<Map<number, StopWeatherData>>(new Map());
  const [isLoadingWeather, setIsLoadingWeather] = useState(false);
  const [overallWeatherLevel, setOverallWeatherLevel] = useState<AdverseConditionLevel>('none');
  const [mapKey, setMapKey] = useState(0); // Key to force map re-mount on reset
  const mapRef = useRef<google.maps.Map | null>(null);
  const directionsServiceRef = useRef<google.maps.DirectionsService | null>(null);

  const { isLoaded, loadError } = useJsApiLoader({
    googleMapsApiKey: GOOGLE_MAPS_API_KEY,
    libraries,
  });

  // Default center - use config store or calculate from stops
  const center = stops.length > 0
    ? {
        lat: stops.reduce((sum, s) => sum + s.lat, 0) / stops.length,
        lng: stops.reduce((sum, s) => sum + s.lng, 0) / stops.length,
      }
    : { lat: appConfig.defaultCenter.lat, lng: appConfig.defaultCenter.lng };

  const onMapLoad = useCallback((map: google.maps.Map) => {
    mapRef.current = map;
    directionsServiceRef.current = new google.maps.DirectionsService();

    // Fit bounds to stops
    if (stops.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      stops.forEach((stop) => bounds.extend({ lat: stop.lat, lng: stop.lng }));
      map.fitBounds(bounds, 50);
    }
  }, [stops]);

  // Fetch directions for a single segment with retry logic
  const fetchDirectionsSegment = useCallback(async (
    origin: google.maps.LatLngLiteral,
    destination: google.maps.LatLngLiteral,
    waypoints: google.maps.DirectionsWaypoint[],
    retries: number = 3
  ): Promise<google.maps.DirectionsResult | null> => {
    if (!directionsServiceRef.current) return null;

    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const result = await new Promise<google.maps.DirectionsResult | null>((resolve) => {
          // Try with traffic first, then without on retry
          const useTraffic = attempt < 2;

          const request: google.maps.DirectionsRequest = {
            origin,
            destination,
            waypoints: waypoints.slice(0, 23), // Google limits to 23 waypoints
            travelMode: google.maps.TravelMode.DRIVING,
            optimizeWaypoints: false, // Keep cuOPT order
          };

          // Add traffic options only on first attempts
          if (useTraffic) {
            request.drivingOptions = {
              departureTime: new Date(),
              trafficModel: google.maps.TrafficModel.BEST_GUESS,
            };
          }

          directionsServiceRef.current!.route(request, (response, status) => {
            if (status === 'OK') {
              resolve(response);
            } else if (status === 'OVER_QUERY_LIMIT') {
              // Rate limited - will retry with delay
              console.warn('Rate limited, will retry...');
              resolve(null);
            } else {
              console.warn(`Directions failed: ${status}`);
              resolve(null);
            }
          });
        });

        if (result) return result;

        // Exponential backoff before retry
        const delay = Math.min(500 * Math.pow(2, attempt), 3000);
        await new Promise((resolve) => setTimeout(resolve, delay));
      } catch (error) {
        console.error('Directions error:', error);
      }
    }
    return null;
  }, []);

  // Fetch directions for each route with segmentation for long routes
  const fetchDirections = useCallback(async () => {
    if (!directionsServiceRef.current || routes.length === 0 || stops.length === 0) {
      return;
    }

    setIsLoadingDirections(true);
    const newDirections: RouteDirections[] = [];

    for (const route of routes) {
      const color = getVehicleColor(route.vehicle_id);

      // Build waypoints from route with robust lookup (handles AI-generated routes)
      const routeStops = route.route
        .map((stopIdx) => {
          if (stopIdx === 0) return stops[0]; // Depot
          // Try Map lookup first (by stop.id)
          const stopById = stops.find((s) => s.id === stopIdx);
          if (stopById) return stopById;
          // Fallback: try array index (stopIdx might be 1-indexed position)
          if (stopIdx > 0 && stopIdx < stops.length) {
            return stops[stopIdx];
          }
          return undefined;
        })
        .filter(Boolean) as typeof stops;

      if (routeStops.length < 2) {
        newDirections.push({ vehicleId: route.vehicle_id, directions: null, color: color.color });
        continue;
      }

      // For routes with many stops, split into segments
      const MAX_WAYPOINTS_PER_REQUEST = 20;
      const allResults: google.maps.DirectionsResult[] = [];

      if (routeStops.length <= MAX_WAYPOINTS_PER_REQUEST + 2) {
        // Small route - fetch in one request
        const origin = { lat: routeStops[0].lat, lng: routeStops[0].lng };
        const destination = { lat: routeStops[routeStops.length - 1].lat, lng: routeStops[routeStops.length - 1].lng };
        const waypoints = routeStops.slice(1, -1).map((stop) => ({
          location: { lat: stop.lat, lng: stop.lng },
          stopover: true,
        }));

        const result = await fetchDirectionsSegment(origin, destination, waypoints);
        if (result) {
          allResults.push(result);
        }
      } else {
        // Large route - split into segments
        let segmentStart = 0;
        while (segmentStart < routeStops.length - 1) {
          const segmentEnd = Math.min(segmentStart + MAX_WAYPOINTS_PER_REQUEST + 1, routeStops.length - 1);
          const segmentStops = routeStops.slice(segmentStart, segmentEnd + 1);

          const origin = { lat: segmentStops[0].lat, lng: segmentStops[0].lng };
          const destination = { lat: segmentStops[segmentStops.length - 1].lat, lng: segmentStops[segmentStops.length - 1].lng };
          const waypoints = segmentStops.slice(1, -1).map((stop) => ({
            location: { lat: stop.lat, lng: stop.lng },
            stopover: true,
          }));

          const result = await fetchDirectionsSegment(origin, destination, waypoints);
          if (result) {
            allResults.push(result);
          }

          segmentStart = segmentEnd;

          // Delay between segments
          await new Promise((resolve) => setTimeout(resolve, 200));
        }
      }

      // Combine all segment results into one (use first result as base, append routes)
      if (allResults.length > 0) {
        // For simplicity, we'll store the first result but all will be rendered
        newDirections.push({
          vehicleId: route.vehicle_id,
          directions: allResults[0],
          color: color.color,
          additionalSegments: allResults.slice(1),
        });
      } else {
        newDirections.push({ vehicleId: route.vehicle_id, directions: null, color: color.color });
      }

      // Delay between routes to avoid rate limiting
      await new Promise((resolve) => setTimeout(resolve, 150));
    }

    setRouteDirections(newDirections);
    setIsLoadingDirections(false);
  }, [routes, stops, fetchDirectionsSegment]);

  // Clear directions when routes or stops are reset
  // Also increment mapKey to force GoogleMap to re-mount and clear DirectionsRenderers
  useEffect(() => {
    if (routes.length === 0 && stops.length === 0) {
      // Full reset - clear everything and force map re-mount
      setRouteDirections([]);
      setWeatherData(new Map());
      setOverallWeatherLevel('none');
      setSelectedMarker(null);
      setMapKey(prev => prev + 1); // Force map re-mount to clear DirectionsRenderers
    } else if (routes.length === 0) {
      // Routes cleared but stops still loaded - just clear route directions
      setRouteDirections([]);
    }
  }, [routes.length, stops.length]);

  // Fetch directions when we have routes and stops (clear old ones first)
  useEffect(() => {
    if (routes.length > 0 && stops.length > 0 && directionsServiceRef.current) {
      setRouteDirections([]); // Clear old directions before fetching new
      // Small delay to ensure state is cleared before fetching
      const timer = setTimeout(() => {
        fetchDirections();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [routes, fetchDirections, stops.length]);

  // Update map bounds when stops change
  useEffect(() => {
    if (mapRef.current && stops.length > 0) {
      const bounds = new google.maps.LatLngBounds();
      stops.forEach((stop) => bounds.extend({ lat: stop.lat, lng: stop.lng }));
      mapRef.current.fitBounds(bounds, 50);
    }
  }, [stops]);

  // Pan to new location when country/city changes (when no stops loaded)
  useEffect(() => {
    if (mapRef.current && stops.length === 0) {
      mapRef.current.setCenter({
        lat: appConfig.defaultCenter.lat,
        lng: appConfig.defaultCenter.lng,
      });
      mapRef.current.setZoom(appConfig.defaultZoom || 11);
    }
  }, [appConfig.defaultCenter.lat, appConfig.defaultCenter.lng, appConfig.defaultZoom, stops.length]);

  // Fetch weather data for all stops
  useEffect(() => {
    if (stops.length === 0) {
      setWeatherData(new Map());
      setOverallWeatherLevel('none');
      return;
    }

    const fetchWeather = async () => {
      setIsLoadingWeather(true);
      try {
        const weatherMap = await weatherClient.getWeatherForStops(stops);
        const newWeatherData = new Map<number, StopWeatherData>();
        let worstLevel: AdverseConditionLevel = 'none';
        const levelOrder: AdverseConditionLevel[] = ['none', 'low', 'moderate', 'high', 'severe'];

        weatherMap.forEach((weather, stopId) => {
          const assessment = weatherClient.assessAdverseConditions(weather.current);
          newWeatherData.set(stopId, { stopId, weather, assessment });

          // Track worst weather condition
          if (levelOrder.indexOf(assessment.level) > levelOrder.indexOf(worstLevel)) {
            worstLevel = assessment.level;
          }
        });

        setWeatherData(newWeatherData);
        setOverallWeatherLevel(worstLevel);
        console.log('[GoogleRouteMap] Weather loaded for', newWeatherData.size, 'stops. Worst level:', worstLevel);
      } catch (error) {
        console.error('Failed to fetch weather:', error);
      } finally {
        setIsLoadingWeather(false);
      }
    };

    fetchWeather();
  }, [stops]);

  // Calculate weather-adjusted ETA for a route
  const getWeatherAdjustedETA = useCallback((vehicleId: number): { original: number; adjusted: number; multiplier: number } | null => {
    const directions = routeDirections.find((d) => d.vehicleId === vehicleId);
    if (!directions?.directions) return null;

    const originalSeconds = directions.directions.routes[0]?.legs.reduce(
      (acc, leg) => acc + (leg.duration?.value || 0),
      0
    ) || 0;

    // Find route stops and their weather
    const route = routes.find((r) => r.vehicle_id === vehicleId);
    if (!route) return { original: originalSeconds, adjusted: originalSeconds, multiplier: 1 };

    // Calculate average weather multiplier for this route
    let totalMultiplier = 0;
    let count = 0;
    route.route.forEach((stopIdx) => {
      if (stopIdx === 0) return; // Skip depot
      const stopWeather = weatherData.get(stopIdx);
      if (stopWeather) {
        totalMultiplier += stopWeather.assessment.travelTimeMultiplier;
        count++;
      }
    });

    const avgMultiplier = count > 0 ? totalMultiplier / count : 1;
    const adjustedSeconds = Math.round(originalSeconds * avgMultiplier);

    return { original: originalSeconds, adjusted: adjustedSeconds, multiplier: avgMultiplier };
  }, [routeDirections, routes, weatherData]);

  const isDarkTheme = mapTheme === 'dark';
  const currentStyle = MAP_STYLES.find((s) => s.id === mapStyle) || MAP_STYLES[0];

  if (loadError) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-dark-card rounded-xl">
        <div className="text-center p-6">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
          <p className="text-red-400 font-medium">Failed to load Google Maps</p>
          <p className="text-gray-500 text-sm mt-1">Check your API key configuration</p>
        </div>
      </div>
    );
  }

  if (!isLoaded) {
    return (
      <div className="h-full w-full flex items-center justify-center bg-dark-card rounded-xl">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-oracle-red border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-400">Loading Google Maps...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      {/* Map Controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-2">
        {/* Style Toggle Button */}
        <button
          onClick={() => setShowStyleSelector(!showStyleSelector)}
          className={`p-2 rounded-lg shadow-lg transition-colors flex items-center gap-2 ${
            isDarkTheme
              ? 'bg-dark-card border border-dark-border hover:bg-dark-hover text-white'
              : 'bg-white border border-gray-200 hover:bg-gray-50 text-gray-700'
          }`}
          title="Change map style"
        >
          <Layers className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">{currentStyle.name}</span>
        </button>

        {/* Traffic Toggle */}
        <button
          onClick={() => setShowTraffic(!showTraffic)}
          className={`p-2 rounded-lg shadow-lg transition-colors flex items-center gap-2 ${
            showTraffic
              ? 'bg-green-600 text-white'
              : isDarkTheme
              ? 'bg-dark-card border border-dark-border text-gray-400 hover:text-white'
              : 'bg-white border border-gray-200 text-gray-500 hover:text-gray-700'
          }`}
          title={showTraffic ? 'Hide Traffic' : 'Show Traffic'}
        >
          <Car className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">Traffic</span>
        </button>

        {/* Weather Toggle */}
        <button
          onClick={() => setShowWeather(!showWeather)}
          className={`p-2 rounded-lg shadow-lg transition-colors flex items-center gap-2 ${
            showWeather
              ? overallWeatherLevel === 'none' || overallWeatherLevel === 'low'
                ? 'bg-green-600 text-white'
                : overallWeatherLevel === 'moderate'
                ? 'bg-amber-500 text-white'
                : 'bg-red-500 text-white'
              : isDarkTheme
              ? 'bg-dark-card border border-dark-border text-gray-400 hover:text-white'
              : 'bg-white border border-gray-200 text-gray-500 hover:text-gray-700'
          }`}
          title={showWeather ? 'Hide Weather' : 'Show Weather'}
        >
          <Cloud className="w-4 h-4" />
          <span className="text-xs font-medium hidden sm:inline">
            {isLoadingWeather ? 'Loading...' : 'Weather'}
          </span>
        </button>

        {/* Style Dropdown */}
        {showStyleSelector && (
          <div
            className={`absolute top-12 right-0 rounded-lg shadow-xl border overflow-hidden min-w-[180px] ${
              isDarkTheme ? 'bg-dark-card border-dark-border' : 'bg-white border-gray-200'
            }`}
          >
            <div
              className={`px-3 py-2 text-xs font-semibold border-b ${
                isDarkTheme ? 'text-gray-400 border-dark-border' : 'text-gray-500 border-gray-100'
              }`}
            >
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
                    ? isDarkTheme
                      ? 'bg-[#C74634]/20 text-[#C74634]'
                      : 'bg-red-50 text-red-700'
                    : isDarkTheme
                    ? 'text-gray-300 hover:bg-dark-hover'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <MapIcon className="w-4 h-4" />
                <div>
                  <div className="text-sm font-medium">{style.name}</div>
                  <div className={`text-xs ${isDarkTheme ? 'text-gray-500' : 'text-gray-400'}`}>
                    {style.description}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Route Legend with Weather-Adjusted ETAs */}
      {routes.length > 0 && (
        <div
          className={`absolute bottom-4 left-4 z-10 rounded-lg shadow-lg p-3 max-w-[260px] ${
            isDarkTheme ? 'bg-dark-card border border-dark-border' : 'bg-white border border-gray-200'
          }`}
        >
          <div
            className={`text-xs font-semibold mb-2 flex items-center gap-1 ${
              isDarkTheme ? 'text-gray-300' : 'text-gray-700'
            }`}
          >
            <Navigation className="w-3 h-3" />
            Routes ({routes.length})
            {isLoadingDirections && (
              <span className="ml-2 text-orange-400 text-[10px]">Loading...</span>
            )}
          </div>
          <div className="space-y-1.5 max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-gray-500 scrollbar-track-transparent pr-1">
            {routes.map((route) => {
              const color = getVehicleColor(route.vehicle_id);
              const weatherETA = getWeatherAdjustedETA(route.vehicle_id);
              const hasWeatherDelay = weatherETA && weatherETA.multiplier > 1.05;

              return (
                <div key={route.vehicle_id} className="flex items-center gap-2 text-xs">
                  <div
                    className="w-3 h-3 rounded-full border border-white flex-shrink-0"
                    style={{ backgroundColor: color.color }}
                  />
                  <span className={`flex-1 ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
                    {formatVehicleName(route.vehicle_id)} ({route.route.length - 2} stops)
                  </span>
                  {weatherETA && showWeather && (
                    <div className="flex items-center gap-1">
                      {hasWeatherDelay ? (
                        <>
                          <span className="text-[10px] text-gray-500 line-through">
                            {Math.round(weatherETA.original / 60)}m
                          </span>
                          <span className="text-[10px] text-amber-400 font-medium">
                            {Math.round(weatherETA.adjusted / 60)}m
                          </span>
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                        </>
                      ) : (
                        <span className={`text-[10px] ${isDarkTheme ? 'text-gray-500' : 'text-gray-400'}`}>
                          {Math.round(weatherETA.original / 60)}m
                        </span>
                      )}
                    </div>
                  )}
                  {!showWeather && weatherETA && (
                    <span className={`text-[10px] ${isDarkTheme ? 'text-gray-500' : 'text-gray-400'}`}>
                      {Math.round(weatherETA.original / 60)}m
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Weather Impact Summary */}
          {showWeather && weatherData.size > 0 && overallWeatherLevel !== 'none' && (
            <div className={`mt-2 pt-2 border-t ${isDarkTheme ? 'border-dark-border' : 'border-gray-200'}`}>
              <div className="flex items-center gap-2">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: WEATHER_SEVERITY_COLORS[overallWeatherLevel] }}
                />
                <span className={`text-[10px] ${isDarkTheme ? 'text-gray-400' : 'text-gray-600'}`}>
                  {overallWeatherLevel === 'low' && 'Minor weather impact'}
                  {overallWeatherLevel === 'moderate' && 'Moderate delays expected'}
                  {overallWeatherLevel === 'high' && 'Significant delays likely'}
                  {overallWeatherLevel === 'severe' && 'Severe conditions - caution!'}
                </span>
              </div>
            </div>
          )}

          {/* Unassigned Stops Warning */}
          {(() => {
            const assignedStopIds = new Set<number>();
            routes.forEach(r => r.route.forEach(id => { if (id !== 0) assignedStopIds.add(id); }));
            const unassignedCount = stops.slice(1).filter(s => !assignedStopIds.has(s.id)).length;
            if (unassignedCount > 0) {
              return (
                <div className={`mt-2 pt-2 border-t ${isDarkTheme ? 'border-dark-border' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-gray-400 opacity-50 border border-red-500" />
                    <span className={`text-[10px] ${isDarkTheme ? 'text-red-400' : 'text-red-500'}`}>
                      {unassignedCount} unassigned stop{unassignedCount > 1 ? 's' : ''} (time/capacity constraints)
                    </span>
                  </div>
                </div>
              );
            }
            return null;
          })()}
        </div>
      )}

      {/* Weather Alert Banner */}
      {showWeather && overallWeatherLevel === 'severe' && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2 animate-pulse">
          <AlertTriangle className="w-4 h-4" />
          <span className="text-sm font-medium">Severe Weather Alert - Check conditions before dispatch</span>
        </div>
      )}

      {/* Google Branding Badge */}
      <div
        className={`absolute bottom-4 right-4 z-10 px-2 py-1 rounded text-[10px] font-medium ${
          isDarkTheme ? 'bg-dark-card/80 text-gray-400' : 'bg-white/80 text-gray-500'
        }`}
      >
        Powered by Google Maps
      </div>

      <GoogleMap
        key={`google-map-${mapKey}`}
        mapContainerStyle={containerStyle}
        center={center}
        zoom={stops.length > 0 ? 11 : 6}
        onLoad={onMapLoad}
        options={{
          mapTypeId: mapStyle,
          styles: isDarkTheme && mapStyle === 'roadmap' ? darkModeStyles : undefined,
          disableDefaultUI: false,
          zoomControl: true,
          mapTypeControl: false,
          streetViewControl: false,
          fullscreenControl: true,
        }}
      >
        {/* Traffic Layer */}
        {showTraffic && <TrafficLayer />}

        {/* Route Directions - Main segments */}
        {routeDirections
          .filter((rd) => rd.directions)
          .map((rd) => (
            <DirectionsRenderer
              key={`route-${rd.vehicleId}`}
              directions={rd.directions!}
              options={{
                suppressMarkers: true,
                polylineOptions: {
                  strokeColor: rd.color,
                  strokeOpacity: 0.9,
                  strokeWeight: 5,
                },
                preserveViewport: true,
              }}
            />
          ))}

        {/* Route Directions - Additional segments for long routes */}
        {routeDirections
          .filter((rd) => rd.additionalSegments && rd.additionalSegments.length > 0)
          .flatMap((rd) =>
            rd.additionalSegments!.map((segment, idx) => (
              <DirectionsRenderer
                key={`route-${rd.vehicleId}-segment-${idx}`}
                directions={segment}
                options={{
                  suppressMarkers: true,
                  polylineOptions: {
                    strokeColor: rd.color,
                    strokeOpacity: 0.9,
                    strokeWeight: 5,
                  },
                  preserveViewport: true,
                }}
              />
            ))
          )}

        {/* Depot Marker - Larger size, higher zIndex */}
        {stops.length > 0 && (
          <Marker
            key={`depot-${stops[0].lat}-${stops[0].lng}`}
            position={{ lat: stops[0].lat, lng: stops[0].lng }}
            icon={{
              url: `data:image/svg+xml,${encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" fill="#76B900" stroke="white" stroke-width="2"/>
                  <text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">D</text>
                </svg>
              `)}`,
              scaledSize: new google.maps.Size(24, 24),
              anchor: new google.maps.Point(12, 12),
            }}
            title="Depot"
            onClick={() => setSelectedMarker(0)}
            zIndex={9999}
          />
        )}

        {/* Stop Markers with Weather Indicators - Larger size for visibility */}
        {stops.slice(1).map((stop) => {
          // Find which route this stop belongs to (check both by ID and by index)
          const stopIndex = stops.indexOf(stop);
          const assignedRoute = routes.find((r) =>
            r.route.includes(stop.id) || r.route.includes(stopIndex)
          );
          const isAssigned = !!assignedRoute;
          const routeColor = assignedRoute ? getVehicleColor(assignedRoute.vehicle_id).color : '#9CA3AF';
          const isEVStation = !!(stop as any).metadata?.networkName;
          const stopWeather = weatherData.get(stop.id);
          const weatherLevel = stopWeather?.assessment.level || 'none';

          // Unassigned stops: gray with lower opacity and smaller size
          // Assigned stops: route color or weather color if showing weather
          const markerColor = !isAssigned
            ? '#9CA3AF' // Gray for unassigned
            : showWeather && weatherLevel !== 'none' && weatherLevel !== 'low'
              ? WEATHER_SEVERITY_COLORS[weatherLevel]
              : isEVStation
                ? '#22C55E'
                : routeColor;

          // Add weather icon to label if weather is bad
          const weatherIcon = showWeather && stopWeather ? getWeatherIcon(stopWeather.weather) : '';
          const unassignedLabel = !isAssigned && routes.length > 0 ? '⚠️ UNASSIGNED - ' : '';
          const markerTitle = weatherIcon
            ? `${unassignedLabel}${weatherIcon} ${stop.label || `Stop ${stop.id}`}`
            : `${unassignedLabel}${stop.label || `Stop ${stop.id}`}`;

          return (
            <Marker
              key={`stop-${stop.id}-${stop.lat.toFixed(4)}-${stop.lng.toFixed(4)}`}
              position={{ lat: stop.lat, lng: stop.lng }}
              icon={{
                url: `data:image/svg+xml,${encodeURIComponent(`
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
                    <circle cx="10" cy="10" r="8" fill="${markerColor}" stroke="white" stroke-width="2"/>
                  </svg>
                `)}`,
                scaledSize: new google.maps.Size(20, 20),
                anchor: new google.maps.Point(10, 10),
              }}
              title={markerTitle}
              onClick={() => setSelectedMarker(stop.id)}
              zIndex={5000 + stop.id}
            />
          );
        })}

        {/* Info Window for selected marker */}
        {selectedMarker !== null && (
          <InfoWindow
            position={
              selectedMarker === 0
                ? { lat: stops[0].lat, lng: stops[0].lng }
                : (() => {
                    const stop = stops.find((s) => s.id === selectedMarker);
                    return stop ? { lat: stop.lat, lng: stop.lng } : center;
                  })()
            }
            onCloseClick={() => setSelectedMarker(null)}
          >
            <div className="p-2 min-w-[160px]">
              {selectedMarker === 0 ? (
                <>
                  <div className="font-semibold text-gray-900 flex items-center gap-2">
                    <span className="bg-green-600 text-white text-[10px] px-2 py-0.5 rounded">
                      DEPOT
                    </span>
                    Fleet Base
                  </div>
                  <div className="text-xs text-gray-600 mt-2">
                    <div className="flex justify-between">
                      <span>Latitude:</span>
                      <span className="font-mono">{stops[0].lat.toFixed(5)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Longitude:</span>
                      <span className="font-mono">{stops[0].lng.toFixed(5)}</span>
                    </div>
                  </div>
                </>
              ) : (
                (() => {
                  const stop = stops.find((s) => s.id === selectedMarker);
                  if (!stop) return null;
                  const assignedRoute = routes.find((r) => r.route.includes(stop.id));
                  const isEVStation = !!(stop as any).metadata?.networkName;
                  const metadata = (stop as any).metadata;
                  const stopWeather = weatherData.get(stop.id);

                  return (
                    <>
                      <div className="font-semibold text-gray-900 flex items-center gap-2">
                        {isEVStation && (
                          <span className="bg-green-500 text-white text-[10px] px-2 py-0.5 rounded">
                            EV
                          </span>
                        )}
                        {stopWeather && showWeather && (
                          <span className="text-lg">{getWeatherIcon(stopWeather.weather)}</span>
                        )}
                        {stop.label || `Stop ${stop.id}`}
                      </div>
                      <div className="text-xs text-gray-600 mt-2 space-y-1">
                        {stop.postcode && (
                          <div className="flex justify-between">
                            <span>Postcode:</span>
                            <span className="font-medium">{stop.postcode}</span>
                          </div>
                        )}

                        {/* Weather Information */}
                        {stopWeather && showWeather && (
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <div className="font-medium text-gray-700 mb-1">Weather Conditions</div>
                            <div className="flex justify-between">
                              <span>Temperature:</span>
                              <span className="font-medium">{Math.round(stopWeather.weather.current.temperature)}°C</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Conditions:</span>
                              <span>{stopWeather.weather.current.conditions[0]?.description || 'Clear'}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Wind:</span>
                              <span>{Math.round(stopWeather.weather.current.windSpeed * 2.237)} mph</span>
                            </div>
                            {stopWeather.weather.current.rain1h && (
                              <div className="flex justify-between">
                                <span>Rain:</span>
                                <span>{stopWeather.weather.current.rain1h} mm/h</span>
                              </div>
                            )}
                            {stopWeather.assessment.level !== 'none' && (
                              <div
                                className="mt-1 px-2 py-1 rounded text-white text-center font-medium"
                                style={{ backgroundColor: WEATHER_SEVERITY_COLORS[stopWeather.assessment.level] }}
                              >
                                {stopWeather.assessment.level === 'low' && 'Minor Impact'}
                                {stopWeather.assessment.level === 'moderate' && 'Moderate Delay'}
                                {stopWeather.assessment.level === 'high' && 'High Risk'}
                                {stopWeather.assessment.level === 'severe' && 'SEVERE CONDITIONS'}
                                {' '}(+{Math.round((stopWeather.assessment.travelTimeMultiplier - 1) * 100)}% time)
                              </div>
                            )}
                            {stopWeather.assessment.factors.length > 0 && (
                              <div className="mt-1 text-[10px] text-gray-500">
                                {stopWeather.assessment.factors.map((f, i) => (
                                  <div key={i}>• {f.description}</div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {isEVStation && metadata && (
                          <>
                            <div className="flex justify-between">
                              <span>Network:</span>
                              <span>{metadata.networkName}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Power:</span>
                              <span>{metadata.powerGroup}</span>
                            </div>
                          </>
                        )}
                        <div className="flex justify-between">
                          <span>Demand:</span>
                          <span className="font-medium">{stop.demand} units</span>
                        </div>
                        {assignedRoute && (
                          <div
                            className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-2"
                            style={{ color: getVehicleColor(assignedRoute.vehicle_id).color }}
                          >
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor: getVehicleColor(assignedRoute.vehicle_id).color,
                              }}
                            />
                            <span className="font-mono font-semibold">
                              {formatVehicleName(assignedRoute.vehicle_id)}
                            </span>
                          </div>
                        )}
                      </div>
                    </>
                  );
                })()
              )}
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
    </div>
  );
}
