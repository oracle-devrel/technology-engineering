import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import * as common from 'oci-common';
import * as genai from 'oci-generativeaiinference';

// Load .env from the frontend application root
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ============ cuOPT Configuration ============
const cuoptEndpoint = process.env.CUOPT_ENDPOINT || 'https://cuopt-2-cuopt.137-131-27-21.nip.io';

// cuOPT health check
app.get('/api/cuopt/health', async (req, res) => {
  try {
    console.log('[cuOPT] Health check...');
    const response = await fetch(`${cuoptEndpoint}/cuopt/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await response.text();
    console.log('[cuOPT] Health response:', response.status);
    res.status(response.status).send(data);
  } catch (error) {
    console.error('[cuOPT] Health error:', error.message);
    res.status(503).json({ status: 'disconnected', error: error.message });
  }
});

// cuOPT submit request
app.post('/api/cuopt/request', async (req, res) => {
  try {
    console.log('[cuOPT] Submitting optimization request...');
    console.log('[cuOPT] Payload keys:', Object.keys(req.body));
    console.log('[cuOPT] Fleet data:', JSON.stringify(req.body.fleet_data, null, 2));
    const response = await fetch(`${cuoptEndpoint}/cuopt/request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req.body),
    });
    const data = await response.json();
    console.log('[cuOPT] Submit response:', response.status, data);
    res.status(response.status).json(data);
  } catch (error) {
    console.error('[cuOPT] Submit error:', error.message);
    res.status(500).json({ error: 'cuOPT request failed', message: error.message });
  }
});

