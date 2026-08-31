import axios, { AxiosInstance } from 'axios';
import type { Message, ModelId, ChatResponse, CuOptRequest, CuOptResponse, Stop, JobType } from '@/types';
import type { AirTrafficQuery } from '@/types/opensky';
import { CUOPT_SCHEMA_PROMPT, CUOPT_RESPONSE_PROMPT, AIRTRAFFIC_QUERY_PROMPT } from '@/types/genai';
import { getScenarioMetrics, detectScenarioFromPrompt, type ScenarioMetrics } from '@/data/benchmarkData';
import { JOB_TYPE_CONFIGS, DEFAULT_JOB_TYPE_MIX } from '@/types/cuopt';

// Supported AI models
export const SUPPORTED_MODELS: { id: string; name: string; provider: string }[] = [
  { id: 'openai.gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI' },
  { id: 'openai.gpt-4o', name: 'GPT-4o', provider: 'OpenAI' },
  { id: 'google.gemini-2.5-pro', name: 'Gemini 2.5 Pro', provider: 'Google' },
  { id: 'google.gemini-2.5-flash-lite', name: 'Gemini Flash', provider: 'Google' },
  { id: 'cohere.command-r-plus', name: 'Command R+', provider: 'Cohere' },
  { id: 'meta.llama-3.1-70b', name: 'Llama 3.1 70B', provider: 'Meta' },
];

class GenAIClient {
  private client: AxiosInstance;
  private model: ModelId = 'openai.gpt-4o-mini';
  private temperature = 0.7;
  private maxTokens = 4096;
  private topP = 0.9;

