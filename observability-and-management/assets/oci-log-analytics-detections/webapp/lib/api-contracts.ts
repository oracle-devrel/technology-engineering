/**
 * Forge API contract — canonical Zod schemas and inferred TypeScript types for
 * every request/response crossing the `webapp/app/api/forge/*` and
 * `webapp/app/api/health` boundaries.
 *
 * Rules:
 *  - No `import "server-only"` — this file must be safe to import from client
 *    components (for type-only imports) as well as server-side routes.
 *  - All schemas are the single source of truth; interfaces in other files must
 *    be derived from (or replaced by) these schemas.
 *  - No real OCIDs, IPs, credentials, or tenancy-specific values.
 */

import { z } from "zod"

// ── Shared primitive schemas ─────────────────────────────────────────────────

/**
 * All source languages the Forge conversion endpoint accepts.
 * Keep in sync with `scripts/logan_workbench_convert.py`.
 */
export const sourceLanguageSchema = z.enum([
  "sigma_yaml",
  "sentinel_kql",
  "splunk_spl",
  "elastic_lucene",
  "elastic_kuery",
  "elastic_eql",
  "elastic_esql",
  "elastic_toml",
  "osquery_sql",
  "yara",
  "oci_logan",
])
export type SourceLanguage = z.infer<typeof sourceLanguageSchema>

/** Fidelity of a query conversion result. */
export const supportLevelSchema = z.enum(["supported", "partial", "lossy", "unsupported"])
export type SupportLevel = z.infer<typeof supportLevelSchema>

// ── /api/forge/convert ───────────────────────────────────────────────────────

/** Maximum allowed source-query length (characters). */
export const MAX_QUERY_CHARS = 20_000

/**
 * Request body schema for POST /api/forge/convert.
 * Uses `.strict()` so any unknown key is a validation error.
 */
export const conversionRequestSchema = z
  .object({
    sourceLanguage: sourceLanguageSchema,
    sourceQuery: z.string().min(1).max(MAX_QUERY_CHARS),
    readOnly: z.boolean().optional().default(true),
    exampleId: z.string().max(160).optional(),
  })
  .strict()

export type ConversionRequest = z.infer<typeof conversionRequestSchema>

/** A single warning emitted by the conversion backend. */
export const conversionWarningSchema = z.object({
  code: z.string(),
  message: z.string(),
  severity: z.enum(["info", "warning", "error"]),
})
export type ConversionWarning = z.infer<typeof conversionWarningSchema>

/**
 * Schema for the conversion response.  Used by:
 *  - `convert/route.ts` to parse the raw backend response (Python script or
 *    remote API gateway) and to validate the public response before sending.
 *  - `forge-workbench-data.ts` to type the in-component state.
 *  - `forge.spec.ts` for API assertion types.
 *
 * `.passthrough()` is intentional: the Python backend may include extra fields
 * (e.g. debug keys) that we preserve without strict rejection.
 */
export const conversionResponseSchema = z
  .object({
    schema_version: z.literal("1.0.0"),
    generated_at: z.string(),
    source_language: z.string().optional(),
    source_query: z.string().optional(),
    logan_query: z.string(),
    support_level: supportLevelSchema,
    explanation: z.string(),
    warnings: z.array(conversionWarningSchema),
    metadata: z.record(z.unknown()),
    backend: z.string(),
  })
  .passthrough()

export type ConversionResponse = z.infer<typeof conversionResponseSchema>

// ── /api/forge/session ───────────────────────────────────────────────────────

/** Response schema for GET /api/forge/session. */
export const sessionResponseSchema = z.object({
  csrfToken: z.string().min(32),
  expiresInSeconds: z.number().int().positive(),
  rateLimit: z.object({
    limit: z.number().int().positive(),
    windowSeconds: z.number().int().positive(),
  }),
})
export type SessionResponse = z.infer<typeof sessionResponseSchema>

// ── /api/health ──────────────────────────────────────────────────────────────

/** Response schema for GET /api/health. */
export const healthResponseSchema = z.object({
  ok: z.literal(true),
  service: z.string(),
  version: z.string(),
})
export type HealthResponse = z.infer<typeof healthResponseSchema>

// ── /api/forge/artifacts ─────────────────────────────────────────────────────

/**
 * Key identifiers for each workbench artifact file.
 * Must match the keys used in `lib/logan-workbench-artifacts.ts`.
 */
export const artifactKeySchema = z.enum([
  "referenceCatalog",
  "mappingPatterns",
  "conversionExamples",
  "capabilityMatrix",
])
export type ArtifactKey = z.infer<typeof artifactKeySchema>

/** Read status for a single workbench artifact file. */
export const artifactStatusSchema = z.object({
  key: artifactKeySchema,
  label: z.string(),
  relativePath: z.string(),
  ok: z.boolean(),
  error: z.string().optional(),
})
export type ArtifactStatus = z.infer<typeof artifactStatusSchema>

/**
 * Response schema for GET /api/forge/artifacts.
 *
 * Returns lightweight metadata about the repo-generated workbench artifacts:
 * availability, validation status, generation timestamp, and item counts.
 * The full artifact arrays (examples, patterns, commands) are served to the
 * Forge page via server-side rendering, not through this route.
 */
export const artifactsResponseSchema = z.object({
  generatedAt: z.string().nullable(),
  errors: z.array(z.string()),
  statuses: z.array(artifactStatusSchema),
  examplesCount: z.number().int().nonnegative(),
  patternsCount: z.number().int().nonnegative(),
  commandsCount: z.number().int().nonnegative(),
})
export type ArtifactsResponse = z.infer<typeof artifactsResponseSchema>

// ── Shared error response ────────────────────────────────────────────────────

/** Standard error envelope returned by all Forge API routes on failure. */
export const apiErrorResponseSchema = z.object({
  error: z.string(),
})
export type ApiErrorResponse = z.infer<typeof apiErrorResponseSchema>
