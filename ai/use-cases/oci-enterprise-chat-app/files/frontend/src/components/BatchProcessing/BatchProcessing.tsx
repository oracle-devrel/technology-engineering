import React, { useState, useEffect, useCallback } from 'react';
import {
  Database,
  Plus,
  Trash2,
  Play,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Loader2,
  Plug,
  RefreshCw,
  Pencil,
} from 'lucide-react';
import { api } from '../../services/api';
import { ObjectStoreConnector, BatchTrigger, BatchJob, BatchJobFile } from '../../types';

type Tab = 'connectors' | 'triggers' | 'jobs';

const statusColors: Record<string, string> = {
  pending: 'text-yellow-400',
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
  downloading: 'text-blue-400',
  processing: 'text-blue-400', vectorizing: 'text-blue-400', analyzing: 'text-blue-400',
};

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4" />,
  running: <Loader2 className="h-4 w-4 animate-spin" />,
  completed: <CheckCircle className="h-4 w-4" />,
  failed: <XCircle className="h-4 w-4" />,
  downloading: <Loader2 className="h-4 w-4 animate-spin" />,
  processing: <Loader2 className="h-4 w-4 animate-spin" />,
  vectorizing: <Loader2 className="h-4 w-4 animate-spin" />,
  analyzing: <Loader2 className="h-4 w-4 animate-spin" />,
};

