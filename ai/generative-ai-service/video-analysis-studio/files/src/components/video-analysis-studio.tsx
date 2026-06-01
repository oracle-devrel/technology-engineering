// Copyright (c) 2026 Oracle and/or its affiliates.
// SPDX-License-Identifier: UPL-1.0

import {
  Check,
  ChevronDown,
  CircleX,
  Clipboard,
  Columns3,
  Download,
  FileText,
  FileVideo,
  GitCompareArrows,
  Loader2,
  Maximize2,
  PlayCircle,
  RefreshCw,
  Info,
  UploadCloud,
  X
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

type StudioMode = "standalone" | "embedded";

type AnalysisMode =
  | "video-summary"
  | "timeline-key-events"
  | "compliance-safety-review"
  | "object-scene-description"
  | "custom-prompt";

type ModelId = string;

type ApiMetadata = {
  latency_ms?: number;
  input_tokens?: number | null;
  output_tokens?: number | null;
};

type ModelPricing = {
  input_per_million?: number;
  audio_input_per_million?: number;
  output_per_million?: number;
  long_context_input_per_million?: number;
  long_context_output_per_million?: number;
  long_context_threshold_tokens?: number;
  currency?: string;
  source?: string;
};

type ModelFeatures = {
  input_modalities?: string[];
  output_modalities?: string[];
  max_input_tokens?: number;
  max_output_tokens?: number;
  supports_tools?: boolean;
  structured_output?: boolean;
  context_caching?: boolean;
  thinking?: boolean;
  source?: string;
};

type RunMode = "single" | "compare";

type ComparisonStatus = "running" | "success" | "error";

type ComparisonResult = {
  modelId: ModelId;
  status: ComparisonStatus;
  output: string;
  apiMetadata: ApiMetadata | null;
  error: string;
};

type AnalysisResponse = {
  output?: string;
  model_id?: string;
  analysis_mode?: string;
  api_metadata?: ApiMetadata;
  error?: string;
  detail?: string;
};

type ExpandedOutput = {
  title: string;
  modelId: string;
  model: ModelOption;
  output: string;
  apiMetadata: ApiMetadata | null;
};

type ModelOption = {
  label: string;
  value: ModelId;
  detail: string;
  provider?: string;
  capabilities?: string[];
  available_regions?: string[];
  pricing?: ModelPricing;
  features?: ModelFeatures;
  source?: string;
};

type EndpointOption = {
  label: string;
  region: string;
  endpoint: string;
  supportedModels: ModelId[];
  source?: string;
};

type ModelCatalogResponse = {
  source?: string;
  models?: ModelOption[];
  endpoints?: EndpointOption[];
  default_model_id?: ModelId;
  default_region?: string;
  error?: string;
  detail?: string;
};

type EditableElement = HTMLInputElement | HTMLTextAreaElement;

const FALLBACK_MODEL_METADATA: Record<string, Pick<ModelOption, "pricing" | "features">> = {
  "google.gemini-2.5-pro": {
    pricing: {
      input_per_million: 1.25,
      output_per_million: 10,
      long_context_input_per_million: 2.5,
      long_context_output_per_million: 15,
      long_context_threshold_tokens: 200000,
      currency: "USD",
      source: "oracle_price_list_env"
    },
    features: {
      input_modalities: ["text", "image", "video", "audio"],
      output_modalities: ["text"],
      max_input_tokens: 1048576,
      max_output_tokens: 65536,
      supports_tools: true,
      structured_output: true,
      context_caching: true,
      thinking: true,
      source: "oracle_model_docs_env"
    }
  },
  "google.gemini-2.5-flash": {
    pricing: {
      input_per_million: 0.3,
      audio_input_per_million: 1,
      output_per_million: 2.5,
      currency: "USD",
      source: "oracle_price_list_env"
    },
    features: {
      input_modalities: ["text", "image", "video", "audio"],
      output_modalities: ["text"],
      max_input_tokens: 1048576,
      max_output_tokens: 65536,
      supports_tools: true,
      structured_output: true,
      context_caching: true,
      thinking: true,
      source: "oracle_model_docs_env"
    }
  },
  "google.gemini-2.5-flash-lite": {
    pricing: {
      input_per_million: 0.1,
      audio_input_per_million: 0.5,
      output_per_million: 0.4,
      currency: "USD",
      source: "oracle_price_list_env"
    },
    features: {
      input_modalities: ["text", "image", "video", "audio"],
      output_modalities: ["text"],
      max_input_tokens: 1048576,
      max_output_tokens: 65536,
      supports_tools: true,
      structured_output: true,
      context_caching: true,
      thinking: false,
      source: "oracle_model_docs_env"
    }
  }
};

function withFallbackModelMetadata(model: ModelOption): ModelOption {
  const fallback = FALLBACK_MODEL_METADATA[model.value];

  if (!fallback) {
    return model;
  }

  return {
    ...model,
    pricing: { ...fallback.pricing, ...model.pricing },
    features: { ...fallback.features, ...model.features }
  };
}

export type VideoAnalysisStudioProps = {
  mode?: StudioMode;
  apiUrl?: string;
  className?: string;
  initialCompartmentId?: string;
  initialServiceEndpoint?: string;
  initialRegion?: string;
  initialModelId?: ModelId;
  catalogUrl?: string;
};

const MODEL_OPTIONS: ModelOption[] = [
  {
    label: "Gemini 2.5 Pro",
    value: "google.gemini-2.5-pro",
    detail: "Highest quality reasoning"
  },
  {
    label: "Gemini 2.5 Flash",
    value: "google.gemini-2.5-flash",
    detail: "Balanced latency and quality"
  },
  {
    label: "Gemini 2.5 Flash-Lite",
    value: "google.gemini-2.5-flash-lite",
    detail: "Fastest lightweight analysis"
  }
].map(withFallbackModelMetadata);

const OCI_GENAI_ENDPOINT_OPTIONS: EndpointOption[] = [
  {
    label: "US Midwest (Chicago)",
    region: "us-chicago-1",
    endpoint: "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    supportedModels: [
      "google.gemini-2.5-pro",
      "google.gemini-2.5-flash",
      "google.gemini-2.5-flash-lite"
    ]
  },
  {
    label: "US East (Ashburn, identity domain G)",
    region: "us-ashburn-1",
    endpoint: "https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com",
    supportedModels: [
      "google.gemini-2.5-pro",
      "google.gemini-2.5-flash",
      "google.gemini-2.5-flash-lite"
    ]
  },
  {
    label: "US West (Phoenix)",
    region: "us-phoenix-1",
    endpoint: "https://inference.generativeai.us-phoenix-1.oci.oraclecloud.com",
    supportedModels: [
      "google.gemini-2.5-pro",
      "google.gemini-2.5-flash",
      "google.gemini-2.5-flash-lite"
    ]
  },
  {
    label: "Germany Central (Frankfurt, identity domain G)",
    region: "eu-frankfurt-1",
    endpoint: "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
    supportedModels: [
      "google.gemini-2.5-pro",
      "google.gemini-2.5-flash",
      "google.gemini-2.5-flash-lite"
    ]
  },
  {
    label: "India South (Hyderabad)",
    region: "ap-hyderabad-1",
    endpoint: "https://inference.generativeai.ap-hyderabad-1.oci.oraclecloud.com",
    supportedModels: ["google.gemini-2.5-flash"]
  },
  {
    label: "Japan Central (Osaka)",
    region: "ap-osaka-1",
    endpoint: "https://inference.generativeai.ap-osaka-1.oci.oraclecloud.com",
    supportedModels: ["google.gemini-2.5-pro", "google.gemini-2.5-flash"]
  }
];

