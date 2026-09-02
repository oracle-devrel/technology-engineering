import { create } from 'zustand';
import type { Stop } from '@/types';
import { weatherClient } from '@/api/weatherClient';
import type {
  AdverseConditionAssessment,
  AdverseConditionLevel,
  LocationWeather,
  WeatherRoutingImpact,
} from '@/types/weather';

interface WeatherState {
  weatherByStop: Map<number, LocationWeather>;
  routingImpacts: WeatherRoutingImpact[];
  overallAssessment: AdverseConditionAssessment | null;
  isLoading: boolean;
  fetchWeatherForStops: (stops: Stop[]) => Promise<void>;
  fetchRoutingImpacts: (stops: Stop[]) => Promise<void>;
  clearWeather: () => void;
}

function summarizeAssessment(impacts: WeatherRoutingImpact[]): AdverseConditionAssessment | null {
  if (impacts.length === 0) {
    return null;
  }

  const levelOrder: AdverseConditionLevel[] = ['none', 'low', 'moderate', 'high', 'severe'];
  const worstLevel = impacts.reduce<AdverseConditionLevel>((worst, impact) => {
    return levelOrder.indexOf(impact.assessment.level) > levelOrder.indexOf(worst)
      ? impact.assessment.level
      : worst;
  }, 'none');

  const avgMultiplier =
    impacts.reduce((sum, impact) => sum + impact.assessment.travelTimeMultiplier, 0) /
    impacts.length;
  const avgSafety =
    impacts.reduce((sum, impact) => sum + impact.assessment.safetyScore, 0) /
    impacts.length;

  const factors = Array.from(
    new Map(
      impacts
        .flatMap((impact) => impact.assessment.factors)
        .map((factor) => [`${factor.type}:${factor.description}`, factor] as const)
    ).values()
  );

  const recommendations = Array.from(
    new Set(impacts.flatMap((impact) => impact.assessment.recommendations))
  );

  return {
    level: worstLevel,
    factors,
    travelTimeMultiplier: Number(avgMultiplier.toFixed(2)),
    safetyScore: Number(avgSafety.toFixed(0)),
    recommendations,
  };
}

export const useWeatherStore = create<WeatherState>((set) => ({
  weatherByStop: new Map(),
  routingImpacts: [],
  overallAssessment: null,
  isLoading: false,

  fetchWeatherForStops: async (stops) => {
    set({ isLoading: true });
    try {
      const weatherByStop = await weatherClient.getWeatherForStops(stops);
      set({ weatherByStop });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchRoutingImpacts: async (stops) => {
    set({ isLoading: true });
    try {
      const routingImpacts = await weatherClient.getRoutingImpact(stops);
      set({
        routingImpacts,
        overallAssessment: summarizeAssessment(routingImpacts),
      });
    } finally {
      set({ isLoading: false });
    }
  },

  clearWeather: () =>
    set({
      weatherByStop: new Map(),
      routingImpacts: [],
      overallAssessment: null,
      isLoading: false,
    }),
}));
