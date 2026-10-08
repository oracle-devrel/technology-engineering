import React from 'react';
import { ProcessingStatus } from '../../types';

interface StatusIndicatorProps {
  status: ProcessingStatus;
  fileName?: string;
}

const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status, fileName }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'uploading':
        return {
          text: 'Uploading...',
          color: 'text-confidence-medium',
          bgColor: 'bg-confidence-medium/20',
          borderColor: 'border-confidence-medium/30',
          icon: (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ),
        };
      case 'processing':
        return {
          text: 'Extracting parameters...',
          color: 'text-status-review',
          bgColor: 'bg-status-review/20',
          borderColor: 'border-status-review/30',
          icon: (
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
          ),
        };
      case 'completed':
        return {
          text: 'Extraction completed',
          color: 'text-confidence-high',
          bgColor: 'bg-confidence-high/20',
          borderColor: 'border-confidence-high/30',
          icon: (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          ),
        };
      case 'error':
        return {
          text: 'Error occurred',
          color: 'text-confidence-low',
          bgColor: 'bg-confidence-low/20',
          borderColor: 'border-confidence-low/30',
          icon: (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          ),
        };
      default:
        return {
          text: 'Ready',
          color: 'text-oracle-red',
          bgColor: 'bg-oracle-red/20',
          borderColor: 'border-oracle-red/30',
          icon: (
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 10V3L4 14h7v7l9-11h-7z"
              />
            </svg>
          ),
        };
    }
  };

  const config = getStatusConfig();

  if (status === 'idle') {
    return null;
  }

  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <div className={config.color}>{config.icon}</div>
      <div>
        <div className={`text-sm font-medium ${config.color}`}>{config.text}</div>
        {fileName && (
          <div className="text-xs text-dark-300 truncate max-w-xs">{fileName}</div>
        )}
      </div>
    </div>
  );
};

export default StatusIndicator;