const ANALYSIS_MODES: Array<{ label: string; value: AnalysisMode; prompt: string }> = [
  {
    label: "Video summary",
    value: "video-summary",
    prompt: "Describe what is happening in this video. Provide a concise summary."
  },
  {
    label: "Timeline / key events",
    value: "timeline-key-events",
    prompt:
      "Analyze this video and list the key events in chronological order. Include approximate timestamps where possible."
  },
  {
    label: "Compliance or safety review",
    value: "compliance-safety-review",
    prompt:
      "Analyze this video for possible compliance, safety, policy, or operational risks. Return findings with severity, timestamp if visible, and recommended action."
  },
  {
    label: "Object / scene description",
    value: "object-scene-description",
    prompt:
      "Describe the visible scenes, objects, people, movements, and context in this video."
  },
  {
    label: "Custom prompt",
    value: "custom-prompt",
    prompt: ""
  }
];

const DEFAULT_ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com";
const MAX_UPLOAD_MB = 37;
const MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024;
const COST_ESTIMATE_DOCUMENT_SCALE = 1000;
const REDACTED_SECRET = "[redacted secret]";

const SECRET_PATTERNS = [
  /-----BEGIN[\s\S]*?PRIVATE KEY-----[\s\S]*?-----END[\s\S]*?PRIVATE KEY-----/gi,
  /\b(security_token|auth_token|access_token|refresh_token|private_key|api_key)\s*[:=]\s*['"]?[^'"\s]+/gi,
  /\bpass_phrase\s*[:=]\s*['"]?[^'"\s]+/gi
];

type MarkdownInlineSegment =
  | { type: "text"; value: string }
  | { type: "code"; value: string }
  | { type: "strong"; value: string }
  | { type: "em"; value: string }
  | { type: "link"; value: string; href: string };

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatMetric(value: number | null | undefined, suffix = "") {
  return typeof value === "number" ? `${value}${suffix}` : "Not returned";
}

function formatLatency(value: number | null | undefined) {
  return typeof value === "number" ? `${value} ms` : "Not returned";
}

function formatTokenLimit(value: number | null | undefined) {
  if (typeof value !== "number") {
    return "Not returned";
  }

  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(value % 1000000 === 0 ? 0 : 1)}M`;
  }

  if (value >= 1000) {
    return `${Math.round(value / 1000)}K`;
  }

  return `${value}`;
}

function formatCurrency(value: number | null | undefined, currency = "USD") {
  if (typeof value !== "number") {
    return "Not returned";
  }

  if (value === 0) {
    return "$0.00";
  }

  if (value < 0.01) {
    return `< $0.01`;
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 4
  }).format(value);
}

function formatPricePerMillion(value: number | null | undefined, currency = "USD") {
  if (typeof value !== "number") {
    return "Not returned";
  }

  return `${new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 4
  }).format(value)} / M tokens`;
}

function formatBooleanFeature(value: boolean | undefined) {
  if (typeof value !== "boolean") {
    return "Unknown";
  }

  return value ? "Yes" : "No";
}

function formatListFeature(values: string[] | undefined) {
  return values && values.length > 0 ? values.join(", ") : "Not returned";
}

function getEstimatedCost(model: ModelOption, metadata: ApiMetadata | null | undefined) {
  const pricing = model.pricing;
  const inputTokens = metadata?.input_tokens;
  const outputTokens = metadata?.output_tokens;

  if (
    !pricing ||
    typeof inputTokens !== "number" ||
    typeof outputTokens !== "number" ||
    typeof pricing.input_per_million !== "number" ||
    typeof pricing.output_per_million !== "number"
  ) {
    return null;
  }

  const baseInputRate = pricing.input_per_million;
  const baseOutputRate = pricing.output_per_million;
  const useLongContextRates =
    typeof pricing.long_context_threshold_tokens === "number" &&
    inputTokens > pricing.long_context_threshold_tokens &&
    typeof pricing.long_context_input_per_million === "number" &&
    typeof pricing.long_context_output_per_million === "number";
  const inputRate = useLongContextRates
    ? pricing.long_context_input_per_million!
    : baseInputRate;
  const outputRate = useLongContextRates
    ? pricing.long_context_output_per_million!
    : baseOutputRate;

  return {
    value: (inputTokens / 1000000) * inputRate + (outputTokens / 1000000) * outputRate,
    currency: pricing.currency || "USD",
    usesLongContextRates: useLongContextRates
  };
}

function formatEstimatedCost(model: ModelOption, metadata: ApiMetadata | null | undefined) {
  const cost = getEstimatedCost(model, metadata);

  if (!cost) {
    return "Not returned";
  }

  return `${formatCurrency(cost.value * COST_ESTIMATE_DOCUMENT_SCALE, cost.currency)}${
    cost.usesLongContextRates ? " long context" : ""
  }`;
}

function getModelOption(modelId: string, modelOptions = MODEL_OPTIONS) {
  return modelOptions.find((item) => item.value === modelId) ?? modelOptions[1] ?? MODEL_OPTIONS[1];
}

function getEndpointOption(endpoint: string, endpointOptions = OCI_GENAI_ENDPOINT_OPTIONS) {
  return (
    endpointOptions.find((item) => item.endpoint === endpoint) ??
    endpointOptions[0] ??
    OCI_GENAI_ENDPOINT_OPTIONS[0]
  );
}

function endpointSupportsModels(endpoint: EndpointOption, modelIds: ModelId[]) {
  return modelIds.every((modelId) => endpoint.supportedModels.includes(modelId));
}

function chooseEndpointForModels(
  modelIds: ModelId[],
  currentEndpoint: string,
  endpointOptions: EndpointOption[]
) {
  const endpoints = endpointOptions.length > 0 ? endpointOptions : OCI_GENAI_ENDPOINT_OPTIONS;
  const current = endpoints.find((item) => item.endpoint === currentEndpoint);

  if (current && endpointSupportsModels(current, modelIds)) {
    return current;
  }

  return (
    endpoints.find(
      (item) => item.region === "eu-frankfurt-1" && endpointSupportsModels(item, modelIds)
    ) ?? endpoints.find((item) => endpointSupportsModels(item, modelIds))
  );
}

function getCatalogUrl(apiUrl: string, explicitCatalogUrl?: string) {
  if (explicitCatalogUrl) {
    return explicitCatalogUrl;
  }

  return apiUrl.endsWith("/api/analyze-video")
    ? apiUrl.replace(/\/api\/analyze-video$/, "/api/model-catalog")
    : "/api/model-catalog";
}

function getCatalogDiscoverUrl(catalogUrl: string) {
  return `${catalogUrl.replace(/\/$/, "")}/discover`;
}

function isSafeMarkdownHref(href: string) {
  return /^https?:\/\//i.test(href);
}

function parseMarkdownInline(value: string) {
  const segments: MarkdownInlineSegment[] = [];
  const inlinePattern = /(`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*|\[[^\]]+\]\([^)]+\))/g;
  let cursor = 0;

  for (const match of value.matchAll(inlinePattern)) {
    const token = match[0];
    const index = match.index ?? 0;

    if (index > cursor) {
      segments.push({ type: "text", value: value.slice(cursor, index) });
    }

    if (token.startsWith("`")) {
      segments.push({ type: "code", value: token.slice(1, -1) });
    } else if (token.startsWith("**")) {
      segments.push({ type: "strong", value: token.slice(2, -2) });
    } else if (token.startsWith("*")) {
      segments.push({ type: "em", value: token.slice(1, -1) });
    } else {
      const linkMatch = token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      segments.push(
        linkMatch
          ? { type: "link", value: linkMatch[1], href: linkMatch[2] }
          : { type: "text", value: token }
      );
    }

    cursor = index + token.length;
  }

  if (cursor < value.length) {
    segments.push({ type: "text", value: value.slice(cursor) });
  }

  return segments;
}

