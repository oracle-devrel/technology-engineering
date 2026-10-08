export interface ExtractedParameter {
  name: string;
  value: string | number | boolean;
  confidence: number;
  category?: string;
  source_page?: number | null;
  source_text?: string | null;
}

export interface DocumentMetadata {
  filename: string;
  file_size: number;
  page_count: number | null;
  upload_timestamp: string;
  content_type: string;
}

export interface ExtractionResult {
  parameters: ExtractedParameter[];
  raw_response?: Record<string, unknown>;
  processing_time_ms?: number;
  error_message?: string;
}

export interface Document {
  id: string;
  user_id?: string;
  metadata: DocumentMetadata;
  status: 'uploaded' | 'processing' | 'completed' | 'failed';
  extraction_result?: ExtractionResult;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  document_id: string;
  filename: string;
  file_size: number;
  message: string;
}

export interface ExtractionResponse {
  document_id: string;
  status: string;
  parameters: ExtractedParameter[];
}

export interface DocumentStatusResponse {
  document_id: string;
  filename: string;
  status: string;
  extracted_parameters?: ExtractedParameter[];
  error?: string;
}

export type ProcessingStatus = 'idle' | 'uploading' | 'processing' | 'completed' | 'error';

// Auth types
export interface User {
  id: string;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
  message: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}

// Chat types
export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  sources?: ChatSource[];
  confidence?: number;
  isError?: boolean;
}