  constructor() {
    this.client = axios.create({
      baseURL: '/api/genai',
      timeout: 120000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  setModel(model: string): void {
    this.model = model as ModelId;
  }

  setTemperature(temp: number): void {
    this.temperature = Math.max(0, Math.min(1, temp));
  }

  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch {
      return false;
    }
  }

  async chat(
    messages: Message[],
    systemPrompt?: string
  ): Promise<{ content: string; tokensUsed: number }> {
    // Cohere models use COHERE format, all others (OpenAI, Google, xAI, Meta) use GENERIC format
    const isCohere = this.model.startsWith('cohere');

    const payload = isCohere
      ? this.buildCoherePayload(messages, systemPrompt)
      : this.buildGenericPayload(messages, systemPrompt);

    const response = await this.client.post<ChatResponse>('/chat', payload);
    const data = response.data;

    let content = '';
    if (data.chatResponse.text) {
      content = data.chatResponse.text;
    } else if (data.chatResponse.choices?.[0]?.message?.content) {
      content = data.chatResponse.choices[0].message.content
        .filter((c) => c.type === 'TEXT')
        .map((c) => c.text)
        .join('');
    }

    return {
      content,
      tokensUsed:
        (data.usageMetadata?.inputTokenCount || 0) +
        (data.usageMetadata?.outputTokenCount || 0),
    };
  }

  // Intent classification - determine if message is a question or optimization request
  async classifyIntent(userMessage: string): Promise<{
    intent: 'optimization' | 'question' | 'greeting' | 'unclear';
    confidence: number;
    answer?: string;
  }> {
    const lowerMessage = userMessage.toLowerCase().trim();

    // Quick pattern matching for common cases (avoid API call)
    const greetingPatterns = /^(hi|hello|hey|good morning|good afternoon|good evening|howdy|greetings)/i;
    const questionPatterns = /^(what|how|why|when|where|who|which|can you|could you|is it|are there|does|do|explain|tell me about|describe)/i;
    const optimizationKeywords = /(optimize|deliver|route|vehicle|stop|location|cluster|parallel|dispatch|schedule|pickup|drop|fleet|driver|technician|job|service)/i;

    // Check for greetings
    if (greetingPatterns.test(lowerMessage) && lowerMessage.length < 50) {
      return { intent: 'greeting', confidence: 0.95 };
    }

    // Check for questions about cuOPT/system (not optimization requests)
    if (questionPatterns.test(lowerMessage)) {
      // If it has optimization keywords, it's likely an optimization request phrased as question
      if (optimizationKeywords.test(lowerMessage) && /\d+/.test(lowerMessage)) {
        return { intent: 'optimization', confidence: 0.85 };
      }

      // Pure questions about the system
      const infoQuestions = [
        'what is cuopt', 'how does cuopt', 'what can cuopt', 'tell me about cuopt',
        'explain cuopt', 'what is vrp', 'how does this work', 'what is route optimization',
        'compare', 'difference between', 'capabilities', 'features', 'limitations',
      ];

      for (const q of infoQuestions) {
        if (lowerMessage.includes(q)) {
          // Generate a quick answer for common questions
          const answer = this.getQuickAnswer(lowerMessage);
          return { intent: 'question', confidence: 0.9, answer };
        }
      }
    }

    // Check for optimization indicators (numbers + action words)
    if (optimizationKeywords.test(lowerMessage) && /\d+/.test(lowerMessage)) {
      return { intent: 'optimization', confidence: 0.9 };
    }

    // If contains numbers and location-related terms, likely optimization
    if (/\d+/.test(lowerMessage) && /(uk|london|manchester|birmingham|city|region|area|across)/i.test(lowerMessage)) {
      return { intent: 'optimization', confidence: 0.8 };
    }

    // Default to unclear if no strong signals
    return { intent: 'unclear', confidence: 0.5 };
  }

  // Quick answers for common questions (no API call needed)
  private getQuickAnswer(question: string): string {
    const q = question.toLowerCase();

    if (q.includes('what is cuopt')) {
      return `**NVIDIA cuOPT** is a GPU-accelerated optimization engine for solving Vehicle Routing Problems (VRP) and other logistics optimization challenges.

**Key Features:**
- Solves complex routing problems 100x faster than traditional CPU solvers
- Handles thousands of stops with multiple constraints
- Supports time windows, capacity limits, and custom objectives
- Runs on NVIDIA GPUs (A10G, A100, H100)

**This dashboard** provides a visual interface to cuOPT with AI-powered natural language input.`;
    }

    if (q.includes('how does') && (q.includes('work') || q.includes('cuopt'))) {
      return `**How cuOPT Works:**

1. **Input:** You provide stops (locations with coordinates), vehicles (with capacity), and constraints
2. **Optimization:** cuOPT uses GPU-accelerated algorithms to find optimal routes
3. **Output:** Returns vehicle assignments, routes, arrival times, and distances

**Algorithms Used:**
- GPU-parallel local search
- Adaptive large neighborhood search
- Multiple restart strategies

**Typical solve time:** 10-60 seconds for 100-10,000 stops.`;
    }

    if (q.includes('vrp') || q.includes('vehicle routing')) {
      return `**Vehicle Routing Problem (VRP)** is a combinatorial optimization problem that asks:

*"What is the optimal set of routes for a fleet of vehicles to serve a set of customers?"*

**Variants supported:**
- **CVRP:** Capacitated VRP (vehicle capacity limits)
- **VRPTW:** VRP with Time Windows
- **PDVRP:** Pickup and Delivery VRP
- **Multi-depot VRP**

cuOPT solves these using GPU acceleration, making it 10-100x faster than traditional solvers.`;
    }

    if (q.includes('compare') || q.includes('difference')) {
      return `**cuOPT vs Traditional Solvers:**

| Feature | cuOPT | Traditional (OR-Tools, etc.) |
|---------|-------|------------------------------|
| Speed | 10-100x faster | Baseline |
| Hardware | GPU (A10G/A100/H100) | CPU |
| Max stops | 10,000+ | ~1,000-2,000 |
| Real-time | Yes | Limited |

**Best for:** Large-scale logistics, same-day delivery, field service routing.`;
    }

    // Default answer
    return `I can help you with:
- **Route optimization:** "Optimize 100 deliveries with 5 vehicles in London"
- **Questions about cuOPT:** "What is cuOPT?" "How does routing work?"
- **Scenario analysis:** "What if I add more vehicles?"

Try describing your routing problem, and I'll create an optimized solution!`;
  }

  async convertPromptToCuOpt(
    userMessage: string,
    context?: {
      countryName?: string;
      cityName?: string;
      centerLat?: number;
      centerLng?: number;
      radiusKm?: number;
    }
  ): Promise<{
    request: CuOptRequest | null;
    interpretation: string;
    error?: string;
    numStops?: number;
    numVehicles?: number;
    vehicleCapacity?: number;
    useParallel?: boolean;
    numClusters?: number;
    stops?: Stop[];
    location?: string;
    // Extracted config overrides from prompt
    extractedConfig?: {
      enableHomeStart?: boolean;
      balanceWorkload?: boolean;
      forceAllVehicles?: boolean;
      timeLimit?: number;
      serviceTime?: number;
    };
  }> {
    const systemPrompt = CUOPT_SCHEMA_PROMPT;

    try {
      const response = await this.chat(
        [{ id: '1', role: 'user', content: userMessage, timestamp: new Date() }],
        systemPrompt
      );

      const content = response.content;

      // Try to extract JSON from response
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return {
          request: null,
          interpretation: content,
          error: 'Could not extract parameters from response',
        };
      }

      const params = JSON.parse(jsonMatch[0]);

      // Extract parameters with defaults
      const numStops = params.num_stops || 50;
      // Scale vehicles based on stops when not specified:
      // ~25 stops per vehicle is optimal for delivery scenarios
      // Minimum 2 vehicles, maximum 50 vehicles
      const defaultVehicles = Math.min(50, Math.max(2, Math.ceil(numStops / 25)));
      const numVehicles = params.num_vehicles || defaultVehicles;
      const timeLimit = params.time_limit || 30;

      // Location priority:
      // 1. Context location (from selected city/country dropdown) - HIGHEST priority
      // 2. AI-extracted location from prompt (if user explicitly mentioned a place)
      // 3. Default to "United Kingdom"
      const contextLocation = context?.cityName && context?.countryName
        ? `${context.cityName}, ${context.countryName}`
        : context?.countryName;

      // Use context location if available, otherwise fall back to AI-extracted
      const location = contextLocation || params.location || 'United Kingdom';
      const forceAllVehicles = params.force_all_vehicles || false;
      const balanceWorkload = params.balance_workload || false;
      const maxRouteHours = params.max_route_hours || 8;

      // Calculate capacity - ensure it's sufficient for the problem
      let vehicleCapacity = params.vehicle_capacity || 100;

      // Calculate minimum required capacity:
      // - Max single stop demand is ~10
      // - Total demand = numStops * avg_demand (~5.5)
      // - Each vehicle must handle at least (total_demand / num_vehicles)
      const avgDemand = 5.5; // Average demand per stop (range 1-10)
      const maxSingleDemand = 10;
      const totalDemand = Math.ceil(numStops * avgDemand);
      const minCapacityPerVehicle = Math.ceil(totalDemand / numVehicles) + 5; // +5 buffer
      const minCapacity = Math.max(maxSingleDemand, minCapacityPerVehicle);

      // Ensure capacity is sufficient
      if (vehicleCapacity < minCapacity) {
        vehicleCapacity = minCapacity;
      }

      // For service/maintenance tasks or when user wants balanced workload,
      // set capacity to force distribution across vehicles
      const shouldBalance = forceAllVehicles || balanceWorkload;
      if (shouldBalance) {
        // Set capacity so stops are distributed across all vehicles
        // This forces the optimizer to use multiple vehicles
        vehicleCapacity = minCapacityPerVehicle;
      }

      // Extract parallel processing parameters
      // Auto-enable parallel if explicitly requested or if stops >= 500
      const useParallel = params.use_parallel === true || numStops >= 500;
      const numClusters = params.num_clusters || (useParallel ? Math.min(Math.ceil(numStops / 500), 8) : null);

      // Generate interpretation with parallel info
      const parallelInfo = useParallel ? ` Using parallel processing with ${numClusters} clusters.` : '';
      const distributeInfo = shouldBalance ? ` Balancing workload across all ${numVehicles} vehicles (max ${maxRouteHours}h per driver).` : '';
      const interpretation = `Optimizing ${numStops} deliveries with ${numVehicles} vehicles in ${location}. Vehicle capacity: ${vehicleCapacity} units. Solver time limit: ${timeLimit}s.${parallelInfo}${distributeInfo}`;

      // Location coordinates lookup for cities/regions worldwide
      const locationCoords: Record<string, { lat: number; lng: number; radius: number }> = {
        // UK Cities
        'london': { lat: 51.5074, lng: -0.1278, radius: 30 },
        'greater london': { lat: 51.5074, lng: -0.1278, radius: 40 },
        'manchester': { lat: 53.4808, lng: -2.2426, radius: 25 },
        'birmingham': { lat: 52.4862, lng: -1.8904, radius: 25 },
        'leeds': { lat: 53.8008, lng: -1.5491, radius: 20 },
        'glasgow': { lat: 55.8642, lng: -4.2518, radius: 25 },
        'edinburgh': { lat: 55.9533, lng: -3.1883, radius: 20 },
        'liverpool': { lat: 53.4084, lng: -2.9916, radius: 20 },
        'bristol': { lat: 51.4545, lng: -2.5879, radius: 20 },
        'sheffield': { lat: 53.3811, lng: -1.4701, radius: 20 },
        'newcastle': { lat: 54.9783, lng: -1.6178, radius: 20 },
        'nottingham': { lat: 52.9548, lng: -1.1581, radius: 20 },
        'cardiff': { lat: 51.4816, lng: -3.1791, radius: 20 },
        'belfast': { lat: 54.5973, lng: -5.9301, radius: 20 },
        'midlands': { lat: 52.6369, lng: -1.1398, radius: 60 },
        'scotland': { lat: 56.4907, lng: -4.2026, radius: 150 },
        'wales': { lat: 52.1307, lng: -3.7837, radius: 100 },
        'south east': { lat: 51.3, lng: 0.5, radius: 80 },
        'north west': { lat: 53.8, lng: -2.6, radius: 80 },
        'united kingdom': { lat: 54.5, lng: -2.0, radius: 300 },
        'uk': { lat: 54.5, lng: -2.0, radius: 300 },
        // France
        'paris': { lat: 48.8566, lng: 2.3522, radius: 25 },
        'lyon': { lat: 45.7640, lng: 4.8357, radius: 20 },
        'marseille': { lat: 43.2965, lng: 5.3698, radius: 20 },
        'toulouse': { lat: 43.6047, lng: 1.4442, radius: 20 },
        'nice': { lat: 43.7102, lng: 7.2620, radius: 15 },
        'bordeaux': { lat: 44.8378, lng: -0.5792, radius: 20 },
        'lille': { lat: 50.6292, lng: 3.0573, radius: 20 },
        'france': { lat: 46.6034, lng: 1.8883, radius: 400 },
        // Germany
        'berlin': { lat: 52.5200, lng: 13.4050, radius: 30 },
        'munich': { lat: 48.1351, lng: 11.5820, radius: 25 },
        'frankfurt': { lat: 50.1109, lng: 8.6821, radius: 25 },
        'hamburg': { lat: 53.5511, lng: 9.9937, radius: 25 },
        'cologne': { lat: 50.9375, lng: 6.9603, radius: 20 },
        'düsseldorf': { lat: 51.2277, lng: 6.7735, radius: 20 },
        'germany': { lat: 51.1657, lng: 10.4515, radius: 400 },
        // USA
        'new york': { lat: 40.7128, lng: -74.0060, radius: 30 },
        'nyc': { lat: 40.7128, lng: -74.0060, radius: 30 },
        'los angeles': { lat: 34.0522, lng: -118.2437, radius: 40 },
        'chicago': { lat: 41.8781, lng: -87.6298, radius: 30 },
        'houston': { lat: 29.7604, lng: -95.3698, radius: 35 },
        'phoenix': { lat: 33.4484, lng: -112.0740, radius: 35 },
        'san francisco': { lat: 37.7749, lng: -122.4194, radius: 25 },
        'seattle': { lat: 47.6062, lng: -122.3321, radius: 25 },
        'miami': { lat: 25.7617, lng: -80.1918, radius: 25 },
        'usa': { lat: 39.8283, lng: -98.5795, radius: 2000 },
        'united states': { lat: 39.8283, lng: -98.5795, radius: 2000 },
        // Spain
        'madrid': { lat: 40.4168, lng: -3.7038, radius: 25 },
        'barcelona': { lat: 41.3851, lng: 2.1734, radius: 25 },
        'valencia': { lat: 39.4699, lng: -0.3763, radius: 20 },
        'seville': { lat: 37.3891, lng: -5.9845, radius: 20 },
        'spain': { lat: 40.4637, lng: -3.7492, radius: 400 },
        // India
        'mumbai': { lat: 19.05, lng: 72.88, radius: 12 }, // Tighter radius to keep stops in urban core
        'delhi': { lat: 28.7041, lng: 77.1025, radius: 30 },
        'bangalore': { lat: 12.9716, lng: 77.5946, radius: 25 },
        'chennai': { lat: 13.0827, lng: 80.2707, radius: 25 },
        'hyderabad': { lat: 17.3850, lng: 78.4867, radius: 25 },
        'kolkata': { lat: 22.5726, lng: 88.3639, radius: 25 },
        'india': { lat: 20.5937, lng: 78.9629, radius: 1500 },
        // Australia
        'sydney': { lat: -33.8688, lng: 151.2093, radius: 35 },
        'melbourne': { lat: -37.8136, lng: 144.9631, radius: 35 },
        'brisbane': { lat: -27.4698, lng: 153.0251, radius: 30 },
        'perth': { lat: -31.9505, lng: 115.8605, radius: 30 },
        'australia': { lat: -25.2744, lng: 133.7751, radius: 2000 },
        // Netherlands
        'amsterdam': { lat: 52.3676, lng: 4.9041, radius: 20 },
        'rotterdam': { lat: 51.9244, lng: 4.4777, radius: 20 },
        'netherlands': { lat: 52.1326, lng: 5.2913, radius: 150 },
        // Italy
        'rome': { lat: 41.9028, lng: 12.4964, radius: 25 },
        'milan': { lat: 45.4642, lng: 9.1900, radius: 25 },
        'naples': { lat: 40.8518, lng: 14.2681, radius: 20 },
        'italy': { lat: 41.8719, lng: 12.5674, radius: 400 },
        // Canada
        'toronto': { lat: 43.6532, lng: -79.3832, radius: 30 },
        'vancouver': { lat: 49.2827, lng: -123.1207, radius: 25 },
        'montreal': { lat: 45.5017, lng: -73.5673, radius: 25 },
        'canada': { lat: 56.1304, lng: -106.3468, radius: 2000 },
      };

      // Use context coordinates if provided, otherwise look up from location name
      let coords: { lat: number; lng: number; radius: number };

      if (context?.centerLat && context?.centerLng) {
        // Use provided context coordinates (from selected city)
        coords = {
          lat: context.centerLat,
          lng: context.centerLng,
          radius: context.radiusKm || 50
        };
      } else {
        // Find matching location (case-insensitive)
        const locationKey = location.toLowerCase();
        coords = Object.entries(locationCoords).find(([key]) =>
          locationKey.includes(key) || key.includes(locationKey)
        )?.[1] || locationCoords['united kingdom'];
      }

      // Generate random stops in the specified location with service times
      const { generateRandomStops } = await import('@/data/benchmarkData');
      const baseStops = generateRandomStops(numStops, coords.lat, coords.lng, coords.radius);

      // Add service times based on job type mix
      const stops = baseStops.map((stop, i) => {
        // Randomly assign job type based on mix percentages
        const rand = Math.random() * 100;
        let cumulative = 0;
        let selectedJobType: JobType = 'delivery';
        let serviceDuration = 30; // Default 30 min

        for (const [type, percentage] of Object.entries(DEFAULT_JOB_TYPE_MIX)) {
          cumulative += percentage;
          if (rand <= cumulative) {
            selectedJobType = type as JobType;
            const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];
            serviceDuration = jobConfig?.defaultDuration || 30;
            break;
          }
        }

        const jobConfig = JOB_TYPE_CONFIGS[selectedJobType];

        return {
          ...stop,
          label: `${jobConfig?.label || 'Stop'} ${i + 1}`,
          jobType: selectedJobType,
          serviceDuration,
          revenue: jobConfig?.revenue || 0,
        };
      });

      // Build vehicles array
      // Note: Set startLat/startLng to 0 to avoid triggering home-start mode
      // Home-start mode should only be enabled explicitly via config
      const vehicles = Array.from({ length: numVehicles }, (_, i) => ({
        id: i,
        capacity: vehicleCapacity,
        startLat: 0,
        startLng: 0,
      }));

      // Build cuOPT payload using the existing buildPayload method
      const { cuoptClient } = await import('@/api/cuoptClient');
      const request = cuoptClient.buildPayload(stops, vehicles, {
        numVehicles,
        vehicleCapacity,
        timeLimit,
        objective: 'minimize_distance',
        enableTimeWindows: false,
        enableCapacity: true,
        enableHomeStart: false, // Disable home-start mode for AI-generated requests
        parallelJobs: 1,
        parallelMode: 'auto',
        solverMode: 'balanced',
      });

      // Build extracted config for values that should override dashboard settings
      const extractedConfig = {
        balanceWorkload,
        forceAllVehicles,
        timeLimit,
      };

      return {
        request,
        interpretation,
        numStops,
        numVehicles,
        vehicleCapacity,
        useParallel,
        numClusters,
        stops,
        location,
        extractedConfig,
      };
    } catch (error) {
      return {
        request: null,
        interpretation: '',
        error: `Failed to convert prompt: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  async convertResponseToNaturalLanguage(
    cuoptResult: CuOptResponse,
    originalPrompt: string,
    weatherContext?: string,
    stops?: Stop[],
    scenarioId?: string,
    location?: string
  ): Promise<string> {
    // Detect scenario from prompt or use provided scenarioId
    const scenario: ScenarioMetrics = scenarioId
      ? getScenarioMetrics(scenarioId)
      : detectScenarioFromPrompt(originalPrompt);

    // Include weather context if available
    const weatherSection = weatherContext
      ? `\n\nWeather Data Available:\n${weatherContext}\n(Note: Weather details will be shown separately - do not state that weather data was not provided)`
      : '';

    // Calculate operational impact metrics
    const vehicleData = cuoptResult.vehicle_data || [];
    const vehiclesUsed = vehicleData.filter(v => v.route && v.route.length > 2).length;
    const stopsServed = vehicleData.reduce((sum, v) => sum + Math.max(0, (v.route?.length || 2) - 2), 0);
    const totalDuration = vehicleData.reduce((sum, v) => sum + (v.route_duration || 0), 0);

    // Calculate job time from stops (if available)
    const totalJobTime = stops?.reduce((sum, s) => sum + (s.serviceDuration || 0), 0) || 0;
    const totalDriveTime = Math.max(0, totalDuration - totalJobTime);
    const productiveRatio = totalDuration > 0 ? (totalJobTime / totalDuration) * 100 : 0;

    // Calculate business metrics using SCENARIO-SPECIFIC values
    const jobsPerTechPerDay = vehiclesUsed > 0 ? stopsServed / vehiclesUsed : 0;
    const baselineJobsPerTech = scenario.baselineJobsPerTech;
    const efficiencyImprovement = baselineJobsPerTech > 0
      ? ((jobsPerTechPerDay - baselineJobsPerTech) / baselineJobsPerTech) * 100
      : 0;

    // Calculate savings using SCENARIO-SPECIFIC costs/revenue
    const totalDistance = cuoptResult.solution_cost || 0;
    const fuelCostPerKm = scenario.fuelCostPerKm;
    const avgRevenuePerJob = scenario.avgRevenuePerJob;
    const distanceReduction = totalDistance * 0.15; // 15% assumed optimization benefit
    const fuelSavingsDaily = distanceReduction * fuelCostPerKm;
    const additionalJobsPerDay = Math.max(0, jobsPerTechPerDay - baselineJobsPerTech) * vehiclesUsed;
    const additionalRevenueDaily = additionalJobsPerDay * avgRevenuePerJob;
    const totalDailySavings = fuelSavingsDaily + additionalRevenueDaily;
    const annualSavings = totalDailySavings * 250; // 250 working days

    // Build scenario context header for LLM grounding
    const scenarioContext = `
=== OPTIMIZATION CONTEXT ===
Scenario: ${scenario.name}
Type: ${scenario.type}
Job Type: ${scenario.jobType}
Location: ${location || 'Not specified'}
Jobs Optimized: ${stopsServed}
Vehicles Used: ${vehiclesUsed}
Total Distance: ${totalDistance.toFixed(1)} km
Solve Time: ${cuoptResult.solve_time || 0}s
===========================
`;

    const operationalMetrics = `
Operational Impact Metrics (${scenario.name}):
- Jobs per Tech per Day: ${jobsPerTechPerDay.toFixed(1)} (${scenario.type} baseline: ${baselineJobsPerTech})
- Efficiency vs Baseline: ${efficiencyImprovement >= 0 ? '+' : ''}${efficiencyImprovement.toFixed(0)}%
- Productive Time: ${productiveRatio.toFixed(0)}% on jobs, ${(100 - productiveRatio).toFixed(0)}% driving
- Total Job Time: ${Math.round(totalJobTime)} min, Total Drive Time: ${Math.round(totalDriveTime)} min
- Avg Revenue per ${scenario.jobType}: £${avgRevenuePerJob}
- Estimated Daily Savings: £${Math.round(totalDailySavings).toLocaleString()} (fuel + productivity)
- Estimated Annual Potential: £${Math.round(annualSavings).toLocaleString()} (scaled to 250 days)
`;

    const systemPrompt = `${CUOPT_RESPONSE_PROMPT}

${scenarioContext}

Original user question: "${originalPrompt}"${weatherSection}

${operationalMetrics}

cuOPT Result:
${JSON.stringify(cuoptResult, null, 2)}`;

    const response = await this.chat(
      [
        {
          id: '1',
          role: 'user',
          content: 'Explain this optimization result to me.',
          timestamp: new Date(),
        },
      ],
      systemPrompt
    );

    return response.content;
  }

  /**
   * Convert natural language query to air traffic parameters
   */
  async convertToAirTrafficQuery(userMessage: string): Promise<{
    query: AirTrafficQuery | null;
    interpretation: string;
    error?: string;
  }> {
    try {
      const response = await this.chat(
        [{ id: '1', role: 'user', content: userMessage, timestamp: new Date() }],
        AIRTRAFFIC_QUERY_PROMPT
      );

      const content = response.content;

      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        return {
          query: null,
          interpretation: content,
          error: 'Could not extract parameters from response',
        };
      }

      const query = JSON.parse(jsonMatch[0]) as AirTrafficQuery;

      let interpretation = '';
      switch (query.intent) {
        case 'live_traffic_region':
          interpretation = `Showing live aircraft over ${query.region || 'the selected area'}`;
          break;
        case 'airport_departures':
          interpretation = `Showing departures from ${query.airport || 'the airport'} in the last ${query.time_range_hours || 1} hour(s)`;
          break;
        case 'airport_arrivals':
          interpretation = `Showing arrivals to ${query.airport || 'the airport'} in the last ${query.time_range_hours || 1} hour(s)`;
          break;
        case 'track_flight':
          interpretation = `Tracking flight ${query.callsign || 'requested callsign'}`;
          break;
        case 'airline_filter':
          interpretation = `Filtering flights by ${query.airline || query.country || 'requested operator'}`;
          break;
        case 'altitude_filter':
          interpretation = `Filtering aircraft between ${query.altitude_min ?? 0}m and ${query.altitude_max ?? 'maximum altitude'}`;
          break;
        case 'traffic_density':
          interpretation = `Analyzing traffic density over ${query.region || 'the selected area'}`;
          break;
        default:
          interpretation = 'Processing air traffic query...';
      }

      return { query, interpretation };
    } catch (error) {
      return {
        query: null,
        interpretation: '',
        error: `Failed to process query: ${error instanceof Error ? error.message : 'Unknown error'}`,
      };
    }
  }

  async *streamChat(
    messages: Message[],
    systemPrompt?: string
  ): AsyncGenerator<string, void, unknown> {
    // For now, simulate streaming with chunked response
    // In production, this would use Server-Sent Events
    const response = await this.chat(messages, systemPrompt);
    const words = response.content.split(' ');

    for (const word of words) {
      yield word + ' ';
      await this.delay(30); // Simulate typing
    }
  }

  private buildCoherePayload(messages: Message[], systemPrompt?: string) {
    const lastMessage = messages[messages.length - 1];
    const chatHistory = messages.slice(0, -1).map((m) => ({
      role: m.role === 'user' ? 'USER' : 'CHATBOT',
      message: m.content,
    }));

    return {
      chatRequest: {
        apiFormat: 'COHERE',
        message: lastMessage.content,
        preambleOverride: systemPrompt,
        chatHistory: chatHistory.length > 0 ? chatHistory : undefined,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
        topP: this.topP,
      },
    };
  }

  private buildGenericPayload(messages: Message[], systemPrompt?: string) {
    const formattedMessages: Array<{
      role: string;
      content: Array<{ type: string; text: string }>;
    }> = [];

    if (systemPrompt) {
      formattedMessages.push({
        role: 'SYSTEM',
        content: [{ type: 'TEXT', text: systemPrompt }],
      });
    }

    messages.forEach((m) => {
      formattedMessages.push({
        role: m.role === 'assistant' ? 'ASSISTANT' : 'USER',
        content: [{ type: 'TEXT', text: m.content }],
      });
    });

    return {
      chatRequest: {
        apiFormat: 'GENERIC',
        messages: formattedMessages,
        maxTokens: this.maxTokens,
        temperature: this.temperature,
        topP: this.topP,
      },
    };
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

export const genaiClient = new GenAIClient();
export default genaiClient;
