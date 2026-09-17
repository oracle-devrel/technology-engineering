import React, { useState, useEffect } from 'react';
import { X, FolderOpen, Loader2 } from 'lucide-react';
import { useWorkflowStore } from '../../stores/workflowStore';
import { api } from '../../services/api';
import { Project, ObjectStoreConnector } from '../../types';

const NodeConfigPanel: React.FC = () => {
  const { nodes, edges, selectedNodeId, updateNodeData, selectNode, hasChatNode } = useWorkflowStore();
  const node = nodes.find(n => n.id === selectedNodeId);

  const [label, setLabel] = useState('');
  const [config, setConfig] = useState<Record<string, any>>({});
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(false);
  const [readingFile, setReadingFile] = useState(false);
  const [connectors, setConnectors] = useState<ObjectStoreConnector[]>([]);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api.listConnectors().then(setConnectors).catch(() => setError('Could not load OCI connectors'));
  }, []);

  useEffect(() => {
    if (node) {
      setLabel(node.data.label as string || '');
      setConfig((node.data.config as Record<string, any>) || {});
    }
  }, [node]);

  // Load projects when input type is project
  useEffect(() => {
    if (config.input_type === 'project' && projects.length === 0) {
      setLoadingProjects(true);
      api.listProjects().then(p => setProjects(p)).catch(() => setError('Could not load projects')).finally(() => setLoadingProjects(false));
    }
  }, [config.input_type]);

  if (!node) return null;

  const nodeType = node.data.nodeType as string;

  const handleSave = () => {
    let savedConfig = config;
    if (config.input_type === 'project') {
      const projectId = config.project?.project_id || config.project_id;
      const project = projects.find(p => p.id === projectId);
      if (!project?.document_ids.length) { setError('Choose a project containing indexed documents'); return; }
      savedConfig = { ...config, project_id: project.id, document_ids: project.document_ids };
    }
    updateNodeData(node.id, { label, config: savedConfig });
    selectNode(null);
  };

  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const updateNestedConfig = (parent: string, key: string, value: any) => {
    setConfig(prev => ({
      ...prev,
      [parent]: { ...(prev[parent] || {}), [key]: value },
    }));
  };

  // Get connected sources for agent nodes
  const getConnectedSources = () => {
    if (!node || nodeType !== 'agent') return [];
    return edges
      .filter(e => e.target === node.id)
      .map(e => {
        const sourceNode = nodes.find(n => n.id === e.source);
        return sourceNode ? { id: sourceNode.id, type: sourceNode.type, label: sourceNode.data.label as string } : null;
      })
      .filter(Boolean);
  };

  return (
    <div className="w-80 bg-dark-800 border-l border-dark-700 flex flex-col h-full overflow-y-auto">
      <div className="flex items-center justify-between p-4 border-b border-dark-700">
        <h3 className="text-white font-medium">Configure Node</h3>
        <button onClick={() => selectNode(null)} className="text-dark-400 hover:text-white transition-colors">
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
        {/* Label */}
        <div>
          <label className="block text-sm text-dark-300 mb-1">Label</label>
          <input
            type="text"
            aria-label="Node label"
            value={label}
            onChange={e => setLabel(e.target.value)}
            className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
          />
        </div>

        {/* Agent config */}
        {nodeType === 'agent' && (
          <>
            {/* Connected sources indicator */}
            {getConnectedSources().length > 0 && (
              <div>
                <label className="block text-sm text-dark-300 mb-1">Connected Inputs</label>
                <div className="space-y-1">
                  {getConnectedSources().map((src: any) => (
                    <div key={src.id} className="flex items-center gap-2 px-2 py-1 bg-dark-900 rounded text-xs">
                      <span className={`w-2 h-2 rounded-full ${
                        src.type === 'input' ? 'bg-blue-400' :
                        src.type === 'agent' ? 'bg-purple-400' :
                        src.type === 'data_source' ? 'bg-emerald-400' :
                        src.type === 'chat' ? 'bg-green-400' : 'bg-dark-400'
                      }`} />
                      <span className="text-dark-300">{src.label}</span>
                      <span className="text-dark-500 ml-auto">{src.type}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            <div>
              <label className="block text-sm text-dark-300 mb-1">System Prompt</label>
              <textarea
                aria-label="System Prompt"
                value={config.prompt || ''}
                onChange={e => updateConfig('prompt', e.target.value)}
                rows={4}
                placeholder="You are a helpful assistant..."
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red resize-none"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Model</label>
              <input
                type="text"
                value={config.model || ''}
                onChange={e => updateConfig('model', e.target.value)}
                placeholder="(default server model)"
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Temperature: {config.temperature ?? 0.3}</label>
              <input
                type="range"
                min="0" max="2" step="0.1"
                value={config.temperature ?? 0.3}
                onChange={e => updateConfig('temperature', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Max Tokens</label>
              <input
                type="number"
                value={config.max_tokens || 2048}
                onChange={e => updateConfig('max_tokens', parseInt(e.target.value))}
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
              />
            </div>
          </>
        )}

        {/* Data Source config */}
        {nodeType === 'data_source' && (
          <>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Source Type</label>
              <select
                aria-label="Source Type"
                value={config.source_type || 'oracle_vector_db'}
                onChange={e => updateConfig('source_type', e.target.value)}
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
              >
                <option value="oracle_vector_db">Oracle Vector DB</option>
                <option value="object_storage">Object Storage</option>
              </select>
            </div>
            <div>
              {config.source_type === 'object_storage' && <div className="mb-3">
                <label className="block text-sm text-dark-300 mb-1">OCI Connector</label>
                <select aria-label="Source OCI Connector" value={config.connector_id || ''} onChange={e => updateConfig('connector_id', e.target.value)} className="w-full bg-dark-900 border border-dark-600 rounded px-3 py-2 text-white text-sm">
                  <option value="">Select a connector</option>
                  {connectors.map(c => <option key={c.id} value={c.id}>{c.name} · {c.bucket_name}</option>)}
                </select>
                <p className="text-xs text-dark-400 mt-2">Manage connectors in Batch. Reads PDF, TXT, Markdown, JSON and CSV within the connector prefix (up to 20 files).</p>
              </div>}
              <label className="block text-sm text-dark-300 mb-1">Top K (vector search): {config.top_k ?? 5}</label>
              <input
                type="range"
                min="1" max="20" step="1"
                value={config.top_k ?? 5}
                onChange={e => updateConfig('top_k', parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </>
        )}

        {/* Input config */}
        {nodeType === 'input' && (
          <>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Input Type</label>
              <select
                value={config.input_type || 'text'}
                onChange={e => updateConfig('input_type', e.target.value)}
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
              >
                <option value="text">Text</option>
                <option value="file">File</option>
                <option value="project">Project (RAG)</option>
              </select>
            </div>

            {config.input_type === 'file' && <div>
              <label className="block text-sm text-dark-300 mb-1">Input file (up to 10 MB)</label>
              <input aria-label="Input file" type="file" accept=".pdf,.txt,.md,.json,.csv" disabled={readingFile}
                className="w-full text-sm text-dark-300"
                onChange={async event => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  setReadingFile(true); setError(null);
                  try {
                    const result = await api.readWorkflowInputFile(file);
                    setConfig(prev => ({ ...prev, file_name: result.filename, file_content: result.text }));
                  } catch (err: any) { setError(err?.response?.data?.detail || 'Could not read the file'); }
                  finally { setReadingFile(false); }
                }} />
              <p className="text-xs text-dark-400 mt-2">{readingFile ? 'Reading file...' : config.file_name || 'Choose a file'}. Extracted text is saved with this workflow.</p>
            </div>}

            {/* Project selector */}
            {config.input_type === 'project' && (
              <div>
                <label className="block text-sm text-dark-300 mb-1">
                  <FolderOpen className="inline h-3.5 w-3.5 mr-1" />
                  Select Project
                </label>
                {loadingProjects ? (
                  <div className="flex items-center gap-2 text-dark-400 text-sm py-2">
                    <Loader2 className="h-4 w-4 animate-spin" /> Loading projects...
                  </div>
                ) : (
                  <select
                    value={config.project?.project_id || config.project_id || ''}
                    onChange={e => updateNestedConfig('project', 'project_id', e.target.value)}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  >
                    <option value="">-- Select a project --</option>
                    {projects.map(p => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </select>
                )}
                <div className="flex items-center gap-2 mt-2">
                  <input
                    type="checkbox"
                    checked={config.project?.use_as_rag !== false}
                    onChange={e => updateNestedConfig('project', 'use_as_rag', e.target.checked)}
                    className="rounded border-dark-600"
                  />
                  <span className="text-xs text-dark-400">Use as RAG context</span>
                </div>
              </div>
            )}
          </>
        )}

        {/* Output config */}
        {nodeType === 'output' && (
          <>
            <div>
              <label className="block text-sm text-dark-300 mb-1">Output Type</label>
              <select
                aria-label="Output Type"
                value={config.output_type || 'text'}
                onChange={e => updateConfig('output_type', e.target.value)}
                className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
              >
                <option value="text">Text</option>
                <option value="json">JSON</option>
                {hasChatNode() && <option value="chat">Chat</option>}
                <option value="object_store">Object Store</option>
              </select>
            </div>

            {/* Object Store config */}
            {config.output_type === 'object_store' && (
              <>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">OCI Connector</label>
                  <select aria-label="Output OCI Connector" value={config.object_store?.connector_id || ''} onChange={e => updateNestedConfig('object_store', 'connector_id', e.target.value)} className="w-full bg-dark-900 border border-dark-600 rounded px-3 py-2 text-white text-sm">
                    <option value="">Use explicit bucket settings</option>
                    {connectors.map(c => <option key={c.id} value={c.id}>{c.name} · {c.bucket_name}</option>)}
                  </select>
                </div>
                {!config.object_store?.connector_id && ['namespace', 'region'].map(field => <div key={field}>
                  <label className="block text-sm text-dark-300 mb-1 capitalize">{field}</label>
                  <input aria-label={`Output ${field}`} value={config.object_store?.[field] || ''} onChange={e => updateNestedConfig('object_store', field, e.target.value)} className="w-full bg-dark-900 border border-dark-600 rounded px-3 py-2 text-white text-sm" />
                </div>)}
                <div>
                  <label className="block text-sm text-dark-300 mb-1">Bucket Name</label>
                  <input
                    type="text"
                    value={config.object_store?.bucket_name || ''}
                    onChange={e => updateNestedConfig('object_store', 'bucket_name', e.target.value)}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  />
                </div>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">File Path / Key</label>
                  <input
                    type="text"
                    value={config.object_store?.object_path || ''}
                    onChange={e => updateNestedConfig('object_store', 'object_path', e.target.value)}
                    placeholder="outputs/{{workflow_name}}/{{timestamp}}.json"
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  />
                  <p className="text-xs text-dark-500 mt-1">
                    Variables: {'{{workflow_name}}'}, {'{{timestamp}}'}, {'{{execution_id}}'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm text-dark-300 mb-1">File Format</label>
                  <select
                    value={config.object_store?.file_format || 'json'}
                    onChange={e => updateNestedConfig('object_store', 'file_format', e.target.value)}
                    className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red"
                  >
                    <option value="json">JSON</option>
                    <option value="txt">TXT</option>
                    <option value="csv">CSV</option>
                    <option value="pdf">PDF</option>
                  </select>
                </div>
              </>
            )}

            {config.output_type === 'chat' && (
              <p className="text-xs text-dark-400 bg-dark-900 rounded-md p-2">
                Output will be routed to the Chat block for conversational display.
              </p>
            )}
          </>
        )}

        {/* Chat config */}
        {nodeType === 'chat' && (
          <p className="text-xs text-dark-400 bg-dark-900 rounded-md p-2">
            Use the Chat block at the start to supply a message, or at the end to collect a response. Graphs must remain acyclic. Only one Chat block is allowed per workflow.
          </p>
        )}

        <button
          onClick={handleSave}
          disabled={readingFile}
          className="w-full px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm font-medium transition-colors"
        >
          Save Configuration
        </button>
      </div>
    </div>
  );
};

export default NodeConfigPanel;
