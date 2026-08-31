import { useMemo, useState } from 'react';
import { AirTrafficMap } from './AirTrafficMap';
import { MarkdownContent } from '@/components/shared';
import { cuoptClient, genaiClient } from '@/api';
import type { BoundingBox, StateVector } from '@/types/opensky';
import type { Message } from '@/types';
import type { Stop, Vehicle, CuOptResponse } from '@/types';
import type { AirTrafficSnapshot } from './AirTrafficMap';

interface RegionOption {
  name: string;
  bbox?: BoundingBox;
}

const REGIONS: RegionOption[] = [
  { name: 'New York', bbox: { lamin: 40.5, lomin: -74.5, lamax: 41.0, lomax: -73.5 } },
  { name: 'Dubai', bbox: { lamin: 24.8, lomin: 54.9, lamax: 25.4, lomax: 55.6 } },
  { name: 'Tokyo', bbox: { lamin: 35.4, lomin: 139.4, lamax: 36.0, lomax: 140.1 } },
];

interface CityAirport {
  icao: string;
  iata: string;
  name: string;
  lat: number;
  lng: number;
  baseSlotsPerHour: number;
}

interface MetarRecord {
  icaoId?: string;
  wspd?: number | string;
  wgst?: number | string | null;
  visib?: number | string;
  weather?: string;
  rawOb?: string;
  dataSource?: string;
  fallbackReason?: string;
}

interface SequencedAssignment {
  callsign: string;
  airportIcao: string;
  airportIata: string;
  airportName: string;
  distanceKm: number;
  etaMin: number;
  altitudeM: number;
  speedKmh: number;
}

interface SequencingRunResult {
  mode: 'cuopt' | 'greedy-fallback';
  message: string;
  consideredAircraft: number;
  assignedAircraft: number;
  unassignedAircraft: number;
  totalSlots: number;
  averageEtaMin: number;
  assignments: SequencedAssignment[];
  airportWeatherSummary: Array<{
    icao: string;
    iata: string;
    name: string;
    weatherFactor: number;
    effectiveSlots: number;
    source: string;
    weatherText: string;
  }>;
}

const CITY_AIRPORTS: Record<string, CityAirport[]> = {
  'New York': [
    { icao: 'KJFK', iata: 'JFK', name: 'John F. Kennedy', lat: 40.6413, lng: -73.7781, baseSlotsPerHour: 12 },
    { icao: 'KLGA', iata: 'LGA', name: 'LaGuardia', lat: 40.7769, lng: -73.874, baseSlotsPerHour: 10 },
    { icao: 'KEWR', iata: 'EWR', name: 'Newark Liberty', lat: 40.6895, lng: -74.1745, baseSlotsPerHour: 10 },
  ],
  Dubai: [
    { icao: 'OMDB', iata: 'DXB', name: 'Dubai International', lat: 25.2532, lng: 55.3657, baseSlotsPerHour: 14 },
    { icao: 'OMDW', iata: 'DWC', name: 'Al Maktoum International', lat: 24.8964, lng: 55.1614, baseSlotsPerHour: 8 },
  ],
  Tokyo: [
    { icao: 'RJTT', iata: 'HND', name: 'Haneda', lat: 35.5494, lng: 139.7798, baseSlotsPerHour: 16 },
    { icao: 'RJAA', iata: 'NRT', name: 'Narita', lat: 35.7719, lng: 140.3929, baseSlotsPerHour: 12 },
  ],
};

function toNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function parseVisibilityMeters(visib: unknown): number {
  if (typeof visib === 'number' && Number.isFinite(visib)) {
    return visib;
  }
  if (typeof visib !== 'string') {
    return 10000;
  }

  const normalized = visib.trim().toUpperCase();
  if (normalized === '10+' || normalized === '9999') {
    return 10000;
  }

  const numeric = Number(normalized);
  if (Number.isFinite(numeric)) {
    return numeric > 100 ? numeric : numeric * 1609;
  }

  if (normalized.endsWith('SM')) {
    const miles = Number(normalized.replace('SM', '').trim());
    if (Number.isFinite(miles)) {
      return Math.round(miles * 1609.34);
    }
  }

  return 10000;
}