function renderInlineMarkdown(value: string): ReactNode[] {
  return parseMarkdownInline(value).map((segment, index) => {
    const key = `${segment.type}-${index}`;

    if (segment.type === "code") {
      return <code key={key}>{segment.value}</code>;
    }

    if (segment.type === "strong") {
      return <strong key={key}>{segment.value}</strong>;
    }

    if (segment.type === "em") {
      return <em key={key}>{segment.value}</em>;
    }

    if (segment.type === "link" && isSafeMarkdownHref(segment.href)) {
      return (
        <a key={key} href={segment.href} target="_blank" rel="noreferrer">
          {segment.value}
        </a>
      );
    }

    return <span key={key}>{segment.value}</span>;
  });
}

function isMarkdownTableSeparator(value: string) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(value);
}

function parseMarkdownTableRow(value: string) {
  return value
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function MarkdownOutput({ value, className = "" }: { value: string; className?: string }) {
  const lines = value.trim().split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (/^```(\w+)?\s*$/.test(line)) {
      const codeLines: string[] = [];
      index += 1;

      while (index < lines.length && !lines[index].startsWith("```")) {
        codeLines.push(lines[index]);
        index += 1;
      }

      if (index < lines.length) {
        index += 1;
      }

      blocks.push(
        <pre key={`code-${index}`}>
          <code>{codeLines.join("\n")}</code>
        </pre>
      );
      continue;
    }

    const headingMatch = line.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const content = renderInlineMarkdown(headingMatch[2]);
      blocks.push(
        level === 1 ? (
          <h1 key={`heading-${index}`}>{content}</h1>
        ) : level === 2 ? (
          <h2 key={`heading-${index}`}>{content}</h2>
        ) : (
          <h3 key={`heading-${index}`}>{content}</h3>
        )
      );
      index += 1;
      continue;
    }

    if (/^\s*[-*_]{3,}\s*$/.test(line)) {
      blocks.push(<hr key={`rule-${index}`} />);
      index += 1;
      continue;
    }

    if (line.includes("|") && index + 1 < lines.length && isMarkdownTableSeparator(lines[index + 1])) {
      const headerCells = parseMarkdownTableRow(line);
      const rows: string[][] = [];
      index += 2;

      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        rows.push(parseMarkdownTableRow(lines[index]));
        index += 1;
      }

      blocks.push(
        <div className="markdown-table-wrap" key={`table-${index}`}>
          <table>
            <thead>
              <tr>
                {headerCells.map((cell, cellIndex) => (
                  <th key={`head-${cellIndex}`}>{renderInlineMarkdown(cell)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`row-${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`cell-${rowIndex}-${cellIndex}`}>{renderInlineMarkdown(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    const listMatch = line.match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/);
    if (listMatch) {
      const ordered = /^\s*\d+[.)]\s+/.test(line);
      const items: string[] = [];

      while (index < lines.length) {
        const currentMatch = lines[index].match(/^\s*(?:[-*]|\d+[.)])\s+(.+)$/);
        if (!currentMatch || /^\s*\d+[.)]\s+/.test(lines[index]) !== ordered) {
          break;
        }

        items.push(currentMatch[1]);
        index += 1;
      }

      blocks.push(
        ordered ? (
          <ol key={`list-${index}`}>
            {items.map((item, itemIndex) => (
              <li key={`item-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
            ))}
          </ol>
        ) : (
          <ul key={`list-${index}`}>
            {items.map((item, itemIndex) => (
              <li key={`item-${itemIndex}`}>{renderInlineMarkdown(item)}</li>
            ))}
          </ul>
        )
      );
      continue;
    }

    if (/^\s*>/.test(line)) {
      const quoteLines: string[] = [];

      while (index < lines.length && /^\s*>/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^\s*>\s?/, ""));
        index += 1;
      }

      blocks.push(
        <blockquote key={`quote-${index}`}>
          {quoteLines.map((quoteLine, quoteIndex) => (
            <p key={`quote-line-${quoteIndex}`}>{renderInlineMarkdown(quoteLine)}</p>
          ))}
        </blockquote>
      );
      continue;
    }

    const paragraphLines = [line.trim()];
    index += 1;

    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^```/.test(lines[index]) &&
      !/^(#{1,3})\s+/.test(lines[index]) &&
      !/^\s*(?:[-*]|\d+[.)])\s+/.test(lines[index]) &&
      !/^\s*>/.test(lines[index])
    ) {
      paragraphLines.push(lines[index].trim());
      index += 1;
    }

    blocks.push(
      <p key={`paragraph-${index}`}>{renderInlineMarkdown(paragraphLines.join(" "))}</p>
    );
  }

  return <div className={`markdown-output ${className}`}>{blocks}</div>;
}

function MetricStack({
  model,
  metadata,
  compact = false
}: {
  model: ModelOption;
  metadata: ApiMetadata | null | undefined;
  compact?: boolean;
}) {
  return (
    <div className={compact ? "metric-stack metric-stack-compact" : "metric-stack"}>
      <div className="metric-row">
        <span>Input tokens</span>
        <strong>{formatMetric(metadata?.input_tokens)}</strong>
      </div>
      <div className="metric-row">
        <span>Output tokens</span>
        <strong>{formatMetric(metadata?.output_tokens)}</strong>
      </div>
      <div className="metric-row">
        <span>Latency</span>
        <strong>{formatLatency(metadata?.latency_ms)}</strong>
      </div>
      <div className="metric-row">
        <span title="Projected from this run's input and output token counts.">
          Estimated cost / 1K docs*
        </span>
        <strong>{formatEstimatedCost(model, metadata)}</strong>
      </div>
    </div>
  );
}

function ModelInfoPanel({
  model,
  compact = false
}: {
  model: ModelOption;
  compact?: boolean;
}) {
  const pricing = model.pricing ?? {};
  const features = model.features ?? {};
  const currency = pricing.currency || "USD";

  return (
    <div className={compact ? "model-info-panel model-info-panel-compact" : "model-info-panel"}>
      <section>
        <h4>Pricing</h4>
        <div className="model-info-row">
          <span>Text/image/video input</span>
          <strong>{formatPricePerMillion(pricing.input_per_million, currency)}</strong>
        </div>
        {typeof pricing.audio_input_per_million === "number" && (
          <div className="model-info-row">
            <span>Audio input</span>
            <strong>{formatPricePerMillion(pricing.audio_input_per_million, currency)}</strong>
          </div>
        )}
        <div className="model-info-row">
          <span>Output</span>
          <strong>{formatPricePerMillion(pricing.output_per_million, currency)}</strong>
        </div>
        {typeof pricing.long_context_threshold_tokens === "number" && (
          <div className="model-info-row">
            <span>Long context</span>
            <strong>{`>${formatTokenLimit(pricing.long_context_threshold_tokens)} tokens`}</strong>
          </div>
        )}
      </section>

      <section>
        <h4>Features</h4>
        <div className="model-info-row">
          <span>Input modalities</span>
          <strong>{formatListFeature(features.input_modalities)}</strong>
        </div>
        <div className="model-info-row">
          <span>Output modalities</span>
          <strong>{formatListFeature(features.output_modalities)}</strong>
        </div>
        <div className="model-info-row">
          <span>Max input tokens</span>
          <strong>{formatTokenLimit(features.max_input_tokens)}</strong>
        </div>
        <div className="model-info-row">
          <span>Max output tokens</span>
          <strong>{formatTokenLimit(features.max_output_tokens)}</strong>
        </div>
        <div className="model-info-row">
          <span>Supports tools</span>
          <strong>{formatBooleanFeature(features.supports_tools)}</strong>
        </div>
        <div className="model-info-row">
          <span>Structured output</span>
          <strong>{formatBooleanFeature(features.structured_output)}</strong>
        </div>
        <div className="model-info-row">
          <span>Context caching</span>
          <strong>{formatBooleanFeature(features.context_caching)}</strong>
        </div>
        <div className="model-info-row">
          <span>Thinking</span>
          <strong>{formatBooleanFeature(features.thinking)}</strong>
        </div>
      </section>

      <section>
        <h4>Availability</h4>
        <div className="model-info-row">
          <span>Available regions</span>
          <strong>{model.available_regions?.length ?? 0}</strong>
        </div>
      </section>
    </div>
  );
}

function getPrompt(mode: AnalysisMode) {
  return ANALYSIS_MODES.find((item) => item.value === mode)?.prompt ?? "";
}

function describeApiTarget(apiUrl: string) {
  if (apiUrl.startsWith("http")) {
    return apiUrl;
  }

  return `${window.location.origin}${apiUrl}`;
}

function looksLikeOciConfigContents(value: string) {
  const configKeys = ["[default]", "user=", "fingerprint=", "tenancy=", "key_file="];
  const normalized = value.toLowerCase();
  return configKeys.filter((key) => normalized.includes(key)).length >= 3;
}

function redactSecrets(value: string) {
  let redacted = value;
  let changed = false;

  for (const pattern of SECRET_PATTERNS) {
    redacted = redacted.replace(pattern, () => {
      changed = true;
      return REDACTED_SECRET;
    });
  }

  if (looksLikeOciConfigContents(redacted)) {
    changed = true;
    redacted = REDACTED_SECRET;
  }

  return { value: redacted, changed };
}

export function VideoAnalysisStudio({
  mode = "standalone",
  apiUrl = "/api/analyze-video",
  className = "",
  initialCompartmentId = "",
  initialServiceEndpoint = DEFAULT_ENDPOINT,
  initialRegion = "eu-frankfurt-1",
  initialModelId = "google.gemini-2.5-flash",
  catalogUrl
}: VideoAnalysisStudioProps) {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreviewUrl, setVideoPreviewUrl] = useState("");
  const [compartmentId, setCompartmentId] = useState(initialCompartmentId);
  const [compartmentDisplayValue, setCompartmentDisplayValue] = useState(initialCompartmentId);
  const [isCompartmentFocused, setIsCompartmentFocused] = useState(false);
  const [serviceEndpoint, setServiceEndpoint] = useState(initialServiceEndpoint);
  const [region, setRegion] = useState(initialRegion);
  const [modelId, setModelId] = useState<ModelId>(initialModelId);
  const [modelOptions, setModelOptions] = useState<ModelOption[]>(MODEL_OPTIONS);
  const [endpointOptions, setEndpointOptions] =
    useState<EndpointOption[]>(OCI_GENAI_ENDPOINT_OPTIONS);
  const [isRefreshingCatalog, setIsRefreshingCatalog] = useState(false);
  const [runMode, setRunMode] = useState<RunMode>("single");
  const [comparisonModelIds, setComparisonModelIds] = useState<ModelId[]>(() =>
    getEndpointOption(initialServiceEndpoint).supportedModels.slice(0, 3)
  );
  const [comparisonResults, setComparisonResults] = useState<ComparisonResult[]>([]);
  const [modelOcid, setModelOcid] = useState("");
  const [authProfile, setAuthProfile] = useState("DEFAULT");
  const [authFileLocation, setAuthFileLocation] = useState("~/.oci/config");
  const [showAuthDetails, setShowAuthDetails] = useState(false);
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("video-summary");
  const [prompt, setPrompt] = useState(getPrompt("video-summary"));
  const [output, setOutput] = useState("");
  const [apiMetadata, setApiMetadata] = useState<ApiMetadata | null>(null);
  const [error, setError] = useState("");
  const [securityWarning, setSecurityWarning] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(true);
  const [copyLabel, setCopyLabel] = useState("Copy output");
  const [renderMarkdown, setRenderMarkdown] = useState(false);
  const [expandedOutput, setExpandedOutput] = useState<ExpandedOutput | null>(null);
  const resolvedCatalogUrl = useMemo(() => getCatalogUrl(apiUrl, catalogUrl), [apiUrl, catalogUrl]);

  const selectedModel = useMemo(
    () => getModelOption(modelId, modelOptions),
    [modelId, modelOptions]
  );
  const selectedEndpoint = useMemo(
    () => getEndpointOption(serviceEndpoint, endpointOptions),
    [serviceEndpoint, endpointOptions]
  );
  const selectedComparisonModels = useMemo(
    () => comparisonModelIds.map((id) => getModelOption(id, modelOptions)),
    [comparisonModelIds, modelOptions]
  );
  const usingModelOcid = modelOcid.trim().length > 0;
  const displayedCompartmentId = isCompartmentFocused ? compartmentId : compartmentDisplayValue;
  const isBusy = isRunning || isComparing;
  const comparisonSuccessResults = useMemo(
    () => comparisonResults.filter((result) => result.status === "success"),
    [comparisonResults]
  );
  const fastestComparisonResult = useMemo(
    () =>
      comparisonSuccessResults.reduce<ComparisonResult | null>((fastest, result) => {
        const latency = result.apiMetadata?.latency_ms;
        const fastestLatency = fastest?.apiMetadata?.latency_ms;

        if (typeof latency !== "number") {
          return fastest;
        }

        if (typeof fastestLatency !== "number" || latency < fastestLatency) {
          return result;
        }

        return fastest;
      }, null),
    [comparisonSuccessResults]
  );
  const lowestOutputTokenResult = useMemo(
    () =>
      comparisonSuccessResults.reduce<ComparisonResult | null>((lowest, result) => {
        const outputTokens = result.apiMetadata?.output_tokens;
        const lowestTokens = lowest?.apiMetadata?.output_tokens;

        if (typeof outputTokens !== "number") {
          return lowest;
        }

        if (typeof lowestTokens !== "number" || outputTokens < lowestTokens) {
          return result;
        }

        return lowest;
      }, null),
    [comparisonSuccessResults]
  );
  const comparisonOutputText = useMemo(
    () =>
      comparisonResults
        .map((result) => {
          const model = getModelOption(result.modelId, modelOptions);
          const metadata = result.apiMetadata;

          return [
            `Model: ${model.label} (${result.modelId})`,
            `Status: ${result.status}`,
            `Latency: ${formatLatency(metadata?.latency_ms)}`,
            `Input tokens: ${formatMetric(metadata?.input_tokens)}`,
            `Output tokens: ${formatMetric(metadata?.output_tokens)}`,
            `Estimated cost / 1K similar docs: ${formatEstimatedCost(model, metadata)}`,
            result.status === "error"
              ? `Error: ${result.error}`
              : `Output:\n${result.output || "No output returned."}`
          ].join("\n");
        })
        .join("\n\n---\n\n"),
    [comparisonResults, modelOptions]
  );
  const activeOutputText = runMode === "compare" ? comparisonOutputText : output;
  const copyButtonLabel =
    copyLabel === "Copied" ? "Copied" : runMode === "compare" ? "Copy comparison" : "Copy output";

  useEffect(() => {
    if (!videoFile) {
      setVideoPreviewUrl("");
      return;
    }

    const objectUrl = URL.createObjectURL(videoFile);
    setVideoPreviewUrl(objectUrl);

    return () => URL.revokeObjectURL(objectUrl);
  }, [videoFile]);

  useEffect(() => {
    if (!expandedOutput) {
      return;
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setExpandedOutput(null);
      }
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [expandedOutput]);

  function applyModelCatalog(catalog: ModelCatalogResponse) {
    const nextModels =
      catalog.models?.filter((item) => item.value).map(withFallbackModelMetadata) ?? [];
    const nextEndpoints =
      catalog.endpoints?.filter((item) => item.endpoint && item.supportedModels.length > 0) ?? [];

    if (nextModels.length === 0 || nextEndpoints.length === 0) {
      throw new Error(catalog.error || catalog.detail || "Model catalog did not include usable models.");
    }

    setModelOptions(nextModels);
    setEndpointOptions(nextEndpoints);

    const preferredModelId =
      nextModels.find((item) => item.value === modelId)?.value ??
      nextModels.find((item) => item.value === catalog.default_model_id)?.value ??
      nextModels[0].value;
    const nextEndpoint = chooseEndpointForModels(
      [preferredModelId],
      serviceEndpoint,
      nextEndpoints
    );

    setModelId(preferredModelId);
    if (nextEndpoint) {
      setServiceEndpoint(nextEndpoint.endpoint);
      setRegion(nextEndpoint.region);
    }

    setComparisonModelIds((currentModelIds) => {
      const nextEndpointForComparison = nextEndpoint ?? nextEndpoints[0];
      const supportedSelections = currentModelIds
        .filter((id) => nextEndpointForComparison.supportedModels.includes(id))
        .slice(0, 3);

      return supportedSelections.length > 0
        ? supportedSelections
        : nextEndpointForComparison.supportedModels.slice(0, 3);
    });
  }

  useEffect(() => {
    let isCancelled = false;

    async function loadModelCatalog() {
      try {
        const response = await fetch(resolvedCatalogUrl);
        const catalog = (await response.json().catch(() => ({}))) as ModelCatalogResponse;

        if (!response.ok) {
          throw new Error(
            catalog.error || catalog.detail || `The catalog API returned HTTP ${response.status}.`
          );
        }

        if (!isCancelled) {
          applyModelCatalog(catalog);
        }
      } catch (catalogError) {
        if (!isCancelled) {
          console.warn("Model catalog load failed.", catalogError);
        }
      }
    }

    loadModelCatalog();

    return () => {
      isCancelled = true;
    };
  }, [resolvedCatalogUrl]);

  useEffect(() => {
    setComparisonModelIds((currentModelIds) => {
      const supportedSelections = currentModelIds
        .filter((id) => selectedEndpoint.supportedModels.includes(id))
        .slice(0, 3);

      return supportedSelections.length > 0
        ? supportedSelections
        : selectedEndpoint.supportedModels.slice(0, 3);
    });
  }, [selectedEndpoint]);

  function handleModeChange(nextMode: AnalysisMode) {
    setAnalysisMode(nextMode);

    if (nextMode !== "custom-prompt") {
      setPrompt(getPrompt(nextMode));
    }
  }

  function handleEndpointChange(nextEndpoint: string) {
    const endpointOption = getEndpointOption(nextEndpoint, endpointOptions);

    setServiceEndpoint(endpointOption.endpoint);
    setRegion(endpointOption.region);

    if (!endpointOption.supportedModels.includes(modelId)) {
      setModelId(endpointOption.supportedModels[0]);
    }
  }

  function handleModelChange(nextModelId: ModelId) {
    const nextEndpoint = chooseEndpointForModels([nextModelId], serviceEndpoint, endpointOptions);

    setModelId(nextModelId);
    if (nextEndpoint) {
      setServiceEndpoint(nextEndpoint.endpoint);
      setRegion(nextEndpoint.region);
    }
  }

  async function refreshModelCatalog() {
    setError("");

    if (!compartmentId.trim()) {
      setError("Enter an OCI compartment OCID before refreshing model availability.");
      return;
    }

    const formData = new FormData();
    formData.append("compartment_id", compartmentId);
    formData.append("auth_profile", authProfile);
    formData.append("auth_file_location", authFileLocation);

    setIsRefreshingCatalog(true);
    try {
      const response = await fetch(getCatalogDiscoverUrl(resolvedCatalogUrl), {
        method: "POST",
        body: formData
      });
      const catalog = (await response.json().catch(() => ({}))) as ModelCatalogResponse;

      if (!response.ok) {
        throw new Error(
          catalog.error || catalog.detail || `The catalog API returned HTTP ${response.status}.`
        );
      }

      applyModelCatalog(catalog);
    } catch (catalogError) {
      const message =
        catalogError instanceof Error
          ? catalogError.message
          : "Could not refresh models.";
      setError(message);
      revealAuthDetailsIfNeeded(message);
    } finally {
      setIsRefreshingCatalog(false);
    }
  }

  function updateVideoFile(file: File | null) {
    setError("");
    setSecurityWarning("");
    setOutput("");
    setApiMetadata(null);
    setComparisonResults([]);

    if (!file) {
      setVideoFile(null);
      return true;
    }

    if (!file.type.startsWith("video/")) {
      setVideoFile(null);
      setError("Choose a valid video file.");
      return false;
    }

    if (file.size > MAX_UPLOAD_BYTES) {
      setVideoFile(null);
      setError(`Choose a video smaller than ${MAX_UPLOAD_MB} MB.`);
      return false;
    }

    setVideoFile(file);
    return true;
  }

  function handleVideoChange(event: React.ChangeEvent<HTMLInputElement>) {
    const accepted = updateVideoFile(event.target.files?.[0] ?? null);
    if (!accepted) {
      event.currentTarget.value = "";
    }
  }

  function handleVideoDragOver(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
  }

  function handleVideoDrop(event: React.DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    updateVideoFile(event.dataTransfer.files?.[0] ?? null);
  }

  function toggleComparisonModel(nextModelId: ModelId) {
    setComparisonResults([]);
    setCopyLabel("Copy output");
    const nextModelIds = comparisonModelIds.includes(nextModelId)
      ? comparisonModelIds.filter((id) => id !== nextModelId)
      : comparisonModelIds.length >= 3
        ? comparisonModelIds
        : [...comparisonModelIds, nextModelId];
    const nextEndpoint = chooseEndpointForModels(nextModelIds, serviceEndpoint, endpointOptions);

    if (!nextEndpoint && nextModelIds.length > 0) {
      setError("No configured OCI region supports that model combination.");
      return;
    }

    if (nextEndpoint) {
      setServiceEndpoint(nextEndpoint.endpoint);
      setRegion(nextEndpoint.region);
    }
    setComparisonModelIds(nextModelIds);
  }

  function maskCompartmentOcid(value: string) {
    const trimmed = value.trim();
    if (!trimmed) {
      return "";
    }

    return trimmed.toLowerCase().startsWith("ocid1.compartment.")
      ? "ocid1.compartment.***"
      : "ocid1.compartment.***";
  }

  function updateCompartmentId(value: string, shouldMask: boolean) {
    const sanitizedValue = sanitizeTextInput(value);
    setCompartmentId(sanitizedValue);
    setCompartmentDisplayValue(shouldMask ? maskCompartmentOcid(sanitizedValue) : sanitizedValue);
  }

  function handleCompartmentPaste(event: React.ClipboardEvent<HTMLInputElement>) {
    event.preventDefault();
    const pastedText = event.clipboardData.getData("text");
    const redacted = redactSecrets(pastedText);
    if (redacted.changed) {
      showSecretWarning();
      setCompartmentId("");
      setCompartmentDisplayValue(REDACTED_SECRET);
      return;
    }

    updateCompartmentId(pastedText, true);
  }

  function validateAnalysisInputs() {
    if (!videoFile) {
      return "Upload a video before running analysis.";
    }

    if (videoFile.size > MAX_UPLOAD_BYTES) {
      return `Choose a video smaller than ${MAX_UPLOAD_MB} MB.`;
    }

    if (!compartmentId.trim() || !serviceEndpoint.trim() || !region.trim()) {
      return "Compartment OCID, OCI GenAI endpoint, and region are required.";
    }

    if (showAuthDetails && (!authProfile.trim() || !authFileLocation.trim())) {
      return "OCI config profile and config file path are required.";
    }

    if (!prompt.trim()) {
      return "Enter a prompt before running analysis.";
    }

    return "";
  }

  function createAnalysisFormData(
    selectedVideo: File,
    selectedModelId: ModelId,
    selectedModelOcid: string
  ) {
    const formData = new FormData();
    const cleanModelOcid = selectedModelOcid.trim();

    formData.append("video", selectedVideo);
    formData.append("prompt", prompt);
    formData.append("model_id", cleanModelOcid ? "" : selectedModelId);
    formData.append("analysis_mode", analysisMode);
    formData.append("compartment_id", compartmentId);
    formData.append("service_endpoint", serviceEndpoint);
    formData.append("region", region);
    formData.append("model_ocid", cleanModelOcid);
    formData.append("auth_profile", authProfile);
    formData.append("auth_file_location", authFileLocation);

    return formData;
  }

  async function requestAnalysis(
    selectedVideo: File,
    selectedModelId: ModelId,
    selectedModelOcid: string
  ) {
    const formData = createAnalysisFormData(selectedVideo, selectedModelId, selectedModelOcid);
    const response = await fetch(apiUrl, {
      method: "POST",
      body: formData
    });
    const data = (await response.json().catch(() => ({}))) as AnalysisResponse;

    if (!response.ok) {
      throw new Error(
        data.error || data.detail || `The backend returned HTTP ${response.status}.`
      );
    }

    return data;
  }

  function getRequestErrorMessage(requestError: unknown) {
    return requestError instanceof TypeError
      ? `Could not reach the backend API at ${describeApiTarget(
          apiUrl
        )}. Confirm FastAPI is running, the Vite proxy target matches the backend port, and local CORS allows this frontend origin.`
      : requestError instanceof Error
        ? requestError.message
        : "The backend could not analyze the video.";
  }

  function revealAuthDetailsIfNeeded(message: string) {
    if (
      message.toLowerCase().includes("oci config") ||
      message.toLowerCase().includes("auth profile") ||
      message.toLowerCase().includes("config file")
    ) {
      setShowAuthDetails(true);
    }
  }

  function updateComparisonResult(nextResult: ComparisonResult) {
    setComparisonResults((currentResults) =>
      currentResults.map((result) =>
        result.modelId === nextResult.modelId ? nextResult : result
      )
    );
  }

  function openExpandedOutput(result: ComparisonResult) {
    const model = getModelOption(result.modelId, modelOptions);

    setExpandedOutput({
      title: model.label,
      modelId: result.modelId,
      model,
      output: result.output || "No output returned.",
      apiMetadata: result.apiMetadata
    });
  }

  async function runAnalysis() {
    setError("");
    setSecurityWarning("");
    setCopyLabel("Copy output");
    setApiMetadata(null);

    const validationError = validateAnalysisInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    if (!videoFile) {
      return;
    }

    setIsRunning(true);

    try {
      const data = await requestAnalysis(videoFile, modelId, modelOcid);

      setOutput(data.output ?? "");
      setApiMetadata(data.api_metadata ?? null);
    } catch (requestError) {
      const message = getRequestErrorMessage(requestError);
      setError(message);
      revealAuthDetailsIfNeeded(message);
    } finally {
      setIsRunning(false);
    }
  }

  async function runComparison() {
    setError("");
    setSecurityWarning("");
    setCopyLabel("Copy output");
    setComparisonResults([]);

    const validationError = validateAnalysisInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    if (usingModelOcid) {
      setError("Clear the Model OCID field before comparing public Gemini model IDs.");
      return;
    }

    const modelsToCompare = comparisonModelIds
      .filter((id) => selectedEndpoint.supportedModels.includes(id))
      .slice(0, 3);

    if (modelsToCompare.length === 0) {
      setError("Select at least one supported model before running comparison.");
      return;
    }

    if (!videoFile) {
      return;
    }

    setComparisonResults(
      modelsToCompare.map((comparisonModelId) => ({
        modelId: comparisonModelId,
        status: "running",
        output: "",
        apiMetadata: null,
        error: ""
      }))
    );
    setIsComparing(true);

    try {
      await Promise.all(
        modelsToCompare.map(async (comparisonModelId) => {
          try {
            const data = await requestAnalysis(videoFile, comparisonModelId, "");
            updateComparisonResult({
              modelId: comparisonModelId,
              status: "success",
              output: data.output ?? "",
              apiMetadata: data.api_metadata ?? null,
              error: ""
            });
          } catch (requestError) {
            const message = getRequestErrorMessage(requestError);
            revealAuthDetailsIfNeeded(message);
            updateComparisonResult({
              modelId: comparisonModelId,
              status: "error",
              output: "",
              apiMetadata: null,
              error: message
            });
          }
        })
      );
    } finally {
      setIsComparing(false);
    }
  }

  function showSecretWarning() {
    setSecurityWarning(
      "Secret-like content was redacted in the browser. Do not paste private keys, tokens, or OCI config file contents into this app."
    );
  }

  function handleSensitivePaste(event: React.ClipboardEvent<EditableElement>) {
    const pastedText = event.clipboardData.getData("text");
    const redacted = redactSecrets(pastedText);

    if (!redacted.changed) {
      return;
    }

    event.preventDefault();
    showSecretWarning();

    const target = event.currentTarget;
    const start = target.selectionStart ?? target.value.length;
    const end = target.selectionEnd ?? target.value.length;
    const nextValue =
      target.value.slice(0, start) + redacted.value + target.value.slice(end);

    const nativeSetter = Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype,
      "value"
    )?.set;
    const nativeTextAreaSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype,
      "value"
    )?.set;
    const setter = target instanceof HTMLTextAreaElement ? nativeTextAreaSetter : nativeSetter;
    setter?.call(target, nextValue);
    target.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function sanitizeTextInput(value: string) {
    const redacted = redactSecrets(value);
    if (redacted.changed) {
      showSecretWarning();
    }

    return redacted.value;
  }

  async function copyOutput() {
    if (!activeOutputText) {
      return;
    }

    await navigator.clipboard.writeText(activeOutputText);
    setCopyLabel("Copied");
    window.setTimeout(() => setCopyLabel("Copy output"), 1800);
  }

  function downloadOutput() {
    if (!activeOutputText) {
      return;
    }

    const blob = new Blob([activeOutputText], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${
      runMode === "compare" ? "oci-genai-video-model-comparison" : "oci-genai-video-analysis"
    }-${new Date().toISOString().slice(0, 10)}.txt`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  return (
    <section
      className={`studio-shell studio-shell--${mode} ${className}`}
      aria-label="OCI GenAI Video Analysis Studio"
    >
      {mode === "standalone" && (
        <header className="studio-header">
          <div>
            <p className="eyebrow">Oracle Cloud Infrastructure demo asset</p>
            <h1>OCI GenAI Video Analysis Studio</h1>
            <p className="header-copy">
              Upload a video, choose an OCI Gemini model, tune the prompt, and send the
              analysis request through a server-side FastAPI backend.
            </p>
          </div>
          <div className="header-badge">
            <Info aria-hidden="true" size={18} />
            <span>Gemini via Google Vertex AI</span>
          </div>
        </header>
      )}

      <div className="studio-flow">
        <section className="panel connection-panel" aria-label="OCI connection settings">
          <div className="control-section">
            <button
              className="settings-toggle"
              type="button"
              onClick={() => setSettingsOpen((value) => !value)}
              aria-expanded={settingsOpen}
            >
              <span>OCI Connection Settings</span>
              <ChevronDown
                aria-hidden="true"
                size={18}
                className={settingsOpen ? "chevron chevron-open" : "chevron"}
              />
            </button>

          {settingsOpen && (
            <div className="settings-panel">
              <p className="security-note">
                Authentication uses the API key profile on the backend host. The default
                profile is `DEFAULT` and the default config path is `~/.oci/config`.
              </p>

              {showAuthDetails && (
                <>
                  <div className="field-row">
                    <div className="field">
                      <label htmlFor="auth-profile">OCI config profile</label>
                      <input
                        id="auth-profile"
                        value={authProfile}
                        onPaste={handleSensitivePaste}
                        onChange={(event) => setAuthProfile(sanitizeTextInput(event.target.value))}
                        placeholder="DEFAULT"
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="auth-file-location">OCI config file path</label>
                      <input
                        id="auth-file-location"
                        value={authFileLocation}
                        onPaste={handleSensitivePaste}
                        onChange={(event) =>
                          setAuthFileLocation(sanitizeTextInput(event.target.value))
                        }
                        placeholder="~/.oci/config"
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="field">
                <label htmlFor="compartment-id">OCI compartment OCID</label>
                <input
                  id="compartment-id"
                  value={displayedCompartmentId}
                  onFocus={() => {
                    setIsCompartmentFocused(true);
                    setCompartmentDisplayValue(compartmentId);
                  }}
                  onBlur={() => {
                    setIsCompartmentFocused(false);
                    setCompartmentDisplayValue(maskCompartmentOcid(compartmentId));
                  }}
                  onPaste={handleCompartmentPaste}
                  onChange={(event) => updateCompartmentId(event.target.value, false)}
                  placeholder="YOUR_COMPARTMENT_OCID"
                />
              </div>
              <div className="field">
                <div className="field-heading-row">
                  <label htmlFor="service-endpoint">OCI GenAI endpoint</label>
                  <button
                    type="button"
                    className="inline-tool-button"
                    onClick={refreshModelCatalog}
                    disabled={isRefreshingCatalog || isBusy}
                  >
                    {isRefreshingCatalog ? (
                      <Loader2 className="spin" aria-hidden="true" size={15} />
                    ) : (
                      <RefreshCw aria-hidden="true" size={15} />
                    )}
                    <span>Refresh from OCI</span>
                  </button>
                </div>
                <select
                  id="service-endpoint"
                  value={serviceEndpoint}
                  onChange={(event) => handleEndpointChange(event.target.value)}
                >
                  {endpointOptions.map((item) => (
                    <option key={item.region} value={item.endpoint}>
                      {item.label} - {item.region}
                    </option>
                  ))}
                </select>
                <p className="field-help">
                  {selectedEndpoint.endpoint}. Supports:{" "}
                  {selectedEndpoint.supportedModels
                    .map((value) => modelOptions.find((model) => model.value === value)?.label)
                    .filter(Boolean)
                    .join(", ")}
                </p>
              </div>

              <div className="field">
                <label htmlFor="model-ocid">Model OCID optional</label>
                <input
                  id="model-ocid"
                  value={modelOcid}
                  onPaste={handleSensitivePaste}
                  onChange={(event) => setModelOcid(sanitizeTextInput(event.target.value))}
                  placeholder="optional_if_needed"
                />
                <p className="field-help">
                  When a model OCID is provided, it is sent instead of the public Gemini
                  model ID.
                </p>
              </div>
              <p className="security-note">
                Private keys, config files, tokens, and tenancy secrets must stay out of
                browser code. Enter only the server-side profile name and config path if
                the default profile cannot be found.
              </p>
            </div>
          )}
          </div>
        </section>

        <section className="panel panel-primary video-workflow-panel">
          <div className="panel-heading">
            <div>
              <h2>Upload, preview, and analyze</h2>
              <p className="panel-kicker">Choose video</p>
            </div>
            <FileVideo aria-hidden="true" size={22} />
          </div>

          <label
            className={videoFile ? "upload-zone upload-zone-compact" : "upload-zone"}
            htmlFor="video-upload"
            onDragOver={handleVideoDragOver}
            onDrop={handleVideoDrop}
          >
            <UploadCloud aria-hidden="true" size={videoFile ? 19 : 30} />
            <span className="upload-copy">
              <span className="upload-title">
                {videoFile ? videoFile.name : "Choose a video file"}
              </span>
              <span className="upload-meta">
                {videoFile
                  ? `${videoFile.type || "video"} - ${formatBytes(videoFile.size)}`
                  : `MP4, MOV, WebM, or any browser-supported video up to ${MAX_UPLOAD_MB} MB`}
              </span>
            </span>
            <input
              id="video-upload"
              type="file"
              accept="video/*"
              onChange={handleVideoChange}
            />
          </label>

          <div className="preview-frame">
            {videoPreviewUrl ? (
              <video src={videoPreviewUrl} controls playsInline />
            ) : (
              <div className="preview-empty">
                <PlayCircle aria-hidden="true" size={42} />
                <span>Video preview appears here</span>
              </div>
            )}
          </div>

          <div className="analysis-layout">
            <div className="analysis-column analysis-column-model">
              <div className="field control-section">
                <span className="field-label">Run mode</span>
                <div className="mode-switch" role="group" aria-label="Run mode">
                  <button
                    type="button"
                    className={runMode === "single" ? "mode-switch-active" : ""}
                    onClick={() => setRunMode("single")}
                    aria-pressed={runMode === "single"}
                  >
                    <PlayCircle aria-hidden="true" size={17} />
                    <span>Single model</span>
                  </button>
                  <button
                    type="button"
                    className={runMode === "compare" ? "mode-switch-active" : ""}
                    onClick={() => setRunMode("compare")}
                    aria-pressed={runMode === "compare"}
                  >
                    <Columns3 aria-hidden="true" size={17} />
                    <span>Compare models</span>
                  </button>
                </div>
              </div>

              {runMode === "single" ? (
                <div className="field control-section">
                  <label htmlFor="model-selector">Gemini model</label>
                  <select
                    id="model-selector"
                    value={modelId}
                    disabled={usingModelOcid}
                    onChange={(event) => handleModelChange(event.target.value as ModelId)}
                  >
                    {modelOptions.map((model) => (
                      <option key={model.value} value={model.value}>
                        {model.label}
                      </option>
                    ))}
                  </select>
                  <p className="field-help">
                    {usingModelOcid
                      ? "Disabled because an explicit model OCID is set."
                      : selectedModel.detail}
                  </p>
                </div>
              ) : (
                <div className="field control-section">
                  <div className="comparison-control-heading">
                    <span id="compare-models-label" className="field-label">
                      Models to compare
                    </span>
                    <span>{comparisonModelIds.length}/3 selected</span>
                  </div>
                  <div
                    className="model-choice-grid"
                    role="group"
                    aria-labelledby="compare-models-label"
                  >
                    {modelOptions.map((model) => {
                      const isSelected = comparisonModelIds.includes(model.value);
                      const cannotAddModel = !isSelected && comparisonModelIds.length >= 3;

                      return (
                        <button
                          key={model.value}
                          type="button"
                          className={
                            isSelected ? "model-choice model-choice-selected" : "model-choice"
                          }
                          onClick={() => toggleComparisonModel(model.value)}
                          aria-pressed={isSelected}
                          disabled={usingModelOcid || isBusy || cannotAddModel}
                        >
                          <span className="model-choice-check" aria-hidden="true">
                            {isSelected && <Check size={14} />}
                          </span>
                          <span>
                            <strong>{model.label}</strong>
                            <small>{model.detail}</small>
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <p className="field-help">
                    {usingModelOcid
                      ? "Comparison uses public model IDs. Clear Model OCID to compare models."
                      : "Comparison runs the same video and prompt against each selected model."}
                  </p>
                </div>
              )}
            </div>

            <div className="analysis-column analysis-column-prompt">
              <div className="field control-section">
                <label htmlFor="analysis-mode">Analysis mode</label>
                <select
                  id="analysis-mode"
                  value={analysisMode}
                  onChange={(event) => handleModeChange(event.target.value as AnalysisMode)}
                >
                  {ANALYSIS_MODES.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field control-section prompt-section">
                <label htmlFor="prompt">Prompt</label>
                <textarea
                  id="prompt"
                  value={prompt}
                  onPaste={handleSensitivePaste}
                  onChange={(event) => setPrompt(sanitizeTextInput(event.target.value))}
                  rows={7}
                  placeholder="Ask Gemini to analyze the uploaded video."
                />
              </div>
            </div>
          </div>

          <button
            className={runMode === "compare" ? "run-button run-button-compare" : "run-button"}
            type="button"
            onClick={runMode === "compare" ? runComparison : runAnalysis}
            disabled={isBusy}
          >
            {isBusy ? (
              <Loader2 className="spin" aria-hidden="true" size={18} />
            ) : runMode === "compare" ? (
              <GitCompareArrows aria-hidden="true" size={18} />
            ) : (
              <PlayCircle aria-hidden="true" size={18} />
            )}
            <span>
              {isRunning
                ? "Analyzing video"
                : isComparing
                  ? "Comparing models"
                  : runMode === "compare"
                    ? "Run Comparison"
                    : "Run Analysis"}
            </span>
          </button>
        </section>
      </div>

      <div className="output-panel">
        <div className="output-header">
          <div>
            <h2>{runMode === "compare" ? "Model comparison" : "Analysis result"}</h2>
          </div>
          <div className="output-actions">
            <button
              type="button"
              onClick={() => setRenderMarkdown((value) => !value)}
              disabled={!activeOutputText}
              aria-pressed={renderMarkdown}
            >
              <FileText aria-hidden="true" size={16} />
              <span>{renderMarkdown ? "Show raw text" : "Render markdown"}</span>
            </button>
            <button type="button" onClick={copyOutput} disabled={!activeOutputText}>
              <Clipboard aria-hidden="true" size={16} />
              <span>{copyButtonLabel}</span>
            </button>
            <button type="button" onClick={downloadOutput} disabled={!activeOutputText}>
              <Download aria-hidden="true" size={16} />
              <span>{runMode === "compare" ? "Download comparison" : "Download output"}</span>
            </button>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}
        {securityWarning && <div className="security-warning">{securityWarning}</div>}

        {runMode === "compare" ? (
          <div className="comparison-view" aria-label="Model output comparison">
            {comparisonResults.length > 0 ? (
              <>
                <div className="comparison-summary">
                  <div className="comparison-summary-item">
                    <span>Completed</span>
                    <strong>
                      {comparisonSuccessResults.length}/{comparisonResults.length}
                    </strong>
                  </div>
                  <div className="comparison-summary-item">
                    <span>Fastest</span>
                    <strong>
                      {fastestComparisonResult
                        ? `${getModelOption(fastestComparisonResult.modelId, modelOptions).label} (${formatLatency(
                            fastestComparisonResult.apiMetadata?.latency_ms
                          )})`
                        : "Not returned"}
                    </strong>
                  </div>
                  <div className="comparison-summary-item">
                    <span>Lowest output tokens</span>
                    <strong>
                      {lowestOutputTokenResult
                        ? `${getModelOption(lowestOutputTokenResult.modelId, modelOptions).label} (${formatMetric(
                            lowestOutputTokenResult.apiMetadata?.output_tokens
                          )})`
                        : "Not returned"}
                    </strong>
                  </div>
                </div>

                <div
                  className={`comparison-grid comparison-grid-${Math.min(
                    comparisonResults.length,
                    3
                  )}`}
                >
                  {comparisonResults.map((result) => {
                    const model = getModelOption(result.modelId, modelOptions);

                    return (
                      <article
                        key={result.modelId}
                        className={`comparison-card comparison-card-${result.status}`}
                      >
                        <div className="comparison-card-header">
                          <div>
                            <p className="panel-kicker">Model</p>
                            <h3>{model.label}</h3>
                            <span>{result.modelId}</span>
                          </div>
                          <div className="comparison-card-actions">
                            <span className={`status-pill status-pill-${result.status}`}>
                              {result.status === "running"
                                ? "Running"
                                : result.status === "success"
                                  ? "Complete"
                                  : "Error"}
                            </span>
                            {result.status === "success" && (
                              <button
                                type="button"
                                className="comparison-expand-button"
                                onClick={() => openExpandedOutput(result)}
                                aria-label={`Open ${model.label} output full screen`}
                                title="Open output full screen"
                              >
                                <Maximize2 aria-hidden="true" size={15} />
                              </button>
                            )}
                          </div>
                        </div>

                        <MetricStack model={model} metadata={result.apiMetadata} compact />

                        {result.status === "running" && (
                          <div className="comparison-loading">
                            <Loader2 className="spin" aria-hidden="true" size={20} />
                            <span>Running this model</span>
                          </div>
                        )}
                        {result.status === "error" && (
                          <div className="comparison-error">
                            <CircleX aria-hidden="true" size={18} />
                            <span>{result.error}</span>
                          </div>
                        )}
                        {result.status === "success" && (
                          <>
                            {renderMarkdown ? (
                              <MarkdownOutput
                                value={result.output || "No output returned."}
                                className="comparison-markdown"
                              />
                            ) : (
                              <pre className="comparison-output">
                                {result.output || "No output returned."}
                              </pre>
                            )}
                            <ModelInfoPanel model={model} compact />
                          </>
                        )}
                      </article>
                    );
                  })}
                </div>
              </>
            ) : (
              <div className="comparison-empty">
                <Columns3 aria-hidden="true" size={36} />
                <h3>No comparison run yet</h3>
                <p>Run the current prompt against selected models to compare outputs and metadata.</p>
                <div className="selected-model-info-grid" aria-label="Selected model metadata">
                  {selectedComparisonModels.map((model) => (
                    <ModelInfoPanel key={model.value} model={model} compact />
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            <div className="metadata-panel" aria-label="Processed video metadata">
              <h3>Analysis metrics</h3>

              {apiMetadata ? (
                <MetricStack model={selectedModel} metadata={apiMetadata} />
              ) : (
                <p className="metadata-empty">
                  Input tokens, output tokens, latency, and estimated cost / 1K similar docs appear after a successful analysis.
                </p>
              )}
            </div>

            {renderMarkdown && output ? (
              <MarkdownOutput value={output} className="output-markdown" />
            ) : (
              <pre className={output ? "output-box" : "output-box output-box-empty"}>
                {output || "Run analysis to view the OCI GenAI response."}
              </pre>
            )}
            <ModelInfoPanel model={selectedModel} />
          </>
        )}
      </div>

      {expandedOutput && (
        <div
          className="output-modal-backdrop"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setExpandedOutput(null);
            }
          }}
        >
          <section
            className="output-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="expanded-output-title"
          >
            <div className="output-modal-header">
              <div>
                <p className="panel-kicker">Expanded model output</p>
                <h2 id="expanded-output-title">{expandedOutput.title}</h2>
                <span>{expandedOutput.modelId}</span>
              </div>
              <div className="output-modal-actions">
                <button
                  type="button"
                  onClick={() => setRenderMarkdown((value) => !value)}
                  aria-pressed={renderMarkdown}
                >
                  <FileText aria-hidden="true" size={16} />
                  <span>{renderMarkdown ? "Show raw text" : "Render markdown"}</span>
                </button>
                <button
                  type="button"
                  className="output-modal-close"
                  onClick={() => setExpandedOutput(null)}
                  aria-label="Close expanded output"
                >
                  <X aria-hidden="true" size={18} />
                </button>
              </div>
            </div>

            <MetricStack model={expandedOutput.model} metadata={expandedOutput.apiMetadata} />

            <div className="output-modal-body">
              {renderMarkdown ? (
                <MarkdownOutput
                  value={expandedOutput.output}
                  className="output-modal-markdown"
                />
              ) : (
                <pre className="output-modal-output">{expandedOutput.output}</pre>
              )}
              <ModelInfoPanel model={expandedOutput.model} />
            </div>
          </section>
        </div>
      )}
    </section>
  );
}
