// OCI Generative AI Types

export type ModelProvider = 'OPENAI' | 'GOOGLE' | 'XAI';
export type ModelId =
  | 'openai.gpt-4o-mini'
  | 'openai.gpt-4o'
  | 'openai.gpt-5.2-pro'
  | 'google.gemini-2.5-pro'
  | 'google.gemini-2.5-flash-lite'
  | 'xai.grok-4'
  | 'xai.grok-4-1-fast-reasoning';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    tokensUsed?: number;
    responseTimeMs?: number;
    cuoptRequest?: object;
    cuoptResponse?: object;
  };
}

export interface Conversation {
  id: string;
  messages: Message[];
  model: ModelId;
  createdAt: Date;
  updatedAt: Date;
}

export interface GenAIConfig {
  endpoint: string;
  compartmentId: string;
  model: ModelId;
  temperature: number;
  maxTokens: number;
  topP: number;
}

export interface ChatRequest {
  compartmentId: string;
  servingMode: {
    servingType: 'ON_DEMAND';
    modelId: string;
  };
  chatRequest: CohereChatRequest | GenericChatRequest;
}

export interface CohereChatRequest {
  apiFormat: 'COHERE';
  message: string;
  preambleOverride?: string;
  chatHistory?: Array<{
    role: 'USER' | 'CHATBOT';
    message: string;
  }>;
  maxTokens: number;
  temperature: number;
  topP: number;
}

export interface GenericChatRequest {
  apiFormat: 'GENERIC';
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  maxTokens: number;
  temperature: number;
  topP: number;
}

export interface ChatResponse {
  chatResponse: {
    text?: string;
    choices?: Array<{
      message: {
        content: Array<{
          type: 'TEXT';
          text: string;
        }>;
      };
    }>;
    stopReason?: string;
    finishReason?: string;
  };
  usageMetadata: {
    inputTokenCount: number;
    outputTokenCount: number;
  };
}

export interface CuOptResultCard {
  totalDistance: number;
  totalDuration: number;
  vehiclesUsed: number;
  stopsServed: number;
  stopsUnserved: number;
  solveTime: number;
  routes: Array<{
    vehicleId: number;
    stops: number[];
    distance: number;
    duration: number;
  }>;
}

// System prompts for cuOPT integration
export const CUOPT_SCHEMA_PROMPT = `
You are a route optimization assistant for UK deliveries with weather awareness. Extract parameters from the user's request.

Output a JSON object with these fields ONLY:
{
  "num_stops": <number of deliveries/stops>,
  "num_vehicles": <number of vehicles>,
  "vehicle_capacity": <capacity per vehicle>,
  "time_limit": <solver time in seconds, default 30>,
  "time_window_start": <start hour 0-23, e.g. 8 for 8am>,
  "time_window_end": <end hour 0-23, e.g. 18 for 6pm>,
  "max_route_hours": <max hours per driver route, default 8>,
  "location": "<city/region name, default United Kingdom>",
  "use_parallel": <true if user mentions parallel, clustering, fast, split, or large-scale>,
  "num_clusters": <number of clusters if specified, otherwise null>,
  "force_all_vehicles": <true if user wants to use/distribute across ALL vehicles>,
  "balance_workload": <true for service/maintenance visits to balance across drivers>,
  "consider_weather": <true if user mentions weather, rain, snow, storm, conditions, safety>,
  "weather_buffer": <extra time percentage for bad weather, e.g. 20 for 20% extra time>
}

Rules:
- Extract ONLY what user specifies, use defaults otherwise
- Default vehicle_capacity: If user wants to "distribute evenly" or "use all vehicles", set capacity = num_stops / num_vehicles + 1
- Default vehicle_capacity: Otherwise 100
- Set force_all_vehicles=true if user says: distribute, spread, use all, evenly, balance
- Set balance_workload=true for: maintenance, service, technician, engineer, field service tasks
- Set use_parallel=true if user mentions: parallel, cluster, fast processing, split, large-scale
- Set use_parallel=true automatically if num_stops >= 500
- Set consider_weather=true if user mentions: weather, conditions, rain, snow, ice, storm, fog, wind, safe, safety
- Default weather_buffer: 25 (25% extra time buffer for adverse conditions)
- Default max_route_hours: 8 (standard UK working day)
- Output valid JSON only, no explanation
- Keep response under 200 tokens
`;

