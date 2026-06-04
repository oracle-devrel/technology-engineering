"use client";

import { Box, Typography } from "@mui/material";
import { useEffect, useState, useMemo, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ReactFlow,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  BaseEdge,
  getBezierPath,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Wrench, Sparkles, Database, Globe, FileText, Code, Search, Mail } from "lucide-react";
import { MCPService } from "../../services/mcpService";

// Icon mapping for different tool types
const getToolIcon = (serverId, serverName) => {
  const name = (serverName || serverId || "").toLowerCase();
  if (name.includes("database") || name.includes("sql") || name.includes("db")) return Database;
  if (name.includes("web") || name.includes("fetch") || name.includes("http")) return Globe;
  if (name.includes("file") || name.includes("doc")) return FileText;
  if (name.includes("code") || name.includes("script")) return Code;
  if (name.includes("search")) return Search;
  if (name.includes("mail") || name.includes("email")) return Mail;
  return Wrench;
};

// Oracle Redwood color palette
const REDWOOD_PRIMARY = "#161513"; // Oracle Black
const REDWOOD_RED = "#C74634"; // Oracle Red
const REDWOOD_ACCENT = "#8B5D33"; // Warm brown

// Color palette for tool nodes - filled with low opacity, border at full opacity
const TOOL_COLORS = [
  { border: "#C74634", fill: "rgba(199, 70, 52, 0.08)", icon: "#C74634" }, // Oracle Red
  { border: "#8B5D33", fill: "rgba(139, 93, 51, 0.08)", icon: "#8B5D33" }, // Warm brown
  { border: "#5C5650", fill: "rgba(92, 86, 80, 0.08)", icon: "#5C5650" }, // Dark gray-brown
  { border: "#6B8E23", fill: "rgba(107, 142, 35, 0.08)", icon: "#6B8E23" }, // Olive green
  { border: "#4682B4", fill: "rgba(70, 130, 180, 0.08)", icon: "#4682B4" }, // Steel blue
  { border: "#A0522D", fill: "rgba(160, 82, 45, 0.08)", icon: "#A0522D" }, // Sienna
];

// Central model node - simple and clean design
function ModelNode({ data }) {
  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{
        duration: 0.6,
        delay: 0.1,
        ease: [0.23, 1, 0.32, 1]
      }}
    >
      {/* Handles on all sides */}
      <Handle type="source" position={Position.Top} id="top" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="source" position={Position.Left} id="left" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="source" position={Position.Right} id="right" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />

      {/* Main square with rounded corners - red theme */}
      <Box
        sx={{
          width: 100,
          height: 100,
          borderRadius: "16px",
          backgroundColor: "rgba(199, 70, 52, 0.08)",
          border: `2px solid ${REDWOOD_RED}`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Sparkles size={28} strokeWidth={1.5} style={{ color: REDWOOD_RED }} />
        <Typography
          sx={{
            fontSize: "0.65rem",
            color: REDWOOD_RED,
            fontWeight: 600,
            mt: 0.5,
            textAlign: "center",
            maxWidth: 85,
            lineHeight: 1.2,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {data.label}
        </Typography>
      </Box>
    </motion.div>
  );
}

// Tool node with colorful styling - filled with low opacity, border at full opacity
function ToolNode({ data }) {
  const Icon = getToolIcon(data.serverId, data.label);
  const color = TOOL_COLORS[data.colorIndex % TOOL_COLORS.length];

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0, y: 20 }}
      animate={{ scale: 1, opacity: 1, y: 0 }}
      exit={{ scale: 0, opacity: 0, y: 20 }}
      transition={{
        duration: 0.7,
        delay: data.delay,
        ease: [0.23, 1, 0.32, 1]
      }}
      whileHover={{ scale: 1.06, transition: { duration: 0.2 } }}
      style={{ cursor: "pointer" }}
    >
      {/* Handles on all sides */}
      <Handle type="target" position={Position.Top} id="top" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="target" position={Position.Bottom} id="bottom" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="target" position={Position.Left} id="left" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />
      <Handle type="target" position={Position.Right} id="right" style={{ background: "transparent", border: "none", width: 1, height: 1 }} />

      {/* Main circle - filled with low opacity, border at full opacity */}
      <Box
        sx={{
          width: 70,
          height: 70,
          borderRadius: "50%",
          backgroundColor: color.fill,
          border: `2px solid ${color.border}`,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon size={20} strokeWidth={1.5} style={{ color: color.icon }} />
        <Typography
          sx={{
            fontSize: "0.5rem",
            color: color.icon,
            fontWeight: 600,
            mt: 0.3,
            textAlign: "center",
            maxWidth: 60,
            lineHeight: 1.1,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {data.label}
        </Typography>
      </Box>
    </motion.div>
  );
}

// Custom animated edge with dashed line
function AnimatedEdge({ id, sourceX, sourceY, targetX, targetY, sourcePosition, targetPosition, data }) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    curvature: 0.25,
  });

  const color = data?.color || "#D1D5DB";
  const delay = data?.delay || 0;

  return (
    <>
      {/* Main dashed path with fade-in animation */}
      <path
        d={edgePath}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeDasharray="6 4"
        opacity={0}
      >
        <animate
          attributeName="opacity"
          from={0}
          to={1}
          dur="0.6s"
          begin={`${delay}s`}
          fill="freeze"
          calcMode="spline"
          keySplines="0.23 1 0.32 1"
        />
      </path>
    </>
  );
}

