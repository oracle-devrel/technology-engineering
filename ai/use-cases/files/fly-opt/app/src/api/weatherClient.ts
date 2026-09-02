import type { Stop } from '@/types';
import type {
  AdverseConditionAssessment,
  AdverseConditionLevel,
  LocationWeather,
  WeatherCurrent,
  WeatherRoutingImpact,
} from '@/types/weather';

class WeatherClient {
  async getWeatherForStops(stops: Stop[]): Promise<Map<number, LocationWeather>> {
    const result = new Map<number, LocationWeather>();
    stops.forEach((stop) => {
      result.set(stop.id, this.createSyntheticWeather(stop.lat, stop.lng, stop.id));
    });
    return result;
  }

  async getRoutingImpact(stops: Stop[]): Promise<WeatherRoutingImpact[]> {
    const weatherMap = await this.getWeatherForStops(stops);
    return stops
      .map((stop) => {
        const weather = weatherMap.get(stop.id);
        if (!weather) {
          return null;
        }
        return {
          stopId: stop.id,
          weather: weather.current,
          assessment: this.assessAdverseConditions(weather.current),
        };
      })
      .filter((item): item is WeatherRoutingImpact => item !== null);
  }

  assessAdverseConditions(current: WeatherCurrent): AdverseConditionAssessment {
    const factors: AdverseConditionAssessment['factors'] = [];
    let scorePenalty = 0;
    let multiplier = 1;

    if (current.temperature <= 0 || current.temperature >= 35) {
      factors.push({
        type: 'temperature',
        severity: current.temperature <= -5 || current.temperature >= 40 ? 'high' : 'moderate',
        description: `Temperature ${current.temperature.toFixed(0)}C may impact operations`,
      });
      scorePenalty += current.temperature <= -5 || current.temperature >= 40 ? 20 : 10;
      multiplier += current.temperature <= -5 || current.temperature >= 40 ? 0.12 : 0.06;
    }

    if (current.windSpeed >= 8) {
      factors.push({
        type: 'wind',
        severity: current.windSpeed >= 14 ? 'high' : 'moderate',
        description: `Wind speed ${current.windSpeed.toFixed(1)} m/s may slow travel`,
      });
      scorePenalty += current.windSpeed >= 14 ? 22 : 11;
      multiplier += current.windSpeed >= 14 ? 0.15 : 0.08;
    }

    const rain = current.rain1h ?? 0;
    const snow = current.snow1h ?? 0;
    if (rain > 0 || snow > 0) {
      const heavy = rain >= 6 || snow >= 3;
      factors.push({
        type: 'precipitation',
        severity: heavy ? 'high' : 'moderate',
        description: heavy
          ? 'Heavy precipitation expected'
          : 'Light precipitation expected',
      });
      scorePenalty += heavy ? 25 : 12;
      multiplier += heavy ? 0.16 : 0.07;
    }

    if (typeof current.visibility === 'number' && current.visibility < 3000) {
      const severe = current.visibility < 1500;
      factors.push({
        type: 'visibility',
        severity: severe ? 'severe' : 'high',
        description: `Reduced visibility (${Math.round(current.visibility)} m)`,
      });
      scorePenalty += severe ? 30 : 18;
      multiplier += severe ? 0.2 : 0.1;
    }

    const level = this.toLevel(factors);
    const safetyScore = Math.max(0, Math.min(100, 100 - scorePenalty));

    return {
      level,
      factors,
      travelTimeMultiplier: Number(multiplier.toFixed(2)),
      safetyScore,
      recommendations: this.buildRecommendations(level),
    };
  }

  private toLevel(
    factors: AdverseConditionAssessment['factors']
  ): AdverseConditionLevel {
    if (factors.some((f) => f.severity === 'severe')) return 'severe';
    if (factors.some((f) => f.severity === 'high')) return 'high';
    if (factors.some((f) => f.severity === 'moderate')) return 'moderate';
    if (factors.some((f) => f.severity === 'low')) return 'low';
    return 'none';
  }

  private buildRecommendations(level: AdverseConditionLevel): string[] {
    if (level === 'none') return ['Normal operations'];
    if (level === 'low') return ['Monitor conditions'];
    if (level === 'moderate') return ['Add travel buffer', 'Prioritize critical jobs'];
    if (level === 'high') return ['Reduce route density', 'Dispatch with caution'];
    return ['Delay non-critical jobs', 'Consider temporary suspension in risk zones'];
  }

  private createSyntheticWeather(lat: number, lng: number, seed: number): LocationWeather {
    const hash = Math.abs(Math.sin((lat * 12.9898) + (lng * 78.233) + (seed * 0.1234)));
    const temperature = Number((8 + (hash * 30)).toFixed(1));
    const humidity = Math.round(35 + (hash * 60));
    const windSpeed = Number((1 + (hash * 14)).toFixed(1));
    const rain1h = hash > 0.75 ? Number(((hash - 0.74) * 10).toFixed(1)) : undefined;
    const visibility = Math.round(1200 + ((1 - hash) * 9000));

    const conditionId =
      rain1h && rain1h > 4 ? 501 : rain1h ? 500 : windSpeed > 12 ? 804 : 800;
    const conditionMain = rain1h ? 'Rain' : windSpeed > 12 ? 'Clouds' : 'Clear';
    const conditionDescription =
      rain1h && rain1h > 4
        ? 'moderate rain'
        : rain1h
        ? 'light rain'
        : windSpeed > 12
        ? 'overcast clouds'
        : 'clear sky';

    return {
      lat,
      lng,
      source: 'synthetic',
      current: {
        temperature,
        humidity,
        windSpeed,
        rain1h,
        visibility,
        conditions: [
          {
            id: conditionId,
            main: conditionMain,
            description: conditionDescription,
          },
        ],
        timestamp: Date.now(),
      },
    };
  }
}

export const weatherClient = new WeatherClient();
export default weatherClient;
