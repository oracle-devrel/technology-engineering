import axios, { AxiosProgressEvent } from 'axios';
import {
  UploadResponse,
  ExtractionResponse,
  DocumentStatusResponse,
  LoginRequest,
  LoginResponse,
  User,
  Document,
  ChatRequest,
  ChatResponse,
  ChatHistoryMessage,
  RAGHealthResponse,
  ModelSettings,
  LlamaModel,
  UserProfileUpdate,
  PasswordChangeRequest,
  DirectoryConfiguration,
  DirectoryConfigurationUpdate,
  DirectoryConnectionCheck,
  WordCloudResponse,
  WebSourceResponse,
  ObjectStoreConnector,
  BatchTrigger,
  BatchJob,
  BatchJobFile,
  Workflow,
  WorkflowExecution,
  WorkflowSchedule,
  ScheduledRun,
  Project,
  ResearchResponse,
  ReportTemplate,
  ComplianceCheckResponse,
  DocumentComplianceResult,
  IndustryOption,
  DomainInfo,
  DomainDetail,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';
const ENTERPRISE_AI_DOMAIN = import.meta.env.VITE_ENTERPRISE_AI_DOMAIN || 'generic';

type EnterpriseAIDocument = {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  page_count: number | null;
  status: Document['status'];
  created_at: string;
};

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Auth endpoints
  /**
   * Login with username and password
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    console.log('API login called with:', credentials.username);
    const response = await apiClient.post<LoginResponse>('/api/auth/login', credentials);
    console.log('API login response:', response.status, response.data);
    return response.data;
  },

  /**
   * Logout current user
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/api/auth/logout');
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/auth/me');
    return response.data;
  },

  /**
   * Verify session is valid
   */
  verifySession: async (): Promise<boolean> => {
    try {
      await apiClient.get('/api/auth/verify');
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Upload a PDF file
   */
  uploadDocument: async (
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<UploadResponse>('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: AxiosProgressEvent) => {
        if (progressEvent.total && onProgress) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });

    return response.data;
  },

  /**
   * Trigger extraction for a document
   */
  extractParameters: async (documentId: string): Promise<ExtractionResponse> => {
    const response = await apiClient.post<ExtractionResponse>(
      `/api/extract/${documentId}`
    );
    return response.data;
  },

  /**
   * Get document status and extracted parameters
   */
  getDocumentStatus: async (documentId: string): Promise<DocumentStatusResponse> => {
    const response = await apiClient.get<DocumentStatusResponse>(
      `/api/document/${documentId}`
    );
    return response.data;
  },

  /**
   * Get PDF URL for viewing
   */
  getPdfUrl: (documentId: string): string => {
    return `${API_BASE_URL}/api/document/${documentId}/pdf`;
  },

  /**
   * Poll document status until extraction is complete
   */
  pollDocumentStatus: async (
    documentId: string,
    interval: number = 2000,
    maxAttempts: number = 60,
    onUpdate?: (status: DocumentStatusResponse) => void
  ): Promise<DocumentStatusResponse> => {
    let attempts = 0;

    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await api.getDocumentStatus(documentId);

          if (onUpdate) {
            onUpdate(status);
          }

          if (status.status === 'completed' || status.status === 'error') {
            resolve(status);
            return;
          }

          attempts++;
          if (attempts >= maxAttempts) {
            reject(new Error('Polling timeout: Maximum attempts reached'));
            return;
          }

          setTimeout(poll, interval);
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },

  /**
   * List all documents for current user
   */
  listDocuments: async (): Promise<Document[]> => {
    const response = await apiClient.get<Document[] | { documents: EnterpriseAIDocument[] }>('/api/documents');
    const payload = response.data;

    // EnterpriseAI returns a compact record inside a `documents` envelope.
    // Adapt it at the boundary so existing components retain the local
    // Document model.
    if (Array.isArray(payload)) {
      return payload;
    }

    if (Array.isArray(payload.documents)) {
      return payload.documents.map((document) => ({
        id: document.id,
        metadata: {
          filename: document.filename,
          file_size: document.file_size,
          page_count: document.page_count,
          upload_timestamp: document.created_at,
          content_type: document.mime_type,
        },
        status: document.status,
        created_at: document.created_at,
        updated_at: document.created_at,
      }));
    }

    return [];
  },

  /**
   * Delete a document
   */
  deleteDocument: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/api/document/${documentId}`);
  },

  /**
   * Chat with documents - sends message and returns AI response with sources
   */
  chat: async (
    message: string,
    documentIds: string[],
    conversationHistory: ChatHistoryMessage[] = [],
    maxSources: number = 5,
    modelSettings?: Partial<ModelSettings>,
    inferenceModel?: string
  ): Promise<ChatResponse> => {
    const request: ChatRequest & { domain: string } = {
      message,
      document_ids: documentIds,
      conversation_history: conversationHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
        timestamp: msg.timestamp || new Date().toISOString(),
      })),
      max_sources: maxSources,
      model_settings: modelSettings,
      inference_model: inferenceModel || undefined,
      domain: ENTERPRISE_AI_DOMAIN,
    };
    const response = await apiClient.post<ChatResponse>('/api/chat', request, {
      timeout: 60000, // 60 second timeout for chat
    });
    return {
      ...response.data,
      // EnterpriseAI may return retrieval diagnostics in `sources` rather
      // than document-level citations. Only render citations the local UI can
      // identify truthfully.
      sources: response.data.sources?.filter(
        (source) => Boolean(source.document_name)
      ) || [],
    };
  },

  /**
   * Check RAG service health
   */
  checkRAGHealth: async (): Promise<RAGHealthResponse> => {
    const response = await apiClient.get<RAGHealthResponse>('/api/rag/health');
    return response.data;
  },

  /**
   * List available models from the llamastack endpoint
   */
  listModels: async (): Promise<LlamaModel[]> => {
    const response = await apiClient.get<LlamaModel[]>('/api/models');
    return response.data;
  },

  /**
   * Update user profile (name, email)
   */
  updateProfile: async (data: UserProfileUpdate): Promise<User> => {
    const response = await apiClient.put<User>('/api/auth/profile', data);
    return response.data;
  },

  /**
   * Change user password
   */
  changePassword: async (data: PasswordChangeRequest): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>('/api/auth/change-password', data);
    return response.data;
  },

  /**
   * Get the safe-to-display Microsoft Entra ID directory configuration.
   */
  getDirectoryConfiguration: async (): Promise<DirectoryConfiguration> => {
    const response = await apiClient.get<DirectoryConfiguration>('/api/auth/directory');
    return response.data;
  },

  /**
   * Save Microsoft Entra ID OIDC settings. The client secret is write-only.
   */
  updateDirectoryConfiguration: async (
    data: DirectoryConfigurationUpdate
  ): Promise<DirectoryConfiguration> => {
    const response = await apiClient.put<DirectoryConfiguration>('/api/auth/directory', data);
    return response.data;
  },

  /**
   * Verify the configured Microsoft Entra ID OpenID discovery endpoint.
   */
  testDirectoryConnection: async (): Promise<DirectoryConnectionCheck> => {
    const response = await apiClient.post<DirectoryConnectionCheck>(
      '/api/auth/directory/test-connection',
      undefined,
      { timeout: 15000 }
    );
    return response.data;
  },

  /**
   * Scrape a web URL and index for RAG
   */
  scrapeWebUrl: async (url: string, title: string = ''): Promise<WebSourceResponse> => {
    const response = await apiClient.post<WebSourceResponse>('/api/web/scrape', {
      url,
      title,
    }, { timeout: 60000 });
    return response.data;
  },

  /**
   * Get web source details
   */
  getWebSource: async (webSourceId: string): Promise<WebSourceResponse> => {
    const response = await apiClient.get<WebSourceResponse>(`/api/web/${webSourceId}`);
    return response.data;
  },

  /**
   * List all web sources
   */
  listWebSources: async (): Promise<WebSourceResponse[]> => {
    const response = await apiClient.get<WebSourceResponse[]>('/api/web/sources');
    return response.data;
  },

  /**
   * Delete a web source and its vectors
   */
  deleteWebSource: async (webSourceId: string): Promise<void> => {
    await apiClient.delete(`/api/web/${webSourceId}`);
  },

  /**
   * Generate word cloud data from document texts
   */
  getWordCloud: async (documentIds: string[], maxWords: number = 100): Promise<WordCloudResponse> => {
    const response = await apiClient.post<WordCloudResponse>('/api/wordcloud', {
      document_ids: documentIds,
      max_words: maxWords,
    }, { timeout: 60000 });
    return response.data;
  },

  // ── Batch Processing ──────────────────────────────────────────────────

  /**
   * List all object-store connectors
   */
  runConnector: async (id: string, processingMode: 'normal' | 'batch'): Promise<BatchJob> => {
    const response = await apiClient.post<BatchJob>(`/api/batch/connectors/${id}/run`,
      { processing_mode: processingMode }, { timeout: 0 });
    return response.data;
  },

  updateConnector: async (id: string, data: Omit<ObjectStoreConnector, 'id' | 'created_at' | 'updated_at'>): Promise<ObjectStoreConnector> => {
    const response = await apiClient.put<ObjectStoreConnector>(`/api/batch/connectors/${id}`, data);
    return response.data;
  },

  listConnectors: async (): Promise<ObjectStoreConnector[]> => {
    const response = await apiClient.get<ObjectStoreConnector[]>('/api/batch/connectors');
    return response.data;
  },

  /**
   * Create a new object-store connector
   */
  createConnector: async (data: Omit<ObjectStoreConnector, 'id' | 'created_at' | 'updated_at'>): Promise<ObjectStoreConnector> => {
    const response = await apiClient.post<ObjectStoreConnector>('/api/batch/connectors', data);
    return response.data;
  },

  /**
   * Delete an object-store connector
   */
  deleteConnector: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/batch/connectors/${id}`);
  },

  /**
   * Test connectivity of an object-store connector
   */
  testConnector: async (id: string): Promise<{ status: string; error?: string }> => {
    const response = await apiClient.post<{ status: string; error?: string }>(`/api/batch/connectors/${id}/test`);
    return response.data;
  },

  /**
   * Test connectivity with raw connection parameters (before saving)
   */
  testConnection: async (data: { namespace: string; bucket_name: string; compartment_id: string; region: string }): Promise<{ status: string; error?: string }> => {
    const response = await apiClient.post<{ status: string; error?: string }>('/api/batch/connectors/test', data);
    return response.data;
  },

  /**
   * List all batch triggers
   */
  listTriggers: async (): Promise<BatchTrigger[]> => {
    const response = await apiClient.get<BatchTrigger[]>('/api/batch/triggers');
    return response.data;
  },

  /**
   * Create a new batch trigger
   */
  createTrigger: async (data: { connector_id: string; name: string; schedule: string; is_active: boolean; parallelism: number }): Promise<BatchTrigger> => {
    const response = await apiClient.post<BatchTrigger>('/api/batch/triggers', data);
    return response.data;
  },

  /**
   * Update an existing batch trigger
   */
  updateTrigger: async (id: string, data: Partial<{ name: string; schedule: string; is_active: boolean }>): Promise<BatchTrigger> => {
    const response = await apiClient.put<BatchTrigger>(`/api/batch/triggers/${id}`, data);
    return response.data;
  },

  /**
   * Delete a batch trigger
   */
  deleteTrigger: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/batch/triggers/${id}`);
  },

  /**
   * Manually run a batch trigger
   */
  runTrigger: async (id: string): Promise<BatchJob> => {
    const response = await apiClient.post<BatchJob>(`/api/batch/triggers/${id}/run`);
    return response.data;
  },

  /**
   * List batch jobs, optionally filtered by trigger
   */
  listBatchJobs: async (triggerId?: string): Promise<BatchJob[]> => {
    const params = triggerId ? { trigger_id: triggerId } : {};
    const response = await apiClient.get<BatchJob[]>('/api/batch/jobs', { params });
    return response.data;
  },

  /**
   * Get a single batch job by id
   */
  getBatchJob: async (id: string): Promise<BatchJob> => {
    const response = await apiClient.get<BatchJob>(`/api/batch/jobs/${id}`);
    return response.data;
  },

  /**
   * Get file statuses for a batch job
   */
  getBatchJobFiles: async (jobId: string): Promise<BatchJobFile[]> => {
    const response = await apiClient.get<BatchJobFile[]>(`/api/batch/jobs/${jobId}/files`);
    return response.data;
  },

  // ── Workflows ───────────────────────────────────────────────────────

  readWorkflowInputFile: async (file: File): Promise<{ filename: string; text: string }> => {
    const data = new FormData();
    data.append('file', file);
    const response = await apiClient.post('/api/workflows/input-file', data,
      { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 60000 });
    return response.data;
  },

  listWorkflows: async (): Promise<Workflow[]> => {
    const response = await apiClient.get<Workflow[]>('/api/workflows');
    return response.data;
  },

  createWorkflow: async (data: { name: string; description: string; nodes: any[]; edges: any[] }): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>('/api/workflows', data);
    return response.data;
  },

  getWorkflow: async (id: string): Promise<Workflow> => {
    const response = await apiClient.get<Workflow>(`/api/workflows/${id}`);
    return response.data;
  },

  updateWorkflow: async (id: string, data: Partial<{ name: string; description: string; nodes: any[]; edges: any[] }>): Promise<Workflow> => {
    const response = await apiClient.put<Workflow>(`/api/workflows/${id}`, data);
    return response.data;
  },

  deleteWorkflow: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/workflows/${id}`);
  },

  executeWorkflow: async (id: string, inputData: Record<string, any>): Promise<WorkflowExecution> => {
    const response = await apiClient.post<WorkflowExecution>(`/api/workflows/${id}/execute`, { input_data: inputData }, { timeout: 120000 });
    return response.data;
  },

  listWorkflowExecutions: async (workflowId: string): Promise<WorkflowExecution[]> => {
    const response = await apiClient.get<WorkflowExecution[]>(`/api/workflows/${workflowId}/executions`);
    return response.data;
  },

  getWorkflowExecution: async (executionId: string): Promise<WorkflowExecution> => {
    const response = await apiClient.get<WorkflowExecution>(`/api/workflows/executions/${executionId}`);
    return response.data;
  },

  // ── Workflow Scheduling ─────────────────────────────────────────────

  createWorkflowSchedule: async (workflowId: string, data: {
    schedule_type: 'one_time' | 'recurring';
    cron_expression?: string;
    run_at?: string;
    input_data?: Record<string, any>;
    is_active?: boolean;
  }): Promise<WorkflowSchedule> => {
    const response = await apiClient.post<WorkflowSchedule>(`/api/workflows/${workflowId}/schedule`, data);
    return response.data;
  },

  getWorkflowSchedule: async (workflowId: string): Promise<WorkflowSchedule> => {
    const response = await apiClient.get<WorkflowSchedule>(`/api/workflows/${workflowId}/schedule`);
    return response.data;
  },

  deleteWorkflowSchedule: async (workflowId: string): Promise<void> => {
    await apiClient.delete(`/api/workflows/${workflowId}/schedule`);
  },

  toggleWorkflowSchedule: async (workflowId: string, isActive: boolean): Promise<WorkflowSchedule> => {
    const response = await apiClient.patch<WorkflowSchedule>(`/api/workflows/${workflowId}/schedule/toggle`, { is_active: isActive });
    return response.data;
  },

  listScheduledRuns: async (workflowId: string): Promise<ScheduledRun[]> => {
    const response = await apiClient.get<ScheduledRun[]>(`/api/workflows/${workflowId}/scheduled-runs`);
    return response.data;
  },

  listProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/api/projects');
    return response.data;
  },

  // ── Research ────────────────────────────────────────────────────────

  generateReport: async (query: string, documentIds: string[], reportType: string = 'summary'): Promise<ResearchResponse> => {
    const response = await apiClient.post<ResearchResponse>('/api/research/report', {
      query,
      document_ids: documentIds,
      report_type: reportType,
    }, { timeout: 120000 });
    return response.data;
  },

  getReportTemplates: async (): Promise<ReportTemplate[]> => {
    const response = await apiClient.get<{ templates: ReportTemplate[] }>('/api/research/templates');
    return response.data.templates;
  },

  // ── Compliance ─────────────────────────────────────────────────────

  checkCompliance: async (documentIds: string[], industry: string = 'generic'): Promise<ComplianceCheckResponse> => {
    const response = await apiClient.post<ComplianceCheckResponse>('/api/compliance/check', {
      document_ids: documentIds,
      industry,
    }, { timeout: 60000 });
    return response.data;
  },

  reviewCompliance: async (
    documentId: string,
    reviewer: string,
    decision: 'approved' | 'changes_requested',
    notes?: string,
  ): Promise<DocumentComplianceResult> => {
    const response = await apiClient.put<DocumentComplianceResult>(`/api/compliance/${documentId}/review`, {
      reviewer,
      decision,
      notes: notes || undefined,
    });
    return response.data;
  },

  listIndustries: async (): Promise<IndustryOption[]> => {
    const response = await apiClient.get<{ industries: IndustryOption[] }>('/api/compliance/industries');
    return response.data.industries;
  },

  // ── Domain Adapters ────────────────────────────────────────────────────

  listDomains: async (): Promise<DomainInfo[]> => {
    const response = await apiClient.get<{ domains: DomainInfo[] }>('/api/domains');
    return response.data.domains;
  },

  getDomainDetail: async (domain: string): Promise<DomainDetail> => {
    const response = await apiClient.get<DomainDetail>(`/api/domains/${domain}`);
    return response.data;
  },

  toggleDomain: async (domain: string, enabled: boolean): Promise<{ domain: string; enabled: boolean }> => {
    const response = await apiClient.patch<{ domain: string; enabled: boolean }>(`/api/domains/${domain}/toggle`, { enabled });
    return response.data;
  },

  updateDomainConfig: async (domain: string, fileType: string, data: any): Promise<{ message: string }> => {
    const response = await apiClient.put<{ message: string }>(`/api/domains/${domain}/config`, {
      file_type: fileType,
      data,
    });
    return response.data;
  },

  // ── Metrics / Benchmarking ────────────────────────────────────────────

  getMetricsOverview: async (): Promise<any> => {
    const response = await apiClient.get('/api/metrics/overview');
    return response.data;
  },

  getComplianceSummary: async (): Promise<any> => {
    const response = await apiClient.get('/api/metrics/compliance-summary');
    return response.data;
  },

  getDomainUsage: async (): Promise<any> => {
    const response = await apiClient.get('/api/metrics/domain-usage');
    return response.data;
  },

  getBaselines: async (): Promise<any> => {
    const response = await apiClient.get('/api/metrics/baselines');
    return response.data;
  },
};

export default api;
