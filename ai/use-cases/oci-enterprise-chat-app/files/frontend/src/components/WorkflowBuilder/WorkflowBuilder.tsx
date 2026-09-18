import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  useReactFlow,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Save,
  Play,
  Trash2,
  ArrowLeft,
  Bot,
  Database,
  ArrowDownToLine,
  ArrowUpFromLine,
  MessageSquare,
  FolderOpen,
  Plus,
  X,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  History,
  AlertTriangle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { Workflow, WorkflowExecution } from '../../types';
import { useWorkflowStore } from '../../stores/workflowStore';
import AgentNode from './nodes/AgentNode';
import DataSourceNode from './nodes/DataSourceNode';
import InputNode from './nodes/InputNode';
import OutputNode from './nodes/OutputNode';
import ChatNode from './nodes/ChatNode';
import NodeConfigPanel from './NodeConfigPanel';
import ScheduleModal from './ScheduleModal';

const nodeTypes = {
  agent: AgentNode,
  data_source: DataSourceNode,
  input: InputNode,
  output: OutputNode,
  chat: ChatNode,
};

const paletteItems = [
  { type: 'input', label: 'Input', icon: ArrowDownToLine, color: 'text-blue-400' },
  { type: 'agent', label: 'Agent', icon: Bot, color: 'text-purple-400' },
  { type: 'data_source', label: 'Data Source', icon: Database, color: 'text-emerald-400' },
  { type: 'output', label: 'Output', icon: ArrowUpFromLine, color: 'text-amber-400' },
  { type: 'chat', label: 'Chat', icon: MessageSquare, color: 'text-green-400' },
];

