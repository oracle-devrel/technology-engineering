"use client";

import { ArrowLeft, Plus, Trash2, Save, MessageSquare, Wrench, MousePointer, Edit2, Check, X } from "lucide-react";
import ChipEditor from "../../../components/settings/flows/ChipEditor";
import InteractiveEditor from "../../../components/settings/flows/InteractiveEditor";
import TextEditor from "../../../components/settings/flows/TextEditor";
import VerticalTabs from "../../../components/ui/VerticalTabs";
import { Box, IconButton, TextField, Typography, Button, Card, List, ListItem, ListItemText, ToggleButton, ToggleButtonGroup, Switch, FormControlLabel } from "@mui/material";
import { useRouter, useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { getAllMockFlows } from "../../../services/mockService";

const STORAGE_KEYS = {
  FLOWS: 'customAgentFlows'
};

export default function FlowDetail() {
  const router = useRouter();
  const params = useParams();
  const flowId = params.id;
  
  const [flow, setFlow] = useState(null);
  const [editedFlow, setEditedFlow] = useState(null);
  const [newMessage, setNewMessage] = useState({ type: "text", content: "", delay: 100 });
  const [newInteractiveData, setNewInteractiveData] = useState({ 
    title: "", 
    options: []
  });
  const [newChipData, setNewChipData] = useState({
    label: "",
    status: "info",
    icon: "Brain", 
    content: ""
  });
  const [newTriggerPhrase, setNewTriggerPhrase] = useState("");
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editingMessageValue, setEditingMessageValue] = useState({ content: "", delay: 100 });
  const [editingInteractiveData, setEditingInteractiveData] = useState({ title: "", options: [] });
  const [editingChipData, setEditingChipData] = useState({ label: "", status: "info", icon: "Brain", content: "" });
  const [activeTab, setActiveTab] = useState(0);
  const [showAddMessage, setShowAddMessage] = useState(false);

  useEffect(() => {
    // Load flows from localStorage or original
    const originalFlows = getAllMockFlows();
    let flows = originalFlows;
    
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEYS.FLOWS);
      if (stored) {
        try {
          flows = JSON.parse(stored);
        } catch (e) {
          console.error('Error parsing stored flows:', e);
        }
      }
    }
    
    // Find the specific flow
    const foundFlow = flows.find(f => f.id === flowId);
    if (foundFlow) {
      setFlow(foundFlow);
      setEditedFlow(JSON.parse(JSON.stringify(foundFlow))); // Deep clone
    }
  }, [flowId]);

  const handleSave = () => {
    if (!editedFlow) return;
    
    // Load current flows
    const originalFlows = getAllMockFlows();
    let flows = originalFlows;
    
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem(STORAGE_KEYS.FLOWS);
      if (stored) {
        try {
          flows = JSON.parse(stored);
        } catch (e) {
          console.error('Error parsing stored flows:', e);
        }
      }
      
      // Update the flow
      const index = flows.findIndex(f => f.id === flowId);
      if (index !== -1) {
        flows[index] = editedFlow;
      } else {
        // New flow
        flows.push(editedFlow);
      }
      
      // Save to localStorage
      localStorage.setItem(STORAGE_KEYS.FLOWS, JSON.stringify(flows));
      
      // Navigate back
      router.push('/settings');
    }
  };

  const handleAddTriggerPhrase = () => {
    if (newTriggerPhrase.trim() && editedFlow) {
      setEditedFlow({
        ...editedFlow,
        triggerPhrases: [...(editedFlow.triggerPhrases || []), newTriggerPhrase.trim()]
      });
      setNewTriggerPhrase("");
    }
  };

  const handleDeleteTriggerPhrase = (index) => {
    if (editedFlow) {
      setEditedFlow({
        ...editedFlow,
        triggerPhrases: editedFlow.triggerPhrases.filter((_, i) => i !== index)
      });
    }
  };

  const handleAddMessage = () => {
    if ((newMessage.type === 'interactive' && newInteractiveData.options.length > 0) || 
        (newMessage.type === 'chip' && newChipData.label.trim()) ||
        (newMessage.type === 'text' && newMessage.content.trim()) && editedFlow) {
      const message = {
        ...newMessage,
        delay: parseInt(newMessage.delay) || 100
      };
      
      // Configure message based on type
      if (message.type === "chip") {
        message.chipData = {
          label: newChipData.label,
          status: newChipData.status,
          icon: newChipData.icon,
          content: newChipData.content
        };
      } else if (message.type === "interactive") {
        message.interactiveData = {
          inputType: "choice",
          title: newInteractiveData.title,
          options: newInteractiveData.options.map(opt => ({
            value: opt.label.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, ''),
            label: opt.label,
            type: "action"
          }))
        };
      } else {
        message.content = newMessage.content.trim();
      }
      
      setEditedFlow({
        ...editedFlow,
        messages: [...(editedFlow.messages || []), message]
      });
      setNewMessage({ type: "text", content: "", delay: 100 });
      setNewInteractiveData({ title: "", options: [] });
      setNewChipData({ label: "", status: "info", icon: "Brain", content: "" });
      setShowAddMessage(false);
    }
  };

  const handleDeleteMessage = (index) => {
    if (editedFlow) {
      setEditedFlow({
        ...editedFlow,
        messages: editedFlow.messages.filter((_, i) => i !== index)
      });
    }
  };

  const handleEditMessage = (index) => {
    const message = editedFlow.messages[index];
    setEditingMessageIndex(index);
    
    if (message.type === 'interactive') {
      setEditingInteractiveData({
        title: message.interactiveData?.title || '',
        options: message.interactiveData?.options || []
      });
      setEditingMessageValue({ content: '', delay: message.delay || 100 });
    } else if (message.type === 'chip') {
      setEditingChipData({
        label: message.chipData?.label || '',
        status: message.chipData?.status || 'info',
        icon: message.chipData?.icon || 'Brain',
        content: message.chipData?.content || ''
      });
      setEditingMessageValue({ content: '', delay: message.delay || 100 });
    } else {
      setEditingMessageValue({
        content: message.content || '',
        delay: message.delay || 100
      });
    }
  };

  const handleSaveMessage = () => {
    if (editedFlow && editingMessageIndex !== null) {
      const newMessages = [...editedFlow.messages];
      const message = newMessages[editingMessageIndex];
      
      if (message.type === 'chip') {
        message.chipData = {
          label: editingChipData.label,
          status: editingChipData.status,
          icon: editingChipData.icon,
          content: editingChipData.content
        };
      } else if (message.type === 'interactive') {
        message.interactiveData = {
          inputType: "choice",
          title: editingInteractiveData.title,
          options: editingInteractiveData.options.map(opt => ({
            value: opt.label.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, ''),
            label: opt.label,
            type: "action"
          }))
        };
      } else {
        message.content = editingMessageValue.content;
      }
      message.delay = parseInt(editingMessageValue.delay) || 100;
      
      setEditedFlow({
        ...editedFlow,
        messages: newMessages
      });
      setEditingMessageIndex(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditingMessageValue({ content: "", delay: 100 });
    setEditingInteractiveData({ title: "", options: [] });
    setEditingChipData({ label: "", status: "info", icon: "Brain", content: "" });
  };

  const handleMessageChange = (index, field, value) => {
    if (editedFlow) {
      const newMessages = [...editedFlow.messages];
      if (field === 'content' && newMessages[index].type === 'chip') {
        if (!newMessages[index].chipData) {
          newMessages[index].chipData = {};
        }
        newMessages[index].chipData.content = value;
      } else if (field === 'delay') {
        newMessages[index].delay = value;
      } else {
        newMessages[index][field] = value;
      }
      setEditedFlow({
        ...editedFlow,
        messages: newMessages
      });
    }
  };

  if (!flow || !editedFlow) {
    return (
      <Box sx={{ p: 4 }}>
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        width: "100%",
        backgroundImage: "url('/backgrounds/white-red-background.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        p: 4,
      }}
    >
      <Box sx={{ maxWidth: "900px", mx: "auto" }}>
        {/* Header */}
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 4 }}>
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <IconButton
              onClick={() => router.push("/settings")}
              sx={{
                mr: 2,
                color: "rgba(0, 0, 0, 0.6)",
                "&:hover": {
                  backgroundColor: "rgba(0, 0, 0, 0.04)",
                },
              }}
            >
              <ArrowLeft size={20} />
            </IconButton>
            <Typography
              variant="h4"
              sx={{
                fontSize: { xs: "1.5rem", sm: "2rem" },
                fontWeight: 300,
                color: "#1a1a1a",
                fontFamily: "var(--font-oracle-sans), sans-serif",
              }}
            >
              Edit Flow
            </Typography>
          </Box>
          <Button
            startIcon={<Save size={18} />}
            onClick={handleSave}
            variant="contained"
            sx={{
              textTransform: "none",
              backgroundColor: "#1a1a1a",
              "&:hover": {
                backgroundColor: "#333",
              },
            }}
          >
            Save Changes
          </Button>
        </Box>

        {/* Vertical tabs layout */}
        <VerticalTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          tabs={["General", "Messages"]}
          tabsWidth="220px"
        >
          {activeTab === 0 && (
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 3 }}>
                <Typography variant="h6" sx={{ fontSize: "1.1rem", fontWeight: 400 }}>
                  General
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={!editedFlow.isDisabled}
                      onChange={(e) => setEditedFlow({ ...editedFlow, isDisabled: !e.target.checked })}
                      size="small"
                      sx={{
                        "& .MuiSwitch-switchBase.Mui-checked": {
                          color: "#1a1a1a",
                        },
                        "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                          backgroundColor: "#1a1a1a",
                        },
                      }}
                    />
                  }
                  label={editedFlow.isDisabled ? "Disabled" : "Active"}
                  sx={{ 
                    margin: 0, 
                    "& .MuiFormControlLabel-label": {
                      fontSize: "0.85rem",
                      color: editedFlow.isDisabled ? "rgba(0, 0, 0, 0.4)" : "#1a1a1a"
                    }
                  }}
                />
              </Box>
              
              {/* Basic Information */}
              <Card sx={{ p: 3, mb: 3, backgroundColor: "rgba(255, 255, 255, 0.7)", backdropFilter: "blur(10px)" }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontSize: "1rem", fontWeight: 500 }}>
                  Basic Information
                </Typography>
                <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                  <TextField
                    label="Flow ID"
                    value={editedFlow.id || ""}
                    disabled
                    fullWidth
                    variant="outlined"
                    size="small"
                  />
                  <TextField
                    label="Flow Name"
                    value={editedFlow.name || ""}
                    onChange={(e) => setEditedFlow({ ...editedFlow, name: e.target.value })}
                    fullWidth
                    variant="outlined"
                    size="small"
                  />
                </Box>
              </Card>
              
              {/* Trigger Phrases */}
              <Card sx={{ p: 3, backgroundColor: "rgba(255, 255, 255, 0.7)", backdropFilter: "blur(10px)" }}>
                <Typography variant="subtitle1" sx={{ mb: 2, fontSize: "1rem", fontWeight: 500 }}>
                  Trigger Phrases
                </Typography>
                <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
                  <TextField
                    value={newTriggerPhrase}
                    onChange={(e) => setNewTriggerPhrase(e.target.value)}
                    placeholder="Add trigger phrase..."
                    variant="outlined"
                    size="small"
                    fullWidth
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleAddTriggerPhrase();
                    }}
                  />
                  <Button
                    onClick={handleAddTriggerPhrase}
                    variant="outlined"
                    size="small"
                    sx={{ minWidth: "auto" }}
                  >
                    <Plus size={18} />
                  </Button>
                </Box>
                
                <List sx={{ p: 0 }}>
                  {editedFlow.triggerPhrases?.map((phrase, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        px: 2,
                        py: 1,
                        mb: 1,
                        backgroundColor: "rgba(0, 0, 0, 0.02)",
                        borderRadius: 1,
                      }}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={() => handleDeleteTriggerPhrase(index)}
                          sx={{ color: "rgba(0, 0, 0, 0.4)" }}
                        >
                          <Trash2 size={16} />
                        </IconButton>
                      }
                    >
                      <ListItemText primary={phrase} />
                    </ListItem>
                  ))}
                </List>
              </Card>
            </Box>
          )}

          {activeTab === 1 && (
            <Box>
              <Typography variant="h6" sx={{ mb: 3, fontSize: "1.1rem", fontWeight: 400 }}>
                Messages ({editedFlow.messages?.length || 0})
              </Typography>
              <Card sx={{ p: 3, backgroundColor: "rgba(255, 255, 255, 0.7)", backdropFilter: "blur(10px)" }}>
          
          {/* Add New Message */}
          {!showAddMessage ? (
            <Box sx={{ display: "flex", justifyContent: "center", mb: 2 }}>
              <Button
                startIcon={<Plus size={18} />}
                onClick={() => setShowAddMessage(true)}
                variant="outlined"
                sx={{
                  textTransform: "none",
                  color: "rgba(0, 0, 0, 0.6)",
                  borderColor: "rgba(0, 0, 0, 0.2)",
                  "&:hover": {
                    backgroundColor: "rgba(0, 0, 0, 0.04)",
                  },
                }}
              >
                Add Message
              </Button>
            </Box>
          ) : (
            <Box sx={{ p: 2, mb: 2, backgroundColor: "rgba(0, 0, 0, 0.02)", borderRadius: 1 }}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ mb: 1, fontSize: "0.9rem", fontWeight: 500 }}>
                Message Type
              </Typography>
              <ToggleButtonGroup
                value={newMessage.type}
                exclusive
                onChange={(e, newType) => {
                  if (newType) {
                    setNewMessage({ ...newMessage, type: newType });
                    // Auto-populate data with examples when switching types
                    if (newType === 'interactive' && newInteractiveData.options.length === 0) {
                      setNewInteractiveData({
                        title: "What would you like to do?",
                        options: [
                          { label: "Proceed with order" },
                          { label: "Request more information" },
                          { label: "Cancel request" }
                        ]
                      });
                    } else if (newType === 'chip' && newChipData.label === "") {
                      setNewChipData({
                        label: "Planning",
                        status: "info",
                        icon: "Brain",
                        content: "Analyzing the request and preparing the appropriate response..."
                      });
                    } else if (newType !== 'interactive') {
                      // Reset interactive data when switching away from interactive
                      setNewInteractiveData({ title: "", options: [] });
                    }
                    if (newType !== 'chip') {
                      // Reset chip data when switching away from chip
                      setNewChipData({ label: "", status: "info", icon: "Brain", content: "" });
                    }
                  }
                }}
                sx={{ width: "100%" }}
              >
                <ToggleButton 
                  value="text" 
                  sx={{ 
                    flex: 1, 
                    py: 1.5,
                    textTransform: "none",
                    display: "flex",
                    flexDirection: "column",
                    gap: 0.5,
                    "&.Mui-selected": {
                      backgroundColor: "rgba(26, 26, 26, 0.08)",
                    }
                  }}
                >
                  <MessageSquare size={20} />
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>AI Response</Typography>
                  <Typography variant="caption" sx={{ fontSize: "0.7rem", color: "rgba(0, 0, 0, 0.6)" }}>
                    Regular text
                  </Typography>
                </ToggleButton>
                <ToggleButton 
                  value="chip" 
                  sx={{ 
                    flex: 1, 
                    py: 1.5,
                    textTransform: "none",
                    display: "flex",
                    flexDirection: "column",
                    gap: 0.5,
                    "&.Mui-selected": {
                      backgroundColor: "rgba(26, 26, 26, 0.08)",
                    }
                  }}
                >
                  <Wrench size={20} />
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>Tool/Planning</Typography>
                  <Typography variant="caption" sx={{ fontSize: "0.7rem", color: "rgba(0, 0, 0, 0.6)" }}>
                    Status chips
                  </Typography>
                </ToggleButton>
                <ToggleButton 
                  value="interactive" 
                  sx={{ 
                    flex: 1, 
                    py: 1.5,
                    textTransform: "none",
                    display: "flex",
                    flexDirection: "column",
                    gap: 0.5,
                    "&.Mui-selected": {
                      backgroundColor: "rgba(26, 26, 26, 0.08)",
                    }
                  }}
                >
                  <MousePointer size={20} />
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>User Options</Typography>
                  <Typography variant="caption" sx={{ fontSize: "0.7rem", color: "rgba(0, 0, 0, 0.6)" }}>
                    Clickable choices
                  </Typography>
                </ToggleButton>
              </ToggleButtonGroup>
            </Box>
            
            <Box sx={{ display: "flex", gap: 2, mb: 2, alignItems: "flex-end" }}>
              <TextField
                label="Delay (ms)"
                type="number"
                value={newMessage.delay}
                onChange={(e) => setNewMessage({ ...newMessage, delay: e.target.value })}
                size="small"
                sx={{ width: 120 }}
              />
              <Typography variant="body2" sx={{ fontSize: "0.85rem", color: "rgba(0, 0, 0, 0.6)", flex: 1 }}>
                {newMessage.type === 'text' && "Regular text response from the AI assistant"}
                {newMessage.type === 'chip' && "Shows AI actions like 'Searching database' or 'Planning'"}
                {newMessage.type === 'interactive' && "Presents buttons for user to click"}
              </Typography>
            </Box>
            {newMessage.type === 'chip' ? (
              <ChipEditor
                chipData={newChipData}
                onChipDataChange={setNewChipData}
                onSave={handleAddMessage}
                showSaveButton={false}
              />
            ) : newMessage.type === 'interactive' ? (
              <InteractiveEditor
                interactiveData={newInteractiveData}
                onInteractiveDataChange={setNewInteractiveData}
                onSave={handleAddMessage}
                showSaveButton={false}
              />
            ) : (
              <TextEditor
                content={newMessage.content}
                onContentChange={(content) => setNewMessage({ ...newMessage, content })}
                onSave={handleAddMessage}
                showSaveButton={false}
              />
            )}
            
            {/* Form buttons */}
            <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1, mt: 2 }}>
              <Button
                onClick={() => {
                  setShowAddMessage(false);
                  setNewMessage({ type: "text", content: "", delay: 100 });
                  setNewInteractiveData({ title: "", options: [] });
                  setNewChipData({ label: "", status: "info", icon: "Brain", content: "" });
                }}
                variant="outlined"
                size="small"
                sx={{ 
                  textTransform: "none",
                  color: "rgba(0, 0, 0, 0.6)",
                  borderColor: "rgba(0, 0, 0, 0.2)"
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddMessage}
                variant="contained"
                size="small"
                sx={{
                  textTransform: "none",
                  backgroundColor: "#1a1a1a",
                  "&:hover": {
                    backgroundColor: "#333",
                  },
                }}
              >
                Add Message
              </Button>
            </Box>
          </Box>
          )}
          
          {/* Messages List */}
          <List sx={{ p: 0 }}>
            {editedFlow.messages?.map((message, index) => (
              <Box
                key={index}
                sx={{
                  p: 2,
                  mb: 2,
                  backgroundColor: "rgba(0, 0, 0, 0.02)",
                  borderRadius: 1,
                  border: "1px solid rgba(0, 0, 0, 0.08)",
                }}
              >
                {editingMessageIndex === index ? (
                  // Edit mode
                  <>
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1.5 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        {message.type === 'text' && <MessageSquare size={16} />}
                        {message.type === 'chip' && <Wrench size={16} />}
                        {message.type === 'interactive' && <MousePointer size={16} />}
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {message.type === 'text' ? 'AI Response' : 
                           message.type === 'chip' ? 'Tool/Planning' : 
                           message.type === 'interactive' ? 'User Options' : 
                           message.type}
                        </Typography>
                      </Box>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        <TextField
                          value={editingMessageValue.delay}
                          onChange={(e) => setEditingMessageValue({ ...editingMessageValue, delay: e.target.value })}
                          type="number"
                          size="small"
                          variant="outlined"
                          label="Delay (ms)"
                          sx={{ width: 100 }}
                        />
                        <IconButton
                          size="small"
                          onClick={handleSaveMessage}
                          sx={{ color: "green" }}
                        >
                          <Check size={18} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={handleCancelEdit}
                          sx={{ color: "red" }}
                        >
                          <X size={18} />
                        </IconButton>
                      </Box>
                    </Box>
                    {message.type === 'chip' ? (
                      <ChipEditor
                        chipData={editingChipData}
                        onChipDataChange={setEditingChipData}
                        onSave={handleSaveMessage}
                        showSaveButton={false}
                        autoFocus={true}
                      />
                    ) : message.type === 'interactive' ? (
                      <InteractiveEditor
                        interactiveData={editingInteractiveData}
                        onInteractiveDataChange={setEditingInteractiveData}
                        onSave={handleSaveMessage}
                        showSaveButton={false}
                        autoFocus={true}
                      />
                    ) : (
                      <TextEditor
                        content={editingMessageValue.content}
                        onContentChange={(content) => setEditingMessageValue({ ...editingMessageValue, content })}
                        onSave={handleSaveMessage}
                        showSaveButton={false}
                        autoFocus={true}
                      />
                    )}
                  </>
                ) : (
                  // View mode
                  <>
                    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 1 }}>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                        {message.type === 'text' && <MessageSquare size={16} />}
                        {message.type === 'chip' && <Wrench size={16} />}
                        {message.type === 'interactive' && <MousePointer size={16} />}
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {message.type === 'text' ? 'AI Response' : 
                           message.type === 'chip' ? 'Tool/Planning' : 
                           message.type === 'interactive' ? 'User Options' : 
                           message.type}
                        </Typography>
                        <Typography variant="caption" sx={{ color: "rgba(0, 0, 0, 0.5)" }}>
                          • {message.delay || 100}ms
                        </Typography>
                      </Box>
                      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                        <IconButton
                          size="small"
                          onClick={() => handleEditMessage(index)}
                          sx={{ 
                            color: "rgba(0, 0, 0, 0.4)",
                            "&:hover": {
                              color: "rgba(0, 0, 0, 0.7)"
                            }
                          }}
                        >
                          <Edit2 size={16} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDeleteMessage(index)}
                          sx={{ 
                            color: "rgba(0, 0, 0, 0.4)",
                            "&:hover": {
                              color: "red"
                            }
                          }}
                        >
                          <Trash2 size={16} />
                        </IconButton>
                      </Box>
                    </Box>
                    {message.type === 'interactive' ? (
                      <Box>
                        <Typography variant="body2" sx={{ fontSize: "0.9rem", mb: 1 }}>
                          {message.interactiveData?.title || 'No title defined'}
                        </Typography>
                        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                          {message.interactiveData?.options?.map((option, optIndex) => (
                            <Box
                              key={optIndex}
                              sx={{
                                p: 1.5,
                                backgroundColor: "rgba(0, 0, 0, 0.05)",
                                borderRadius: 1,
                                border: "1px solid rgba(0, 0, 0, 0.1)",
                                fontSize: "0.85rem",
                              }}
                            >
                              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 0.5 }}>
                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                  {option.label}
                                </Typography>
                                <Typography 
                                  variant="caption" 
                                  sx={{ 
                                    px: 1, 
                                    py: 0.25, 
                                    backgroundColor: option.type === 'action' ? 'rgba(0,100,0,0.1)' : 
                                                     option.type === 'product' ? 'rgba(0,0,200,0.1)' : 
                                                     'rgba(200,0,0,0.1)',
                                    borderRadius: 0.5,
                                    fontSize: "0.7rem",
                                    fontWeight: 500
                                  }}
                                >
                                  {option.type}
                                </Typography>
                              </Box>
                              <Typography variant="caption" sx={{ color: "rgba(0, 0, 0, 0.6)", fontSize: "0.75rem" }}>
                                Value: {option.value}
                              </Typography>
                              {option.details && (
                                <Typography variant="caption" sx={{ display: "block", mt: 0.5, fontSize: "0.75rem", fontStyle: "italic" }}>
                                  {option.details}
                                </Typography>
                              )}
                            </Box>
                          ))}
                        </Box>
                      </Box>
                    ) : message.type === 'chip' && typeof message.chipData?.content === 'object' ? (
                      <Box>
                        {message.chipData.content.description && (
                          <Typography 
                            variant="body2" 
                            sx={{ 
                              fontSize: "0.9rem",
                              color: "rgba(0, 0, 0, 0.8)",
                              lineHeight: 1.6,
                              mb: 2
                            }}
                          >
                            {message.chipData.content.description}
                          </Typography>
                        )}
                        <Box sx={{ 
                          backgroundColor: "rgba(0, 0, 0, 0.03)", 
                          borderRadius: 1, 
                          p: 2,
                          border: "1px solid rgba(0, 0, 0, 0.08)"
                        }}>
                          {message.chipData.content.function && (
                            <Box sx={{ mb: 1.5 }}>
                              <Typography variant="caption" sx={{ color: "rgba(0, 0, 0, 0.5)", fontWeight: 500 }}>
                                Function
                              </Typography>
                              <Typography variant="body2" sx={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                                {message.chipData.content.function}
                              </Typography>
                            </Box>
                          )}
                          {message.chipData.content.endpoint && (
                            <Box sx={{ mb: 1.5 }}>
                              <Typography variant="caption" sx={{ color: "rgba(0, 0, 0, 0.5)", fontWeight: 500 }}>
                                Endpoint
                              </Typography>
                              <Typography variant="body2" sx={{ 
                                fontFamily: "monospace", 
                                fontSize: "0.75rem",
                                wordBreak: "break-all",
                                color: "rgba(0, 0, 200, 0.8)"
                              }}>
                                {message.chipData.content.endpoint}
                              </Typography>
                            </Box>
                          )}
                          {message.chipData.content.parameters && (
                            <Box>
                              <Typography variant="caption" sx={{ color: "rgba(0, 0, 0, 0.5)", fontWeight: 500 }}>
                                Parameters
                              </Typography>
                              <Box sx={{ 
                                mt: 0.5,
                                p: 1, 
                                backgroundColor: "rgba(0, 0, 0, 0.02)", 
                                borderRadius: 0.5,
                                fontFamily: "monospace",
                                fontSize: "0.75rem",
                                whiteSpace: "pre",
                                overflowX: "auto"
                              }}>
                                {JSON.stringify(message.chipData.content.parameters, null, 2)}
                              </Box>
                            </Box>
                          )}
                        </Box>
                      </Box>
                    ) : (
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          whiteSpace: "pre-wrap",
                          fontSize: "0.9rem",
                          color: "rgba(0, 0, 0, 0.8)",
                          lineHeight: 1.6
                        }}
                      >
                        {message.type === 'chip' ? message.chipData?.content || '' : message.content || ''}
                      </Typography>
                    )}
                  </>
                )}
              </Box>
            ))}
          </List>
              </Card>
            </Box>
          )}
        </VerticalTabs>
      </Box>
    </Box>
  );
}