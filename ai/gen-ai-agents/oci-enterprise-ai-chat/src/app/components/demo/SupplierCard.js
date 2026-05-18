"use client";

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Chip,
  Grid,
  LinearProgress
} from '@mui/material';
import {
  Building2,
  Phone,
  Mail,
  Clock,
  Star,
  TrendingUp,
  ShoppingCart
} from 'lucide-react';

const SupplierCard = ({ data }) => {
  const { name, orderValue, performance, contact, notes } = data;

  const getStarRating = (rating) => {
    const numRating = parseFloat(rating.split('/')[0]);
    return Math.floor(numRating);
  };

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
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 1,
              backgroundColor: '#f8f9ff',
              border: '1px solid #e3f2fd',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Building2 size={20} color="#2196f3" />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
              {name}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <Chip
                icon={<ShoppingCart size={14} />}
                label={`Order Value: ${orderValue}`}
                size="small"
                variant="outlined"
                sx={{ color: '#666', borderColor: '#ddd', fontSize: '0.75rem' }}
              />
              <Chip
                label="Preferred Supplier"
                size="small"
                variant="outlined"
                sx={{ color: '#2196f3', borderColor: '#2196f3', fontSize: '0.75rem' }}
              />
            </Box>
          </Box>
        </Box>
      </Box>

      <Box sx={{ p: 2 }}>
        {/* Performance Metrics */}
        <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 2, color: '#1a1a1a' }}>
          Performance Metrics
        </Typography>
        
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1 }}>
                <TrendingUp size={16} color="#2196f3" />
                <Typography variant="h6" sx={{ fontWeight: 500, color: '#2196f3' }}>
                  {performance.onTimeDelivery}
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                On-Time Delivery
              </Typography>
              <LinearProgress
                variant="determinate"
                value={parseFloat(performance.onTimeDelivery.replace('%', ''))}
                sx={{
                  mt: 1,
                  height: 4,
                  borderRadius: 2,
                  backgroundColor: '#f0f0f0',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: '#2196f3',
                    borderRadius: 2
                  }
                }}
              />
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1 }}>
                <Star size={16} color="#2196f3" />
                <Typography variant="h6" sx={{ fontWeight: 500, color: '#2196f3' }}>
                  {performance.qualityRating}
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                Quality Rating
              </Typography>
              <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center', gap: 0.5 }}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <Star
                    key={star}
                    size={12}
                    color={star <= getStarRating(performance.qualityRating) ? '#2196f3' : '#e0e0e0'}
                    fill={star <= getStarRating(performance.qualityRating) ? '#2196f3' : '#e0e0e0'}
                  />
                ))}
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 1 }}>
                <ShoppingCart size={16} color="#2196f3" />
                <Typography variant="h6" sx={{ fontWeight: 500, color: '#2196f3' }}>
                  {performance.totalOrders}
                </Typography>
              </Box>
              <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                Total Orders
              </Typography>
              <Typography variant="caption" display="block" sx={{ color: '#666', fontSize: '0.75rem', mt: 0.5 }}>
                Completed successfully
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Contact Information */}
        <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 2, color: '#1a1a1a' }}>
          Contact Information
        </Typography>

        <Grid container spacing={1.5} sx={{ mb: 3 }}>
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Phone size={16} color="#666" />
              <Box>
                <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                  Phone
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                  {contact.phone}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Mail size={16} color="#666" />
              <Box>
                <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                  Email
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                  {contact.email}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, p: 1.5, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0' }}>
              <Clock size={16} color="#666" />
              <Box>
                <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                  Support Hours
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                  {contact.supportHours}
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>

        {/* Notes */}
        {notes && (
          <Box
            sx={{
              p: 1.5,
              backgroundColor: '#f8f9ff',
              borderRadius: 1,
              border: '1px solid #e3f2fd'
            }}
          >
            <Typography variant="body2" sx={{ color: '#2196f3', fontSize: '0.875rem' }}>
              {notes}
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default SupplierCard;