/** Determine edge style based on source/target node types. */
const getEdgeStyle = (sourceType: string | undefined, targetType: string | undefined) => {
  // RAG/Data connections: blue dashed
  if (sourceType === 'data_source' || (sourceType === 'input')) {
    return {
      style: { stroke: '#60a5fa', strokeWidth: 2, strokeDasharray: '6 3' },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#60a5fa' },
    };
  }
  // Agent-to-agent chaining: solid orange
  if (sourceType === 'agent' && targetType === 'agent') {
    return {
      style: { stroke: '#fb923c', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#fb923c' },
    };
  }
  // Chat connections: green
  if (sourceType === 'chat' || targetType === 'chat') {
    return {
      style: { stroke: '#4ade80', strokeWidth: 2 },
      label: '',
      markerEnd: { type: MarkerType.ArrowClosed, color: '#4ade80' },
    };
  }
  // Default: gray
  return {
    style: { stroke: '#6b7280', strokeWidth: 2 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#6b7280' },
  };
};

const WorkflowCanvas: React.FC = () => {
  const navigate = useNavigate();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const { screenToFlowPosition } = useReactFlow();

  const {
    nodes, edges, onNodesChange, onEdgesChange, onConnect,
    addNode, selectNode, selectedNodeId,
    workflowId, workflowName, workflowDescription,
    setWorkflowMeta, setNodes, setEdges, reset,
    hasChatNode, canAddChatNode, validateConnection,
  } = useWorkflowStore();

  const [showWorkflowList, setShowWorkflowList] = useState(false);
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [saving, setSaving] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<WorkflowExecution | null>(null);
  const [executeInput, setExecuteInput] = useState('');
  const [showExecuteModal, setShowExecuteModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [history, setHistory] = useState<WorkflowExecution[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const errorText = (err: any) => {
    const detail = err?.response?.data?.detail;
    return typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((item: any) => item.msg).join('; ') : err.message || 'Request failed';
  };

  const loadHistory = useCallback(async () => {
    if (!workflowId) return;
    try { setHistory(await api.listWorkflowExecutions(workflowId)); }
    catch (err) { setError(errorText(err)); }
  }, [workflowId]);

  useEffect(() => {
    if (!showHistory) return;
    loadHistory();
    const timer = setInterval(loadHistory, 3000);
    return () => clearInterval(timer);
  }, [showHistory, loadHistory]);

  const loadWorkflows = useCallback(async () => {
    try {
      const data = await api.listWorkflows();
      setWorkflows(data);
    } catch (err) { setError(errorText(err)); }
  }, []);

  useEffect(() => { loadWorkflows(); }, [loadWorkflows]);

  // Clear connection error after 3 seconds
  useEffect(() => {
    if (connectionError) {
      const timer = setTimeout(() => setConnectionError(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [connectionError]);

  const handleNodeClick = useCallback((_: any, node: any) => {
    selectNode(node.id);
  }, [selectNode]);

  const handlePaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    const type = event.dataTransfer.getData('application/reactflow');
    if (!type) return;

    // Enforce chat singleton at drop time
    if (type === 'chat' && !canAddChatNode()) {
      setConnectionError('Only one Chat block is allowed per workflow.');
      return;
    }

    const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
    addNode(type, position);
  }, [screenToFlowPosition, addNode, canAddChatNode]);

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  // Apply edge styles based on node types
  const styledEdges: Edge[] = useMemo(() => {
    const nodeMap = new Map(nodes.map(node => [node.id, node]));
    return edges.map(edge => ({ ...edge,
      ...getEdgeStyle(nodeMap.get(edge.source)?.type, nodeMap.get(edge.target)?.type),
    }));
  }, [nodes, edges]);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    setNotice(null);
    try {
      if (!workflowName.trim()) throw new Error('Enter a workflow name');
      const workflowNodes = nodes.map(n => ({
        id: n.id,
        type: n.type || 'agent',
        label: (n.data.label as string) || '',
        position: n.position,
        config: (n.data.config as Record<string, any>) || {},
      }));
      const workflowEdges = edges.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target,
        source_handle: e.sourceHandle || undefined,
        target_handle: e.targetHandle || undefined,
      }));

      let savedId = workflowId;
      if (workflowId) {
        await api.updateWorkflow(workflowId, {
          name: workflowName,
          description: workflowDescription,
          nodes: workflowNodes,
          edges: workflowEdges,
        });
      } else {
        const wf = await api.createWorkflow({
          name: workflowName,
          description: workflowDescription,
          nodes: workflowNodes,
          edges: workflowEdges,
        });
        savedId = wf.id;
        setWorkflowMeta(wf.id, wf.name, wf.description);
      }
      await loadWorkflows();
      setNotice('Workflow saved');
      return savedId;
    } catch (err) {
      setError(errorText(err));
      return null;
    } finally { setSaving(false); }
  };

  const handleLoadWorkflow = async (wf: Workflow) => {
    setWorkflowMeta(wf.id, wf.name, wf.description);
    selectNode(null);
    setExecutionResult(null);
    setError(null);
    const loadedNodes = wf.nodes.map((n: any) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: { label: n.label, nodeType: n.type, config: n.config || {} },
    }));
    const loadedEdges = wf.edges.map((e: any) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: e.source_handle,
      targetHandle: e.target_handle,
    }));
    setNodes(loadedNodes);
    setEdges(loadedEdges);
    setShowWorkflowList(false);
  };

  const handleDeleteWorkflow = async (id: string) => {
    try {
      await api.deleteWorkflow(id);
      if (workflowId === id) reset();
      await loadWorkflows();
    } catch (err) { setError(errorText(err)); }
  };

  const handleExecute = async () => {
    if (await handleSave()) setShowExecuteModal(true);
  };

  const handleRunExecution = async () => {
    setExecuting(true);
    setExecutionResult(null);
    try {
      const id = workflowId || useWorkflowStore.getState().workflowId;
      if (!id) throw new Error('Save the workflow before running it');
      const result = await api.executeWorkflow(id, { message: executeInput });
      setExecutionResult(result);
    } catch (err) { setError(errorText(err)); }
    finally { setExecuting(false); }
  };

  const handleNew = () => {
    reset();
    setExecutionResult(null);
    setError(null);
    setNotice(null);
    setHistory([]);
    setShowHistory(false);
  };

  const handleSchedule = async () => {
    if (await handleSave()) setShowScheduleModal(true);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Left Palette */}
      <div className="w-56 bg-dark-800 border-r border-dark-700 flex flex-col">
        <div className="p-4 border-b border-dark-700">
          <h3 className="text-sm font-semibold text-dark-300 uppercase tracking-wider">Node Palette</h3>
        </div>
        <div className="p-3 space-y-2">
          {paletteItems.map(item => {
            const Icon = item.icon;
            const isChatDisabled = item.type === 'chat' && !canAddChatNode();
            return (
              <div
                key={item.type}
                role="button"
                tabIndex={isChatDisabled ? -1 : 0}
                aria-label={`Add ${item.label} node`}
                onClick={() => !isChatDisabled && addNode(item.type, { x: 80 + (nodes.length % 2) * 240, y: 80 + Math.floor(nodes.length / 2) * 160 })}
                onKeyDown={event => { if (event.key === 'Enter' && !isChatDisabled) addNode(item.type, { x: 100, y: 100 }); }}
                draggable={!isChatDisabled}
                onDragStart={e => !isChatDisabled && onDragStart(e, item.type)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-colors ${
                  isChatDisabled
                    ? 'bg-dark-800 border-dark-700 cursor-not-allowed opacity-50'
                    : 'bg-dark-700 hover:bg-dark-600 cursor-grab active:cursor-grabbing border-dark-600'
                }`}
                title={isChatDisabled ? 'Only one Chat block is allowed per workflow.' : undefined}
              >
                <Icon className={`h-5 w-5 ${item.color}`} />
                <span className="text-sm text-white">{item.label}</span>
                {isChatDisabled && (
                  <AlertTriangle className="h-3.5 w-3.5 text-dark-500 ml-auto" />
                )}
              </div>
            );
          })}
        </div>

        <div className="mt-auto p-3 border-t border-dark-700 space-y-2">
          <button onClick={() => setShowWorkflowList(true)} className="flex items-center gap-2 w-full px-3 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
            <FolderOpen className="h-4 w-4" /> My Workflows
          </button>
          <button onClick={handleNew} className="flex items-center gap-2 w-full px-3 py-2 bg-dark-700 hover:bg-dark-600 text-dark-200 rounded-md text-sm transition-colors">
            <Plus className="h-4 w-4" /> New Workflow
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Top Bar */}
        <div className="flex flex-wrap gap-2 items-center justify-between px-4 py-3 bg-dark-800 border-b border-dark-700">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="p-1.5 text-dark-400 hover:text-white transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
            <input
              type="text"
              value={workflowName}
              onChange={e => setWorkflowMeta(workflowId, e.target.value, workflowDescription)}
              className="bg-transparent border-none text-white text-lg font-medium focus:outline-none"
              placeholder="Workflow Name"
            />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setShowHistory(true)} disabled={!workflowId} className="flex items-center gap-2 px-3 py-2 bg-dark-700 text-white rounded-md text-sm disabled:opacity-50"><History className="h-4 w-4" /> Runs</button>
            <button onClick={() => navigate('/batch')} className="px-3 py-2 bg-dark-700 text-white rounded-md text-sm">Batch</button>
            <button onClick={handleSchedule} disabled={nodes.length === 0 || saving || executing} className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-md text-sm transition-colors disabled:opacity-50">
              <Clock className="h-4 w-4" /> Schedule
            </button>
            <button onClick={handleSave} disabled={saving} className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 text-white rounded-md text-sm transition-colors disabled:opacity-50">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              Save
            </button>
            <button onClick={handleExecute} disabled={nodes.length === 0 || saving || executing} className="flex items-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm transition-colors disabled:opacity-50">
              <Play className="h-4 w-4" /> Execute
            </button>
          </div>
        </div>

        {(error || notice) && <div role={error ? 'alert' : 'status'} className={`px-4 py-2 text-sm ${error ? 'text-red-300 bg-red-500/10' : 'text-green-300 bg-green-500/10'}`}>{error || notice}</div>}

        {/* Connection error toast */}
        {connectionError && (
          <div className="absolute top-20 left-1/2 -translate-x-1/2 z-50 px-4 py-2 bg-red-500/20 border border-red-500/40 rounded-lg text-red-300 text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            {connectionError}
          </div>
        )}

        {/* React Flow Canvas */}
        <div className="flex-1 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={styledEdges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={connection => {
              const result = validateConnection(connection);
              if (!result.valid) setConnectionError(result.message || 'Invalid connection');
              else onConnect(connection);
            }}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            onDrop={onDrop}
            onDragOver={onDragOver}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ maxZoom: 1 }}
            snapToGrid
            snapGrid={[15, 15]}
            className="bg-dark-900"
          >
            <Controls className="!bg-dark-800 !border-dark-700 !rounded-lg [&>button]:!bg-dark-700 [&>button]:!border-dark-600 [&>button]:!text-white [&>button:hover]:!bg-dark-600" />
            <MiniMap
              className="!bg-dark-800 !border-dark-700 !rounded-lg"
              nodeColor={(node) => {
                switch (node.type) {
                  case 'chat': return '#4ade80';
                  case 'agent': return '#a78bfa';
                  case 'input': return '#60a5fa';
                  case 'data_source': return '#34d399';
                  case 'output': return '#fbbf24';
                  default: return '#C74634';
                }
              }}
              maskColor="rgba(0,0,0,0.6)"
            />
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#374151" />
          </ReactFlow>
        </div>
      </div>

      {/* Right Config Panel */}
      {selectedNodeId && <NodeConfigPanel />}

      {/* Workflow List Modal */}
      {showWorkflowList && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 w-[500px] max-h-[600px] flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-dark-700">
              <h3 className="text-white font-medium">My Workflows</h3>
              <button onClick={() => setShowWorkflowList(false)} className="text-dark-400 hover:text-white"><X className="h-5 w-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {workflows.length === 0 ? (
                <p className="text-center text-dark-400 py-8">No saved workflows</p>
              ) : (
                workflows.map(wf => (
                  <div key={wf.id} className="flex items-center justify-between p-3 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors">
                    <button onClick={() => handleLoadWorkflow(wf)} className="flex-1 text-left">
                      <div className="flex items-center gap-2">
                        <p className="text-white font-medium">{wf.name}</p>
                        {wf.schedule && wf.schedule.is_active && (
                          <span title="Scheduled"><Clock className="h-3.5 w-3.5 text-green-400" /></span>
                        )}
                      </div>
                      <p className="text-xs text-dark-400">{wf.nodes.length} nodes &middot; {new Date(wf.updated_at).toLocaleDateString()}</p>
                    </button>
                    <button onClick={() => handleDeleteWorkflow(wf.id)} className="p-1.5 text-dark-400 hover:text-red-400 transition-colors">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Execute Modal */}
      {showExecuteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 w-[500px]">
            <div className="flex items-center justify-between p-4 border-b border-dark-700">
              <h3 className="text-white font-medium">Execute Workflow · Normal processing</h3>
              <button onClick={() => { setShowExecuteModal(false); setExecutionResult(null); }} className="text-dark-400 hover:text-white"><X className="h-5 w-5" /></button>
            </div>
            <div className="p-4 space-y-4">
              {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
              <div>
                <label className="block text-sm text-dark-300 mb-1">Input Message (optional for storage sources)</label>
                <textarea
                  value={executeInput}
                  onChange={e => setExecuteInput(e.target.value)}
                  rows={3}
                  placeholder="Enter your input for the workflow..."
                  className="w-full bg-dark-900 border border-dark-600 rounded-md px-3 py-2 text-white text-sm focus:outline-none focus:border-oracle-red resize-none"
                />
              </div>
              <button onClick={handleRunExecution} disabled={executing} className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-oracle-red hover:bg-oracle-red/90 text-white rounded-md text-sm transition-colors disabled:opacity-50">
                {executing ? <><Loader2 className="h-4 w-4 animate-spin" /> Running...</> : <><Play className="h-4 w-4" /> Run</>}
              </button>

              {executionResult && (
                <div className={`p-3 rounded-lg border ${executionResult.status === 'completed' ? 'border-green-500/30 bg-green-500/10' : 'border-red-500/30 bg-red-500/10'}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {executionResult.status === 'completed' ? <CheckCircle className="h-4 w-4 text-green-400" /> : <XCircle className="h-4 w-4 text-red-400" />}
                    <span className={`text-sm font-medium ${executionResult.status === 'completed' ? 'text-green-400' : 'text-red-400'}`}>
                      {executionResult.status === 'completed' ? 'Completed' : 'Failed'}
                    </span>
                  </div>
                  {executionResult.output_data && (
                    <pre className="text-xs text-dark-300 overflow-auto max-h-48">
                      {JSON.stringify(executionResult.output_data, null, 2)}
                    </pre>
                  )}
                  {executionResult.error_message && (
                    <p className="text-sm text-red-400">{executionResult.error_message}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {showHistory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-dark-800 rounded-lg border border-dark-700 w-[700px] max-h-[80vh] overflow-auto p-4 space-y-3">
            <div className="flex justify-between"><h3 className="text-white font-medium">Workflow Runs</h3><button aria-label="Close runs" onClick={() => setShowHistory(false)}><X className="h-5 w-5 text-white" /></button></div>
            {history.length === 0 && <p className="text-dark-300">No runs yet</p>}
            {history.map(run => <details key={run.id} className="p-3 bg-dark-900 rounded text-dark-200">
              <summary className="cursor-pointer">{run.status} · {run.triggered_by && run.triggered_by !== 'user' ? 'Scheduled' : 'Manual'} · {new Date(run.created_at).toLocaleString()}</summary>
              {run.error_message && <p className="text-red-300 mt-2">{run.error_message}</p>}
              <pre className="text-xs overflow-auto mt-2">{JSON.stringify({ output: run.output_data, nodes: run.node_results }, null, 2)}</pre>
            </details>)}
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && workflowId && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => { setShowScheduleModal(false); loadWorkflows(); }}
          workflowId={workflowId}
          workflowName={workflowName}
          hasChatNode={hasChatNode()}
        />
      )}
    </div>
  );
};

const WorkflowBuilder: React.FC = () => {
  return (
    <ReactFlowProvider>
      <WorkflowCanvas />
    </ReactFlowProvider>
  );
};

export default WorkflowBuilder;
