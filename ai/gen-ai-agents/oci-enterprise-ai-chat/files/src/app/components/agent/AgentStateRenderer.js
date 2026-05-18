"use client";

import { Box, Chip, CircularProgress, Stack, Tooltip, Typography, Collapse, IconButton, Paper } from "@mui/material";
import { 
  Error as ErrorIcon, 
  CheckCircle as CheckCircleIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Build as BuildIcon
} from "@mui/icons-material";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import TypingEffect from "./ui/TypingEffect";
import { useState } from "react";
import JsonView from '@uiw/react-json-view';

// Common chip styles
const chipStyles = {
  height: 'auto',
  fontSize: '0.85em !important',
  padding: '0.25rem 0.75rem',
  borderRadius: '100px',
  width: 'fit-content',
  animation: 'slideInLeft 0.4s ease-out',
  cursor: 'pointer',
  '@keyframes slideInLeft': {
    '0%': {
      transform: 'translateX(-20px)',
      opacity: 0
    },
    '100%': {
      transform: 'translateX(0)',
      opacity: 1
    }
  },
  '& .MuiChip-icon': {
    fontSize: '0.85em !important'
  },
  '& .MuiChip-label': {
    fontSize: '0.85em !important',
    display: 'flex',
    alignItems: 'center',
    gap: 0.5
  }
};

// Common text styles
const textStyles = {
  fontSize: "inherit", 
  fontWeight: "inherit",
  opacity: 0.7
};

// Expandable chip component
const ExpandableChip = ({ icon, label, color, variant, content, sx = {} }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <Box>
      <Chip
        icon={icon}
        label={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            {label}
            {content && (
              expanded ? <ExpandLessIcon sx={{ fontSize: '1em' }} /> : <ExpandMoreIcon sx={{ fontSize: '1em' }} />
            )}
          </Box>
        }
        color={color}
        variant={variant}
        onClick={() => content && setExpanded(!expanded)}
        sx={{ ...chipStyles, ...sx }}
      />
      {content && (
        <Collapse in={expanded}>
          <Paper 
            elevation={0}
            sx={{ 
              mt: 1, 
              p: 2, 
              backgroundColor: 'rgba(0, 0, 0, 0.02)',
              border: '1px solid rgba(0, 0, 0, 0.08)',
              borderRadius: 2,
              fontSize: '13px !important',
              '& *': {
                fontSize: '13px !important'
              }
            }}
          >
            {typeof content === 'string' ? (
              <Typography sx={{ fontSize: '13px !important', fontFamily: 'monospace' }}>
                {content}
              </Typography>
            ) : (
              <Box>
                <JsonView 
                  value={content}
                  collapsed={1}
                  style={{
                    backgroundColor: 'transparent',
                    fontSize: '13px'
                  }}
                />
              </Box>
            )}
          </Paper>
        </Collapse>
      )}
    </Box>
  );
};

const AgentStateRenderer = ({ states }) => {
  // Remove consecutive duplicate states
  const dedupedStates = states.filter((state, index) => {
    if (index === 0) return true;
    const prev = states[index - 1];
    
    // Compare states for equality (excluding text type which should accumulate)
    if (state.type === 'text') return true;
    
    return !(
      state.trace === prev.trace &&
      state.error === prev.error &&
      state.done === prev.done &&
      state.tool_use === prev.tool_use &&
      state.message === prev.message &&
      state.type === prev.type
    );
  });

  // Simple helper to check if trace is completed (has something after it)
  const isTraceCompleted = (index) => {
    return index < dedupedStates.length - 1 && 
           dedupedStates.slice(index + 1).some(s => s.done || s.type === 'text' || s.type === 'error' || s.trace);
  };

  // Render different types of components
  const renderErrorChip = (content, key) => (
    <Box key={key} sx={{ display: 'flex' }}>
      <ExpandableChip
        icon={<ErrorIcon />}
        label="Error"
        color="error"
        variant="outlined"
        content={content}
      />
    </Box>
  );

  const renderTraceChip = (trace, message, isCompleted, key) => {
    const isConnecting = trace === 'connecting';
    const customStyles = isConnecting ? {
      animation: 'slideInLeft 0.4s ease-out 0.5s both',
    } : {};
    
    const label = trace.charAt(0).toUpperCase() + trace.slice(1);
    
    return (
      <Box key={key} sx={{ display: 'flex' }}>
        <ExpandableChip
          icon={isCompleted ? <CheckCircleIcon /> : <CircularProgress size={16} />}
          label={label}
          color={isCompleted ? "success" : "default"}
          variant="outlined"
          content={message}
          sx={customStyles}
        />
      </Box>
    );
  };

  const renderToolUse = (toolData, key) => {
    const toolName = toolData.tool || 'Unknown Tool';
    const status = toolData.status || 'executing';
    const isCompleted = status === 'completed';
    
    const label = isCompleted 
      ? `Tool response: ${toolName}`
      : `Calling tool: ${toolName}`;
    
    return (
      <Box key={key} sx={{ display: 'flex' }}>
        <ExpandableChip
          icon={isCompleted ? <CheckCircleIcon /> : <BuildIcon />}
          label={label}
          color={isCompleted ? "success" : "primary"}
          variant="outlined"
          content={toolData}
        />
      </Box>
    );
  };

  const renderText = (content, key) => (
    <Typography key={key} component="div" sx={textStyles}>
      {content}
    </Typography>
  );

  const renderMarkdown = (text, key) => (
    <Box key={key} sx={{
      '& table': {
        borderCollapse: 'collapse',
        width: '100%',
        marginBottom: 2
      },
      '& th, & td': {
        border: '1px solid #ddd',
        padding: '8px',
        textAlign: 'left'
      },
      '& th': {
        backgroundColor: '#f5f5f5',
        fontWeight: 'bold'
      }
    }}>
      <TypingEffect text={text} speed={5}>
        {(text) => (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {text}
          </ReactMarkdown>
        )}
      </TypingEffect>
    </Box>
  );
  
  // Process states and build elements array
  let currentTextBlock = "";
  const elements = [];
  
  const flushTextBlock = () => {
    if (currentTextBlock) {
      elements.push(renderMarkdown(currentTextBlock, `text-${elements.length}`));
      currentTextBlock = "";
    }
  };

  dedupedStates.forEach((state, index) => {
    // Accumulate text chunks
    if (state.type === 'text') {
      currentTextBlock += state.content;
      return;
    }
    
    // Flush any accumulated text before rendering other elements
    flushTextBlock();
    
    // Render based on state type
    if (state.type === 'error') {
      elements.push(renderErrorChip(state.content, `error-${index}`));
    } else if (state.error) {
      elements.push(renderErrorChip(state.error, `stream-error-${index}`));
    } else if (state.done) {
      // Skip done states - they're used only for clock status
    } else if (state.trace) {
      elements.push(renderTraceChip(state.trace, state.message, isTraceCompleted(index), `trace-${index}`));
    } else if (state.tool_use) {
      elements.push(renderToolUse(state.tool_use, `tool-${index}`));
    } else if (state.message) {
      elements.push(renderText(state.message, `message-${index}`));
    } else if (Object.keys(state).length > 0) {
      elements.push(renderText(JSON.stringify(state), `unknown-${index}`));
    }
  });
  
  // Flush any remaining text
  flushTextBlock();
  
  return <Stack spacing={2} sx={{ overflow: 'visible' }}>{elements}</Stack>;
};


export default AgentStateRenderer;