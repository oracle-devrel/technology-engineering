export type AdverseConditionLevel = 'none' | 'low' | 'moderate' | 'high' | 'severe';

export interface WeatherCondition {
  id: number;
  main: string;
  description: string;
}

export interface WeatherCurrent {
  temperature: number;
  humidity: number;
  windSpeed: number;
  rain1h?: number;
  snow1h?: number;
  visibility?: number;
  conditions: WeatherCondition[];
  timestamp: number;
}

export interface LocationWeather {
  lat: number;
  lng: number;
  current: WeatherCurrent;
  source: 'synthetic';
}

export interface WeatherImpactFactor {
  type: 'temperature' | 'wind' | 'precipitation' | 'visibility';
  severity: AdverseConditionLevel;
  description: string;
}

export interface AdverseConditionAssessment {
  level: AdverseConditionLevel;
  factors: WeatherImpactFactor[];
  travelTimeMultiplier: number;
  safetyScore: number;
  recommendations: string[];
}

export interface WeatherRoutingImpact {
  stopId: number;
  weather: WeatherCurrent;
  assessment: AdverseConditionAssessment;
}