const BatchProcessing: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>('connectors');
  const [processingMode, setProcessingMode] = useState<'normal' | 'batch'>('batch');
  const [editingConnector, setEditingConnector] = useState<string | null>(null);
  const [runningConnector, setRunningConnector] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const showError = (err: any) => {
    const detail = err?.response?.data?.detail;
    setError(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg).join('; ') : err.message);
  };
  const runConnector = async (id: string) => {
    setRunningConnector(id);
    setError(null);
    try { await api.runConnector(id, processingMode); setActiveTab('jobs'); await loadJobs(); }
    catch (err) { showError(err); }
    finally { setRunningConnector(null); }
  };

  // Connectors state
  const [connectors, setConnectors] = useState<ObjectStoreConnector[]>([]);
  const [showConnectorForm, setShowConnectorForm] = useState(false);
  const [connectorForm, setConnectorForm] = useState({
    name: '', namespace: '', bucket_name: '', compartment_id: '', region: '', prefix: '',
  });
  const [testResults, setTestResults] = useState<Record<string, { status: string; error?: string }>>({});
  const [formTestResult, setFormTestResult] = useState<{ status: string; error?: string } | null>(null);
  const [formTesting, setFormTesting] = useState(false);

  // Triggers state
  const [triggers, setTriggers] = useState<BatchTrigger[]>([]);
  const [showTriggerForm, setShowTriggerForm] = useState(false);
  const [triggerForm, setTriggerForm] = useState({
    connector_id: '', name: '', schedule: '', is_active: true, parallelism: 1,
  });

  // Jobs state
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [jobFiles, setJobFiles] = useState<Record<string, BatchJobFile[]>>({});

  const [loading, setLoading] = useState(false);

  const loadConnectors = useCallback(async () => {
    try {
      const data = await api.listConnectors();
      setConnectors(data);
    } catch (err) { showError(err); }
  }, []);

  const loadTriggers = useCallback(async () => {
    try {
      const data = await api.listTriggers();
      setTriggers(data);
    } catch (err) { showError(err); }
  }, []);

  const loadJobs = useCallback(async () => {
    try {
      const data = await api.listBatchJobs();
      setJobs(data);
    } catch (err) { showError(err); }
  }, []);

  useEffect(() => {
    loadConnectors();
    loadTriggers();
    loadJobs();
  }, [loadConnectors, loadTriggers, loadJobs]);

  // Auto-refresh jobs
  useEffect(() => {
    if (activeTab !== 'jobs') return;
    const refresh = async () => {
      await loadJobs();
      if (expandedJob) {
        try { const files = await api.getBatchJobFiles(expandedJob); setJobFiles(prev => ({ ...prev, [expandedJob]: files })); }
        catch (err) { showError(err); }
      }
    };
    const interval = setInterval(refresh, 2000);
    return () => clearInterval(interval);
  }, [activeTab, loadJobs, expandedJob]);

  const handleTestConnectionInForm = async () => {
    setFormTesting(true);
    setFormTestResult(null);
    try {
      const result = await api.testConnection({
        namespace: connectorForm.namespace,
        bucket_name: connectorForm.bucket_name,
        compartment_id: connectorForm.compartment_id,
        region: connectorForm.region,
      });
      setFormTestResult(result);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      const errorMsg = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((d: any) => d.msg).join(', ') : err.message;
      setFormTestResult({ status: 'failed', error: errorMsg });
    }
    setFormTesting(false);
  };

  const canTestConnection = connectorForm.namespace && connectorForm.bucket_name && connectorForm.compartment_id && connectorForm.region;

  const handleCreateConnector = async () => {
    setLoading(true);
    try {
      const save = editingConnector ? (data: any) => api.updateConnector(editingConnector, data) : api.createConnector;
      await save({
        name: connectorForm.name,
        namespace: connectorForm.namespace,
        bucket_name: connectorForm.bucket_name,
        compartment_id: connectorForm.compartment_id,
        region: connectorForm.region,
        prefix: connectorForm.prefix || undefined,
      });
      setShowConnectorForm(false);
      setEditingConnector(null);
      setFormTestResult(null);
      setConnectorForm({ name: '', namespace: '', bucket_name: '', compartment_id: '', region: '', prefix: '' });
      await loadConnectors();
    } catch (err) { showError(err); }
    setLoading(false);
  };

  const handleTestConnector = async (id: string) => {
    setTestResults(prev => ({ ...prev, [id]: { status: 'testing' } }));
    try {
      const result = await api.testConnector(id);
      setTestResults(prev => ({ ...prev, [id]: result }));
    } catch (err: any) {
      setTestResults(prev => ({ ...prev, [id]: { status: 'failed', error: err.message } }));
    }
  };

  const handleDeleteConnector = async (id: string) => {
    try {
      await api.deleteConnector(id);
      await loadConnectors();
    } catch (err) { showError(err); }
  };

  const handleCreateTrigger = async () => {
    setLoading(true);
    try {
      await api.createTrigger(triggerForm);
      setShowTriggerForm(false);
      setTriggerForm({ connector_id: '', name: '', schedule: '', is_active: true, parallelism: 1 });
      await loadTriggers();
    } catch (err) { showError(err); }
    setLoading(false);
  };

  const handleToggleTrigger = async (trigger: BatchTrigger) => {
    try {
      await api.updateTrigger(trigger.id, { is_active: !trigger.is_active });
      await loadTriggers();
    } catch (err) { showError(err); }
  };

  const handleRunTrigger = async (id: string) => {
    try {
      await api.runTrigger(id);
      setActiveTab('jobs');
      await loadJobs();
    } catch (err) { showError(err); }
  };

  const handleDeleteTrigger = async (id: string) => {
    try {
      await api.deleteTrigger(id);
      await loadTriggers();
    } catch (err) { showError(err); }
  };

  const handleExpandJob = async (jobId: string) => {
    if (expandedJob === jobId) {
      setExpandedJob(null);
      return;
    }
    setExpandedJob(jobId);
    if (!jobFiles[jobId]) {
      try {
        const files = await api.getBatchJobFiles(jobId);
        setJobFiles(prev => ({ ...prev, [jobId]: files }));
      } catch (err) { showError(err); }
    }
  };

  const tabs: { key: Tab; label: string; icon: React.ReactNode }[] = [
    { key: 'connectors', label: 'Connectors', icon: <Plug className="h-4 w-4" /> },
    { key: 'triggers', label: 'Triggers', icon: <Clock className="h-4 w-4" /> },
    { key: 'jobs', label: 'Jobs', icon: <Database className="h-4 w-4" /> },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Batch Processing</h1>
        <p className="text-dark-300 mt-1">Process documents from OCI Object Storage at scale</p>
      </div>

      {error && <div role="alert" className="mb-4 p-3 bg-red-500/10 text-red-300 rounded">{error}</div>}
      <div className="flex items-center gap-4 mb-4 text-dark-200 text-sm">
        <span>Processing mode</span>
        {(['normal', 'batch'] as const).map(mode => <label key={mode} className="flex items-center gap-2">
          <input type="radio" name="processing-mode" value={mode} checked={processingMode === mode} onChange={() => setProcessingMode(mode)} />
          {mode === 'normal' ? 'Normal (wait for results)' : 'Batch (background)'}
        </label>)}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-dark-800 rounded-lg p-1 border border-dark-700 w-fit">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-oracle-red text-white'
                : 'text-dark-300 hover:text-white hover:bg-dark-700'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Connectors Tab */}
      {activeTab === 'connectors' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">OCI Object Storage Connectors</h2>
            <button
              onClick={() => { setEditingConnector(null); setConnectorForm({ name: '', namespace: '', bucket_name: '', compartment_id: '', region: '', prefix: '' }); setShowConnectorForm(true); }}
              className="flex items-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md transition-colors"
            >
              <Plus className="h-4 w-4" /> Add Connector
            </button>
          </div>

          {showConnectorForm && (
            <div className="bg-dark-800 rounded-lg border border-dark-700 p-6 mb-4">
              <h3 className="text-white font-medium mb-4">{editingConnector ? 'Edit Connector' : 'New Connector'}</h3>
              <div className="grid grid-cols-2 gap-4">
                {(['name', 'namespace', 'bucket_name', 'compartment_id', 'region', 'prefix'] as const).map(field => (
                  <div key={field}>
                    <label className="block text-sm text-dark-300 mb-1 capitalize">{field.replace('_', ' ')}</label>
                    <input
                      type="text"
                      aria-label={field.replace('_', ' ')}
                      value={connectorForm[field]}
                      onChange={e => setConnectorForm(prev => ({ ...prev, [field]: e.target.value }))}
                      placeholder={field === 'prefix' ? '(optional)' : ''}
                      className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                    />
                  </div>
                ))}
              </div>
              <div className="flex items-center gap-2 mt-4">
                <button onClick={handleCreateConnector} disabled={loading} className="px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm transition-colors disabled:opacity-50">
                  {loading ? 'Saving...' : editingConnector ? 'Save Connector' : 'Create'}
                </button>
                <button
                  onClick={handleTestConnectionInForm}
                  disabled={!canTestConnection || formTesting}
                  className="px-4 py-2 bg-dark-600 hover:bg-dark-500 text-white rounded-md text-sm transition-colors disabled:opacity-50 border border-dark-500"
                >
                  {formTesting ? 'Testing...' : 'Test Connection'}
                </button>
                <button onClick={() => { setShowConnectorForm(false); setFormTestResult(null); }} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-md text-sm transition-colors">
                  Cancel
                </button>
                {formTestResult && (
                  <span className={`ml-2 text-sm font-medium ${formTestResult.status === 'connected' ? 'text-green-400' : 'text-red-400'}`}>
                    {formTestResult.status === 'connected' ? '✓ Connection successful' : `✗ ${formTestResult.error || 'Connection failed'}`}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="space-y-3">
            {connectors.length === 0 ? (
              <div className="text-center py-12 text-dark-400">
                <Database className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No connectors configured yet</p>
              </div>
            ) : (
              connectors.map(c => (
                <div key={c.id} className="bg-dark-800 rounded-lg border border-dark-700 p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-white font-medium">{c.name}</h3>
                      <p className="text-sm text-dark-400 mt-1">
                        {c.namespace}/{c.bucket_name} &middot; {c.region}
                        {c.prefix && <span> &middot; prefix: {c.prefix}</span>}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button aria-label={`Run ${c.name}`} disabled={!!runningConnector} onClick={() => runConnector(c.id)} className="text-sm text-dark-200 disabled:opacity-50">{runningConnector === c.id ? 'Processing...' : 'Run'}</button>
                      <button aria-label={`Edit ${c.name}`} onClick={() => { setEditingConnector(c.id); setConnectorForm({ name: c.name, namespace: c.namespace, bucket_name: c.bucket_name, compartment_id: c.compartment_id, region: c.region, prefix: c.prefix || '' }); setShowConnectorForm(true); }} className="p-2 text-dark-300"><Pencil className="h-4 w-4" /></button>
                      <button onClick={() => handleTestConnector(c.id)} className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
                        Test
                      </button>
                      <button onClick={() => handleDeleteConnector(c.id)} className="p-1.5 text-dark-400 hover:text-red-400 transition-colors">
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                  {testResults[c.id] && (
                    <div className={`mt-2 text-sm ${testResults[c.id].status === 'connected' ? 'text-green-400' : testResults[c.id].status === 'testing' ? 'text-blue-400' : 'text-red-400'}`}>
                      {testResults[c.id].status === 'testing' ? 'Testing...' : testResults[c.id].status === 'connected' ? 'Connected successfully' : `Failed: ${testResults[c.id].error || 'Connection failed'}`}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Triggers Tab */}
      {activeTab === 'triggers' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Scheduled Triggers</h2>
            <button
              onClick={() => setShowTriggerForm(true)}
              className="flex items-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md transition-colors"
            >
              <Plus className="h-4 w-4" /> Create Trigger
            </button>
          </div>

          {showTriggerForm && (
            <div className="bg-dark-800 rounded-lg border border-dark-700 p-6 mb-4">
              <h3 className="text-white font-medium mb-4">New Trigger</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Connector</label>
                  <select
                    value={triggerForm.connector_id}
                    onChange={e => setTriggerForm(prev => ({ ...prev, connector_id: e.target.value }))}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  >
                    <option value="">Select connector...</option>
                    {connectors.map(c => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Name</label>
                  <input
                    type="text"
                    value={triggerForm.name}
                    onChange={e => setTriggerForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  />
                </div>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Schedule (cron)</label>
                  <input
                    type="text"
                    value={triggerForm.schedule}
                    onChange={e => setTriggerForm(prev => ({ ...prev, schedule: e.target.value }))}
                    placeholder="0 2 * * *"
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  />
                  <p className="text-xs text-dark-500 mt-1">minute hour day month weekday</p>
                </div>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Parallel Jobs</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={triggerForm.parallelism}
                    onChange={e => setTriggerForm(prev => ({ ...prev, parallelism: Math.max(1, Math.min(5, parseInt(e.target.value) || 1)) }))}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  />
                  <p className="text-xs text-dark-500 mt-1">Files processed concurrently (1-5)</p>
                </div>
                <div className="flex items-center gap-2 pt-6">
                  <input
                    type="checkbox"
                    checked={triggerForm.is_active}
                    onChange={e => setTriggerForm(prev => ({ ...prev, is_active: e.target.checked }))}
                    className="rounded"
                  />
                  <label className="text-sm text-dark-300">Active</label>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button onClick={handleCreateTrigger} disabled={loading} className="px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm transition-colors disabled:opacity-50">
                  {loading ? 'Saving...' : editingConnector ? 'Save Connector' : 'Create'}
                </button>
                <button onClick={() => setShowTriggerForm(false)} className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-md text-sm transition-colors">
                  Cancel
                </button>
              </div>
            </div>
          )}

          <div className="space-y-3">
            {triggers.length === 0 ? (
              <div className="text-center py-12 text-dark-400">
                <Clock className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No triggers configured yet</p>
              </div>
            ) : (
              triggers.map(t => {
                const connector = connectors.find(c => c.id === t.connector_id);
                return (
                  <div key={t.id} className="bg-dark-800 rounded-lg border border-dark-700 p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-white font-medium">{t.name}</h3>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_active ? 'bg-green-500/20 text-green-400' : 'bg-dark-600 text-dark-400'}`}>
                            {t.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </div>
                        <p className="text-sm text-dark-400 mt-1">
                          {connector?.name || t.connector_id} &middot; {t.schedule} &middot; {t.parallelism || 1}x parallel
                          {t.last_run && <span> &middot; Last: {new Date(t.last_run).toLocaleString()}</span>}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={() => handleToggleTrigger(t)} className="px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
                          {t.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button onClick={() => handleRunTrigger(t.id)} className="flex items-center gap-1 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
                          <Play className="h-3 w-3" /> Run Now
                        </button>
                        <button onClick={() => handleDeleteTrigger(t.id)} className="p-1.5 text-dark-400 hover:text-red-400 transition-colors">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}

      {/* Jobs Tab */}
      {activeTab === 'jobs' && (
        <div>
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-white">Batch Jobs</h2>
            <button onClick={loadJobs} className="flex items-center gap-2 px-3 py-1.5 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
              <RefreshCw className="h-4 w-4" /> Refresh
            </button>
          </div>

          <div className="space-y-3">
            {jobs.length === 0 ? (
              <div className="text-center py-12 text-dark-400">
                <AlertCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No batch jobs yet. Create a trigger and run it.</p>
              </div>
            ) : (
              jobs.map(job => (
                <div key={job.id} className="bg-dark-800 rounded-lg border border-dark-700">
                  <button
                    onClick={() => handleExpandJob(job.id)}
                    className="w-full p-4 text-left"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className={statusColors[job.status]}>
                          {statusIcons[job.status]}
                        </span>
                        <div>
                          <span className="text-white font-medium capitalize">{job.status}</span>
                          <p className="text-sm text-dark-400 mt-0.5">
                            {job.files_found} found &middot; {job.files_processed} processed &middot; {job.files_failed} failed
                          </p>
                        </div>
                      </div>
                      <div className="text-sm text-dark-400">
                        {job.started_at ? new Date(job.started_at).toLocaleString() : new Date(job.created_at).toLocaleString()}
                      </div>
                    </div>
                  </button>

                  {expandedJob === job.id && jobFiles[job.id] && (
                    <div className="border-t border-dark-700 p-4">
                      <h4 className="text-sm font-medium text-dark-300 mb-2">Files</h4>
                      {jobFiles[job.id].length === 0 ? (
                        <p className="text-sm text-dark-500">No files processed</p>
                      ) : (
                        <div className="space-y-1">
                          {jobFiles[job.id].map(file => (
                            <div key={file.id} className="text-sm py-2 border-b border-dark-700">
                              <div className="flex items-center gap-2">
                                <span className={statusColors[file.status]}>
                                  {statusIcons[file.status]}
                                </span>
                                <span className="text-dark-200">{file.file_name}</span>
                              </div>
                              <span className="text-dark-400">
                                {file.file_size ? `${(file.file_size / 1024).toFixed(1)} KB` : ''}
                                {' · '}{file.status} · Vectorization: {file.vectorization_status || 'pending'} ({file.chunks_indexed || 0} chunks) · Analysis: {file.analysis_status || 'pending'}
                              </span>
                              {file.error_message && <p className="text-red-300 mt-1">{file.error_message}</p>}
                              {file.analysis_result && <details className="mt-2 text-dark-200"><summary className="cursor-pointer">Analysis result</summary><p className="whitespace-pre-wrap mt-2">{file.analysis_result.summary}</p></details>}
                            </div>
                          ))}
                        </div>
                      )}
                      {job.error_message && (
                        <p className="text-sm text-red-400 mt-2">{job.error_message}</p>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BatchProcessing;