// cuOPT get solution
app.get('/api/cuopt/solution/:reqId', async (req, res) => {
  try {
    const { reqId } = req.params;
    const response = await fetch(`${cuoptEndpoint}/cuopt/solution/${reqId}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await response.json();

    // Log full response when there's an error or a completed response
    if (data.error || data.response) {
      console.log('[cuOPT] Full solution data:', JSON.stringify(data, null, 2));
    }

    res.status(response.status).json(data);
  } catch (error) {
    console.error('[cuOPT] Solution error:', error.message);
    res.status(500).json({ error: 'cuOPT solution failed', message: error.message });
  }
});

// cuOPT health check (alternate endpoint)
app.get('/api/cuopt-health', async (req, res) => {
  try {
    const response = await fetch(`${cuoptEndpoint}/cuopt/health`);
    if (response.ok) {
      res.json({ status: 'connected', endpoint: cuoptEndpoint });
    } else {
      res.status(503).json({ status: 'unavailable' });
    }
  } catch (error) {
    res.status(503).json({ status: 'disconnected', error: error.message });
  }
});

// ============ OCI GenAI Configuration ============
const genaiEndpoint = process.env.OCI_GENAI_ENDPOINT || 'https://inference.generativeai.us-phoenix-1.oci.oraclecloud.com';
const compartmentId = process.env.OCI_COMPARTMENT_ID || '';
const modelId = process.env.OCI_GENAI_MODEL_ID || '';
const configProfile = process.env.OCI_CONFIG_PROFILE || 'DEFAULT';

// Initialize OCI GenAI client
let genaiClient = null;

async function initGenAIClient() {
  try {
    // Use OCI config file authentication (~/.oci/config)
    const provider = new common.ConfigFileAuthenticationDetailsProvider(
      undefined, // Use default config file location
      configProfile
    );

    genaiClient = new genai.GenerativeAiInferenceClient({
      authenticationDetailsProvider: provider,
    });

    // Set the endpoint
    genaiClient.endpoint = genaiEndpoint;

    console.log('[GenAI] OCI client initialized successfully');
    return true;
  } catch (error) {
    console.error('[GenAI] Failed to initialize OCI client:', error.message);
    return false;
  }
}

// GenAI Chat endpoint
app.post('/api/genai/chat', async (req, res) => {
  try {
    if (!genaiClient) {
      const initialized = await initGenAIClient();
      if (!initialized) {
        return res.status(503).json({ error: 'GenAI client not initialized' });
      }
    }

    const { chatRequest } = req.body;

    // Build the chat request using OCI SDK
    // Matches Python: GenericChatRequest with specific parameters
    const chatDetails = {
      compartmentId: compartmentId,
      servingMode: {
        servingType: 'ON_DEMAND',
        modelId: modelId,
      },
      chatRequest: {
        apiFormat: 'GENERIC',
        messages: chatRequest.messages || [],
        // Newer OpenAI models on OCI reject the legacy maxTokens parameter
        maxCompletionTokens: 2048,
        temperature: 1,
        topP: 1,
        topK: 0,
        frequencyPenalty: 0,
        presencePenalty: 0,
      },
    };

    console.log('[GenAI] Sending chat request...');
    const response = await genaiClient.chat({ chatDetails });

    // Extract the response
    const chatResult = response.chatResult;
    console.log('[GenAI] Raw response:', JSON.stringify(chatResult, null, 2));

    // Handle different response structures
    let text = '';
    let choices = null;
    let finishReason = '';

    // Try GENERIC format (chatResponse.choices)
    if (chatResult.chatResponse?.choices?.[0]) {
      const choice = chatResult.chatResponse.choices[0];
      choices = chatResult.chatResponse.choices;
      finishReason = choice.finishReason || '';

      // Content can be a string or array
      const content = choice.message?.content;
      if (typeof content === 'string') {
        text = content;
      } else if (Array.isArray(content)) {
        text = content
          .filter(c => c.type === 'TEXT')
          .map(c => c.text)
          .join('');
      }
    }
    // Try Cohere format (text directly)
    else if (chatResult.chatResponse?.text) {
      text = chatResult.chatResponse.text;
    }
    // Fallback - check other structures
    else if (chatResult.text) {
      text = chatResult.text;
    }

    console.log('[GenAI] Extracted text length:', text.length);

    res.json({
      chatResponse: {
        text,
        choices,
        finishReason,
      },
      usageMetadata: {
        inputTokenCount: chatResult.modelMetrics?.inputTokenCount || 0,
        outputTokenCount: chatResult.modelMetrics?.outputTokenCount || 0,
      },
    });
  } catch (error) {
    console.error('[GenAI] Error:', error.message);
    res.status(500).json({ error: 'GenAI error', message: error.message });
  }
});

// GenAI health check
app.get('/api/genai/health', async (req, res) => {
  try {
    if (!genaiClient) {
      const initialized = await initGenAIClient();
      if (initialized) {
        res.json({ status: 'connected', endpoint: genaiEndpoint });
      } else {
        res.status(503).json({ status: 'not_initialized' });
      }
    } else {
      res.json({ status: 'connected', endpoint: genaiEndpoint });
    }
  } catch (error) {
    res.status(503).json({ status: 'disconnected', error: error.message });
  }
});

// ============ OpenSky Network API Configuration ============
const openskyEndpoint = process.env.OPENSKY_ENDPOINT || 'https://opensky-network.org/api';
const openskyUsername = process.env.OPENSKY_USERNAME || '';
const openskyPassword = process.env.OPENSKY_PASSWORD || '';
const openskyTimeoutMs = Number(process.env.OPENSKY_TIMEOUT_MS || 15000);
const openskyFallbackEnabled = (process.env.OPENSKY_FALLBACK_ENABLED || 'true').toLowerCase() !== 'false';
const aviationWeatherEndpoint = process.env.AVIATION_WEATHER_ENDPOINT || 'https://aviationweather.gov/api/data';
const aviationWeatherTimeoutMs = Number(process.env.AVIATION_WEATHER_TIMEOUT_MS || 12000);

// OpenSky authentication helper
function getOpenskyAuth() {
  if (openskyUsername && openskyPassword) {
    const credentials = Buffer.from(`${openskyUsername}:${openskyPassword}`).toString('base64');
    return { 'Authorization': `Basic ${credentials}` };
  }
  return {};
}

async function fetchOpenSky(url) {
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...getOpenskyAuth(),
    },
    signal: AbortSignal.timeout(openskyTimeoutMs),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    return { ok: false, status: response.status, errorText };
  }

  const data = await response.json();
  return { ok: true, status: response.status, data };
}

function toNumberOrDefault(value, defaultValue) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : defaultValue;
}

function createFallbackStatesResponse(bbox, reason) {
  const lamin = toNumberOrDefault(bbox?.lamin, 35);
  const lomin = toNumberOrDefault(bbox?.lomin, -10);
  const lamax = toNumberOrDefault(bbox?.lamax, 70);
  const lomax = toNumberOrDefault(bbox?.lomax, 40);

  const latMin = Math.min(lamin, lamax);
  const latMax = Math.max(lamin, lamax);
  const lonMin = Math.min(lomin, lomax);
  const lonMax = Math.max(lomin, lomax);

  const spanLat = Math.max(0.05, latMax - latMin);
  const spanLon = Math.max(0.05, lonMax - lonMin);
  const area = spanLat * spanLon;
  const count = Math.max(10, Math.min(80, Math.round(area * 2.5)));

  const nowSec = Math.floor(Date.now() / 1000);
  const states = Array.from({ length: count }, (_, index) => {
    const lat = latMin + Math.random() * spanLat;
    const lon = lonMin + Math.random() * spanLon;
    const speed = 140 + Math.random() * 130;
    const altitude = 1200 + Math.random() * 11500;
    const heading = Math.random() * 360;
    const vertical = (Math.random() - 0.5) * 16;
    const icao24 = (Math.floor(Math.random() * 0xffffff)).toString(16).padStart(6, '0');
    const callsign = `FB${String(1000 + index).padStart(4, '0')}`;

    return [
      icao24,
      callsign,
      'Fallback Data',
      nowSec - Math.floor(Math.random() * 8),
      nowSec - Math.floor(Math.random() * 4),
      Number(lon.toFixed(5)),
      Number(lat.toFixed(5)),
      Number(altitude.toFixed(0)),
      false,
      Number(speed.toFixed(2)),
      Number(heading.toFixed(1)),
      Number(vertical.toFixed(2)),
      null,
      Number((altitude + 80).toFixed(0)),
      '',
      false,
      0,
    ];
  });

  return {
    time: nowSec,
    states,
    dataSource: 'fallback',
    fallbackReason: reason,
    fallbackActive: true,
  };
}

function createFallbackMetar(icaoId, reason) {
  return {
    icaoId,
    rawOb: `${icaoId} 000000Z VRB05KT 9999 FEW020 22/14 Q1013`,
    wdir: 'VRB',
    wspd: 5,
    wgst: null,
    visib: '10+',
    cloudCover: ['FEW'],
    weather: '',
    temp: 22,
    dewp: 14,
    altim: 1013,
    dataSource: 'fallback',
    fallbackReason: reason,
  };
}

async function fetchAviationWeatherMetar(ids) {
  const idsParam = ids.join(',');
  const url = `${aviationWeatherEndpoint}/metar?ids=${encodeURIComponent(idsParam)}&format=json`;
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'fly-opt-airtraffic/1.0',
    },
    signal: AbortSignal.timeout(aviationWeatherTimeoutMs),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => response.statusText);
    return { ok: false, status: response.status, errorText };
  }

  const data = await response.json();
  const list = Array.isArray(data) ? data : [];
  return { ok: true, status: response.status, data: list };
}

// OpenSky health check
app.get('/api/opensky/health', async (req, res) => {
  try {
    console.log('[OpenSky] Health check...');
    const result = await fetchOpenSky(`${openskyEndpoint}/states/all?lamin=50&lomin=0&lamax=52&lomax=2`);

    if (result.ok) {
      const data = result.data;
      console.log('[OpenSky] Health OK - Aircraft count:', data.states?.length || 0);
      res.json({
        status: 'connected',
        endpoint: openskyEndpoint,
        aircraftCount: data.states?.length || 0,
        authenticated: !!(openskyUsername && openskyPassword),
      });
    } else {
      res.status(503).json({
        status: 'unavailable',
        endpoint: openskyEndpoint,
        error: `OpenSky upstream returned ${result.status}`,
        message: result.errorText || 'Unknown upstream error',
      });
    }
  } catch (error) {
    console.error('[OpenSky] Health error:', error.message);
    res.status(503).json({
      status: 'disconnected',
      endpoint: openskyEndpoint,
      error: error.name === 'TimeoutError' ? `OpenSky request timed out after ${openskyTimeoutMs}ms` : 'OpenSky network failure',
      message: error.message,
    });
  }
});

// Get all aircraft states (with optional bounding box)
app.get('/api/opensky/states/all', async (req, res) => {
  const { lamin, lomin, lamax, lomax } = req.query;
  const fallbackBbox = { lamin, lomin, lamax, lomax };

  try {
    let url = `${openskyEndpoint}/states/all`;

    // Add bounding box if provided
    if (lamin && lomin && lamax && lomax) {
      url += `?lamin=${lamin}&lomin=${lomin}&lamax=${lamax}&lomax=${lomax}`;
    }

    console.log('[OpenSky] Fetching states:', url);
    const result = await fetchOpenSky(url);

    if (!result.ok) {
      if (openskyFallbackEnabled) {
        const fallbackReason = `OpenSky upstream returned ${result.status}`;
        console.warn(`[OpenSky] States fallback enabled: ${fallbackReason}`);
        return res.json(createFallbackStatesResponse(fallbackBbox, fallbackReason));
      }

      return res.status(result.status).json({
        error: `OpenSky upstream returned ${result.status}`,
        message: result.errorText || 'Unknown upstream error',
      });
    }

    const data = {
      ...result.data,
      dataSource: 'api',
      fallbackActive: false,
    };
    console.log('[OpenSky] States retrieved:', data.states?.length || 0, 'aircraft');
    res.json(data);
  } catch (error) {
    console.error('[OpenSky] States error:', error.message);
    if (openskyFallbackEnabled) {
      const fallbackReason =
        error.name === 'TimeoutError'
          ? `OpenSky request timed out after ${openskyTimeoutMs}ms`
          : 'OpenSky network failure';
      console.warn(`[OpenSky] States fallback enabled: ${fallbackReason}`);
      return res.json(createFallbackStatesResponse(fallbackBbox, fallbackReason));
    }

    res.status(500).json({
      error: error.name === 'TimeoutError' ? `OpenSky request timed out after ${openskyTimeoutMs}ms` : 'OpenSky network failure',
      message: error.message,
    });
  }
});

// Get flights for a time interval
app.get('/api/opensky/flights/all', async (req, res) => {
  try {
    const { begin, end } = req.query;

    if (!begin || !end) {
      return res.status(400).json({ error: 'begin and end timestamps required' });
    }

    const url = `${openskyEndpoint}/flights/all?begin=${begin}&end=${end}`;
    console.log('[OpenSky] Fetching flights:', url);

    const result = await fetchOpenSky(url);
    if (!result.ok) {
      return res.status(result.status).json({
        error: `OpenSky upstream returned ${result.status}`,
        message: result.errorText || 'Unknown upstream error',
      });
    }

    const data = result.data;
    console.log('[OpenSky] Flights retrieved:', data?.length || 0);
    res.json(data);
  } catch (error) {
    console.error('[OpenSky] Flights error:', error.message);
    res.status(500).json({
      error: error.name === 'TimeoutError' ? `OpenSky request timed out after ${openskyTimeoutMs}ms` : 'OpenSky flights failed',
      message: error.message,
    });
  }
});

// Get flights by airport
app.get('/api/opensky/flights/airport', async (req, res) => {
  try {
    const { airport, begin, end, type } = req.query;

    if (!airport || !begin || !end) {
      return res.status(400).json({ error: 'airport, begin, and end required' });
    }

    const endpoint = type === 'arrival' ? 'arrival' : 'departure';
    const url = `${openskyEndpoint}/flights/${endpoint}?airport=${airport}&begin=${begin}&end=${end}`;
    console.log('[OpenSky] Fetching airport flights:', url);

    const result = await fetchOpenSky(url);
    if (!result.ok) {
      return res.status(result.status).json({
        error: `OpenSky upstream returned ${result.status}`,
        message: result.errorText || 'Unknown upstream error',
      });
    }

    const data = result.data;
    console.log('[OpenSky] Airport flights retrieved:', data?.length || 0);
    res.json(data);
  } catch (error) {
    console.error('[OpenSky] Airport flights error:', error.message);
    res.status(500).json({
      error: error.name === 'TimeoutError' ? `OpenSky request timed out after ${openskyTimeoutMs}ms` : 'OpenSky airport flights failed',
      message: error.message,
    });
  }
});

// ============ AviationWeather API Configuration ============
app.get('/api/aviationweather/metar', async (req, res) => {
  const idsRaw = typeof req.query.ids === 'string' ? req.query.ids : '';
  const ids = idsRaw
    .split(',')
    .map((id) => id.trim().toUpperCase())
    .filter(Boolean)
    .slice(0, 20);

  if (ids.length === 0) {
    return res.status(400).json({ error: 'ids query parameter is required (comma-separated ICAO codes)' });
  }

  try {
    console.log('[AviationWeather] Fetching METAR for:', ids.join(', '));
    const result = await fetchAviationWeatherMetar(ids);

    if (!result.ok) {
      const reason = `AviationWeather upstream returned ${result.status}`;
      const fallback = ids.map((id) => createFallbackMetar(id, reason));
      return res.json({
        dataSource: 'fallback',
        fallbackActive: true,
        fallbackReason: reason,
        metars: fallback,
      });
    }

    const byId = new Map(
      result.data
        .filter((m) => (m?.icaoId || '').length > 0)
        .map((m) => [String(m.icaoId).toUpperCase(), { ...m, dataSource: 'api' }])
    );

    const merged = ids.map((id) => byId.get(id) || createFallbackMetar(id, 'METAR not returned by source'));
    const hasFallback = merged.some((m) => m.dataSource === 'fallback');

    return res.json({
      dataSource: hasFallback ? 'mixed' : 'api',
      fallbackActive: hasFallback,
      metars: merged,
    });
  } catch (error) {
    console.error('[AviationWeather] METAR error:', error.message);
    const reason =
      error.name === 'TimeoutError'
        ? `AviationWeather request timed out after ${aviationWeatherTimeoutMs}ms`
        : 'AviationWeather network failure';
    const fallback = ids.map((id) => createFallbackMetar(id, reason));
    return res.json({
      dataSource: 'fallback',
      fallbackActive: true,
      fallbackReason: reason,
      metars: fallback,
    });
  }
});

// Initialize and start server
async function startServer() {
  // Initialize GenAI client
  await initGenAIClient();

  // Start server
  app.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════════════╗
║            cuOPT Frontend Proxy Server                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Server:        http://localhost:${PORT}                           ║
║  cuOPT:         ${cuoptEndpoint}
║  GenAI:         ${genaiEndpoint}
║  OpenSky:       ${openskyEndpoint}
║  Compartment:   ${compartmentId.substring(0, 50)}...
║  Model ID:      ${modelId.substring(0, 50)}...
╚══════════════════════════════════════════════════════════════════╝
    `);
  });
}

startServer();