const nodeTypes = { model: ModelNode, tool: ToolNode };
const edgeTypes = { animated: AnimatedEdge };

// Helper to get the best handle based on angle
function getHandles(angle) {
  const a = ((angle % 360) + 360) % 360;
  if (a >= 315 || a < 45) return { source: "right", target: "left" };
  if (a >= 45 && a < 135) return { source: "bottom", target: "top" };
  if (a >= 135 && a < 225) return { source: "left", target: "right" };
  return { source: "top", target: "bottom" };
}

export default function ArchitectureDiagram({ selectedModel }) {
  const [enabledTools, setEnabledTools] = useState([]);
  const [servers, setServers] = useState([]);
  const [sessionDisabledServers, setSessionDisabledServers] = useState(new Set());
  const hasFittedRef = useRef(false);
  const reactFlowInstance = useRef(null);

  const handleInit = useCallback((instance) => {
    reactFlowInstance.current = instance;
    if (!hasFittedRef.current) {
      instance.fitView({ padding: 0.4, maxZoom: 1 });
      hasFittedRef.current = true;
    }
  }, []);

  useEffect(() => {
    const refresh = () => {
      setEnabledTools(MCPService.getEnabledTools());
      setServers(MCPService.getServers());
    };

    const handleSessionChange = (e) => {
      const disabled = e.detail?.disabledServers || [];
      setSessionDisabledServers(new Set(disabled));
    };

    refresh();

    // Refresh when window gains focus (user returns from settings)
    window.addEventListener("focus", refresh);
    // Refresh on storage changes (cross-tab)
    window.addEventListener("storage", refresh);
    // Refresh on custom event from ToolsTab (same window)
    window.addEventListener("mcp-tools-changed", refresh);
    // Listen for session toggle changes from ChatInput
    window.addEventListener("mcp-session-changed", handleSessionChange);

    return () => {
      window.removeEventListener("focus", refresh);
      window.removeEventListener("storage", refresh);
      window.removeEventListener("mcp-tools-changed", refresh);
      window.removeEventListener("mcp-session-changed", handleSessionChange);
    };
  }, []);

  const uniqueServers = useMemo(
    () => [...new Set(enabledTools.map((t) => t.split(":")[0]))]
      .filter(serverId => !sessionDisabledServers.has(serverId)),
    [enabledTools, sessionDisabledServers]
  );

  const modelLabel = selectedModel?.split(".").pop() || "AI Model";

  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    const nodes = [];
    const edges = [];

    const centerX = 230;
    const centerY = 180;
    const radius = 130;
    const modelSize = 100;
    const toolSize = 70;

    // Model at center
    nodes.push({
      id: "model",
      type: "model",
      position: { x: centerX - modelSize / 2, y: centerY - modelSize / 2 },
      data: { label: modelLabel },
      draggable: false,
    });

    // Tools around
    uniqueServers.forEach((serverId, i) => {
      const angle = (i * 360) / uniqueServers.length - 90;
      const rad = (angle * Math.PI) / 180;
      const x = centerX + Math.cos(rad) * radius - toolSize / 2;
      const y = centerY + Math.sin(rad) * radius - toolSize / 2;

      const server = servers.find((s) => s.id === serverId);
      const toolCount = enabledTools.filter((t) => t.startsWith(serverId)).length;
      const handles = getHandles(angle);
      const delay = 0.2 + i * 0.15;

      nodes.push({
        id: serverId,
        type: "tool",
        position: { x, y },
        data: {
          label: server?.name || serverId,
          serverId,
          toolCount,
          colorIndex: i,
          delay,
        },
        draggable: false,
      });

      edges.push({
        id: `e-${serverId}`,
        source: "model",
        target: serverId,
        sourceHandle: handles.source,
        targetHandle: handles.target,
        type: "animated",
        data: { color: "#D1D5DB", delay: delay + 1 },
      });
    });

    return { nodes, edges };
  }, [modelLabel, uniqueServers, servers, enabledTools]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  return (
    <Box
      sx={{
        width: "100%",
        height: "calc(100vh - 140px)", // Account for header (60px) and paddings
        minHeight: 400,
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "center",
        pt: 6,
      }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onInit={handleInit}
        proOptions={{ hideAttribution: true }}
        panOnDrag={false}
        zoomOnScroll={false}
        zoomOnPinch={false}
        zoomOnDoubleClick={false}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        preventScrolling={false}
      >
        <Background color={`${REDWOOD_PRIMARY}08`} gap={24} />
      </ReactFlow>
    </Box>
  );
}
