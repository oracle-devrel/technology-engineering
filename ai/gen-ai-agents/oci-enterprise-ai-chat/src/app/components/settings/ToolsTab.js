"use client";

import { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  IconButton,
  Collapse,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem as MuiMenuItem,
  Tabs,
  Tab,
  InputAdornment,
  Checkbox,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, ChevronDown, ChevronRight, ChevronLeft, RefreshCw, Wrench, Pencil, Check, X, Plug, Unplug, Power, Globe, Blocks, Search, FileSearch, Database, Eye, EyeOff, Upload, FileText, CloudUpload, FolderOpen, ImagePlus, ArrowLeft, Info, Send, Tag, Terminal, Zap, Sparkles, ExternalLink, KeyRound, Download } from "lucide-react";
import IOSSwitch from "../ui/IOSSwitch";
import mcpService, { MCPService } from "../../services/mcpService";
import ToolForm from "./ToolForm";
import { INTERNAL_TOOL_TABS, INTERNAL_ADDONS } from "../../config/tools-internal";

const NATIVE_TOOLS = [
  {
    id: "native_web_search",
    name: "Web Search",
    description: "Search the web in real time to find up-to-date information, articles, documentation, and more. Results are summarized and cited automatically.",
    icon: Search,
    color: "#4285F4",
    endpoint: null,
    comingSoon: true,
  },
  {
    id: "native_rag",
    name: "File Search",
    description: "Retrieve relevant context from your knowledge bases and documents using vector search. Grounds AI responses in your own data for accurate, sourced answers.",
    icon: FileSearch,
    color: "#6B7280",
    endpoint: null,
    hasConfig: true,
  },
  {
    id: "native_code_interpreter",
    name: "Code Interpreter",
    description: "Run Python code in a secure sandbox with 420+ preinstalled libraries. Ideal for calculations, data analysis, chart generation, and file processing.",
    icon: Terminal,
    color: "#10B981",
    endpoint: null,
  },
  {
    id: "native_text_to_sql",
    name: "Text to SQL",
    description: "Convert natural language questions into SQL queries and execute them against your databases. Get structured results and insights from your data instantly.",
    icon: Database,
    color: "#F59E0B",
    endpoint: null,
    hasConfig: true,
    comingSoon: true,
    configType: "semantic_store",
  },
];

const STATUS_CHIP = {
  connected: { label: "Connected", bg: "rgba(16, 185, 129, 0.12)", color: "#059669" },
  error: { label: "Error", bg: "rgba(198, 40, 40, 0.12)", color: "#c62828" },
};

const ADDON_TOOLS = [
  ...INTERNAL_ADDONS,
  {
    id: "addon_image_generation",
    name: "Image Generation",
    description: "Generate images from text descriptions. The AI will create images when your prompt requests visual content.",
    color: "#4f46e5",
    icon: ImagePlus,
    isNative: true,
  },
];

function generateSubjectId() {
  return "user_" + crypto.randomUUID().replace(/-/g, "").slice(0, 12);
}


const ALL_TOOLS_TABS = [
  { label: "Native", icon: <Blocks size={15} />, id: "native" },
  { label: "Custom", icon: <Plug size={15} />, id: "custom" },
  ...INTERNAL_TOOL_TABS,
];