function computeWeatherFactor(metar?: MetarRecord): number {
  if (!metar) {
    return 0.75;
  }

  let factor = 1;
  const visibility = parseVisibilityMeters(metar.visib);
  const windKts = Math.max(toNumber(metar.wspd, 0), toNumber(metar.wgst, 0));
  const wx = `${metar.weather || ''} ${metar.rawOb || ''}`.toUpperCase();

  if (visibility < 5000) factor -= 0.25;
  if (visibility < 2000) factor -= 0.2;
  if (windKts > 20) factor -= 0.15;
  if (windKts > 30) factor -= 0.2;
  if (wx.includes('TS') || wx.includes('THUNDER')) factor -= 0.3;
  if (wx.includes('SN') || wx.includes('FZ') || wx.includes('FG')) factor -= 0.2;
  if (wx.includes('RA')) factor -= 0.1;

  return Math.max(0.35, Math.min(1, factor));
}

function formatWeatherText(metar?: MetarRecord): string {
  if (!metar) {
    return 'No METAR available';
  }

  const vis = metar.visib ?? 'N/A';
  const wind = `Wind ${toNumber(metar.wspd, 0)}kt`;
  const weather = metar.weather && String(metar.weather).trim().length > 0
    ? String(metar.weather).trim()
    : 'No significant weather';

  return `${weather} | ${wind} | Vis ${vis}`;
}