export interface ChatSource {
  document_name: string | null;
  page_number: number | null;
  snippet: string;
  relevance_score: number;
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ModelSettings {
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
}

export const DEFAULT_MODEL_SETTINGS: ModelSettings = {
  temperature: 0.3,
  max_tokens: 2048,
  top_p: 1.0,
  frequency_penalty: 0.0,
  presence_penalty: 0.0,
};

export interface ChatRequest {
  message: string;
  document_ids: string[];
  conversation_history: ChatHistoryMessage[];
  max_sources?: number;
  model_settings?: Partial<ModelSettings>;
  inference_model?: string;
}

export interface ChatResponse {
  message: string;
  sources: ChatSource[];
  confidence: number;
  processing_time_ms: number | null;
}

export interface LlamaModel {
  id: string;
  type?: string;
}

export interface UserProfileUpdate {
  full_name?: string;
  email?: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface DirectoryGroupMapping {
  group_id: string;
  role: string;
}

export interface DirectoryConfiguration {
  provider: 'microsoft_entra_id';
  protocol: 'oidc';
  tenant_id: string | null;
  client_id: string | null;
  redirect_uri: string | null;
  authority: string | null;
  group_sync_enabled: boolean;
  group_mappings: DirectoryGroupMapping[];
  is_configured: boolean;
  client_secret_configured: boolean;
  configured_at: string | null;
  updated_at: string | null;
}

export interface DirectoryConfigurationUpdate {
  tenant_id: string;
  client_id: string;
  redirect_uri: string;
  client_secret?: string;
  group_sync_enabled: boolean;
  group_mappings: DirectoryGroupMapping[];
}

export interface DirectoryConnectionCheck {
  status: 'connected' | 'failed';
  message: string;
  issuer: string | null;
  checked_at: string;
}

export interface RAGHealthResponse {
  status: 'healthy' | 'unhealthy' | 'unavailable';
  endpoint?: string;
  response_time_ms?: number;
  error?: string;
}

// Word Cloud types
export interface WordFrequency {
  word: string;
  count: number;
}

export interface WordCloudResponse {
  words: WordFrequency[];
  total_documents: number;
  total_words_processed: number;
}

// Project types
export interface WebSource {
  id: string;
  url: string;
  title: string;
  status?: 'pending' | 'scraping' | 'indexing' | 'completed' | 'failed';
  content_length?: number;
  chunks_indexed?: number;
  error_message?: string;
  added_at: string;
  created_at?: string;
  updated_at?: string;
}

export interface WebSourceResponse {
  id: string;
  url: string;
  title: string;
  status: string;
  content_length?: number;
  chunks_indexed?: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  tags: string[];
  document_ids: string[];
  web_sources: WebSource[];
  created_at: string;
  updated_at: string;
}

export type ChatSourceType = 'all' | 'single_file' | 'web_url';

export interface ChatSourceSelection {
  type: ChatSourceType;
  document_id?: string;
  web_source_id?: string;
}

// Batch Processing types
export interface ObjectStoreConnector {
  id: string;
  name: string;
  namespace: string;
  bucket_name: string;
  compartment_id: string;
  prefix?: string;
  region: string;
  created_at: string;
  updated_at: string;
}

export interface BatchTrigger {
  id: string;
  connector_id: string;
  name: string;
  schedule: string;
  is_active: boolean;
  parallelism: number;
  last_run?: string;
  next_run?: string;
  created_at: string;
}

export interface BatchJob {
  id: string;
  trigger_id?: string;
  connector_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  files_found: number;
  files_processed: number;
  files_failed: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
}

export interface BatchJobFile {
  id: string;
  job_id: string;
  file_name: string;
  file_size?: number;
  status: 'pending' | 'downloading' | 'processing' | 'vectorizing' | 'analyzing' | 'completed' | 'failed';
  error_message?: string;
  document_id?: string;
  chunks_indexed?: number;
  vectorization_status?: string;
  analysis_status?: string;
  analysis_result?: { filename: string; summary: string; sections_analyzed: number };
}

// Workflow types
export type WorkflowNodeType = 'agent' | 'data_source' | 'input' | 'output' | 'chat';

export interface WorkflowNode {
  id: string;
  type: WorkflowNodeType;
  label: string;
  position: { x: number; y: number };
  config: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  source_handle?: string;
  target_handle?: string;
}

export interface WorkflowSchedule {
  id: string;
  workflow_id: string;
  schedule_type: 'one_time' | 'recurring';
  cron_expression?: string;
  run_at?: string;
  input_data?: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  next_run_at?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  created_at: string;
  updated_at: string;
  created_by?: string;
  is_active: boolean;
  schedule?: WorkflowSchedule | null;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  node_results: Record<string, { status: string; output?: any; error?: string }>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
  triggered_by?: string;
}

export interface ScheduledRun {
  execution_id: string;
  workflow_id: string;
  status: string;
  triggered_by?: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

// Research types
export interface ResearchSource {
  page: number | null;
  relevance: number;
  snippet: string;
  document_id: string;
  document_name: string;
}

export interface TimelineEvent {
  date: string;
  type: string;
  description: string;
  page: string;
}

export interface ResearchResponse {
  report: string;
  query: string;
  report_type: string;
  sources: ResearchSource[];
  timeline: TimelineEvent[];
  chunks_searched: number;
  chunks_used: number;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
}

// Compliance types
export interface ComplianceFinding {
  rule_id: string;
  category: string;
  status: 'pass' | 'warning' | 'review' | 'fail' | 'not_assessable';
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  extracted_value?: string | null;
  evidence: ComplianceEvidence[];
  confidence: number;
  requires_human_review: boolean;
}

export interface ComplianceEvidence {
  page?: number | null;
  section?: string | null;
  quote: string;
  matched_text: string;
}

export interface DocumentComplianceResult {
  document_id: string;
  filename: string;
  industry: string;
  total: number;
  passes: number;
  warnings: number;
  reviews: number;
  fails: number;
  pass_rate: number;
  findings: ComplianceFinding[];
  critical_count: number;
  high_count: number;
  ruleset_version: string;
  document_sha256?: string | null;
  assessed_at?: string | null;
  assessment_status: 'completed' | 'not_assessable' | 'failed';
  error_message?: string | null;
  review_status: 'pending' | 'approved' | 'changes_requested';
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_notes?: string | null;
}

export interface ComplianceCheckResponse {
  results: DocumentComplianceResult[];
  industry: string;
  total_documents: number;
  errors: Array<{ document_id: string; message: string }>;
}

export interface IndustryOption {
  id: string;
  name: string;
  description: string;
  rules_count: number;
}

// Domain Adapter types
export interface AdapterField {
  name: string;
  label: string;
  type: string;
  group: string;
  description: string;
}

export interface AdapterRule {
  id: string;
  type: string;
  field_name?: string;
  keyword?: string;
  standard?: string;
  aliases?: string[];
  missing_status?: 'warning' | 'review' | 'fail';
  category: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  pass_message: string;
  fail_message: string;
}

export interface AdapterLesson {
  id: string;
  title: string;
  description: string;
  keywords: string[];
  severity: 'low' | 'medium' | 'high' | 'critical';
  recommendation: string;
}

export interface AdapterPrompts {
  extraction: string;
  chat: string;
  compliance_report: string;
}

export interface DomainInfo {
  name: string;
  display_name: string;
  description: string;
  field_count: number;
  rule_count: number;
  lesson_count: number;
  enabled: boolean;
}

export interface DomainDetail {
  domain: string;
  schema: {
    domain: string;
    name: string;
    description: string;
    fields: AdapterField[];
  };
  prompts: AdapterPrompts;
  rules: {
    domain: string;
    checks: AdapterRule[];
  };
  lessons: {
    domain: string;
    items: AdapterLesson[];
  };
}