export default function ToolsTab() {
  const [servers, setServers] = useState([]);
  const [enabledTools, setEnabledTools] = useState([]);
  const [expandedServers, setExpandedServers] = useState({});
  const [serverTools, setServerTools] = useState({}); // serverId -> tools[]
  const [loadingServers, setLoadingServers] = useState({}); // serverId -> boolean
  const [serverStatus, setServerStatus] = useState({}); // serverId -> 'connected' | 'error' | null
  const [isHydrated, setIsHydrated] = useState(false);

  // Add/Edit form state lives entirely inside <ToolForm>; ToolsTab only tracks
  // which form is open: showAddForm and editingServerId.
  const [showAddForm, setShowAddForm] = useState(false);
  const [toast, setToast] = useState(null); // { message, severity }
  // OAuth 2.1 token status per server: 'authorized' | 'needs_auth' | undefined (unknown)
  const [oauth21Status, setOauth21Status] = useState({});
  // Server id to scroll/highlight after navigation from a chat banner (?focus=<id>)
  const [focusedServerId, setFocusedServerId] = useState(null);

  // Native tools enabled state
  const [nativeToolsEnabled, setNativeToolsEnabled] = useState({});
  const [semanticStores, setSemanticStores] = useState([]);
  const [loadingSemanticStores, setLoadingSemanticStores] = useState(false);
  const [selectedSemanticStoreId, setSelectedSemanticStoreId] = useState("");

  // Edit server — only need to know which one is being edited; values live in <ToolForm>
  const [editingServerId, setEditingServerId] = useState(null);

  const [vectorStores, setVectorStores] = useState([]);
  const [loadingVectorStores, setLoadingVectorStores] = useState(false);
  const [selectedVectorStoreIds, setSelectedVectorStoreIds] = useState([]);
  const [activeVectorStoreId, setActiveVectorStoreId] = useState(null);
  const [vectorStoreFiles, setVectorStoreFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [deletingFile, setDeletingFile] = useState(null);
  const [allFiles, setAllFiles] = useState([]);

  // VS detail: edit dialog
  const [showEditVSDialog, setShowEditVSDialog] = useState(false);
  const [editVSNameValue, setEditVSNameValue] = useState("");
  const [editVSExpiresEnabled, setEditVSExpiresEnabled] = useState(false);
  const [editVSExpiresDays, setEditVSExpiresDays] = useState("7");
  const [editVSMetadata, setEditVSMetadata] = useState("");
  const [savingVS, setSavingVS] = useState(false);

  // VS detail: tabs & search
  const [vsDetailTab, setVsDetailTab] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState(null);
  const [searching, setSearching] = useState(false);

  // VS detail: file attributes
  const [editingFileAttrs, setEditingFileAttrs] = useState(null); // file id
  const [fileAttrsValue, setFileAttrsValue] = useState("");
  const [savingFileAttrs, setSavingFileAttrs] = useState(false);

  // Batch upload progress
  const [uploadProgress, setUploadProgress] = useState(null); // { done, total } | null

  // File preview modal
  const [previewFile, setPreviewFile] = useState(null); // { id, filename }
  const [previewContent, setPreviewContent] = useState("");
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(null);
  const [downloadingFile, setDownloadingFile] = useState(null);

  const handlePreviewFile = async (fileId, filename) => {
    setPreviewFile({ id: fileId, filename });
    setPreviewContent("");
    setPreviewError(null);
    setPreviewLoading(true);
    try {
      const vsParam = activeVectorStoreId ? `&vsId=${activeVectorStoreId}` : '';
      const res = await fetch(`/api/files/${fileId}/content?limit=10240${vsParam}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        const msg = typeof err.error === 'string' ? err.error : (err.error?.message || JSON.stringify(err.error));
        throw new Error(msg || `HTTP ${res.status}`);
      }
      const text = await res.text();
      setPreviewContent(text);
    } catch (e) {
      setPreviewError(e.message);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDownloadFile = async (fileId, filename) => {
    setDownloadingFile(fileId);
    try {
      const vsParam = activeVectorStoreId ? `&vsId=${activeVectorStoreId}` : '';
      const res = await fetch(`/api/files/${fileId}/content?download=1&filename=${encodeURIComponent(filename)}${vsParam}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Download failed:', e);
    } finally {
      setDownloadingFile(null);
    }
  };
  const [deletingVS, setDeletingVS] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [activeVsStatus, setActiveVsStatus] = useState(null); // 'completed' | 'in_progress' | etc
  const vsPollingRef = useRef(null);

  // Add-on tools state
  const [addonEnabled, setAddonEnabled] = useState({});
  const [addonLoading, setAddonLoading] = useState({});
  const [addonStatus, setAddonStatus] = useState({}); // 'connected' | 'error' | 'needs_auth' | null
  const [addonTools, setAddonTools] = useState({});
  const [addonAuthUrl, setAddonAuthUrl] = useState({}); // addonId -> authorize URL

  // Sync native tools as MCP servers based on enabled state
  const syncNativeServers = (enabledState) => {
    const currentServers = MCPService.getServers();

    NATIVE_TOOLS.forEach(tool => {
      if (!tool.endpoint) return; // skip tools without endpoint
      const exists = currentServers.find(s => s.id === tool.id);

      if (enabledState[tool.id]) {
        if (!exists) {
          // Register as MCP server
          const newServer = {
            id: tool.id,
            name: tool.name,
            endpoint: tool.endpoint,
            enabled: true,
            isNative: true,
          };
          currentServers.push(newServer);
        } else if (!exists.enabled) {
          exists.enabled = true;
        }
      } else {
        if (exists) {
          exists.enabled = false;
        }
      }
    });

    MCPService.setServers(currentServers);
    setServers(currentServers.filter(s => !s.isNative && !s.isAddon));
  };

  // Sync addon tools as MCP servers based on enabled state
  const syncAddonServers = (enabledState) => {
    const currentServers = MCPService.getServers();

    ADDON_TOOLS.filter(a => !a.isNative).forEach(addon => {
      const exists = currentServers.find(s => s.id === addon.id);

      if (enabledState[addon.id]) {
        if (!exists) {
          const newServer = {
            id: addon.id,
            name: addon.name,
            endpoint: addon.endpoint,
            authType: addon.authType,
            authKey: addon.authKey,
            enabled: true,
            isAddon: true,
          };
          currentServers.push(newServer);
        } else {
          exists.enabled = true;
          exists.name = addon.name;
          exists.endpoint = addon.endpoint;
          exists.authType = addon.authType;
          exists.authKey = addon.authKey;
        }
      } else {
        if (exists) {
          exists.enabled = false;
        }
      }
    });

    MCPService.setServers(currentServers);
    setServers(currentServers.filter(s => !s.isNative && !s.isAddon));
  };

  const loadAddonTools = async (addon) => {
    setAddonLoading(prev => ({ ...prev, [addon.id]: true }));
    setAddonStatus(prev => ({ ...prev, [addon.id]: null }));

    try {
      const serverConfig = {
        id: addon.id,
        endpoint: addon.endpoint,
        authType: addon.authType,
        authKey: addon.authKey,
      };
      const tools = await mcpService.listToolsFromServer(serverConfig);
      setAddonStatus(prev => ({ ...prev, [addon.id]: 'connected' }));
      setAddonTools(prev => ({ ...prev, [addon.id]: tools || [] }));

      // Auto-enable all discovered tools
      if (tools && tools.length > 0) {
        const toolIds = tools.map(t => `${addon.id}:${t.name}`);
        setEnabledTools(prev => {
          const cleaned = prev.filter(t => !t.startsWith(`${addon.id}:`));
          return [...cleaned, ...toolIds];
        });
      }
    } catch (error) {
      console.error(`Failed to connect to addon ${addon.name}:`, error);
      if (error.message === 'needs_auth' && error.authorizeUrl) {
        setAddonStatus(prev => ({ ...prev, [addon.id]: 'needs_auth' }));
        setAddonAuthUrl(prev => ({ ...prev, [addon.id]: error.authorizeUrl }));
      } else {
        setAddonStatus(prev => ({ ...prev, [addon.id]: 'error' }));
      }
      setAddonTools(prev => ({ ...prev, [addon.id]: [] }));
    } finally {
      setAddonLoading(prev => ({ ...prev, [addon.id]: false }));
    }
  };

  const handleToggleAddon = (addonId, enabled) => {
    const addon = ADDON_TOOLS.find(a => a.id === addonId);

    // Native addons (no MCP endpoint) — sync via nativeToolsEnabled
    if (addon?.isNative) {
      const nativeId = addonId.replace('addon_', 'native_');
      setNativeToolsEnabled(prev => ({ ...prev, [nativeId]: enabled }));
      const newState = { ...addonEnabled, [addonId]: enabled };
      setAddonEnabled(newState);
      return;
    }

    const newState = { ...addonEnabled, [addonId]: enabled };
    setAddonEnabled(newState);

    if (enabled) {
      syncAddonServers(newState);
      if (addon) loadAddonTools(addon);
    } else {
      // Remove tools from enabled list and clear loading state
      setEnabledTools(prev => prev.filter(t => !t.startsWith(`${addonId}:`)));
      setAddonStatus(prev => ({ ...prev, [addonId]: null }));
      setAddonTools(prev => ({ ...prev, [addonId]: [] }));
      setAddonLoading(prev => ({ ...prev, [addonId]: false }));
      syncAddonServers(newState);
    }
  };

  // Load from localStorage after mount
  useEffect(() => {
    // Load native tools enabled state first
    let nativeState = {};
    try {
      const stored = localStorage.getItem('nativeToolsEnabled');
      if (stored) {
        nativeState = JSON.parse(stored);
      } else {
        NATIVE_TOOLS.forEach(t => { nativeState[t.id] = false; });
      }
    } catch { /* ignore */ }
    setNativeToolsEnabled(nativeState);
    setSelectedSemanticStoreId(localStorage.getItem('nl2sqlSemanticStoreId') || '');

    try {
      const savedVsIds = JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]');
      if (savedVsIds.length > 0) {
        setSelectedVectorStoreIds(savedVsIds);
      }
    } catch { /* ignore */ }

    if (nativeState.native_rag) {
      fetchVectorStores();
    }
    if (nativeState.native_text_to_sql) {
      fetchSemanticStores();
    }

    // Sync native tools as MCP servers
    syncNativeServers(nativeState);

    // Load addon tools enabled state (default: all enabled)
    let addonState = {};
    try {
      const storedAddon = localStorage.getItem('addonToolsEnabled');
      if (storedAddon) {
        addonState = JSON.parse(storedAddon);
      } else {
        ADDON_TOOLS.forEach(a => { addonState[a.id] = true; });
      }
    } catch { /* ignore */ }
    // Sync native addon states from nativeToolsEnabled
    ADDON_TOOLS.filter(a => a.isNative).forEach(a => {
      const nativeId = a.id.replace('addon_', 'native_');
      addonState[a.id] = !!nativeState[nativeId];
    });
    setAddonEnabled(addonState);
    syncAddonServers(addonState);

    // Load custom (non-native, non-addon) servers
    const allServers = MCPService.getServers();
    const customServers = allServers.filter(s => !s.isNative && !s.isAddon);
    setServers(customServers);
    setEnabledTools(MCPService.getEnabledTools());

    setIsHydrated(true);

    // Auto-load tools from custom servers
    customServers.forEach(server => {
      loadServerTools(server);
    });

    // Auto-connect enabled add-ons (skip native ones)
    ADDON_TOOLS.forEach(addon => {
      if (addonState[addon.id] && !addon.isNative) {
        loadAddonTools(addon);
      }
    });
  }, []);

  // Save native tools enabled state and sync MCP servers
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem('nativeToolsEnabled', JSON.stringify(nativeToolsEnabled));
      syncNativeServers(nativeToolsEnabled);
    }
  }, [nativeToolsEnabled, isHydrated]);

  // Save addon tools enabled state
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem('addonToolsEnabled', JSON.stringify(addonEnabled));
    }
  }, [addonEnabled, isHydrated]);


  const handleToggleNativeTool = (toolId, enabled) => {
    setNativeToolsEnabled(prev => ({ ...prev, [toolId]: enabled }));
    if (toolId === 'native_rag' && enabled) {
      fetchVectorStores();
    }
    if (toolId === 'native_text_to_sql' && enabled) {
      fetchSemanticStores();
    }
  };

  const fetchVectorStores = async () => {
    setLoadingVectorStores(true);
    try {
      const res = await fetch('/api/vector-stores');
      if (res.ok) {
        const data = await res.json();
        let stores = data.data || [];

        // Recover stores saved in localStorage but missing from the list (eventual consistency)
        const savedIds = JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]');
        const listedIds = new Set(stores.map(s => s.id));
        const missingIds = savedIds.filter(id => !listedIds.has(id));
        if (missingIds.length > 0) {
          const fetched = await Promise.all(
            missingIds.map(id => fetch(`/api/vector-stores?id=${id}`).then(r => r.ok ? r.json() : null).catch(() => null))
          );
          stores = [...stores, ...fetched.filter(Boolean)];
        }

        setVectorStores(stores);

        // Save valid (completed) VS IDs so genaiAgentsService can filter stale ones
        const validIds = stores.filter(s => s.status === 'completed').map(s => s.id);
        localStorage.setItem('ragValidVectorStoreIds', JSON.stringify(validIds));
      } else {
        console.error('Failed to fetch vector stores:', res.status);
      }
    } catch (error) {
      console.error('Failed to fetch vector stores:', error);
    } finally {
      setLoadingVectorStores(false);
    }
  };

  const fetchSemanticStores = async () => {
    setLoadingSemanticStores(true);
    try {
      const res = await fetch('/api/semantic-stores');
      if (res.ok) {
        const data = await res.json();
        setSemanticStores(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch semantic stores:', error);
    } finally {
      setLoadingSemanticStores(false);
    }
  };

  const handleSelectSemanticStore = (storeId) => {
    const next = selectedSemanticStoreId === storeId ? '' : storeId;
    setSelectedSemanticStoreId(next);
    localStorage.setItem('nl2sqlSemanticStoreId', next);
  };

  const deleteVectorStore = async (vsId) => {
    setDeletingVS(vsId);
    try {
      const res = await fetch(`/api/vector-stores?id=${vsId}`, { method: 'DELETE' });
      if (res.ok) {
        setVectorStores(prev => prev.filter(vs => vs.id !== vsId));
        setSelectedVectorStoreIds(prev => {
          const next = prev.filter(id => id !== vsId);
          localStorage.setItem('ragVectorStoreIds', JSON.stringify(next));
          return next;
        });
        if (activeVectorStoreId === vsId) {
          setActiveVectorStoreId(null);
          setVectorStoreFiles([]);
        }
      }
    } catch (error) {
      console.error('Failed to delete vector store:', error);
    } finally {
      setDeletingVS(null);
    }
  };

  const fetchVectorStoreFiles = async (vsId) => {
    setLoadingFiles(true);
    try {
      const [vsRes, allRes] = await Promise.all([
        fetch(`/api/vector-stores?id=${vsId}&files=1`),
        fetch('/api/files'),
      ]);
      if (vsRes.ok) {
        const data = await vsRes.json();
        setVectorStoreFiles(data.data || []);
      }
      if (allRes.ok) {
        const allData = await allRes.json();
        setAllFiles(allData.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch vector store files:', error);
    } finally {
      setLoadingFiles(false);
    }
  };

  const handleToggleVectorStore = (vsId) => {
    setSelectedVectorStoreIds(prev => {
      const next = prev.includes(vsId) ? prev.filter(id => id !== vsId) : [...prev, vsId];
      localStorage.setItem('ragVectorStoreIds', JSON.stringify(next));
      return next;
    });
  };

  const handleActivateVectorStore = (vsId) => {
    setActiveVectorStoreId(vsId);
    // Clear previous polling
    if (vsPollingRef.current) { clearInterval(vsPollingRef.current); vsPollingRef.current = null; }
    // Check current status
    const vs = vectorStores.find(v => v.id === vsId);
    const status = vs?.status || 'in_progress';
    setActiveVsStatus(status);
    if (status === 'completed') {
      fetchVectorStoreFiles(vsId);
    } else {
      // Poll until completed
      vsPollingRef.current = setInterval(async () => {
        try {
          const res = await fetch(`/api/vector-stores?id=${vsId}`);
          if (res.ok) {
            const data = await res.json();
            setActiveVsStatus(data.status);
            setVectorStores(prev => prev.map(v => v.id === vsId ? { ...v, status: data.status } : v));
            if (data.status === 'completed' || data.status === 'expired') {
              clearInterval(vsPollingRef.current);
              vsPollingRef.current = null;
              if (data.status === 'completed') fetchVectorStoreFiles(vsId);
            }
          }
        } catch {}
      }, 3000);
    }
  };

  const handleDeleteFile = async (fileId) => {
    if (!activeVectorStoreId) return;
    setDeletingFile(fileId);
    try {
      const res = await fetch(`/api/vector-stores?id=${activeVectorStoreId}&file_id=${fileId}`, { method: 'DELETE' });
      if (res.ok) {
        setVectorStoreFiles(prev => prev.filter(f => f.id !== fileId));
      }
    } catch (error) {
      console.error('Failed to delete file:', error);
    } finally {
      setDeletingFile(null);
    }
  };

  // Single-file upload helper (returns the OCI file_id or throws).
  const uploadOneFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('purpose', 'user_data');
    const uploadRes = await fetch('/api/files', { method: 'POST', body: formData });
    if (!uploadRes.ok) {
      const errText = await uploadRes.text().catch(() => '');
      let msg = `Upload failed (${uploadRes.status})`;
      try {
        const parsed = JSON.parse(errText);
        const inner = typeof parsed?.error === 'string' ? (() => { try { return JSON.parse(parsed.error); } catch { return null; } })() : null;
        msg = inner?.message || parsed?.error?.message || parsed?.message || msg;
      } catch { /* not JSON */ }
      throw new Error(msg);
    }
    const uploaded = await uploadRes.json();
    return uploaded.id;
  };

  // Upload N files: parallelizes uploads in chunks of 10 to avoid rate limits,
  // then attaches them all to the vector store via the batch endpoint.
  const handleUploadFiles = async (filesArr) => {
    const files = Array.from(filesArr || []).filter(Boolean);
    if (files.length === 0 || !activeVectorStoreId) return;
    if (activeVsStatus !== 'completed') {
      setUploadError('Vector store is still provisioning. Please wait.');
      return;
    }

    setUploadingFile(true);
    setUploadError(null);
    setUploadProgress({ done: 0, total: files.length });

    const CHUNK_SIZE = 10;
    const fileIds = [];
    const failures = [];
    try {
      for (let i = 0; i < files.length; i += CHUNK_SIZE) {
        const chunk = files.slice(i, i + CHUNK_SIZE);
        const results = await Promise.allSettled(chunk.map(f => uploadOneFile(f)));
        results.forEach((r, idx) => {
          if (r.status === 'fulfilled') fileIds.push(r.value);
          else failures.push({ name: chunk[idx]?.name || '?', error: r.reason?.message || 'Upload failed' });
        });
        setUploadProgress({ done: Math.min(i + chunk.length, files.length), total: files.length });
      }

      if (fileIds.length > 0) {
        // Single file → use attach-file (cheaper). Multiple → use batch endpoint.
        const path = fileIds.length === 1
          ? `/api/vector-stores?id=${activeVectorStoreId}&action=attach-file`
          : `/api/vector-stores?id=${activeVectorStoreId}&action=attach-batch`;
        const body = fileIds.length === 1 ? { file_id: fileIds[0] } : { file_ids: fileIds };
        const attachRes = await fetch(path, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!attachRes.ok) {
          setUploadError(`Failed to attach file${fileIds.length === 1 ? '' : 's'} (${attachRes.status})`);
          return;
        }
      }

      if (failures.length > 0) {
        setUploadError(`${failures.length} of ${files.length} failed: ${failures.slice(0, 3).map(f => f.name).join(', ')}${failures.length > 3 ? '…' : ''}`);
      }

      fetchVectorStoreFiles(activeVectorStoreId);
    } catch (error) {
      console.error('Batch upload failed:', error);
      setUploadError(error.message || 'Upload failed');
    } finally {
      setUploadingFile(false);
      setUploadProgress(null);
    }
  };

  // Backwards-compat wrapper — existing callers still pass a single file.
  const handleUploadFile = (file) => handleUploadFiles([file]);

  const openEditVSDialog = () => {
    const vs = vectorStores.find(v => v.id === activeVectorStoreId);
    if (!vs) return;
    setEditVSNameValue(vs.name || '');
    setEditVSExpiresEnabled(!!vs.expires_after);
    setEditVSExpiresDays(vs.expires_after?.days?.toString() || '7');
    setEditVSMetadata(vs.metadata ? JSON.stringify(vs.metadata, null, 2) : '');
    setShowEditVSDialog(true);
  };

  const handleUpdateVS = async () => {
    if (!activeVectorStoreId) return;
    setSavingVS(true);
    try {
      const body = {};
      if (editVSNameValue.trim()) body.name = editVSNameValue.trim();
      if (editVSExpiresEnabled && parseInt(editVSExpiresDays) > 0) {
        body.expires_after = { anchor: "last_active_at", days: parseInt(editVSExpiresDays) };
      } else if (!editVSExpiresEnabled) {
        body.expires_after = null;
      }
      if (editVSMetadata.trim()) {
        try { body.metadata = JSON.parse(editVSMetadata); } catch { /* ignore */ }
      } else {
        body.metadata = {};
      }
      const res = await fetch(`/api/vector-stores?id=${activeVectorStoreId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        const updated = await res.json();
        setVectorStores(prev => prev.map(vs => vs.id === activeVectorStoreId ? { ...vs, ...updated } : vs));
        setShowEditVSDialog(false);
      }
    } catch (e) {
      console.error('Failed to update VS:', e);
    } finally {
      setSavingVS(false);
    }
  };

  const handleSearchVS = async () => {
    if (!searchQuery.trim() || !activeVectorStoreId) return;
    setSearching(true);
    setSearchResults(null);
    try {
      const res = await fetch(`/api/vector-stores?id=${activeVectorStoreId}&action=search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery.trim(), max_num_results: 5 }),
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.data || []);
      }
    } catch (e) {
      console.error('Search failed:', e);
    } finally {
      setSearching(false);
    }
  };

  const handleUpdateFileAttrs = async (fileId) => {
    if (!activeVectorStoreId) return;
    setSavingFileAttrs(true);
    try {
      let attrs = {};
      try { attrs = JSON.parse(fileAttrsValue); } catch { /* ignore parse error */ }
      const res = await fetch(`/api/vector-stores?id=${activeVectorStoreId}&file_id=${fileId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ attributes: attrs }),
      });
      if (res.ok) {
        setEditingFileAttrs(null);
        fetchVectorStoreFiles(activeVectorStoreId);
      }
    } catch (e) {
      console.error('Failed to update file attrs:', e);
    } finally {
      setSavingFileAttrs(false);
    }
  };

  const handleDeleteFileGlobal = async (fileId) => {
    try {
      await fetch(`/api/files?id=${fileId}`, { method: 'DELETE' });
    } catch (e) {
      console.error('Failed to delete file globally:', e);
    }
  };

  // Save servers when changed (merge with native + addon servers)
  useEffect(() => {
    if (isHydrated) {
      const allStored = MCPService.getServers();
      const nativeServers = allStored.filter(s => s.isNative);
      const addonServers = allStored.filter(s => s.isAddon);
      MCPService.setServers([...nativeServers, ...addonServers, ...servers]);
    }
  }, [servers, isHydrated]);

  // Check OAuth 2.1 token presence for each oauth2.1 server
  useEffect(() => {
    const checkOauth21Tokens = async () => {
      const oauth21Servers = servers.filter(s => s.authType === 'oauth2.1');
      if (oauth21Servers.length === 0) return;
      const updates = {};
      await Promise.all(
        oauth21Servers.map(async (s) => {
          try {
            const res = await fetch(`/api/mcp/oauth/token?endpoint=${encodeURIComponent(s.endpoint)}`);
            const data = await res.json().catch(() => ({}));
            updates[s.id] = data.hasToken ? 'authorized' : 'needs_auth';
          } catch {
            updates[s.id] = 'needs_auth';
          }
        })
      );
      setOauth21Status(prev => ({ ...prev, ...updates }));
    };
    if (isHydrated) checkOauth21Tokens();
  }, [servers, isHydrated]);

  // Show feedback when returning from an OAuth callback (success or error)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    const result = params.get('mcp_auth');
    if (result === 'success') {
      setToast({ message: 'Tool authorized successfully', severity: 'success' });
    } else if (result === 'error') {
      setToast({ message: 'Authorization failed. Try again or check the tool configuration.', severity: 'error' });
    }
    if (result) {
      // Clean the URL so a refresh doesn't re-trigger the toast
      params.delete('mcp_auth');
      const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : '') + window.location.hash;
      window.history.replaceState({}, '', newUrl);
    }
  }, []);

  // Honor ?focus=<serverId> coming from the chat banner. Expand + scroll + highlight
  // the failing server so the user sees it immediately on landing.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!isHydrated || servers.length === 0) return;
    const params = new URLSearchParams(window.location.search);
    const focus = params.get('focus');
    if (!focus) return;
    const target = servers.find(s => s.id === focus);
    if (!target) return;
    setExpandedServers(prev => ({ ...prev, [focus]: true }));
    setFocusedServerId(focus);
    // Strip ?focus from URL so a refresh doesn't re-trigger
    params.delete('focus');
    const newUrl = window.location.pathname + (params.toString() ? `?${params.toString()}` : '') + window.location.hash;
    window.history.replaceState({}, '', newUrl);
    // Scroll to the server card and clear the highlight after a few seconds
    setTimeout(() => {
      const el = document.getElementById(`mcp-server-${focus}`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
    setTimeout(() => setFocusedServerId(null), 4000);
  }, [isHydrated, servers]);

  // Save enabled tools when changed
  useEffect(() => {
    if (isHydrated) {
      MCPService.setEnabledTools(enabledTools);
      // Dispatch custom event so ArchitectureDiagram can update
      window.dispatchEvent(new CustomEvent("mcp-tools-changed"));
    }
  }, [enabledTools, isHydrated]);

  // Receives the validated server data + tools (when the form already tested) from <ToolForm>
  const handleAddServer = (serverData, testTools) => {
    const newServer = MCPService.addServer({ ...serverData, enabled: true });

    // Transfer MCP session from the form's test id to the real server id
    const testStateId = `test-${newServer.id}` in (mcpService.servers && Object.fromEntries(mcpService.servers))
      ? `test-${newServer.id}`
      : 'test-new';
    const testState = mcpService.servers.get(testStateId);
    if (testState) {
      mcpService.servers.set(newServer.id, { ...testState, config: newServer });
      mcpService.servers.delete(testStateId);
    }

    setServers(prev => [...prev, newServer]);
    setShowAddForm(false);
    setExpandedServers(prev => ({ ...prev, [newServer.id]: true }));

    const hasTestTools = Array.isArray(testTools) && testTools.length > 0;
    if (hasTestTools) {
      const tools = testTools.map(t => ({ ...t, serverId: newServer.id, serverName: newServer.name }));
      setServerTools(prev => ({ ...prev, [newServer.id]: tools }));
      setServerStatus(prev => ({ ...prev, [newServer.id]: 'connected' }));
      const toolIds = tools.map(t => `${newServer.id}:${t.name}`);
      setEnabledTools(prev => [...prev, ...toolIds]);
      setToast({ message: `${newServer.name} added · ${tools.length} tools enabled`, severity: 'success' });
    } else if (newServer.authType === 'oauth2.1') {
      // Interactive flow — kick off authorization right away. The user comes back to /settings
      // when done. After return, the server's tools/list will succeed and the chip will load.
      setServerStatus(prev => ({ ...prev, [newServer.id]: null }));
      const returnTo = typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/settings';
      window.location.href = `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(newServer.endpoint)}&returnTo=${encodeURIComponent(returnTo)}`;
    } else {
      loadServerTools(newServer);
    }
  };

  const handleRemoveServer = (serverId) => {
    MCPService.removeServer(serverId);
    setServers(servers.filter(s => s.id !== serverId));

    // Remove tools from this server from enabled list
    const newEnabledTools = enabledTools.filter(t => !t.startsWith(`${serverId}:`));
    setEnabledTools(newEnabledTools);
  };

  const handleToggleServer = (serverId, enabled) => {
    MCPService.updateServer(serverId, { enabled });
    setServers(servers.map(s => s.id === serverId ? { ...s, enabled } : s));
  };

  const handleStartEdit = (server) => setEditingServerId(server.id);
  const handleCancelEdit = () => setEditingServerId(null);

  // Called by <ToolForm mode="edit"> when the user clicks Save
  const handleSaveEdit = (serverData) => {
    const id = serverData.id || editingServerId;
    const updates = {
      name: serverData.name,
      endpoint: serverData.endpoint,
      authType: serverData.authType,
      authKey: serverData.authKey,
      oauth: serverData.oauth,
    };
    MCPService.updateServer(id, updates);
    setServers(prev => prev.map(s => (s.id === id ? { ...s, ...updates } : s)));
    setEditingServerId(null);
    setToast({ message: `${updates.name} updated`, severity: 'success' });
  };

  // Test connection and update tools list
  const testServerConnection = async (server) => {
    setLoadingServers(prev => ({ ...prev, [server.id]: true }));
    setServerStatus(prev => ({ ...prev, [server.id]: null }));

    try {
      const tools = await mcpService.listToolsFromServer(server);
      setServerStatus(prev => ({ ...prev, [server.id]: 'connected' }));
      if (tools) {
        setServerTools(prev => ({ ...prev, [server.id]: tools }));
        // Auto-enable new tools
        const validToolIds = tools.map(t => `${server.id}:${t.name}`);
        setEnabledTools(prev => {
          const cleaned = prev.filter(t => !t.startsWith(`${server.id}:`) || validToolIds.includes(t));
          const toAdd = validToolIds.filter(id => !cleaned.includes(id));
          return toAdd.length > 0 ? [...cleaned, ...toAdd] : cleaned;
        });
      }
    } catch (error) {
      setServerStatus(prev => ({ ...prev, [server.id]: 'error' }));
    } finally {
      setLoadingServers(prev => ({ ...prev, [server.id]: false }));
    }
  };

  const handleTestConnection = async (server) => {
    await testServerConnection(server);
  };


  const loadServerTools = async (server) => {
    setLoadingServers(prev => ({ ...prev, [server.id]: true }));
    setServerStatus(prev => ({ ...prev, [server.id]: null }));

    try {
      const tools = await mcpService.listToolsFromServer(server);
      setServerTools(prev => ({ ...prev, [server.id]: tools }));
      setServerStatus(prev => ({ ...prev, [server.id]: 'connected' }));

      // Clean up enabledTools: remove tools that no longer exist, add new ones
      const validToolIds = tools ? tools.map(t => `${server.id}:${t.name}`) : [];

      setEnabledTools(prev => {
        // Remove tools from this server that no longer exist
        const cleaned = prev.filter(t => {
          if (!t.startsWith(`${server.id}:`)) return true; // keep tools from other servers
          return validToolIds.includes(t); // only keep if still exists
        });

        // Auto-enable new tools (if not already enabled)
        const toAdd = validToolIds.filter(id => !cleaned.includes(id));
        return toAdd.length > 0 ? [...cleaned, ...toAdd] : cleaned;
      });
    } catch (error) {
      console.error(`Failed to load tools from ${server.name}:`, error);
      setServerStatus(prev => ({ ...prev, [server.id]: 'error' }));
      setServerTools(prev => ({ ...prev, [server.id]: [] }));
    } finally {
      setLoadingServers(prev => ({ ...prev, [server.id]: false }));
    }
  };

  const handleToggleExpand = (serverId) => {
    const isExpanding = !expandedServers[serverId];
    setExpandedServers({ ...expandedServers, [serverId]: isExpanding });

    // Load tools if expanding and not loaded yet
    const server = servers.find(s => s.id === serverId);
    if (isExpanding && server && !serverTools[serverId]) {
      loadServerTools(server);
    }
  };

  const handleToggleTool = (serverId, toolName, enabled) => {
    const toolId = `${serverId}:${toolName}`;
    let newEnabledTools;

    if (enabled) {
      newEnabledTools = [...enabledTools, toolId];
    } else {
      newEnabledTools = enabledTools.filter(t => t !== toolId);
    }

    setEnabledTools(newEnabledTools);
  };

  const isToolEnabled = (serverId, toolName) => {
    return enabledTools.includes(`${serverId}:${toolName}`);
  };

  const [toolsTab, setToolsTab] = useState(0);

  const TOOLS_TABS = ALL_TOOLS_TABS;

  // Map tab index to tab id for content rendering
  const activeTabId = TOOLS_TABS[toolsTab]?.id || "native";

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Typography
        variant="h6"
        sx={{
          fontSize: "1.1rem",
          fontWeight: 400,
          color: "var(--dm-text, #1a1a1a)",
          mb: 2.5,
        }}
      >
        Tools
      </Typography>

      {/* Tabs — contained pill style */}
      <Box sx={{
        display: "flex",
        justifyContent: "flex-start",
        mb: 3,
      }}>
        <Box sx={{
          display: "flex",
          gap: 0.5,
          p: 0.5,
          borderRadius: 2.5,
          backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.04))",
          border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
        }}>
          {TOOLS_TABS.map((tab, i) => (
            <Box
              key={i}
              onClick={() => setToolsTab(i)}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                px: 3,
                py: 1,
                borderRadius: 2,
                cursor: "pointer",
                transition: "all 0.2s ease",
                backgroundColor: toolsTab === i ? "var(--dm-surface, #fff)" : "transparent",
                boxShadow: toolsTab === i ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                color: toolsTab === i ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.45))",
                fontWeight: toolsTab === i ? 600 : 450,
                "&:hover": {
                  color: toolsTab === i ? "var(--dm-text, #1a1a1a)" : "var(--dm-text, rgba(0,0,0,0.65))",
                },
              }}
            >
              {tab.icon}
              <Typography sx={{
                fontSize: "0.88rem",
                fontWeight: "inherit",
                color: "inherit",
              }}>
                {tab.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTabId}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >

      {/* Native Tools tab */}
      {activeTabId === "native" && (
        <Box>
          <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.55))", mb: 2.5, fontSize: "0.8rem" }}>
            Built-in tools available to the AI out of the box.
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2 }}>
            {NATIVE_TOOLS.map((tool) => {
              const Icon = tool.icon;
              return (
                <Box
                  key={tool.id}
                  sx={{
                    position: "relative",
                    borderRadius: 1.5,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                    overflow: "hidden",
                    backgroundColor: "var(--dm-surface)",
                    transition: "all 0.2s ease",
                    "&:hover": {
                      borderColor: "var(--dm-border, rgba(0,0,0,0.15))",
                      boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
                    },
                  }}
                >
                  <Box sx={{ p: 2.5, position: "relative" }}>
                    {/* Switch top-right — absolute */}
                    <Box sx={{ position: "absolute", top: 12, right: 12, zIndex: 1, display: "flex", alignItems: "center", gap: 1 }}>
                      {tool.comingSoon && (
                        <Chip
                          label="Coming soon"
                          size="small"
                          sx={{
                            height: 22,
                            fontSize: "0.7rem",
                            fontWeight: 600,
                            backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.06))",
                            color: "var(--dm-muted, rgba(0,0,0,0.45))",
                          }}
                        />
                      )}
                      <IOSSwitch
                        checked={!tool.comingSoon && !!nativeToolsEnabled[tool.id]}
                        onChange={(e) => handleToggleNativeTool(tool.id, e.target.checked)}
                        disabled={!!tool.comingSoon}
                        sx={{ transform: "scale(0.75)" }}
                      />
                    </Box>
                    <Box sx={{
                      display: "flex",
                      alignItems: "flex-start",
                      gap: 2,
                      opacity: tool.comingSoon ? 0.4 : 1,
                      transition: "opacity 0.2s ease",
                    }}>
                      {/* Icon */}
                      <Box sx={{
                        width: 44,
                        height: 44,
                        borderRadius: 2.5,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        backgroundColor: `${tool.color}10`,
                        border: `1px solid ${tool.color}20`,
                        flexShrink: 0,
                      }}>
                        <Icon size={22} color={tool.color} strokeWidth={2} />
                      </Box>

                      {/* Content */}
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Typography sx={{
                          fontSize: "0.95rem",
                          fontWeight: 600,
                          color: "var(--dm-text, #1a1a1a)",
                          letterSpacing: "-0.01em",
                          mb: 0.5,
                        }}>
                          {tool.name}
                        </Typography>
                        <Typography sx={{
                          fontSize: "0.78rem",
                          color: "var(--dm-muted, rgba(0,0,0,0.55))",
                          lineHeight: 1.6,
                        }}>
                          {tool.description}
                        </Typography>
                      </Box>
                    </Box>
                  </Box>


                  {/* Semantic Store config for Text to SQL */}
                  {tool.configType === 'semantic_store' && nativeToolsEnabled[tool.id] && (
                    <Collapse in={nativeToolsEnabled[tool.id]}>
                      <Box sx={{
                        px: 2.5,
                        pb: 2.5,
                        pt: 0,
                        borderTop: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
                      }}>
                        <Box sx={{ mt: 2 }}>
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
                            <Typography sx={{ fontSize: "0.78rem", fontWeight: 500, color: "var(--dm-text, rgba(0,0,0,0.6))" }}>
                              Semantic Stores
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={fetchSemanticStores}
                              disabled={loadingSemanticStores}
                              sx={{ p: 0.5 }}
                            >
                              <RefreshCw size={14} className={loadingSemanticStores ? "animate-spin" : ""} />
                            </IconButton>
                          </Box>

                          {loadingSemanticStores ? (
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1.5 }}>
                              <CircularProgress size={14} />
                              <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>
                                Loading semantic stores...
                              </Typography>
                            </Box>
                          ) : semanticStores.length > 0 ? (
                            <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                              {semanticStores.map((ss) => {
                                const isSelected = selectedSemanticStoreId === ss.id;
                                const schemas = (ss.schemas?.schemas || []).map(s => s.name).join(', ');
                                return (
                                  <Box
                                    key={ss.id}
                                    onClick={() => handleSelectSemanticStore(ss.id)}
                                    sx={{
                                      display: "flex",
                                      alignItems: "center",
                                      gap: 1,
                                      py: 0.75,
                                      px: 1,
                                      borderRadius: 2,
                                      cursor: "pointer",
                                      transition: "all 0.15s ease",
                                      backgroundColor: isSelected ? "rgba(245, 158, 11, 0.06)" : "transparent",
                                      "&:hover": { backgroundColor: isSelected ? "rgba(245, 158, 11, 0.1)" : "var(--dm-subtle, rgba(0,0,0,0.03))" },
                                    }}
                                  >
                                    <Checkbox
                                      size="small"
                                      checked={isSelected}
                                      onClick={(e) => e.stopPropagation()}
                                      onChange={() => handleSelectSemanticStore(ss.id)}
                                      sx={{
                                        p: 0.5,
                                        color: "var(--dm-muted, rgba(0,0,0,0.25))",
                                        "&.Mui-checked": { color: "#F59E0B" },
                                      }}
                                    />
                                    <Database size={15} color={isSelected ? "#F59E0B" : "var(--dm-muted, rgba(0,0,0,0.35))"} strokeWidth={1.5} style={{ flexShrink: 0 }} />
                                    <Box sx={{ flex: 1, minWidth: 0 }}>
                                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
                                        <Typography sx={{
                                          fontSize: "0.82rem",
                                          fontWeight: isSelected ? 500 : 400,
                                          color: "var(--dm-text, #1a1a1a)",
                                          overflow: "hidden",
                                          textOverflow: "ellipsis",
                                          whiteSpace: "nowrap",
                                          lineHeight: 1.3,
                                        }}>
                                          {ss.displayName}
                                        </Typography>
                                        <Chip
                                          label={ss.lifecycleState === 'ACTIVE' ? 'Active' : ss.lifecycleState}
                                          size="small"
                                          sx={{
                                            height: 18,
                                            fontSize: "0.6rem",
                                            backgroundColor: ss.lifecycleState === 'ACTIVE' ? "rgba(16, 185, 129, 0.1)" : "var(--dm-subtle, rgba(0,0,0,0.06))",
                                            color: ss.lifecycleState === 'ACTIVE' ? "#059669" : "var(--dm-muted, rgba(0,0,0,0.5))",
                                          }}
                                        />
                                      </Box>
                                      {schemas && (
                                        <Typography sx={{ fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", lineHeight: 1.2 }}>
                                          Schema: {schemas}
                                        </Typography>
                                      )}
                                    </Box>
                                  </Box>
                                );
                              })}
                            </Box>
                          ) : (
                            <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", py: 1 }}>
                              No semantic stores found. Create one in OCI Console → Generative AI → Vector Stores (Structured data).
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </Collapse>
                  )}

                  {tool.hasConfig && tool.configType !== 'semantic_store' && nativeToolsEnabled[tool.id] && (
                    <Collapse in={nativeToolsEnabled[tool.id]}>
                      <Box sx={{
                        px: 2.5,
                        pb: 2.5,
                        pt: 0,
                        borderTop: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
                      }}>

                        <Box sx={{ mt: 2 }}>
                          {/* Detail view — single vector store */}
                          {activeVectorStoreId ? (
                            <Box>
                              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 2 }}>
                                <IconButton
                                  size="small"
                                  onClick={() => { if (vsPollingRef.current) { clearInterval(vsPollingRef.current); vsPollingRef.current = null; } setActiveVectorStoreId(null); setActiveVsStatus(null); setVectorStoreFiles([]); setSearchResults(null); setSearchQuery(""); setEditingFileAttrs(null); setVsDetailTab(0); }}
                                  sx={{ p: 0.5 }}
                                >
                                  <ArrowLeft size={16} />
                                </IconButton>
                                <FolderOpen size={15} color="var(--dm-text, #1a1a1a)" strokeWidth={2.2} style={{ flexShrink: 0 }} />
                                <Typography sx={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--dm-text, #1a1a1a)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                  {vectorStores.find(v => v.id === activeVectorStoreId)?.name}
                                </Typography>
                                {activeVsStatus && activeVsStatus !== 'completed' && (
                                  <Chip
                                    size="small"
                                    icon={activeVsStatus === 'expired' ? undefined : <CircularProgress size={10} sx={{ color: "var(--dm-muted, rgba(0,0,0,0.5))" }} />}
                                    label={activeVsStatus === 'expired' ? "Expired" : "Provisioning"}
                                    sx={{
                                      height: 22, fontSize: "0.65rem",
                                      backgroundColor: activeVsStatus === 'expired' ? "rgba(239,68,68,0.08)" : "var(--dm-subtle, rgba(0,0,0,0.06))",
                                      color: activeVsStatus === 'expired' ? "#DC2626" : "var(--dm-muted, rgba(0,0,0,0.5))",
                                    }}
                                  />
                                )}
                                <IconButton size="small" onClick={openEditVSDialog} sx={{ p: 0.5 }}>
                                  <Pencil size={13} />
                                </IconButton>
                                <Checkbox
                                  size="small"
                                  checked={selectedVectorStoreIds.includes(activeVectorStoreId)}
                                  onChange={() => handleToggleVectorStore(activeVectorStoreId)}
                                  title="Use in RAG queries"
                                  sx={{ p: 0.5, color: "var(--dm-muted, rgba(0,0,0,0.25))", "&.Mui-checked": { color: "var(--dm-text, #1a1a1a)" } }}
                                />
                              </Box>

                              {/* Edit VS Dialog */}
                              <Dialog
                                open={showEditVSDialog}
                                onClose={() => setShowEditVSDialog(false)}
                                maxWidth="xs"
                                fullWidth
                                PaperProps={{ sx: { borderRadius: 1.5 } }}
                              >
                                <DialogTitle sx={{ fontSize: "1rem", fontWeight: 600, pb: 1 }}>Edit Vector Store</DialogTitle>
                                <DialogContent sx={{ display: "flex", flexDirection: "column", gap: 2, pt: "8px !important" }}>
                                  <TextField
                                    value={editVSNameValue}
                                    onChange={(e) => setEditVSNameValue(e.target.value)}
                                    label="Name"
                                    size="small"
                                    fullWidth
                                    autoFocus
                                    sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.85rem" } }}
                                  />
                                  <Box>
                                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                      <Checkbox
                                        size="small"
                                        checked={editVSExpiresEnabled}
                                        onChange={(e) => setEditVSExpiresEnabled(e.target.checked)}
                                        sx={{ p: 0.25, color: "var(--dm-muted, rgba(0,0,0,0.25))", "&.Mui-checked": { color: "var(--dm-text, #1a1a1a)" } }}
                                      />
                                      <Typography sx={{ fontSize: "0.82rem", color: "var(--dm-text, rgba(0,0,0,0.7))" }}>Auto-expire</Typography>
                                      <Tooltip title="Automatically delete this vector store after a period of inactivity." arrow placement="top">
                                        <Box sx={{ display: "inline-flex", cursor: "help" }}><Info size={14} color="var(--dm-muted, rgba(0,0,0,0.3))" /></Box>
                                      </Tooltip>
                                      {editVSExpiresEnabled && (
                                        <TextField
                                          value={editVSExpiresDays}
                                          onChange={(e) => setEditVSExpiresDays(e.target.value.replace(/\D/g, ''))}
                                          size="small"
                                          InputProps={{ endAdornment: <InputAdornment position="end"><Typography sx={{ fontSize: "0.72rem" }}>days</Typography></InputAdornment> }}
                                          sx={{ width: 110, "& .MuiOutlinedInput-root": { fontSize: "0.82rem" } }}
                                        />
                                      )}
                                    </Box>
                                  </Box>
                                  <TextField
                                    value={editVSMetadata}
                                    onChange={(e) => setEditVSMetadata(e.target.value)}
                                    label="Metadata (JSON)"
                                    size="small"
                                    fullWidth
                                    multiline
                                    minRows={2}
                                    maxRows={4}
                                    placeholder='{"key": "value"}'
                                    sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.8rem", fontFamily: "monospace" } }}
                                  />
                                </DialogContent>
                                <DialogActions sx={{ px: 3, pb: 2 }}>
                                  <Button onClick={() => setShowEditVSDialog(false)} size="small" sx={{ textTransform: "none", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>
                                    Cancel
                                  </Button>
                                  <Button variant="contained" size="small" onClick={handleUpdateVS} disabled={!editVSNameValue.trim() || savingVS} sx={{ textTransform: "none", minWidth: 80 }}>
                                    {savingVS ? <CircularProgress size={14} /> : "Save"}
                                  </Button>
                                </DialogActions>
                              </Dialog>

                              {/* File Preview Dialog */}
                              <Dialog
                                open={!!previewFile}
                                onClose={() => setPreviewFile(null)}
                                maxWidth="md"
                                fullWidth
                                PaperProps={{ sx: { borderRadius: 1.5, maxHeight: "80vh" } }}
                              >
                                <DialogTitle sx={{ fontSize: "0.95rem", fontWeight: 600, pb: 1, display: "flex", alignItems: "center", gap: 1, pr: 1 }}>
                                  <FileText size={15} style={{ color: "var(--dm-muted, rgba(0,0,0,0.4))", flexShrink: 0 }} />
                                  <Typography sx={{ fontSize: "0.95rem", fontWeight: 600, flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                    {previewFile?.filename}
                                  </Typography>
                                  <IconButton
                                    size="small"
                                    title="Download"
                                    onClick={() => previewFile && handleDownloadFile(previewFile.id, previewFile.filename)}
                                    disabled={downloadingFile === previewFile?.id}
                                    sx={{ p: 0.5 }}
                                  >
                                    {downloadingFile === previewFile?.id ? <CircularProgress size={13} /> : <Download size={13} />}
                                  </IconButton>
                                  <IconButton size="small" onClick={() => setPreviewFile(null)} sx={{ p: 0.5 }}>
                                    <X size={14} />
                                  </IconButton>
                                </DialogTitle>
                                <DialogContent sx={{ pt: "8px !important", pb: 2 }}>
                                  {previewLoading ? (
                                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1, py: 6 }}>
                                      <CircularProgress size={16} />
                                      <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>Loading...</Typography>
                                    </Box>
                                  ) : previewError ? (
                                    <Box sx={{ py: 4, textAlign: "center" }}>
                                      <Typography sx={{ fontSize: "0.78rem", color: "#d32f2f", mb: 0.5 }}>Failed to load preview</Typography>
                                      <Typography sx={{ fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", wordBreak: "break-word" }}>{previewError}</Typography>
                                    </Box>
                                  ) : (
                                    <Box>
                                      <Box sx={{
                                        backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                                        border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
                                        borderRadius: 1.5,
                                        p: 1.5,
                                        maxHeight: "60vh",
                                        overflow: "auto",
                                      }}>
                                        <Typography component="pre" sx={{
                                          fontSize: "0.72rem",
                                          fontFamily: "ui-monospace, 'SF Mono', Menlo, monospace",
                                          color: "var(--dm-text, rgba(0,0,0,0.75))",
                                          lineHeight: 1.55,
                                          whiteSpace: "pre-wrap",
                                          wordBreak: "break-word",
                                          margin: 0,
                                        }}>
                                          {previewContent}
                                        </Typography>
                                      </Box>
                                      <Typography sx={{ fontSize: "0.65rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", mt: 1, textAlign: "right" }}>
                                        Showing first {(previewContent.length / 1024).toFixed(1)} KB · download for full file
                                      </Typography>
                                    </Box>
                                  )}
                                </DialogContent>
                              </Dialog>

                              {/* Tabs: Documents | Search */}
                              <Tabs
                                value={vsDetailTab}
                                onChange={(_, v) => setVsDetailTab(v)}
                                sx={{
                                  minHeight: 0,
                                  mb: 1.5,
                                  "& .MuiTabs-indicator": { height: 2, borderRadius: 1 },
                                  "& .MuiTab-root": { minHeight: 0, py: 0.75, px: 1.5, fontSize: "0.75rem", textTransform: "none", minWidth: 0 },
                                }}
                              >
                                <Tab label={vectorStoreFiles.length > 0 ? `Documents (${vectorStoreFiles.length})` : "Documents"} />
                                <Tab label="Search" />
                              </Tabs>

                              {/* Tab: Documents */}
                              {vsDetailTab === 0 && (
                                <Box>
                                  {(() => {
                                    const vsReady = activeVsStatus === 'completed';
                                    const disabled = !vsReady || uploadingFile;
                                    const hasFiles = vectorStoreFiles.length > 0;
                                    return (
                                      <Box
                                        onDragOver={(e) => { if (!disabled) { e.preventDefault(); e.stopPropagation(); setIsDragging(true); } }}
                                        onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setIsDragging(false); }}
                                        onDrop={(e) => {
                                          e.preventDefault();
                                          e.stopPropagation();
                                          setIsDragging(false);
                                          if (disabled) return;
                                          const files = Array.from(e.dataTransfer.files || []);
                                          if (files.length > 0) handleUploadFiles(files);
                                        }}
                                        sx={{
                                          position: "relative",
                                          borderRadius: 2.5,
                                          border: isDragging ? "2px dashed var(--dm-text, #1a1a1a)" : "2px dashed var(--dm-border, rgba(0,0,0,0.12))",
                                          backgroundColor: isDragging ? "var(--dm-subtle, rgba(26, 26, 26, 0.04))" : disabled ? "var(--dm-subtle, rgba(0,0,0,0.02))" : "transparent",
                                          opacity: vsReady ? 1 : 0.5,
                                          transition: "all 0.2s ease",
                                          overflow: "hidden",
                                          "&:hover": !disabled && !hasFiles ? { borderColor: "rgba(26, 26, 26, 0.3)", backgroundColor: "rgba(26, 26, 26, 0.02)" } : {},
                                        }}
                                      >
                                        {/* File list inside the drop zone */}
                                        {loadingFiles ? (
                                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 1, py: 4 }}>
                                            <CircularProgress size={14} />
                                            <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>Loading...</Typography>
                                          </Box>
                                        ) : hasFiles ? (
                                          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.25, p: 0.75, maxHeight: 240, overflow: "auto" }}>
                                            {vectorStoreFiles.map((f) => {
                                            const fileInfo = allFiles.find(af => af.id === f.id);
                                            const displayName = fileInfo?.filename || f.id;
                                            const hasAttrs = f.attributes && Object.keys(f.attributes).length > 0;
                                            return (
                                              <Box key={f.id}>
                                                <Box
                                                  onClick={() => handlePreviewFile(f.id, displayName)}
                                                  sx={{
                                                    display: "flex", alignItems: "center", gap: 0.75, py: 0.6, px: 0.75, borderRadius: 1.5,
                                                    cursor: "pointer",
                                                    "&:hover": { backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))" }, "&:hover .file-actions": { opacity: 0.5 },
                                                    transition: "background-color 0.15s ease",
                                                  }}
                                                >
                                                  <FileText size={13} style={{ color: "var(--dm-muted, rgba(0,0,0,0.3))", flexShrink: 0 }} />
                                                  <Box sx={{ flex: 1, minWidth: 0 }}>
                                                    <Typography sx={{ fontSize: "0.73rem", color: "var(--dm-text, rgba(0,0,0,0.7))", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                      {displayName}
                                                    </Typography>
                                                    {(f.status || hasAttrs || fileInfo?.bytes) && (
                                                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mt: 0.25 }}>
                                                        {f.status && (
                                                          <Chip
                                                            label={f.status === 'completed' ? 'Completed' : f.status === 'failed' ? 'Failed' : f.status}
                                                            size="small"
                                                            sx={{
                                                              height: 14,
                                                              fontSize: "0.55rem",
                                                              backgroundColor: f.status === 'completed' ? "rgba(16, 185, 129, 0.1)" : f.status === 'failed' ? "rgba(239, 68, 68, 0.1)" : "var(--dm-subtle, rgba(0,0,0,0.06))",
                                                              color: f.status === 'completed' ? "#059669" : f.status === 'failed' ? "#DC2626" : "var(--dm-muted, rgba(0,0,0,0.5))",
                                                            }}
                                                          />
                                                        )}
                                                        {fileInfo?.bytes && (
                                                          <Typography sx={{ fontSize: "0.6rem", color: "var(--dm-muted, rgba(0,0,0,0.4))" }}>
                                                            {fileInfo.bytes < 1024 ? `${fileInfo.bytes} B` : fileInfo.bytes < 1024 * 1024 ? `${(fileInfo.bytes / 1024).toFixed(0)} KB` : `${(fileInfo.bytes / 1024 / 1024).toFixed(1)} MB`}
                                                          </Typography>
                                                        )}
                                                        {hasAttrs && (
                                                          <Typography sx={{ fontSize: "0.6rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                                                            {Object.entries(f.attributes).map(([k, v]) => `${k}: ${v}`).join(', ')}
                                                          </Typography>
                                                        )}
                                                      </Box>
                                                    )}
                                                  </Box>
                                                  <IconButton className="file-actions" size="small" title="Download"
                                                    onClick={(e) => { e.stopPropagation(); handleDownloadFile(f.id, displayName); }}
                                                    disabled={downloadingFile === f.id}
                                                    sx={{ opacity: 0, p: 0.25, "&:hover": { opacity: 1 }, transition: "opacity 0.15s ease" }}
                                                  >
                                                    {downloadingFile === f.id ? <CircularProgress size={11} /> : <Download size={11} />}
                                                  </IconButton>
                                                  <IconButton className="file-actions" size="small" title="Edit attributes"
                                                    onClick={(e) => { e.stopPropagation(); setEditingFileAttrs(editingFileAttrs === f.id ? null : f.id); setFileAttrsValue(f.attributes ? JSON.stringify(f.attributes, null, 2) : '{}'); }}
                                                    sx={{ opacity: 0, p: 0.25, transition: "opacity 0.15s ease" }}
                                                  >
                                                    <Tag size={11} />
                                                  </IconButton>
                                                  <IconButton className="file-actions" size="small"
                                                    onClick={(e) => { e.stopPropagation(); handleDeleteFile(f.id); handleDeleteFileGlobal(f.id); }}
                                                    disabled={deletingFile === f.id}
                                                    sx={{ opacity: 0, p: 0.25, "&:hover": { opacity: 1, color: "#d32f2f" }, transition: "opacity 0.15s ease" }}
                                                  >
                                                    {deletingFile === f.id ? <CircularProgress size={11} /> : <Trash2 size={12} />}
                                                  </IconButton>
                                                </Box>
                                                {editingFileAttrs === f.id && (
                                                  <Box sx={{ pl: 3, pr: 0.75, pb: 0.75, display: "flex", gap: 0.5, alignItems: "flex-start" }}>
                                                    <TextField value={fileAttrsValue} onChange={(e) => setFileAttrsValue(e.target.value)} size="small" multiline minRows={1} maxRows={3}
                                                      placeholder='{"category": "docs"}' sx={{ flex: 1, "& .MuiOutlinedInput-root": { fontSize: "0.7rem", fontFamily: "monospace" } }}
                                                    />
                                                    <IconButton size="small" onClick={() => handleUpdateFileAttrs(f.id)} disabled={savingFileAttrs} sx={{ p: 0.25, mt: 0.5 }}>
                                                      {savingFileAttrs ? <CircularProgress size={11} /> : <Check size={13} />}
                                                    </IconButton>
                                                  </Box>
                                                )}
                                              </Box>
                                            );
                                          })}
                                          </Box>
                                        ) : (
                                          /* Empty state: full-area click-to-upload */
                                          <Box
                                            component="label"
                                            sx={{
                                              display: "flex",
                                              flexDirection: "column",
                                              alignItems: "center",
                                              justifyContent: "center",
                                              py: 4,
                                              px: 1.5,
                                              cursor: disabled ? "default" : "pointer",
                                              pointerEvents: disabled ? "none" : "auto",
                                              minHeight: 140,
                                            }}
                                          >
                                            {uploadingFile ? (
                                              <CircularProgress size={20} sx={{ color: "var(--dm-text, #1a1a1a)", mb: 0.5 }} />
                                            ) : (
                                              <CloudUpload size={26} color={isDragging ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.25))"} strokeWidth={1.5} style={{ marginBottom: 6 }} />
                                            )}
                                            <Typography sx={{ fontSize: "0.78rem", color: isDragging ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.5))", fontWeight: isDragging ? 500 : 400, textAlign: "center" }}>
                                              {activeVsStatus === 'expired' ? "Vector store expired" : !vsReady ? "Provisioning..." : uploadingFile ? (uploadProgress ? `Uploading ${uploadProgress.done}/${uploadProgress.total}...` : "Uploading...") : isDragging ? "Drop files here" : "Drag & drop or click to upload"}
                                            </Typography>
                                            <Typography sx={{ fontSize: "0.65rem", color: "var(--dm-muted, rgba(0,0,0,0.32))", mt: 0.5, textAlign: "center" }}>
                                              PDF, TXT, MD, JSON, HTML
                                            </Typography>
                                            <input type="file" hidden multiple disabled={disabled} accept=".pdf,.txt,.md,.json,.html"
                                              onChange={(e) => { const files = Array.from(e.target.files || []); if (files.length > 0) { handleUploadFiles(files); e.target.value = ''; } }}
                                            />
                                          </Box>
                                        )}

                                        {/* When files exist: compact "add more" footer that stays a click target + drop hint */}
                                        {hasFiles && (
                                          <Box
                                            component="label"
                                            sx={{
                                              display: "flex",
                                              alignItems: "center",
                                              justifyContent: "center",
                                              gap: 0.6,
                                              py: 0.85,
                                              borderTop: "1px dashed var(--dm-border, rgba(0,0,0,0.08))",
                                              cursor: disabled ? "default" : "pointer",
                                              pointerEvents: disabled ? "none" : "auto",
                                              transition: "background-color 0.15s ease",
                                              "&:hover": !disabled ? { backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))" } : {},
                                            }}
                                          >
                                            {uploadingFile ? (
                                              <>
                                                <CircularProgress size={11} sx={{ color: "var(--dm-muted, rgba(0,0,0,0.4))" }} />
                                                <Typography sx={{ fontSize: "0.68rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>
                                                  {uploadProgress ? `Uploading ${uploadProgress.done}/${uploadProgress.total}...` : "Uploading..."}
                                                </Typography>
                                              </>
                                            ) : (
                                              <>
                                                <CloudUpload size={12} color={isDragging ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.35))"} strokeWidth={1.5} />
                                                <Typography sx={{ fontSize: "0.68rem", color: isDragging ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.45))", fontWeight: isDragging ? 500 : 400 }}>
                                                  {isDragging ? "Drop to add" : "Drag & drop or click to add more"}
                                                </Typography>
                                              </>
                                            )}
                                            <input type="file" hidden multiple disabled={disabled} accept=".pdf,.txt,.md,.json,.html"
                                              onChange={(e) => { const files = Array.from(e.target.files || []); if (files.length > 0) { handleUploadFiles(files); e.target.value = ''; } }}
                                            />
                                          </Box>
                                        )}
                                      </Box>
                                    );
                                  })()}
                                  {uploadError && (
                                    <Typography sx={{ fontSize: "0.72rem", color: "#d32f2f", mt: 1, wordBreak: "break-word" }}>{uploadError}</Typography>
                                  )}
                                </Box>
                              )}

                              {/* Tab: Search */}
                              {vsDetailTab === 1 && (
                                <Box>
                                  <Box sx={{ display: "flex", gap: 0.5, mb: 1.5 }}>
                                    <TextField
                                      value={searchQuery}
                                      onChange={(e) => setSearchQuery(e.target.value)}
                                      placeholder="Test a search query..."
                                      size="small"
                                      fullWidth
                                      onKeyDown={(e) => { if (e.key === 'Enter') handleSearchVS(); }}
                                      sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.82rem" } }}
                                    />
                                    <IconButton size="small" onClick={handleSearchVS} disabled={searching || !searchQuery.trim()} sx={{ p: 0.75 }}>
                                      {searching ? <CircularProgress size={14} /> : <Search size={16} />}
                                    </IconButton>
                                  </Box>
                                  {searchResults === null && !searching && (
                                    <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.35))", textAlign: "center", py: 3 }}>
                                      Search your vector store to test that documents are indexed correctly.
                                    </Typography>
                                  )}
                                  {searchResults && searchResults.length === 0 && (
                                    <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", textAlign: "center", py: 2 }}>No results found.</Typography>
                                  )}
                                  {searchResults && searchResults.length > 0 && (
                                    <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                                      {searchResults.map((r, i) => (
                                        <Box key={i} sx={{ p: 1.25, borderRadius: 2, backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))", border: "1px solid var(--dm-border, rgba(0,0,0,0.06))" }}>
                                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 0.75 }}>
                                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                              <FileText size={12} style={{ color: "var(--dm-muted, rgba(0,0,0,0.35))" }} />
                                              <Typography sx={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--dm-text, rgba(0,0,0,0.65))" }}>
                                                {r.filename || r.file_id}
                                              </Typography>
                                            </Box>
                                            <Chip label={`${(r.score * 100).toFixed(1)}%`} size="small" sx={{ height: 18, fontSize: "0.62rem", fontWeight: 600, backgroundColor: r.score > 0.8 ? "rgba(34,197,94,0.1)" : r.score > 0.5 ? "rgba(234,179,8,0.1)" : "var(--dm-subtle, rgba(0,0,0,0.05))", color: r.score > 0.8 ? "#16a34a" : r.score > 0.5 ? "#ca8a04" : "var(--dm-muted, rgba(0,0,0,0.5))" }} />
                                          </Box>
                                          <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.55))", lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                            {r.content?.[0]?.text || 'No content'}
                                          </Typography>
                                        </Box>
                                      ))}
                                    </Box>
                                  )}
                                </Box>
                              )}
                            </Box>
                          ) : (
                            /* List view — all vector stores */
                            <Box>
                              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1.5 }}>
                                <Box sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
                                  <Typography sx={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--dm-text, rgba(0,0,0,0.7))" }}>
                                    Vector Stores
                                  </Typography>
                                  <Tooltip title="Manage in OCI Console" arrow>
                                    <IconButton
                                      size="small"
                                      component="a"
                                      href="https://cloud.oracle.com/ai-service/generative-ai/vectorStores?region=us-chicago-1"
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      sx={{ p: 0.25 }}
                                    >
                                      <ExternalLink size={12} style={{ opacity: 0.5 }} />
                                    </IconButton>
                                  </Tooltip>
                                </Box>
                                <Box sx={{ display: "flex", alignItems: "center", gap: 0.25 }}>
                                  <IconButton
                                    size="small"
                                    onClick={fetchVectorStores}
                                    disabled={loadingVectorStores}
                                    title="Refresh"
                                  >
                                    <RefreshCw size={14} />
                                  </IconButton>
                                </Box>
                              </Box>

                              {loadingVectorStores ? (
                                <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 1.5 }}>
                                  <CircularProgress size={14} />
                                  <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>
                                    Loading vector stores...
                                  </Typography>
                                </Box>
                              ) : vectorStores.length > 0 ? (
                                <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                                  {vectorStores.map((vs) => {
                                    const isChecked = selectedVectorStoreIds.includes(vs.id);
                                    return (
                                      <Box
                                        key={vs.id}
                                        onClick={() => handleActivateVectorStore(vs.id)}
                                        sx={{
                                          display: "flex",
                                          alignItems: "center",
                                          gap: 1,
                                          py: 0.75,
                                          px: 1,
                                          borderRadius: 2,
                                          cursor: "pointer",
                                          transition: "all 0.15s ease",
                                          "&:hover": {
                                            backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.03))",
                                          },
                                          "&:hover .vs-delete": { opacity: 0.5 },
                                          "&:hover .vs-chevron": { opacity: 1 },
                                        }}
                                      >
                                        <Checkbox
                                          size="small"
                                          checked={isChecked}
                                          onClick={(e) => e.stopPropagation()}
                                          onChange={() => handleToggleVectorStore(vs.id)}
                                          sx={{
                                            p: 0.5,
                                            color: "var(--dm-muted, rgba(0,0,0,0.25))",
                                            "&.Mui-checked": { color: "var(--dm-text, #1a1a1a)" },
                                          }}
                                        />
                                        <FolderOpen
                                          size={15}
                                          color="var(--dm-muted, rgba(0,0,0,0.35))"
                                          strokeWidth={1.5}
                                          style={{ flexShrink: 0 }}
                                        />
                                        <Box sx={{ flex: 1, minWidth: 0 }}>
                                          <Typography sx={{
                                            fontSize: "0.82rem",
                                            fontWeight: 400,
                                            color: "var(--dm-text, #1a1a1a)",
                                            overflow: "hidden",
                                            textOverflow: "ellipsis",
                                            whiteSpace: "nowrap",
                                            lineHeight: 1.3,
                                          }}>
                                            {vs.name}
                                          </Typography>
                                          <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mt: 0.25 }}>
                                            <Chip
                                              label={vs.status === 'completed' ? 'Completed' : vs.status === 'expired' ? 'Expired' : vs.status}
                                              size="small"
                                              sx={{
                                                height: 16,
                                                fontSize: "0.6rem",
                                                backgroundColor: vs.status === 'completed' ? "rgba(16, 185, 129, 0.1)" : vs.status === 'expired' ? "rgba(239, 68, 68, 0.1)" : "var(--dm-subtle, rgba(0,0,0,0.06))",
                                                color: vs.status === 'completed' ? "#059669" : vs.status === 'expired' ? "#DC2626" : "var(--dm-muted, rgba(0,0,0,0.5))",
                                              }}
                                            />
                                            <Typography sx={{ fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", lineHeight: 1.2 }}>
                                              {vs.file_counts?.total || 0} files · {vs.usage_bytes ? `${(vs.usage_bytes / 1024).toFixed(0)} KB` : '0 KB'}
                                            </Typography>
                                          </Box>
                                        </Box>
                                        <IconButton
                                          className="vs-delete"
                                          size="small"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            deleteVectorStore(vs.id);
                                          }}
                                          disabled={deletingVS === vs.id}
                                          sx={{
                                            opacity: 0,
                                            "&:hover": { opacity: 1, color: "#d32f2f" },
                                            transition: "opacity 0.15s ease",
                                          }}
                                        >
                                          {deletingVS === vs.id ? <CircularProgress size={12} /> : <Trash2 size={13} />}
                                        </IconButton>
                                        <ChevronRight
                                          className="vs-chevron"
                                          size={14}
                                          style={{ color: "var(--dm-muted, rgba(0,0,0,0.25))", flexShrink: 0, opacity: 0.5 }}
                                        />
                                      </Box>
                                    );
                                  })}
                                </Box>
                              ) : (
                                <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", py: 1 }}>
                                  No vector stores found. Create one to get started.
                                </Typography>
                              )}
                            </Box>
                          )}
                        </Box>
                      </Box>
                    </Collapse>
                  )}
                </Box>
              );
            })}
          </Box>

        </Box>
      )}

      {/* Internal Marketplace tab — gated on INTERNAL_TOOL_TABS (populated only on private branch) */}
      {INTERNAL_TOOL_TABS.length > 0 && activeTabId === "internal" && (
        <Box>
          <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.55))", mb: 2.5, fontSize: "0.8rem" }}>
            Pre-configured tools ready to activate with a single toggle.
          </Typography>
          <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, gap: 2.5, pb: 1 }}>
            {ADDON_TOOLS.map((addon) => {
              const isEnabled = !!addonEnabled[addon.id];
              const isLoading = !!addonLoading[addon.id];
              const status = addonStatus[addon.id];
              const tools = addonTools[addon.id] || [];
              const Icon = addon.icon;
              const Logo = addon.LogoComponent;

              const statusChip = isEnabled && STATUS_CHIP[status];

              return (
                <Box
                  key={addon.id}
                  sx={{
                    position: "relative",
                    p: 2.5,
                    borderRadius: 1.5,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                    overflow: "hidden",
                    backgroundColor: "var(--dm-surface)",
                    transition: "all 0.2s ease",
                    "&:hover": {
                      borderColor: "var(--dm-border, rgba(0,0,0,0.15))",
                      boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
                    },
                  }}
                >
                  <Box sx={{ position: "absolute", top: 12, right: 12, zIndex: 1 }}>
                    <IOSSwitch
                      checked={isEnabled}
                      onChange={(e) => handleToggleAddon(addon.id, e.target.checked)}
                      sx={{ transform: "scale(0.75)" }}
                    />
                  </Box>

                  <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2 }}>
                    <Box sx={{
                      width: 44,
                      height: 44,
                      borderRadius: 2.5,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      backgroundColor: `${addon.color}10`,
                      border: `1px solid ${addon.color}20`,
                      flexShrink: 0,
                    }}>
                      {Logo ? (
                        <Logo size={24} color={addon.color} />
                      ) : (
                        <Icon size={22} color={addon.color} strokeWidth={2} />
                      )}
                    </Box>

                    <Box sx={{ flex: 1, minWidth: 0, pr: 5 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5, flexWrap: "wrap" }}>
                        <Typography sx={{
                          fontSize: "0.95rem",
                          fontWeight: 600,
                          color: "var(--dm-text, #1a1a1a)",
                          letterSpacing: "-0.01em",
                        }}>
                          {addon.name}
                        </Typography>
                        {statusChip && (
                          <Chip
                            label={statusChip.label}
                            size="small"
                            sx={{
                              height: 20,
                              fontSize: "0.65rem",
                              fontWeight: 600,
                              backgroundColor: statusChip.bg,
                              color: statusChip.color,
                            }}
                          />
                        )}
                      </Box>
                      <Typography sx={{
                        fontSize: "0.78rem",
                        color: "var(--dm-muted, rgba(0,0,0,0.55))",
                        lineHeight: 1.6,
                      }}>
                        {addon.description}
                      </Typography>
                    </Box>
                  </Box>

                  {isLoading && (
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mt: 2, pl: 7.5 }}>
                      <CircularProgress size={14} sx={{ color: addon.color }} />
                      <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.55))" }}>
                        Connecting...
                      </Typography>
                    </Box>
                  )}

                  {isEnabled && status === 'needs_auth' && !isLoading && (
                    <Box sx={{ mt: 1.5, pl: 7.5 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => { window.location.href = addonAuthUrl[addon.id]; }}
                        startIcon={<KeyRound size={13} />}
                        sx={{
                          fontSize: "0.72rem",
                          textTransform: "none",
                          borderColor: "var(--dm-border, rgba(0,0,0,0.15))",
                          color: "var(--dm-text, #1a1a1a)",
                          "&:hover": {
                            borderColor: addon.color,
                            backgroundColor: `${addon.color}10`,
                          },
                        }}
                      >
                        Authorize
                      </Button>
                    </Box>
                  )}

                  {isEnabled && status === 'error' && !isLoading && (
                    <Box sx={{ mt: 1.5, pl: 7.5 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => loadAddonTools(addon)}
                        startIcon={<RefreshCw size={13} />}
                        sx={{
                          fontSize: "0.72rem",
                          textTransform: "none",
                          borderColor: "rgba(198, 40, 40, 0.3)",
                          color: "#c62828",
                          "&:hover": {
                            borderColor: "#c62828",
                            backgroundColor: "rgba(198, 40, 40, 0.06)",
                          },
                        }}
                      >
                        Retry
                      </Button>
                    </Box>
                  )}

                  {isEnabled && status === 'connected' && tools.length > 0 && (
                    <Collapse in={true}>
                      <Box sx={{ mt: 2, pl: 7.5, display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                        {tools.map((tool) => (
                          <Chip
                            key={tool.name}
                            icon={<Wrench size={12} />}
                            label={tool.name}
                            size="small"
                            sx={{
                              height: 26,
                              fontSize: "0.72rem",
                              fontWeight: 500,
                              backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.03))",
                              border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                              color: "var(--dm-text, #1a1a1a)",
                              "& .MuiChip-icon": { color: addon.color, ml: 0.5 },
                            }}
                          />
                        ))}
                      </Box>
                    </Collapse>
                  )}
                </Box>
              );
            })}
          </Box>
        </Box>
      )}

      {/* Custom Tools tab */}
      {activeTabId === "custom" && (
        <Box>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
        <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.55))", fontSize: "0.8rem" }}>
          Connect MCP tools to extend AI capabilities.
        </Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<Plus size={16} />}
          onClick={() => setShowAddForm(true)}
          sx={{ flexShrink: 0, ml: 2 }}
        >
          Add Tool
        </Button>
      </Box>

      {/* Add Tool Form — single component handles state, validation, test, OAuth discovery */}
      {showAddForm && (
        <Box
          sx={{
            border: "1px dashed var(--dm-border, rgba(0,0,0,0.2))",
            borderRadius: 2,
            p: 2,
            mb: 2,
            mt: 2,
          }}
        >
          <ToolForm
            mode="add"
            onSave={handleAddServer}
            onCancel={() => {
              setShowAddForm(false);
              mcpService.servers.delete('test-new');
            }}
          />
        </Box>
      )}

      {/* Server List */}
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3, mt: 2 }}>
        {servers.map((server) => (
          <Box
            key={server.id}
            id={`mcp-server-${server.id}`}
            sx={{
              border: focusedServerId === server.id
                ? "2px solid rgba(255, 152, 0, 0.7)"
                : "1px solid var(--dm-border, rgba(0,0,0,0.1))",
              borderRadius: 1.5,
              overflow: "hidden",
              backgroundColor: focusedServerId === server.id
                ? "rgba(255, 152, 0, 0.04)"
                : (server.enabled ? "var(--dm-surface, white)" : "var(--dm-subtle, rgba(0,0,0,0.02))"),
              transition: "border-color 0.3s ease, background-color 0.3s ease",
              boxShadow: focusedServerId === server.id ? "0 0 0 4px rgba(255, 152, 0, 0.12)" : "none",
            }}
          >
            {/* Server Header */}
            {editingServerId === server.id ? (
              /* Edit Mode — same form as add, prefilled with server values */
              <Box sx={{ p: 2 }}>
                <ToolForm
                  mode="edit"
                  initialValues={server}
                  onSave={handleSaveEdit}
                  onCancel={handleCancelEdit}
                />
              </Box>
            ) : (
              /* View Mode */
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 2,
                  p: 2,
                  cursor: "pointer",
                  "&:hover": { backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))" }
                }}
                onClick={() => handleToggleExpand(server.id)}
              >
                <Box onClick={(e) => e.stopPropagation()} sx={{ flexShrink: 0, display: 'flex', alignItems: 'center' }}>
                  <IOSSwitch
                    checked={!!server.enabled}
                    onChange={(e) => handleToggleServer(server.id, e.target.checked)}
                    sx={{ transform: 'scale(0.75)' }}
                  />
                </Box>

                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography sx={{
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}>{server.name}</Typography>
                  <Typography variant="caption" sx={{
                    color: "var(--dm-muted, rgba(0,0,0,0.5))",
                    fontFamily: "monospace",
                    fontSize: "0.7rem",
                    display: "block",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}>
                    {server.endpoint}
                  </Typography>
                </Box>

                {/* Actions — never shrink */}
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, flexShrink: 0 }}>
                  {/* Tools count - show when collapsed and tools are loaded */}
                  {!expandedServers[server.id] && serverTools[server.id]?.length > 0 && (
                    <Typography variant="caption" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.5))", mr: 0.5, whiteSpace: "nowrap" }}>
                      {enabledTools.filter(t => t.startsWith(`${server.id}:`)).length}/{serverTools[server.id].length} tools
                    </Typography>
                  )}

                  {serverStatus[server.id] === 'connected' && (
                    <Chip
                      icon={<Plug size={14} />}
                      label="Connected"
                      size="small"
                      sx={{ height: 24, backgroundColor: "rgba(46, 125, 50, 0.1)", color: "#2e7d32", "& .MuiChip-icon": { fontSize: 14, ml: 0.5, color: "#2e7d32" } }}
                    />
                  )}
                  {serverStatus[server.id] === 'error' && (
                    <Chip
                      icon={<Unplug size={14} />}
                      label="Unable to connect"
                      size="small"
                      sx={{ height: 24, backgroundColor: "rgba(198, 40, 40, 0.1)", color: "#c62828", "& .MuiChip-icon": { fontSize: 14, ml: 0.5, color: "#c62828" } }}
                    />
                  )}
                  {/* OAuth 2.1 authorization status — only shown for oauth2.1 servers */}
                  {server.authType === 'oauth2.1' && oauth21Status[server.id] === 'needs_auth' && (
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<KeyRound size={14} />}
                      onClick={(e) => {
                        e.stopPropagation();
                        const returnTo = window.location.pathname + window.location.search;
                        window.location.href = `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(server.endpoint)}&returnTo=${encodeURIComponent(returnTo)}`;
                      }}
                      sx={{
                        height: 26,
                        textTransform: "none",
                        borderColor: "rgba(255, 152, 0, 0.4)",
                        color: "#e65100",
                        fontSize: "0.72rem",
                        fontWeight: 500,
                        "&:hover": { borderColor: "#e65100", backgroundColor: "rgba(255, 152, 0, 0.08)" },
                      }}
                    >
                      Authorize
                    </Button>
                  )}
                  {server.authType === 'oauth2.1' && oauth21Status[server.id] === 'authorized' && (
                    <Tooltip title="Re-authorize">
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          const returnTo = window.location.pathname + window.location.search;
                          window.location.href = `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(server.endpoint)}&returnTo=${encodeURIComponent(returnTo)}`;
                        }}
                        sx={{ color: "rgba(46, 125, 50, 0.7)" }}
                      >
                        <KeyRound size={15} />
                      </IconButton>
                    </Tooltip>
                  )}
                  {loadingServers[server.id] && (
                    <CircularProgress size={18} />
                  )}

                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleStartEdit(server);
                    }}
                    title="Edit tool"
                  >
                    <Pencil size={16} />
                  </IconButton>

                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      loadServerTools(server);
                    }}
                    title="Refresh tools"
                  >
                    <RefreshCw size={16} />
                  </IconButton>

                  <IconButton
                    size="small"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemoveServer(server.id);
                    }}
                    title="Remove tool"
                    sx={{ color: "error.main" }}
                  >
                    <Trash2 size={16} />
                  </IconButton>

                  {expandedServers[server.id] ? (
                    <ChevronDown size={18} style={{ color: "var(--dm-muted, rgba(0,0,0,0.4))" }} />
                  ) : (
                    <ChevronRight size={18} style={{ color: "var(--dm-muted, rgba(0,0,0,0.4))" }} />
                  )}
                </Box>
              </Box>
            )}

            {/* Tools List (Expanded) */}
            <Collapse in={expandedServers[server.id]}>
              <Box sx={{ px: 2, pb: 2, pt: 0 }}>
                {loadingServers[server.id] ? (
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1, py: 2 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>
                      Loading tools...
                    </Typography>
                  </Box>
                ) : serverTools[server.id]?.length > 0 ? (
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                    {serverTools[server.id].map((tool) => (
                      <Box
                        key={tool.name}
                        sx={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 2,
                          p: 1.5,
                          backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                          borderRadius: 1
                        }}
                      >
                        <Checkbox
                          size="small"
                          checked={isToolEnabled(server.id, tool.name)}
                          onChange={(e) => handleToggleTool(server.id, tool.name, e.target.checked)}
                          sx={{
                            p: 0.5,
                            mt: 0.25,
                            color: "var(--dm-muted, rgba(0,0,0,0.3))",
                            "&.Mui-checked": { color: "var(--dm-text, #1a1a1a)" },
                          }}
                        />
                        <Box sx={{ flex: 1 }}>
                          <Typography sx={{ fontWeight: 500, fontSize: "0.9rem" }}>
                            {tool.name}
                          </Typography>
                          <Typography variant="caption" sx={{ color: "var(--dm-text, rgba(0,0,0,0.6))" }}>
                            {tool.description}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                ) : serverStatus[server.id] === 'error' ? (
                  <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.5))", py: 1 }}>
                    Unable to connect. Please verify the endpoint URL is correct.
                  </Typography>
                ) : (
                  <Typography variant="body2" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.5))", py: 1 }}>
                    No tools available
                  </Typography>
                )}
              </Box>
            </Collapse>
          </Box>
        ))}

        {servers.length === 0 && !showAddForm && (
          <Box sx={{ textAlign: "center", py: 6, color: "var(--dm-muted, rgba(0,0,0,0.4))" }}>
            <Wrench size={40} strokeWidth={1.5} style={{ marginBottom: 12, opacity: 0.5 }} />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>No MCP tools configured</Typography>
            <Typography variant="caption">Add a tool to extend AI capabilities</Typography>
          </Box>
        )}
      </Box>
      </Box>
      )}

        </motion.div>
      </AnimatePresence>

      {/* Feedback for save/update operations */}
      <Snackbar
        open={!!toast}
        autoHideDuration={4000}
        onClose={() => setToast(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        {toast ? (
          <Alert
            severity={toast.severity || 'success'}
            onClose={() => setToast(null)}
            variant="filled"
            sx={{ fontSize: '0.85rem' }}
          >
            {toast.message}
          </Alert>
        ) : null}
      </Snackbar>
    </motion.div>
  );
}
