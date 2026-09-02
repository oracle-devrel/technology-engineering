import { useMemo } from 'react';
import { Marker, Popup, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import type { StateVector } from '@/types/opensky';

interface AircraftMarkerProps {
  aircraft: StateVector;
  showTooltip?: boolean;
}

export function AircraftMarker({ aircraft, showTooltip = true }: AircraftMarkerProps) {
  const icon = useMemo(() => {
    const rotation = aircraft.true_track ?? 0;
    const altitude = aircraft.baro_altitude ?? aircraft.geo_altitude ?? 0;

    let color = '#22c55e';
    if (altitude > 10000) color = '#ef4444';
    else if (altitude > 5000) color = '#f59e0b';
    else if (altitude > 1000) color = '#3b82f6';

    const svgIcon = `
      <svg width="28" height="28" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
        <g transform="rotate(${rotation} 14 14)">
          <path
            d="M14 2
               L16 9
               L24 11
               L24 13
               L16 13
               L14.8 18
               L18.5 21.5
               L18.5 23
               L14 21
               L9.5 23
               L9.5 21.5
               L13.2 18
               L12 13
               L4 13
               L4 11
               L12 9
               Z"
            fill="${color}"
            stroke="#ffffff"
            stroke-width="1.2"
            stroke-linejoin="round"
          />
          <path d="M14 4 L14 20" stroke="#ffffff" stroke-width="0.9" opacity="0.7" />
          <ellipse cx="14" cy="3.2" rx="1.2" ry="1.2" fill="#ffffff" opacity="0.85" />
        </g>
      </svg>
    `;

    return L.divIcon({
      html: svgIcon,
      className: 'aircraft-marker',
      iconSize: [28, 28],
      iconAnchor: [14, 14],
    });
  }, [aircraft.true_track, aircraft.baro_altitude, aircraft.geo_altitude]);

  const position: [number, number] = [aircraft.latitude, aircraft.longitude];
  const altitude = aircraft.baro_altitude ?? aircraft.geo_altitude ?? 0;
  const altitudeStr =
    altitude > 0
      ? `${Math.round(altitude)}m (${Math.round(altitude * 3.28084)}ft)`
      : 'Ground';
  const speedKmh = Math.round((aircraft.velocity ?? 0) * 3.6);
  const speedKnots = Math.round((aircraft.velocity ?? 0) * 1.94384);
  const heading = Math.round(aircraft.true_track ?? 0);

  return (
    <Marker position={position} icon={icon}>
      {showTooltip && (
        <Tooltip permanent={false} direction="top">
          <div className="font-mono text-xs">{aircraft.callsign || aircraft.icao24}</div>
        </Tooltip>
      )}
      <Popup>
        <div className="space-y-1">
          <div className="text-base font-bold">{aircraft.callsign || 'Unknown'}</div>
          <div className="space-y-0.5 text-xs">
            <div>
              <strong>ICAO24:</strong> {aircraft.icao24}
            </div>
            <div>
              <strong>Country:</strong> {aircraft.origin_country}
            </div>
            <div>
              <strong>Altitude:</strong> {altitudeStr}
            </div>
            <div>
              <strong>Speed:</strong> {speedKmh} km/h ({speedKnots} kt)
            </div>
            <div>
              <strong>Heading:</strong> {heading} deg
            </div>
            {aircraft.vertical_rate !== null && (
              <div>
                <strong>Vertical Rate:</strong> {aircraft.vertical_rate > 0 ? 'UP' : 'DOWN'}{' '}
                {Math.abs(Math.round(aircraft.vertical_rate))} m/s
              </div>
            )}
            <div>
              <strong>On Ground:</strong> {aircraft.on_ground ? 'Yes' : 'No'}
            </div>
            <div className="mt-1 text-gray-500">
              Last update: {new Date(aircraft.last_contact * 1000).toLocaleTimeString()}
            </div>
          </div>
        </div>
      </Popup>
    </Marker>
  );
}
