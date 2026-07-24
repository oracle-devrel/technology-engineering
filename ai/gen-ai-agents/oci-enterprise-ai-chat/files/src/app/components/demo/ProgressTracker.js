"use client";

import React from 'react';
import { Box, Typography, Paper, LinearProgress, Chip } from '@mui/material';
import { CheckCircle2, Clock, Hourglass } from 'lucide-react';

const ProgressTracker = ({ data }) => {
  const { title, items } = data;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'received':
        return <CheckCircle2 size={18} color="#2196f3" />;
      case 'pending':
        return <Hourglass size={18} color="#666" />;
      default:
        return <Clock size={18} color="#666" />;
    }
  };

  const completedCount = items.filter(item => item.status === 'received').length;
  const progressPercentage = (completedCount / items.length) * 100;

  return (
    <Paper 
      variant="outlined"
      sx={{
        mb: 2,
        borderRadius: 1,
        overflow: 'hidden',
        border: '1px solid #e0e0e0'
      }}
    >
      <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
        <Typography variant="h6" sx={{ fontWeight: 500, color: '#1a1a1a', mb: 2 }}>
          {title}
        </Typography>
        
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ color: '#666', fontSize: '0.875rem' }}>
              Progress: {completedCount}/{items.length} responses
            </Typography>
            <Typography variant="body2" sx={{ color: '#666', fontSize: '0.875rem' }}>
              {Math.round(progressPercentage)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={progressPercentage}
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: '#f0f0f0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: '#2196f3',
                borderRadius: 3
              }
            }}
          />
        </Box>
      </Box>

      <Box sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          {items.map((item, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                p: 1.5,
                borderRadius: 1,
                border: '1px solid #f0f0f0',
                backgroundColor: item.status === 'received' ? '#f8f9ff' : '#fafafa'
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                {getStatusIcon(item.status)}
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {item.supplier}
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Response time: {item.responseTime}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ textAlign: 'right' }}>
                <Chip
                  label={item.quote}
                  size="small"
                  variant="outlined"
                  sx={{
                    color: item.status === 'received' ? '#2196f3' : '#666',
                    borderColor: item.status === 'received' ? '#2196f3' : '#ddd',
                    fontWeight: 500,
                    mb: 0.5
                  }}
                />
                <Typography variant="caption" display="block" sx={{ color: '#666', fontSize: '0.75rem' }}>
                  {item.status === 'received' ? 'Quote received' : 'Waiting...'}
                </Typography>
              </Box>
            </Box>
          ))}
        </Box>
      </Box>
    </Paper>
  );
};

export default ProgressTracker;