function haversineKm(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) * Math.cos((lat2 * Math.PI) / 180) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function AirTrafficDashboard() {
  const [selectedRegion, setSelectedRegion] = useState<RegionOption>(REGIONS[0]);
  const [aircraftCount, setAircraftCount] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [dataSource, setDataSource] = useState<'api' | 'fallback'>('api');
  const [fallbackReason, setFallbackReason] = useState<string | null>(null);
  const [airTrafficSnapshot, setAirTrafficSnapshot] = useState<AirTrafficSnapshot>({
    states: [],
    dataSource: 'api',
    fetchedAt: Math.floor(Date.now() / 1000),
  });
  const [question, setQuestion] = useState('');
  const [isAsking, setIsAsking] = useState(false);
  const [qaError, setQaError] = useState<string | null>(null);
  const [qaMessages, setQaMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [isSequencing, setIsSequencing] = useState(false);
  const [sequencingError, setSequencingError] = useState<string | null>(null);
  const [sequencingResult, setSequencingResult] = useState<SequencingRunResult | null>(null);

  const aircraftSummary = useMemo(() => {
    const states = airTrafficSnapshot.states;
    if (states.length === 0) {
      return {
        averageAltitudeM: 0,
        averageSpeedKmh: 0,
        topCountries: [] as string[],
      };
    }

    const averageAltitudeM = Math.round(
      states.reduce((sum, s) => sum + (s.baro_altitude ?? s.geo_altitude ?? 0), 0) / states.length
    );
    const averageSpeedKmh = Math.round(
      states.reduce((sum, s) => sum + ((s.velocity ?? 0) * 3.6), 0) / states.length
    );
    const countryCounts = states.reduce((acc, s) => {
      const country = s.origin_country || 'Unknown';
      acc[country] = (acc[country] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    const topCountries = Object.entries(countryCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([country]) => country);

    return { averageAltitudeM, averageSpeedKmh, topCountries };
  }, [airTrafficSnapshot.states]);

  const handleRunSequencing = async () => {
    if (isSequencing) {
      return;
    }

    setIsSequencing(true);
    setSequencingError(null);
    setSequencingResult(null);

    try {
      const cityAirports = CITY_AIRPORTS[selectedRegion.name] || [];
      if (cityAirports.length === 0) {
        throw new Error(`No airport configuration found for ${selectedRegion.name}`);
      }

      const weatherResp = await fetch(
        `/api/aviationweather/metar?ids=${encodeURIComponent(cityAirports.map((a) => a.icao).join(','))}`
      );
      const weatherJson = (await weatherResp.json()) as {
        metars?: MetarRecord[];
        dataSource?: string;
      };
      const metars = weatherJson.metars || [];
      const metarByIcao = new Map(
        metars.map((m) => [String(m.icaoId || '').toUpperCase(), m])
      );

      const airportsWithCapacity = cityAirports.map((airport) => {
        const metar = metarByIcao.get(airport.icao);
        const weatherFactor = computeWeatherFactor(metar);
        const effectiveSlots = Math.max(1, Math.round(airport.baseSlotsPerHour * weatherFactor));
        return {
          ...airport,
          weatherFactor,
          effectiveSlots,
          metar,
          source: metar?.dataSource || weatherJson.dataSource || 'unknown',
        };
      });

      const totalSlots = airportsWithCapacity.reduce((sum, a) => sum + a.effectiveSlots, 0);
      const activeAircraft = airTrafficSnapshot.states.filter((s) => {
        const altitude = s.baro_altitude ?? s.geo_altitude ?? 0;
        return !s.on_ground && altitude > 300;
      });

      if (activeAircraft.length === 0) {
        throw new Error('No airborne aircraft available in current map window.');
      }

      const consideredAircraft = activeAircraft.slice(0, Math.min(30, Math.max(totalSlots * 2, 10)));

      const slots: Array<{ vehicleId: number; airportIcao: string; airportName: string; lat: number; lng: number }> = [];
      let vehicleId = 0;
      airportsWithCapacity.forEach((airport) => {
        for (let i = 0; i < airport.effectiveSlots; i++) {
          slots.push({
            vehicleId: vehicleId++,
            airportIcao: airport.icao,
            airportName: airport.name,
            lat: airport.lat,
            lng: airport.lng,
          });
        }
      });

      const stops: Stop[] = consideredAircraft.map((ac, idx) => ({
        id: idx + 1,
        lat: ac.latitude,
        lng: ac.longitude,
        demand: 1,
        label: ac.callsign || ac.icao24,
      }));

      const vehicles: Vehicle[] = slots.map((slot) => ({
        id: slot.vehicleId,
        capacity: 1,
        startLat: slot.lat,
        startLng: slot.lng,
      }));

      let runMode: SequencingRunResult['mode'] = 'cuopt';
      let assignments: SequencedAssignment[] = [];

      try {
        const payload = cuoptClient.buildPayload(stops, vehicles, {
          numVehicles: vehicles.length,
          vehicleCapacity: 1,
          timeLimit: 20,
          objective: 'minimize_distance',
          enableTimeWindows: false,
          enableCapacity: true,
          parallelJobs: 1,
          parallelMode: 'single',
          solverMode: 'speed',
          enableHomeStart: true,
          returnToDepot: false,
          enforceShiftLimits: false,
        });

        const result: CuOptResponse = await cuoptClient.solveVRP(payload);
        const slotByVehicle = new Map(slots.map((s) => [s.vehicleId, s]));
        const assignedKeys = new Set<string>();

        assignments = (result.vehicle_data || [])
          .map((vehicle) => {
            const taskId = (vehicle.route || []).find((id) => id > 0);
            if (!taskId) return null;

            const aircraft = consideredAircraft[taskId - 1];
            const slot =
              slotByVehicle.get(vehicle.vehicle_id) ||
              slotByVehicle.get(vehicle.vehicle_id - 1) ||
              slotByVehicle.get(vehicle.vehicle_id + 1);
            if (!aircraft || !slot) return null;

            const key = aircraft.icao24 || `${aircraft.latitude}-${aircraft.longitude}`;
            if (assignedKeys.has(key)) return null;
            assignedKeys.add(key);

            const distanceKm = haversineKm(aircraft.latitude, aircraft.longitude, slot.lat, slot.lng);
            const speedKmh = Math.max(220, (aircraft.velocity ?? 0) * 3.6);
            const etaMin = Math.round((distanceKm / speedKmh) * 60);

            return {
              callsign: aircraft.callsign || aircraft.icao24,
              airportIcao: slot.airportIcao,
              airportIata: (cityAirports.find((a) => a.icao === slot.airportIcao)?.iata || ''),
              airportName: slot.airportName,
              distanceKm: Number(distanceKm.toFixed(1)),
              etaMin: Math.max(1, etaMin),
              altitudeM: Math.round(aircraft.baro_altitude ?? aircraft.geo_altitude ?? 0),
              speedKmh: Math.round((aircraft.velocity ?? 0) * 3.6),
            };
          })
          .filter((a): a is SequencedAssignment => a !== null);
      } catch (solverError) {
        runMode = 'greedy-fallback';
        console.warn('[Arrival Sequencing] cuOpt failed, using greedy fallback:', solverError);

        const availableSlots = [...slots];
        assignments = consideredAircraft
          .slice(0, availableSlots.length)
          .map((aircraft) => {
            let nearestIdx = 0;
            let nearestDist = Infinity;
            availableSlots.forEach((slot, idx) => {
              const d = haversineKm(aircraft.latitude, aircraft.longitude, slot.lat, slot.lng);
              if (d < nearestDist) {
                nearestDist = d;
                nearestIdx = idx;
              }
            });
            const slot = availableSlots.splice(nearestIdx, 1)[0];
            const speedKmh = Math.max(220, (aircraft.velocity ?? 0) * 3.6);
            const etaMin = Math.round((nearestDist / speedKmh) * 60);

            return {
              callsign: aircraft.callsign || aircraft.icao24,
              airportIcao: slot.airportIcao,
              airportIata: (cityAirports.find((a) => a.icao === slot.airportIcao)?.iata || ''),
              airportName: slot.airportName,
              distanceKm: Number(nearestDist.toFixed(1)),
              etaMin: Math.max(1, etaMin),
              altitudeM: Math.round(aircraft.baro_altitude ?? aircraft.geo_altitude ?? 0),
              speedKmh: Math.round((aircraft.velocity ?? 0) * 3.6),
            };
          });
      }

      const averageEtaMin =
        assignments.length > 0
          ? Math.round(assignments.reduce((sum, a) => sum + a.etaMin, 0) / assignments.length)
          : 0;

      setSequencingResult({
        mode: runMode,
        message:
          runMode === 'cuopt'
            ? 'Weather-aware arrival sequencing completed with cuOpt.'
            : 'cuOpt unavailable; used greedy fallback sequencing.',
        consideredAircraft: consideredAircraft.length,
        assignedAircraft: assignments.length,
        unassignedAircraft: Math.max(0, consideredAircraft.length - assignments.length),
        totalSlots,
        averageEtaMin,
        assignments: assignments.sort((a, b) => a.etaMin - b.etaMin),
        airportWeatherSummary: airportsWithCapacity.map((a) => ({
          icao: a.icao,
          iata: a.iata,
          name: a.name,
          weatherFactor: Number(a.weatherFactor.toFixed(2)),
          effectiveSlots: a.effectiveSlots,
          source: String(a.source),
          weatherText: formatWeatherText(a.metar),
        })),
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to run arrival sequencing';
      setSequencingError(message);
    } finally {
      setIsSequencing(false);
    }
  };

  const handleAskQuestion = async () => {
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || isAsking) {
      return;
    }

    setIsAsking(true);
    setQaError(null);
    setQaMessages((prev) => [...prev, { role: 'user', content: trimmedQuestion }]);

    try {
      const sampleAircraft = airTrafficSnapshot.states.slice(0, 20).map((s: StateVector) => ({
        callsign: s.callsign || s.icao24,
        icao24: s.icao24,
        country: s.origin_country,
        latitude: s.latitude,
        longitude: s.longitude,
        altitude_m: s.baro_altitude ?? s.geo_altitude ?? 0,
        speed_kmh: Math.round((s.velocity ?? 0) * 3.6),
        heading_deg: Math.round(s.true_track ?? 0),
      }));

      const airTrafficContext = {
        region: selectedRegion.name,
        bbox: selectedRegion.bbox ?? null,
        aircraftCount: airTrafficSnapshot.states.length,
        fetchedAt: new Date(airTrafficSnapshot.fetchedAt * 1000).toISOString(),
        dataSource: airTrafficSnapshot.dataSource,
        fallbackReason: airTrafficSnapshot.fallbackReason || null,
        summary: {
          averageAltitudeM: aircraftSummary.averageAltitudeM,
          averageSpeedKmh: aircraftSummary.averageSpeedKmh,
          topCountries: aircraftSummary.topCountries,
        },
        arrivalSequencing: sequencingResult
          ? {
              mode: sequencingResult.mode,
              assignedAircraft: sequencingResult.assignedAircraft,
              unassignedAircraft: sequencingResult.unassignedAircraft,
              averageEtaMin: sequencingResult.averageEtaMin,
              totalSlots: sequencingResult.totalSlots,
            }
          : null,
        sampleAircraft,
      };

      const systemPrompt = `You are an air traffic Q&A assistant.
Answer user questions using the provided live map context and aircraft snapshot.
If dataSource is "fallback", explicitly mention the answer is based on fallback/simulated aircraft data.
Be concise and operationally useful.

RESPONSE FORMAT (use these exact markdown headings in this exact order):
### Summary
- 2-4 short bullet points answering the question directly.

### Key Insights
- 2-5 bullets with numeric observations from the provided context when possible.

### Actionable Notes
- 1-3 bullets with practical next checks or decisions for operations.

### Data Notice
- One short line:
  - If dataSource is "api": "Data source: Live OpenSky API data."
  - If dataSource is "fallback": "Data source: Fallback/simulated aircraft data due to OpenSky unavailability."

RULES:
- Do not invent aircraft not present in the provided context.
- If context is insufficient, say so clearly in Summary.
- Keep total response under 220 words.

AIR_TRAFFIC_CONTEXT_JSON:
${JSON.stringify(airTrafficContext)}`;

      const messageHistory: Message[] = [
        ...qaMessages.slice(-6).map((m, index) => ({
          id: `air-qa-${Date.now()}-${index}`,
          role: m.role,
          content: m.content,
          timestamp: new Date(),
        })),
        {
          id: `air-qa-${Date.now()}-user`,
          role: 'user',
          content: trimmedQuestion,
          timestamp: new Date(),
        },
      ];

      const response = await genaiClient.chat(messageHistory, systemPrompt);
      setQaMessages((prev) => [...prev, { role: 'assistant', content: response.content }]);
      setQuestion('');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Failed to get response';
      setQaError(message);
      setQaMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${message}` }]);
    } finally {
      setIsAsking(false);
    }
  };

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-gray-900 text-white">
      <div className="flex items-center justify-between border-b border-gray-700 bg-gray-800 px-6 py-4">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Live Air Traffic</h1>
          <div className="flex items-center gap-2 rounded-lg border border-green-600/50 bg-green-600/20 px-3 py-1">
            <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
            <span className="text-sm font-medium">LIVE</span>
          </div>
          <div
            title={dataSource === 'fallback' && fallbackReason ? fallbackReason : 'Live OpenSky API data'}
            className={`flex items-center gap-2 rounded-lg px-3 py-1 text-sm font-medium border ${
              dataSource === 'fallback'
                ? 'border-amber-600/50 bg-amber-600/20 text-amber-300'
                : 'border-emerald-600/50 bg-emerald-600/20 text-emerald-300'
            }`}
          >
            <span>{dataSource === 'fallback' ? 'FALLBACK' : 'API'}</span>
          </div>
        </div>

        <label className="flex cursor-pointer items-center gap-2">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="h-4 w-4"
          />
          <span className="text-sm">Auto-refresh (10s)</span>
        </label>
      </div>

      <div className="flex items-center gap-4 border-b border-gray-700 bg-gray-800/50 px-6 py-3">
        <label className="text-sm font-medium">Region:</label>
        <div className="flex gap-2">
          {REGIONS.map((region) => (
            <button
              key={region.name}
              type="button"
              onClick={() => setSelectedRegion(region)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                selectedRegion.name === region.name
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {region.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-6 border-b border-gray-700 bg-gray-800/30 px-6 py-3">
        <div className="flex flex-col">
          <span className="text-xs text-gray-400">Aircraft Visible</span>
          <span className="text-2xl font-bold text-green-400">{aircraftCount}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-400">Region</span>
          <span className="text-lg font-semibold">{selectedRegion.name}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-xs text-gray-400">Data Source</span>
          <span className="text-sm">
            {dataSource === 'fallback' ? 'Fallback Dataset' : 'OpenSky Network'}
          </span>
        </div>
      </div>

      <div className="flex-1 p-4">
        <div className="grid min-h-full grid-rows-[minmax(380px,1fr)_auto] gap-4">
          <AirTrafficMap
            bbox={selectedRegion.bbox}
            autoRefresh={autoRefresh}
            refreshInterval={10}
            onAircraftCountChange={setAircraftCount}
            onDataSourceChange={(source, reason) => {
              setDataSource(source);
              setFallbackReason(reason || null);
            }}
            onAircraftSnapshotChange={setAirTrafficSnapshot}
          />

          <div className="rounded-lg border border-gray-700 bg-gray-800/70 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-white">Air Traffic Q&A</h3>
              <span className="text-xs text-gray-400">
                Context: {airTrafficSnapshot.states.length} aircraft ({dataSource.toUpperCase()})
              </span>
            </div>

            <div className="mb-3 max-h-40 space-y-2 overflow-y-auto pr-1">
              {qaMessages.length === 0 ? (
                <p className="text-sm text-gray-400">
                  Ask questions about the aircraft currently shown on the map.
                </p>
              ) : (
                qaMessages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`rounded-md px-3 py-2 text-sm ${
                      m.role === 'user'
                        ? 'ml-8 bg-blue-600/20 text-blue-100 border border-blue-500/30'
                        : 'mr-8 bg-gray-700/60 text-gray-100 border border-gray-600'
                    }`}
                  >
                    {m.role === 'assistant' ? (
                      <MarkdownContent content={m.content} />
                    ) : (
                      <span className="whitespace-pre-wrap">{m.content}</span>
                    )}
                  </div>
                ))
              )}
            </div>

            <div className="flex items-center gap-2">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleAskQuestion();
                  }
                }}
                placeholder="Ask about aircraft on the current map (e.g., busiest corridors, altitude trends)"
                rows={3}
                className="w-full rounded-md border border-gray-600 bg-gray-900 px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:border-green-500 focus:outline-none resize-y"
              />
              <button
                type="button"
                onClick={handleAskQuestion}
                disabled={isAsking || !question.trim()}
                className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:cursor-not-allowed disabled:bg-gray-600"
              >
                {isAsking ? 'Asking...' : 'Ask'}
              </button>
            </div>
            {qaError && <div className="mt-2 text-xs text-red-400">{qaError}</div>}

            <div className="mt-4 border-t border-gray-700 pt-4">
              <div className="mb-2 flex items-center justify-between">
                <h4 className="text-sm font-semibold text-white">cuOpt Arrival Sequencing</h4>
                <button
                  type="button"
                  onClick={handleRunSequencing}
                  disabled={isSequencing || airTrafficSnapshot.states.length === 0}
                  className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-gray-600"
                >
                  {isSequencing ? 'Running...' : 'Run Weather-Aware Sequencing'}
                </button>
              </div>
              <p className="text-xs text-gray-400">
                Assigns visible airborne aircraft to city airports using weather-adjusted slot capacity.
              </p>
              {sequencingError && <div className="mt-2 text-xs text-red-400">{sequencingError}</div>}

              {sequencingResult && (
                <div className="mt-3 space-y-3">
                  <div className="rounded-md border border-gray-700 bg-gray-900/70 px-3 py-2 text-xs text-gray-200">
                    <div>
                      <strong>Mode:</strong> {sequencingResult.mode === 'cuopt' ? 'cuOpt' : 'Greedy Fallback'}
                    </div>
                    <div>
                      <strong>Aircraft:</strong> {sequencingResult.assignedAircraft}/{sequencingResult.consideredAircraft} assigned
                    </div>
                    <div>
                      <strong>Unassigned:</strong> {sequencingResult.unassignedAircraft}
                    </div>
                    <div>
                      <strong>Avg ETA:</strong> {sequencingResult.averageEtaMin} min
                    </div>
                    <div>
                      <strong>Slots:</strong> {sequencingResult.totalSlots}
                    </div>
                  </div>

                  <div className="rounded-md border border-gray-700 bg-gray-900/70 p-2">
                    <div className="mb-1 text-xs font-medium text-gray-300">Airport Weather / Capacity</div>
                    <div className="space-y-1 text-xs text-gray-200">
                      {sequencingResult.airportWeatherSummary.map((a) => (
                        <div key={a.icao} className="rounded border border-gray-700 bg-gray-800/40 px-2 py-1">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{a.icao} ({a.iata}) - {a.name}</span>
                            <span>Factor {a.weatherFactor} | Slots {a.effectiveSlots} | {a.source}</span>
                          </div>
                          <div className="mt-0.5 text-gray-300">{a.weatherText}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-md border border-gray-700 bg-gray-900/70 p-2">
                    <div className="mb-1 text-xs font-medium text-gray-300">Top Assignments</div>
                    <div className="max-h-28 space-y-1 overflow-y-auto pb-3 pr-1 text-xs text-gray-100">
                      {sequencingResult.assignments.slice(0, 8).map((a, idx) => (
                        <div key={`${a.callsign}-${idx}`} className="flex items-center justify-between gap-3">
                          <span className="font-mono">{a.callsign}</span>
                          <span>{a.airportIcao} ({a.airportIata}) - {a.airportName}</span>
                          <span>{a.etaMin}m</span>
                          <span>{a.distanceKm}km</span>
                        </div>
                      ))}
                      {sequencingResult.assignments.length === 0 && (
                        <div className="text-gray-400">No assignments produced.</div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-700 bg-gray-800 px-6 py-3 text-xs text-gray-400">
        Data provided by{' '}
        <a
          href="https://opensky-network.org"
          target="_blank"
          rel="noopener noreferrer"
          className="text-green-400 hover:underline"
        >
          OpenSky Network
        </a>{' '}
        | Updates every 10 seconds | Coverage: Global ADS-B receivers
      </div>
    </div>
  );
}
