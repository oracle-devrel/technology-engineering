// A relative API base preserves the AICoE per-session path prefix while still
// resolving to /api during local development at the site root.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'api';

// ── Types ──

export interface GaugeData {
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  total?: number;
}

export interface TrendPoint {
  week_label: string;
  positive_pct: number;
  neutral_pct: number;
  negative_pct: number;
  total_reviews: number;
  avg_score: number;
}

export interface AlertSource {
  url: string;
  domain: string;
  title: string;
  score?: number | null;
}

export interface Alert {
  id: number;
  alert_type: string;
  title: string;
  description: string;
  severity: string;
  source_count: number;
  sources: string;
  sources_data?: AlertSource[];
  detected_at: string;
  brand?: string | null;
}

export interface Action {
  id: number;
  action_text: string;
  priority: string;
  impact: string;
  category: string;
  status: string;
  alert_id: number;
  brand?: string | null;
}

export interface SourceInfo {
  source: string;
  count: number;
  avg_score: number | null;
}

export interface RecentReview {
  id: number;
  source: string;
  author: string;
  review_text: string;
  product: string;
  rating: number | null;
  sentiment: string | null;
  score: number | null;
}

export interface AspectInfo {
  aspect: string;
  count: number;
  avg_score: number;
  sentiment: string;
}

export interface EmotionInfo {
  emotion: string;
  count: number;
}

export interface DashboardData {
  gauges: GaugeData;
  avg_score: number;
  trends: TrendPoint[];
  alerts: Alert[];
  actions: Action[];
  sources: SourceInfo[];
  recent_reviews: RecentReview[];
  top_aspects: AspectInfo[];
  emotion_distribution: EmotionInfo[];
}

export interface ProgressEvent {
  type: 'step_start' | 'step_complete' | 'step_warning' | 'sentiment_progress' | 'complete' | 'error' | 'ping';
  step?: string;
  stepNumber?: number;
  totalSteps?: number;
  message?: string;
  result?: Record<string, unknown>;
  data?: Record<string, unknown>;
  error?: string;
  duration?: number;
}

export interface QueryResult {
  question: string;
  sql?: string;
  data?: Record<string, unknown>[];
  narrative?: string;
}

export interface VolumePoint {
  date: string;
  count: number;
}

export interface ScorePoint {
  date: string;
  avg_score: number;
  count: number;
}

export interface HistoryData {
  volume_over_time: VolumePoint[];
  score_history: ScorePoint[];
  brands: string[];
}

export interface CampaignVariant {
  variant_label: string;
  subject: string;
  body: string;
  tone: string;
  predicted_open_rate: number;
  rationale: string;
}

export interface CampaignResponse {
  variants: CampaignVariant[];
  brand: string;
  campaign_objective: string;
  tone: string;
}

// ── API Functions ──

export async function fetchDashboard(brand?: string): Promise<DashboardData> {
  const params = brand ? `?brand=${encodeURIComponent(brand)}` : '';
  const res = await fetch(`${API_BASE_URL}/dashboard${params}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch dashboard: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchAlerts(): Promise<Alert[]> {
  const res = await fetch(`${API_BASE_URL}/alerts`);
  if (!res.ok) {
    throw new Error(`Failed to fetch alerts: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchActions(): Promise<Action[]> {
  const res = await fetch(`${API_BASE_URL}/actions`);
  if (!res.ok) {
    throw new Error(`Failed to fetch actions: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function fetchHistory(brand?: string): Promise<HistoryData> {
  const params = brand ? `?brand=${encodeURIComponent(brand)}` : '';
  const res = await fetch(`${API_BASE_URL}/history${params}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch history: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function generateCampaign(
  brand: string,
  campaignObjective: string,
  tone: string
): Promise<CampaignResponse> {
  const res = await fetch(`${API_BASE_URL}/generate-campaign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      brand,
      campaign_objective: campaignObjective,
      tone,
    }),
  });
  if (!res.ok) {
    throw new Error(`Campaign generation failed: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

// ── SSE Streaming for Analysis ──

export function runAnalysis(
  topic: string,
  brand: string,
  useWebSearch: boolean,
  onProgress: (event: ProgressEvent) => void
): { cancel: () => void } {
  const controller = new AbortController();

  const startStream = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, brand, use_web_search: useWebSearch }),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Analysis request failed: ${response.status} ${response.statusText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          for (const line of part.split('\n')) {
            if (line.startsWith('data: ')) {
              try {
                const data: ProgressEvent = JSON.parse(line.slice(6));
                onProgress(data);
              } catch {
                // Skip malformed JSON lines
              }
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name !== 'AbortError') {
        onProgress({
          type: 'error',
          error: err.message || 'Connection failed',
        });
      }
    }
  };

  startStream();

  return {
    cancel: () => controller.abort(),
  };
}

// ── RAG Knowledge Base Query ──

export interface RAGResult {
  question: string;
  answer: string;
}

export async function sendRAGQuery(question: string): Promise<RAGResult> {
  const res = await fetch(`${API_BASE_URL}/rag-query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    throw new Error(`RAG query failed: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

// ── Natural Language Query ──

export async function sendQuery(question: string): Promise<QueryResult> {
  const res = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });

  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const errorBody = await res.json();
      if (typeof errorBody?.detail === 'string' && errorBody.detail.trim()) {
        detail = errorBody.detail;
      }
    } catch {
      // Keep the HTTP status when the backend did not return JSON.
    }
    throw new Error(`Query failed: ${detail}`);
  }

  return res.json();
}
