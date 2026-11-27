import { create } from 'zustand';
import {
  Node,
  Edge,
  OnNodesChange,
  OnEdgesChange,
  OnConnect,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
  Connection,
} from '@xyflow/react';

export interface WorkflowState {
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  workflowId: string | null;
  workflowName: string;
  workflowDescription: string;
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: OnConnect;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (type: string, position: { x: number; y: number }) => void;
  updateNodeData: (nodeId: string, data: Record<string, any>) => void;
  selectNode: (nodeId: string | null) => void;
  setWorkflowMeta: (id: string | null, name: string, description: string) => void;
  hasChatNode: () => boolean;
  canAddChatNode: () => boolean;
  validateConnection: (connection: Connection) => { valid: boolean; message?: string };
  reset: () => void;
}

let nodeIdCounter = 0;

const defaultLabels: Record<string, string> = {
  agent: 'Agent',
  data_source: 'Data Source',
  input: 'Input',
  output: 'Output',
  chat: 'Chat',
};

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  workflowId: null,
  workflowName: 'Untitled Workflow',
  workflowDescription: '',

  onNodesChange: (changes) => {
    const nodes = applyNodeChanges(changes, get().nodes);
    const ids = new Set(nodes.map(node => node.id));
    set({ nodes, edges: get().edges.filter(edge => ids.has(edge.source) && ids.has(edge.target)),
      selectedNodeId: ids.has(get().selectedNodeId || '') ? get().selectedNodeId : null });
  },

  onEdgesChange: (changes) => {
    set({ edges: applyEdgeChanges(changes, get().edges) });
  },

  onConnect: (connection: Connection) => {
    const validation = get().validateConnection(connection);
    if (!validation.valid) {
      return;
    }
    set({ edges: addEdge({ ...connection, id: `e-${Date.now()}` }, get().edges) });
  },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (type, position) => {
    // Enforce chat singleton
    if (type === 'chat' && get().hasChatNode()) {
      return;
    }
    const id = `node-${Date.now()}-${++nodeIdCounter}`;
    const newNode: Node = {
      id,
      type,
      position,
      data: {
        label: defaultLabels[type] || type,
        nodeType: type,
        config: {},
      },
    };
    set({ nodes: [...get().nodes, newNode] });
  },

  updateNodeData: (nodeId, data) => {
    set({
      nodes: get().nodes.map(n =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
      ),
    });
  },

  selectNode: (nodeId) => set({ selectedNodeId: nodeId }),

  setWorkflowMeta: (id, name, description) => set({
    workflowId: id,
    workflowName: name,
    workflowDescription: description,
  }),

  hasChatNode: () => {
    return get().nodes.some(n => n.type === 'chat');
  },

  canAddChatNode: () => {
    return !get().hasChatNode();
  },

  validateConnection: (connection: Connection) => {
    const { nodes } = get();
    const sourceNode = nodes.find(n => n.id === connection.source);
    const targetNode = nodes.find(n => n.id === connection.target);
    if (!sourceNode || !targetNode) return { valid: false, message: 'Invalid nodes' };

    const allowed: Record<string, string[]> = {
      input: ['agent', 'data_source', 'output'],
      agent: ['agent', 'data_source', 'output', 'chat'],
      data_source: ['agent', 'output'], output: ['chat'], chat: ['agent'],
    };
    if (connection.source === connection.target) return { valid: false, message: 'A node cannot connect to itself' };
    if (!(allowed[sourceNode.type || ''] || []).includes(targetNode.type || '')) {
      return { valid: false, message: 'This connection is not supported between these node types' };
    }
    const edges = get().edges;
    if (edges.some(e => e.source === connection.source && e.target === connection.target)) {
      return { valid: false, message: 'These nodes are already connected' };
    }
    const pending = [connection.target];
    const visited = new Set<string>();
    while (pending.length) {
      const id = pending.pop()!;
      if (id === connection.source) return { valid: false, message: 'This connection would create a cycle' };
      if (visited.has(id)) continue;
      visited.add(id);
      edges.filter(e => e.source === id).forEach(e => pending.push(e.target));
    }

    return { valid: true };
  },

  reset: () => set({
    nodes: [],
    edges: [],
    selectedNodeId: null,
    workflowId: null,
    workflowName: 'Untitled Workflow',
    workflowDescription: '',
  }),
}));
