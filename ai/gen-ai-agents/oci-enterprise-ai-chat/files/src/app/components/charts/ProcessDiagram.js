"use client";

import React from 'react';
import { Box, Typography, Paper } from '@mui/material';
import { 
  CheckCircle, 
  Settings, 
  Truck, 
  MapPin, 
  Package,
  Building2,
  DollarSign,
  Calendar,
  Zap
} from 'lucide-react';

const ProcessDiagram = ({ data }) => {
  const { title, steps, currentStep, orderInfo } = data;

  const getStepIcon = (stepName) => {
    const iconProps = { size: 24 };
    
    switch (stepName) {
      case 'Order Placed':
        return <CheckCircle {...iconProps} />;
      case 'Processing':
        return <Settings {...iconProps} />;
      case 'In Transit':
        return <Truck {...iconProps} />;
      case 'Out for Delivery':
        return <MapPin {...iconProps} />;
      case 'Delivered':
        return <Package {...iconProps} />;
      default:
        return <CheckCircle {...iconProps} />;
    }
  };

  const getStepStyles = (isCompleted, isCurrent) => {
    if (isCurrent) {
      return {
        iconColor: '#2196f3',
        backgroundColor: '#e3f2fd',
        borderColor: '#2196f3',
        textColor: '#2196f3',
        fontWeight: 600
      };
    } else if (isCompleted) {
      return {
        iconColor: '#4caf50',
        backgroundColor: '#e8f5e8',
        borderColor: '#4caf50',
        textColor: '#4caf50',
        fontWeight: 500
      };
    } else {
      return {
        iconColor: '#9e9e9e',
        backgroundColor: '#fafafa',
        borderColor: '#e0e0e0',
        textColor: '#757575',
        fontWeight: 400
      };
    }
  };

  const isStepCompleted = (stepName) => {
    if (!steps || !currentStep) return false;
    const currentIndex = steps.findIndex(step => step.name === currentStep);
    const stepIndex = steps.findIndex(step => step.name === stepName);
    return stepIndex < currentIndex;
  };

  const isCurrentStep = (stepName) => stepName === currentStep;

  return (
    <Paper
      elevation={0}
      sx={{
        mb: 2,
        borderRadius: 2,
        border: '1px solid #e0e0e0',
        backgroundColor: '#fafafa',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ 
        p: 2.5, 
        borderBottom: '1px solid #e0e0e0', 
        backgroundColor: 'white',
        borderTopLeftRadius: 'inherit',
        borderTopRightRadius: 'inherit'
      }}>
        <Typography 
          variant="h6" 
          sx={{ 
            fontWeight: 600, 
            color: '#1a1a1a',
            fontSize: '1.1rem'
          }}
        >
          {title}
        </Typography>
      </Box>

      <Box sx={{ 
        p: 3, 
        backgroundColor: 'white',
        borderBottomLeftRadius: 'inherit',
        borderBottomRightRadius: 'inherit'
      }}>
        {/* Progress Steps */}
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 1,
            mb: 3,
            '@media (max-width: 768px)': {
              gap: 0.5
            }
          }}
        >
          {steps && steps.map((step, index) => {
            const styles = getStepStyles(
              isStepCompleted(step.name),
              isCurrentStep(step.name)
            );
            
            return (
              <React.Fragment key={step.name}>
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    flex: 1,
                    minWidth: 0,
                    position: 'relative'
                  }}
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      backgroundColor: styles.backgroundColor,
                      border: `2px solid ${styles.borderColor}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      mb: 1,
                      color: styles.iconColor,
                      transition: 'all 0.3s ease',
                      ...(isCurrentStep(step.name) && {
                        animation: 'pulse 2s infinite',
                        '@keyframes pulse': {
                          '0%': {
                            boxShadow: `0 0 0 0 ${styles.borderColor}40`
                          },
                          '70%': {
                            boxShadow: `0 0 0 10px ${styles.borderColor}00`
                          },
                          '100%': {
                            boxShadow: `0 0 0 0 ${styles.borderColor}00`
                          }
                        }
                      })
                    }}
                  >
                    {getStepIcon(step.name)}
                  </Box>
                  <Typography
                    variant="caption"
                    sx={{
                      color: styles.textColor,
                      fontWeight: styles.fontWeight,
                      fontSize: '0.75rem',
                      textAlign: 'center',
                      lineHeight: 1.2,
                      '@media (max-width: 768px)': {
                        fontSize: '0.7rem'
                      }
                    }}
                  >
                    {step.name}
                  </Typography>
                </Box>
                
                {index < steps.length - 1 && (
                  <Box
                    sx={{
                      width: '100%',
                      height: '2px',
                      backgroundColor: isStepCompleted(steps[index + 1].name) || isCurrentStep(steps[index + 1].name) 
                        ? '#4caf50' 
                        : '#e0e0e0',
                      borderRadius: 1,
                      alignSelf: 'center',
                      mt: 3,
                      transition: 'background-color 0.3s ease',
                      maxWidth: '60px',
                      '@media (max-width: 768px)': {
                        maxWidth: '40px'
                      }
                    }}
                  />
                )}
              </React.Fragment>
            );
          })}
        </Box>

        {/* Order Information */}
        {orderInfo && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 500, mb: 2, color: '#1a1a1a' }}>
              Order Details
            </Typography>
            
            <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 2 }}>
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Building2 size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Supplier
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.supplier}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <DollarSign size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Order Value
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.orderValue}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Zap size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Tracking Number
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.tracking}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Truck size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Carrier
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.carrier}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <Calendar size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Estimated Delivery
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.estimatedDelivery}
                  </Typography>
                </Box>
              </Box>
              
              <Box sx={{ p: 2, backgroundColor: '#fafafa', borderRadius: 1, border: '1px solid #f0f0f0', display: 'flex', alignItems: 'center', gap: 2 }}>
                <MapPin size={24} style={{ color: '#666' }} />
                <Box>
                  <Typography variant="caption" sx={{ color: '#666', fontSize: '0.75rem' }}>
                    Delivery Location
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500, color: '#1a1a1a' }}>
                    {orderInfo.deliveryLocation}
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Box>
        )}

      </Box>
    </Paper>
  );
};

export default ProcessDiagram;