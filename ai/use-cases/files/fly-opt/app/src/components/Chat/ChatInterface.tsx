import { useRef, useEffect, useCallback } from 'react';
import { MessageSquare, Sparkles, Code, Eye, EyeOff } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/shared/Card';
import { Button } from '@/components/shared/Button';
import { Badge } from '@/components/shared/Badge';
import { useChatStore, useAppStore, useOptimizationStore, useConfigStore } from '@/store';
import { genaiClient, cuoptClient, weatherClient } from '@/api';
import { examplePrompts } from '@/data/benchmarkData';
import { generateDynamicPrompts } from '@/data/locationData';
import type { Stop } from '@/types';
import type { WeatherRoutingImpact, AdverseConditionAssessment } from '@/types/weather';
import type { AirTrafficQuery } from '@/types/opensky';

// Helper function to generate weather summary for AI response
function generateWeatherSummary(impacts: WeatherRoutingImpact[], assessment: AdverseConditionAssessment | null): string {
  if (!assessment || impacts.length === 0) {
    return '';
  }

  const levelText: Record<string, string> = {
    none: 'Clear conditions',
    low: 'Minor weather impact',
    moderate: 'Moderate weather conditions',
    high: 'Adverse weather warning',
    severe: 'Severe weather alert',
  };

  // Count conditions
  const conditionCounts = impacts.reduce((acc, imp) => {
    const main = imp.weather.conditions[0]?.main || 'Clear';
    acc[main] = (acc[main] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const conditionSummary = Object.entries(conditionCounts)
    .map(([cond, count]) => `${cond}: ${count} stops`)
    .join(', ');

  // Temperature range
  const temps = impacts.map(i => i.weather.temperature);
  const minTemp = Math.min(...temps).toFixed(0);
  const maxTemp = Math.max(...temps).toFixed(0);

  // Wind info
  const maxWind = Math.max(...impacts.map(i => i.weather.windSpeed));
  const avgWind = (impacts.reduce((s, i) => s + i.weather.windSpeed, 0) / impacts.length).toFixed(1);

  let summary = `\n\nWeather Assessment: ${levelText[assessment.level]}`;
  summary += `\nTemperature: ${minTemp}C to ${maxTemp}C`;
  summary += `\nConditions: ${conditionSummary}`;
  summary += `\nWind: avg ${avgWind} m/s, max ${maxWind.toFixed(1)} m/s`;
  summary += `\nTravel time adjustment: +${((assessment.travelTimeMultiplier - 1) * 100).toFixed(0)}%`;
  summary += `\nSafety score: ${assessment.safetyScore}/100`;

  if (assessment.recommendations.length > 0) {
    summary += `\nRecommendations: ${assessment.recommendations.slice(0, 2).join('; ')}`;
  }

  return summary;
}

export function ChatInterface() {
  const {
    messages,
    addMessage,
    addStreamingMessage,
    appendToStreamingMessage,
    finalizeStreamingMessage,
    isProcessing,
    setIsProcessing,
    isStreaming,
    debugMode,
    toggleDebugMode,
    setDebugData,
    lastCuOptRequest,
    lastCuOptResponse,
    lastGenAIPrompt,
    createConversation,
    currentConversationId,
    config,
  } = useChatStore();

  const { addToast } = useAppStore();
  const { setResult, setStops } = useOptimizationStore();
  const { config: appConfig } = useConfigStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate dynamic prompts based on configured location
  const dynamicPrompts = generateDynamicPrompts(
    appConfig.countryCode,
    appConfig.cityId,
    appConfig.activeScenario
  );

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Create conversation if needed
  useEffect(() => {
    if (!currentConversationId) {
      createConversation();
    }
  }, [currentConversationId, createConversation]);

  const switchToAirTraffic = useCallback((query: AirTrafficQuery) => {
    window.dispatchEvent(
      new CustomEvent('app:mode', { detail: { mode: 'airtraffic' } })
    );
    window.dispatchEvent(
      new CustomEvent('airtraffic:query', { detail: query })
    );
  }, []);

  const handleSend = useCallback(
    async (content: string, attachedStops?: Stop[]) => {
      // Add user message with file info if attached
      const userContent = attachedStops
        ? `${content}\n\n[Attached CSV: ${attachedStops.length} stops]`
        : content;
      addMessage({ role: 'user', content: userContent });
      setIsProcessing(true);

      try {
        // Step 0: Classify intent FIRST to avoid unnecessary API calls
        const intentResult = await genaiClient.classifyIntent(content);

        // Handle non-optimization intents without calling cuOPT
        if (intentResult.intent === 'greeting') {
          addMessage({
            role: 'assistant',
            content: `Hello! I'm your cuOPT AI Assistant. I can help you with:

**Route Optimization:** Tell me about your delivery or service routing needs
- "Optimize 50 deliveries with 5 vehicles in London"
- "Plan routes for 200 stops across the UK with 10 trucks"

**Questions:** Ask me about cuOPT, VRP, or route optimization
- "What is cuOPT?"
- "How does vehicle routing work?"

How can I assist you today?`,
          });
          setIsProcessing(false);
          return;
        }

        if (intentResult.intent === 'question' && intentResult.answer) {
          // Answer informational questions directly without calling solver
          addStreamingMessage();
          const words = intentResult.answer.split(' ');
          for (let i = 0; i < words.length; i++) {
            const word = words[i];
            const suffix = i < words.length - 1 ? ' ' : '';
            appendToStreamingMessage(word + suffix);
            await new Promise(resolve => setTimeout(resolve, 20));
          }
          finalizeStreamingMessage({
            model: config.model,
          });
          setIsProcessing(false);
          return;
        }

        const lowerContent = content.toLowerCase();
        const isAirTrafficQuery =
          lowerContent.includes('flight') ||
          lowerContent.includes('aircraft') ||
          lowerContent.includes('airport');

        if (isAirTrafficQuery) {
          const result = await genaiClient.convertToAirTrafficQuery(content);

          if (result.query) {
            addMessage({
              role: 'assistant',
              content: `✈️ ${result.interpretation}\n\nSwitching to Air Traffic view...`,
            });
            switchToAirTraffic(result.query);
          } else {
            addMessage({
              role: 'assistant',
              content: result.error || 'Could not process air traffic query.',
            });
          }

          setIsProcessing(false);
          return;
        }

        if (intentResult.intent === 'unclear' && intentResult.confidence < 0.6) {
          addMessage({
            role: 'assistant',
            content: `I'm not quite sure what you're looking for. Here's what I can help with:

**For Route Optimization**, tell me:
- How many stops/deliveries you have
- How many vehicles are available
- Any location or time constraints

**Example:** "Optimize 100 deliveries with 8 vehicles in Manchester"

**For Information**, ask questions like:
- "What is cuOPT?"
- "How does route optimization work?"

Could you provide more details about what you need?`,
          });
          setIsProcessing(false);
          return;
        }

        // Step 1: Convert prompt to cuOPT request using GenAI
        // If stops are attached, inform GenAI about the stop count
        const promptForGenAI = attachedStops
          ? `${content} (User has uploaded ${attachedStops.length} stops from CSV file)`
          : content;
        const { request, interpretation, error, numStops: extractedNumStops, numVehicles, useParallel: genaiUseParallel, numClusters: genaiNumClusters, stops: generatedStops, location: genaiLocation } =
          await genaiClient.convertPromptToCuOpt(promptForGenAI);

        // Use attached stops if available, otherwise use generated stops from genaiClient
        const numStops = attachedStops?.length || extractedNumStops;
        const stopsToUse = attachedStops || generatedStops || [];

        if (error || !request) {
          addMessage({
            role: 'assistant',
            content: `I couldn't fully understand that request. ${interpretation || error}

Could you please provide more details? For example:
- How many stops/deliveries do you have?
- How many vehicles are available?
- Are there any time constraints?`,
          });
          return;
        }

        setDebugData({ cuoptRequest: request, genaiPrompt: interpretation });

        // Use parallel processing if GenAI detected it from user prompt or if stops >= threshold
        const useParallel = genaiUseParallel || false;
        const numClusters = genaiNumClusters || (useParallel ? Math.min(Math.ceil((numStops || 500) / 500), 8) : 1);

        if (useParallel) {
          // Add message about parallel processing
          addMessage({
            role: 'assistant',
            content: `${interpretation}\n\nLarge problem detected (${numStops} stops). Using parallel processing with ${numClusters} clusters for faster optimization...`,
          });

          // Use stops from genaiClient (already generated with correct location coordinates)
          const stops = stopsToUse;

          // Fetch weather data for stops (sample first 10 for efficiency)
          let weatherSummary = '';
          try {
            const sampleStops = stops.slice(0, Math.min(10, stops.length));
            const weatherImpacts = await weatherClient.getRoutingImpact(sampleStops);

            if (weatherImpacts.length > 0) {
              // Calculate overall assessment
              const levels = ['none', 'low', 'moderate', 'high', 'severe'];
              let worstLevel = 'none';
              weatherImpacts.forEach((imp: WeatherRoutingImpact) => {
                if (levels.indexOf(imp.assessment.level) > levels.indexOf(worstLevel)) {
                  worstLevel = imp.assessment.level;
                }
              });

              const avgMultiplier = weatherImpacts.reduce((s: number, i: WeatherRoutingImpact) => s + i.assessment.travelTimeMultiplier, 0) / weatherImpacts.length;
              const avgSafety = weatherImpacts.reduce((s: number, i: WeatherRoutingImpact) => s + i.assessment.safetyScore, 0) / weatherImpacts.length;

              const overallAssessment: AdverseConditionAssessment = {
                level: worstLevel as AdverseConditionAssessment['level'],
                factors: weatherImpacts.flatMap((i: WeatherRoutingImpact) => i.assessment.factors).slice(0, 3),
                travelTimeMultiplier: avgMultiplier,
                safetyScore: avgSafety,
                recommendations: [...new Set(weatherImpacts.flatMap((i: WeatherRoutingImpact) => i.assessment.recommendations))].slice(0, 3) as string[],
              };

              weatherSummary = generateWeatherSummary(weatherImpacts, overallAssessment);
            }
          } catch (e) {
            // Weather fetch failed, continue without it
            console.log('Weather fetch failed:', e);
          }

          // Cluster the stops
          const clusters = cuoptClient.clusterStops(stops, numClusters);

          // Build payloads for each cluster
          const vehiclesPerCluster = Math.ceil((numVehicles || 10) / numClusters);
          const payloads = clusters.map((cluster) => {
            // Don't set startLat/startLng to avoid triggering home-start mode
            const vehicles = Array.from({ length: vehiclesPerCluster }, (_, i) => ({
              id: i,
              capacity: 100,
              startLat: 0,
              startLng: 0,
            }));
            return cuoptClient.buildPayload(cluster, vehicles, {
              numVehicles: vehiclesPerCluster,
              vehicleCapacity: 100,
              timeLimit: 60,
              objective: 'minimize_distance',
              enableTimeWindows: false,
              enableCapacity: true,
              parallelJobs: numClusters,
              parallelMode: 'auto',
              solverMode: 'balanced',
              enableHomeStart: false, // Explicitly disable home-start for AI chat
            });
          });

          // Run parallel optimization
          let runningClusters = 0;
          const results = await cuoptClient.solveParallel(
            payloads,
            numClusters,
            () => {
              // Progress callback - clusters completed
            },
            () => {
              runningClusters++;
              // Job started callback - could update UI here if needed
            }
          );

          // Merge results with unique numeric vehicle IDs
          let globalVehicleId = 0;
          const mergedVehicleData = results.flatMap((r, clusterIdx) =>
            (r?.vehicle_data || []).map((v: any) => ({
              ...v,
              vehicle_id: globalVehicleId++,
              cluster_id: clusterIdx,
            }))
          );

          const mergedResult = {
            status: 'SUCCESS' as const,
            num_vehicles: mergedVehicleData.length,
            solution_cost: results.reduce((sum, r) => sum + (r?.solution_cost || 0), 0),
            solve_time: Math.max(...results.map(r => r?.solve_time || 0)),
            vehicle_data: mergedVehicleData,
            clusters_used: numClusters,
            parallel_execution: true,
          };

          setDebugData({ cuoptResponse: mergedResult });

          // Sync results to Route Optimizer panel for detailed view
          setStops(stops);
          setResult(mergedResult);

          // Step 3: Convert response to natural language (pass weather context, stops, and location for scenario-aware metrics)
          const explanation = await genaiClient.convertResponseToNaturalLanguage(
            mergedResult,
            content,
            weatherSummary || undefined,
            stops,
            undefined, // scenarioId - let it auto-detect from prompt
            genaiLocation
          );

          // Stream the response word by word like ChatGPT
          let fullResponse = `${explanation}\n\nParallel Processing Complete: ${numClusters} clusters processed, ${mergedResult.num_vehicles} total vehicles, combined solve time ${mergedResult.solve_time.toFixed(2)}s`;

          // Add weather summary if available
          if (weatherSummary) {
            fullResponse += weatherSummary;
          }

          addStreamingMessage();
          const words = fullResponse.split(' ');

          for (let i = 0; i < words.length; i++) {
            const word = words[i];
            const suffix = i < words.length - 1 ? ' ' : '';
            appendToStreamingMessage(word + suffix);
            await new Promise(resolve => setTimeout(resolve, 25));
          }

          finalizeStreamingMessage({
            cuoptRequest: request,
            cuoptResponse: mergedResult,
            model: config.model,
          });

          addToast({
            type: 'success',
            title: 'Parallel Optimization Complete',
            message: `Processed ${numClusters} clusters with ${mergedResult.num_vehicles} vehicles`,
          });
        } else {
          // Standard single request for smaller problems
          addMessage({
            role: 'assistant',
            content: `${interpretation}\n\nRunning optimization...`,
          });

          // Use stops from genaiClient (already generated with correct location coordinates)
          const stops = stopsToUse;

          // Fetch weather data for stops
          let weatherSummary = '';
          try {
            const sampleStops = stops.slice(0, Math.min(10, stops.length));
            const weatherImpacts = await weatherClient.getRoutingImpact(sampleStops);

            if (weatherImpacts.length > 0) {
              const levels = ['none', 'low', 'moderate', 'high', 'severe'];
              let worstLevel = 'none';
              weatherImpacts.forEach((imp: WeatherRoutingImpact) => {
                if (levels.indexOf(imp.assessment.level) > levels.indexOf(worstLevel)) {
                  worstLevel = imp.assessment.level;
                }
              });

              const avgMultiplier = weatherImpacts.reduce((s: number, i: WeatherRoutingImpact) => s + i.assessment.travelTimeMultiplier, 0) / weatherImpacts.length;
              const avgSafety = weatherImpacts.reduce((s: number, i: WeatherRoutingImpact) => s + i.assessment.safetyScore, 0) / weatherImpacts.length;

              const overallAssessment: AdverseConditionAssessment = {
                level: worstLevel as AdverseConditionAssessment['level'],
                factors: weatherImpacts.flatMap((i: WeatherRoutingImpact) => i.assessment.factors).slice(0, 3),
                travelTimeMultiplier: avgMultiplier,
                safetyScore: avgSafety,
                recommendations: [...new Set(weatherImpacts.flatMap((i: WeatherRoutingImpact) => i.assessment.recommendations))].slice(0, 3) as string[],
              };

              weatherSummary = generateWeatherSummary(weatherImpacts, overallAssessment);
            }
          } catch (e) {
            console.log('Weather fetch failed:', e);
          }

          // Step 2: Call cuOPT API
          const cuoptResult = await cuoptClient.solveVRP(request);
          setDebugData({ cuoptResponse: cuoptResult });

          // Sync results to Route Optimizer panel for detailed view
          setStops(stops);
          setResult(cuoptResult);

          // Step 3: Convert response to natural language (pass weather context, stops, and location for scenario-aware metrics)
          const explanation = await genaiClient.convertResponseToNaturalLanguage(
            cuoptResult,
            content,
            weatherSummary || undefined,
            stops,
            undefined, // scenarioId - let it auto-detect from prompt
            genaiLocation
          );

          // Add weather to response
          let fullExplanation = explanation;
          if (weatherSummary) {
            fullExplanation += weatherSummary;
          }

          // Stream the response word by word like ChatGPT
          addStreamingMessage();
          const words = fullExplanation.split(' ');

          for (let i = 0; i < words.length; i++) {
            const word = words[i];
            const suffix = i < words.length - 1 ? ' ' : '';
            appendToStreamingMessage(word + suffix);
            // Small delay between words for typing effect
            await new Promise(resolve => setTimeout(resolve, 25));
          }

          // Finalize with metadata
          finalizeStreamingMessage({
            cuoptRequest: request,
            cuoptResponse: cuoptResult,
            model: config.model,
          });

          addToast({
            type: 'success',
            title: 'Optimization Complete',
            message: `Found solution with ${cuoptResult.num_vehicles} vehicles`,
          });
        }
      } catch (error) {
        addMessage({
          role: 'assistant',
          content: `I encountered an error while processing your request: ${
            error instanceof Error ? error.message : 'Unknown error'
          }

Please try again or rephrase your request.`,
        });

        addToast({
          type: 'error',
          title: 'Processing Error',
          message: error instanceof Error ? error.message : 'Unknown error',
        });
      } finally {
        setIsProcessing(false);
      }
    },
    [addMessage, setIsProcessing, setDebugData, addToast, setResult, setStops, config.model, switchToAirTraffic]
  );

  const handleExampleClick = (prompt: string) => {
    handleSend(prompt);
  };

  return (
    <div className="flex h-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Header */}
        <div className="border-b border-dark-border px-6 py-4 flex items-center justify-between bg-dark-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#C74634]/20 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-[#C74634]" />
            </div>
            <div>
              <h2 className="font-semibold text-white">cuOPT AI Assistant</h2>
              <p className="text-xs text-gray-400">
                Natural language route optimization
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            leftIcon={debugMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            onClick={toggleDebugMode}
          >
            {debugMode ? 'Hide Debug' : 'Debug'}
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-2xl bg-[#C74634]/10 flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8 text-[#C74634]" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                How can I help you today?
              </h3>
              <p className="text-gray-400 max-w-md mb-8">
                Describe your routing problem in natural language, and I'll
                create an optimized solution using NVIDIA cuOPT.
              </p>

              {/* Example Prompts - Dynamic based on configured location */}
              <div className="grid grid-cols-2 gap-3 max-w-2xl">
                {(dynamicPrompts.length > 0 ? dynamicPrompts : examplePrompts).slice(0, 4).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleExampleClick(prompt)}
                    className="p-4 bg-dark-card border border-dark-border rounded-xl text-left hover:bg-dark-hover hover:border-[#C74634]/30 transition-all group"
                  >
                    <span className="text-sm text-gray-300 group-hover:text-white">
                      {prompt}
                    </span>
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Location: {appConfig.cityId.charAt(0).toUpperCase() + appConfig.cityId.slice(1).replace('_', ' ')}, {appConfig.countryCode}
              </p>

              {/* Quick Test Categories - Dynamic based on location */}
              <div className="mt-6 text-left max-w-2xl">
                <p className="text-xs text-gray-500 mb-2">Quick Tests ({appConfig.cityId.charAt(0).toUpperCase() + appConfig.cityId.slice(1).replace('_', ' ')}):</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    { label: '50 Stops', prompt: dynamicPrompts[0] || examplePrompts[0] },
                    { label: '200 Stops', prompt: dynamicPrompts[1] || examplePrompts[1] },
                    { label: '500 Stops', prompt: dynamicPrompts[2] || examplePrompts[2] },
                    { label: 'Priority', prompt: dynamicPrompts[3] || examplePrompts[3] },
                    { label: 'National', prompt: dynamicPrompts[4] || examplePrompts[4] },
                    { label: appConfig.activeScenario === 'belron' ? 'Belron Jobs' : 'Regional', prompt: dynamicPrompts[6] || dynamicPrompts[5] || examplePrompts[5] },
                  ].filter(item => item.prompt).map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleExampleClick(item.prompt)}
                      className="px-3 py-1 text-xs bg-dark-bg border border-dark-border rounded-full text-gray-400 hover:text-[#C74634] hover:border-[#C74634]/50 transition-all"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} isStreaming={isStreaming && message.id === useChatStore.getState().streamingMessageId} />
              ))}
              {isProcessing && !isStreaming && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#C74634]/20 flex items-center justify-center">
                    <MessageSquare className="w-4 h-4 text-[#C74634]" />
                  </div>
                  <div className="bg-dark-card border border-dark-border rounded-2xl rounded-tl-none px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-[#C74634] rounded-full animate-bounce" />
                      <div
                        className="w-2 h-2 bg-[#C74634] rounded-full animate-bounce"
                        style={{ animationDelay: '0.1s' }}
                      />
                      <div
                        className="w-2 h-2 bg-[#C74634] rounded-full animate-bounce"
                        style={{ animationDelay: '0.2s' }}
                      />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <ChatInput onSend={handleSend} isProcessing={isProcessing} />
      </div>

      {/* Debug Panel */}
      {debugMode && (
        <div className="w-96 border-l border-dark-border bg-dark-bg overflow-y-auto">
          <div className="p-4 border-b border-dark-border">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Code className="w-4 h-4 text-[#C74634]" />
              Debug Panel
            </h3>
          </div>

          <div className="p-4 space-y-4">
            {/* GenAI Prompt */}
            {lastGenAIPrompt && (
              <Card variant="bordered" padding="sm">
                <CardHeader>
                  <CardTitle className="text-sm">Interpretation</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-gray-400">{lastGenAIPrompt}</p>
                </CardContent>
              </Card>
            )}

            {/* cuOPT Request */}
            {lastCuOptRequest && (
              <Card variant="bordered" padding="sm">
                <CardHeader>
                  <CardTitle className="text-sm">cuOPT Request</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="info">JSON</Badge>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(lastCuOptRequest, null, 2));
                      }}
                      className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-dark-hover"
                    >
                      Copy
                    </button>
                  </div>
                </CardHeader>
                <CardContent>
                  <pre className="text-xs text-gray-300 overflow-auto font-mono bg-dark-bg p-2 rounded max-h-64">
                    {JSON.stringify(lastCuOptRequest, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}

            {/* cuOPT Response */}
            {lastCuOptResponse && (
              <Card variant="bordered" padding="sm">
                <CardHeader>
                  <CardTitle className="text-sm">cuOPT Response</CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="success">Result</Badge>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(JSON.stringify(lastCuOptResponse, null, 2));
                      }}
                      className="text-xs text-gray-400 hover:text-white px-2 py-1 rounded hover:bg-dark-hover"
                    >
                      Copy
                    </button>
                  </div>
                </CardHeader>
                <CardContent>
                  <pre className="text-xs text-gray-300 overflow-auto font-mono bg-dark-bg p-2 rounded max-h-96">
                    {JSON.stringify(lastCuOptResponse, null, 2)}
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