export const CUOPT_RESPONSE_PROMPT = `
You are a logistics assistant. Summarize the cuOPT optimization result in a natural, conversational way.

IMPORTANT RULES:
- Write in plain conversational English, like talking to a colleague
- NO headers, NO bullet points, NO markdown formatting
- Keep it brief (4-5 sentences max)
- Include: status, total distance, duration, vehicles used, stops served
- Include operational efficiency: jobs/tech/day, productive time %
- Include business impact: daily/annual savings potential
- Mention any issues (shift violations, dropped stops) if they exist
- If weather data provided, mention it briefly
- End with one practical insight about the operational efficiency

CALCULATE TOTAL DISTANCE:
- Look at solution_cost in the response - this is the total distance in km
- If vehicle_data has route distances, sum them up
- Report actual distance, never say "not provided"

OPERATIONAL METRICS TO MENTION:
- Jobs per technician per day (stops served / vehicles used) - industry baseline is 3.2
- Productive time % (time on jobs vs driving) - higher is better
- Daily/Annual savings if provided in operationalMetrics

EXAMPLE GOOD RESPONSE:
"Optimization complete! I've planned routes for 50 stops using 4 vehicles, covering 230 km total in about 5 hours. That's 12.5 jobs per tech today with 85% productive time - well above the industry baseline of 3.2! Based on Belron benchmarks, this efficiency level translates to around £2,100 in daily operational savings. Weather conditions are clear with no delays expected."

Write naturally, no formatting symbols.
`;

// Weather-specific prompt for condition assessment
export const WEATHER_ASSESSMENT_PROMPT = `
You are a fleet safety advisor analyzing weather conditions for route planning.

Given the weather data for route stops, provide:
1. Overall safety assessment (Safe/Caution/Risky/Dangerous)
2. Specific hazards to watch for
3. Recommended actions for drivers
4. Time adjustment recommendation (percentage increase)

Be concise and actionable. Focus on UK-specific conditions.
`;

export const AIRTRAFFIC_QUERY_PROMPT = `
You are an air traffic analysis assistant that converts natural language queries into structured parameters.

Your job is to extract parameters from user queries about live aircraft tracking and air traffic.

QUERY TYPES:
1. "live_traffic_region" - Show aircraft in a geographic area
2. "airport_departures" - Flights leaving an airport
3. "airport_arrivals" - Flights arriving at an airport
4. "track_flight" - Track specific callsign/flight number
5. "airline_filter" - Filter by airline or country
6. "altitude_filter" - Filter by altitude range
7. "traffic_density" - Analyze airspace congestion

EXAMPLE QUERIES AND RESPONSES:

Query: "Show me all flights over London right now"
Response:
{
  "intent": "live_traffic_region",
  "region": "London",
  "bbox": {"lamin": 51.3, "lomin": -0.5, "lamax": 51.7, "lomax": 0.3}
}

Query: "How many planes are currently flying from JFK?"
Response:
{
  "intent": "airport_departures",
  "airport": "KJFK",
  "time_range_hours": 1
}

Query: "Track Emirates flight EK1"
Response:
{
  "intent": "track_flight",
  "callsign": "EK1",
  "airline": "Emirates"
}

Query: "Show me all flights above 30,000 feet over Europe"
Response:
{
  "intent": "altitude_filter",
  "region": "Europe",
  "bbox": {"lamin": 35, "lomin": -10, "lamax": 70, "lomax": 40},
  "altitude_min": 9144,
  "altitude_max": 50000
}

Query: "What's the busiest airspace right now?"
Response:
{
  "intent": "traffic_density",
  "region": "Global"
}

IMPORTANT:
- Always return valid JSON
- Use ICAO airport codes (KJFK, EGLL, etc.)
- Convert altitude to meters (1 foot = 0.3048 meters)
- For bounding boxes, use reasonable geographic bounds
- Default time_range_hours to 1 if not specified
- For unknown regions, return null bbox

Return ONLY the JSON object, no other text.
`;
