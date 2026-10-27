import { useRef, useEffect, useState, useCallback, type ReactNode } from 'react';
import type { WorkflowStep } from './WorkflowProgress';

// ── Agent Definitions ──

interface AgentInfo {
  id: string;
  name: string;
  description: string;
  tools: string[];
  icon: ReactNode;
  stepMapping: string; // maps to WorkflowStep.step
}

const AGENTS: AgentInfo[] = [
  {
    id: 'web_source',
    name: 'Web Source Agent',
    description:
      'Generates smart, targeted search queries using OCI GenAI to discover authentic customer reviews across review platforms, forums, and news sites.',
    tools: ['OCI GenAI', 'Cohere Command A', 'Query Generation'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    stepMapping: 'Web Scout',
  },
  {
    id: 'web_search',
    name: 'Web Search Agent',
    description:
      'Executes DuckDuckGo searches using generated queries, scrapes top results, filters by domain authority, and extracts customer review content.',
    tools: ['DuckDuckGo', 'httpx', 'BeautifulSoup', 'Web Scraper'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    stepMapping: 'Web Scout',
  },
  {
    id: 'ingestion',
    name: 'Data Ingestion',
    description:
      'Stores scraped reviews into Oracle Autonomous Database with deduplication by URL hash. Persists source, content, brand, and metadata.',
    tools: ['Oracle ADB', 'oracledb', 'SQL INSERT'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
    stepMapping: 'Ingestion',
  },
  {
    id: 'sentiment',
    name: 'Sentiment Agent',
    description:
      'Performs IN-DATABASE sentiment analysis using DBMS_CLOUD_AI.GENERATE. AI inference runs directly inside Oracle ADB — no data movement required.',
    tools: ['DBMS_CLOUD_AI', 'OCI GenAI (In-DB)', 'Select AI Profile'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    stepMapping: 'Sentiment Analysis',
  },
  {
    id: 'analytics',
    name: 'Analytics Agent',
    description:
      'Computes sentiment distribution, trends, top aspects, source breakdown, and emotion analysis. Detects alerts for unusual sentiment patterns.',
    tools: ['Oracle SQL', 'Select AI NL2SQL', 'Aggregation'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    stepMapping: 'Analytics',
  },
  {
    id: 'action',
    name: 'Action Agent',
    description:
      'Generates prioritized marketing recommendations using OCI GenAI based on sentiment summary, detected alerts, and web context.',
    tools: ['OCI GenAI', 'Cohere Command A', 'Strategy Engine'],
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    stepMapping: 'Actions',
  },
];

// ── Types ──

type AgentStatus = 'idle' | 'running' | 'complete' | 'error';

interface Connection {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

// ── Component ──

interface AgentFlowDiagramProps {
  workflowSteps: WorkflowStep[];
  isAnalyzing: boolean;
}

export default function AgentFlowDiagram({ workflowSteps }: AgentFlowDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [connections, setConnections] = useState<Connection[]>([]);

  const getAgentStatus = useCallback(
    (agent: AgentInfo): AgentStatus => {
      const step = workflowSteps.find((s) => s.step === agent.stepMapping);
      if (!step) return 'idle';
      if (step.status === 'running') return 'running';
      if (step.status === 'complete') return 'complete';
      if (step.status === 'error') return 'error';
      return 'idle';
    },
    [workflowSteps]
  );

  const getConnectionStatus = useCallback(
    (index: number): 'idle' | 'active' | 'complete' => {
      const fromAgent = AGENTS[index];
      const toAgent = AGENTS[index + 1];
      const fromStatus = getAgentStatus(fromAgent);
      const toStatus = getAgentStatus(toAgent);

      if (fromStatus === 'complete' && (toStatus === 'complete' || toStatus === 'running')) {
        return toStatus === 'running' ? 'active' : 'complete';
      }
      if (fromStatus === 'running') return 'active';
      return 'idle';
    },
    [getAgentStatus]
  );

  // Compute SVG connection coordinates
  useEffect(() => {
    const updateConnections = () => {
      if (!containerRef.current) return;
      const nodes = containerRef.current.querySelectorAll('[data-agent-node]');
      if (nodes.length < 2) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newConns: Connection[] = [];

      for (let i = 0; i < nodes.length - 1; i++) {
        const from = nodes[i].getBoundingClientRect();
        const to = nodes[i + 1].getBoundingClientRect();

        // Determine if nodes are on the same row
        const sameRow = Math.abs(from.top - to.top) < from.height * 0.5;

        if (sameRow) {
          // Horizontal: right edge of "from" → left edge of "to"
          newConns.push({
            x1: from.right - containerRect.left,
            y1: from.top + from.height / 2 - containerRect.top,
            x2: to.left - containerRect.left,
            y2: to.top + to.height / 2 - containerRect.top,
          });
        } else {
          // Different row: bottom center of "from" → top center of "to"
          newConns.push({
            x1: from.left + from.width / 2 - containerRect.left,
            y1: from.bottom - containerRect.top,
            x2: to.left + to.width / 2 - containerRect.left,
            y2: to.top - containerRect.top,
          });
        }
      }

      setConnections(newConns);
    };

    updateConnections();
    window.addEventListener('resize', updateConnections);

    // Also recompute after a short delay (for animation)
    const timer = setTimeout(updateConnections, 500);

    return () => {
      window.removeEventListener('resize', updateConnections);
      clearTimeout(timer);
    };
  }, [workflowSteps]);

  return (
    <div ref={containerRef} className="relative">
      {/* SVG Connection Lines */}
      <svg
        className="absolute inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 0 }}
      >
        {connections.map((conn, i) => {
          const status = getConnectionStatus(i);
          const midX = (conn.x1 + conn.x2) / 2;
          const midY = (conn.y1 + conn.y2) / 2;

          // Determine path: if vertical distance is large, use S-curve
          const isVertical = Math.abs(conn.y2 - conn.y1) > 50;
          const path = isVertical
            ? `M ${conn.x1},${conn.y1} C ${conn.x1},${midY} ${conn.x2},${midY} ${conn.x2},${conn.y2}`
            : `M ${conn.x1},${conn.y1} C ${midX},${conn.y1} ${midX},${conn.y2} ${conn.x2},${conn.y2}`;

          return (
            <g key={i}>
              <path
                d={path}
                className={`flow-line ${status === 'active' ? 'active' : status === 'complete' ? 'complete' : ''}`}
              />
              {status === 'active' && (
                <>
                  <circle r="4" className="flow-particle">
                    <animateMotion dur="1.5s" repeatCount="indefinite" path={path} />
                  </circle>
                  <circle r="4" className="flow-particle" style={{ opacity: 0.5 }}>
                    <animateMotion dur="1.5s" repeatCount="indefinite" path={path} begin="0.75s" />
                  </circle>
                </>
              )}
            </g>
          );
        })}
      </svg>

      {/* Agent Cards Grid */}
      <div className="relative z-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10">
        {AGENTS.map((agent, index) => {
          const status = getAgentStatus(agent);
          return (
            <div
              key={agent.id}
              data-agent-node
              className={`glass-card p-6 transition-all duration-500 ${
                status === 'running'
                  ? 'ring-2 ring-accent/40 shadow-lg shadow-accent/10'
                  : status === 'complete'
                  ? 'ring-2 ring-green-400/40 shadow-lg shadow-green-500/10'
                  : status === 'error'
                  ? 'ring-2 ring-red-400/40 shadow-lg shadow-red-500/10'
                  : 'hover:ring-1 hover:ring-gray-300'
              }`}
              style={{
                animation: `slide-in-up 0.5s ease-out ${index * 100}ms both`,
              }}
            >
              {/* Step number + Status */}
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                  Step {index + 1}
                </span>
                <span
                  className={`px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider ${
                    status === 'running'
                      ? 'bg-accent/10 text-accent'
                      : status === 'complete'
                      ? 'bg-green-50 text-green-600'
                      : status === 'error'
                      ? 'bg-red-50 text-red-600'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {status === 'running'
                    ? 'Running'
                    : status === 'complete'
                    ? 'Done'
                    : status === 'error'
                    ? 'Failed'
                    : 'Idle'}
                </span>
              </div>

              {/* Icon + Name */}
              <div className="flex items-center gap-3 mb-3">
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-500 ${
                    status === 'running'
                      ? 'bg-accent/10 text-accent animate-pulse-ring'
                      : status === 'complete'
                      ? 'bg-green-50 text-green-600'
                      : status === 'error'
                      ? 'bg-red-50 text-red-600'
                      : 'bg-gray-100 text-gray-500'
                  }`}
                >
                  {agent.icon}
                </div>
                <h3 className="text-sm font-bold text-gray-900">{agent.name}</h3>
              </div>

              {/* Description */}
              <p className="text-xs text-gray-500 leading-relaxed mb-4">
                {agent.description}
              </p>

              {/* Running message */}
              {status === 'running' && (
                <div className="mb-4 px-3 py-2 rounded-lg bg-accent/5 border border-accent/15">
                  <div className="flex items-center gap-2">
                    <svg className="w-3 h-3 text-accent animate-spin-slow" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                    <span className="text-[11px] text-accent">
                      {workflowSteps.find((s) => s.step === agent.stepMapping)?.message || 'Processing...'}
                    </span>
                  </div>
                </div>
              )}

              {/* Tools */}
              <div className="flex flex-wrap gap-1.5">
                {agent.tools.map((tool) => (
                  <span
                    key={tool}
                    className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-gray-100 text-gray-500 border border-gray-200"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-8 flex items-center justify-center gap-6">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-300" />
          <span className="text-[10px] text-gray-400 uppercase tracking-wider">Idle</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-accent animate-pulse" />
          <span className="text-[10px] text-gray-400 uppercase tracking-wider">Running</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-[10px] text-gray-400 uppercase tracking-wider">Complete</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span className="text-[10px] text-gray-400 uppercase tracking-wider">Error</span>
        </div>
      </div>
    </div>
  );
}
