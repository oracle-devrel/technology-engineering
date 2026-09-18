import React from 'react';
import { ExtractedParameter } from '../../types';

interface ExtractionPanelProps {
  parameters: ExtractedParameter[] | null;
  isLoading: boolean;
  error?: string;
  highlightedParam?: ExtractedParameter | null;
  onParameterClick?: (param: ExtractedParameter) => void;
}

const ExtractionPanel: React.FC<ExtractionPanelProps> = ({
  parameters,
  isLoading,
  error,
  highlightedParam,
  onParameterClick,
}) => {
  // Group parameters by category
  const groupedParameters = React.useMemo(() => {
    if (!parameters) return {};

    return parameters.reduce((acc, param) => {
      const category = param.category || 'General';
      if (!acc[category]) {
        acc[category] = [];
      }
      acc[category].push(param);
      return acc;
    }, {} as Record<string, ExtractedParameter[]>);
  }, [parameters]);

  const getConfidenceConfig = (confidence: number) => {
    if (confidence >= 0.9) return {
      color: 'text-confidence-high',
      bg: 'bg-confidence-high/20',
      border: 'border-confidence-high/30',
      barColor: 'bg-confidence-high',
      label: 'High'
    };
    if (confidence >= 0.7) return {
      color: 'text-confidence-medium',
      bg: 'bg-confidence-medium/20',
      border: 'border-confidence-medium/30',
      barColor: 'bg-confidence-medium',
      label: 'Medium'
    };
    return {
      color: 'text-confidence-low',
      bg: 'bg-confidence-low/20',
      border: 'border-confidence-low/30',
      barColor: 'bg-confidence-low',
      label: 'Low'
    };
  };

  if (isLoading) {
    return (
      <div className="h-full bg-dark-900 p-6">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-dark-700 rounded w-3/4"></div>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card p-4 space-y-3">
              <div className="h-4 bg-dark-600 rounded w-1/2"></div>
              <div className="h-6 bg-dark-700 rounded w-3/4"></div>
              <div className="h-3 bg-dark-700 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center bg-dark-900">
        <div className="text-center space-y-4 p-6">
          <div className="w-16 h-16 mx-auto rounded-full bg-confidence-low/20 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-confidence-low"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-white">Extraction Error</h3>
          <p className="text-sm text-dark-300">{error}</p>
        </div>
      </div>
    );
  }

  if (!parameters || parameters.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-dark-900">
        <div className="text-center space-y-4">
          <div className="w-24 h-24 mx-auto rounded-full bg-dark-700 flex items-center justify-center">
            <svg
              className="w-12 h-12 text-dark-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-white">No parameters extracted</h3>
            <p className="text-sm text-dark-300 mt-2">
              Upload a document to extract parameters
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-dark-900 overflow-auto">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-white">Extracted Parameters</h2>
          <span className="px-3 py-1 bg-oracle-red/20 text-oracle-red rounded-full text-sm font-medium border border-oracle-red/30">
            {parameters.length} parameter{parameters.length !== 1 ? 's' : ''}
          </span>
        </div>

        {onParameterClick && (
          <p className="text-xs text-dark-400 flex items-center gap-1.5">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Click a parameter to highlight it in the PDF
          </p>
        )}

        {Object.entries(groupedParameters).map(([category, params]) => (
          <div key={category} className="space-y-3">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <svg
                className="w-5 h-5 text-oracle-red"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                />
              </svg>
              <span>{category}</span>
            </h3>

            <div className="space-y-3">
              {params.map((param, index) => {
                const confidenceConfig = getConfidenceConfig(param.confidence);
                const isActive = highlightedParam &&
                  highlightedParam.name === param.name &&
                  String(highlightedParam.value) === String(param.value);
                return (
                  <div
                    key={`${param.name}-${index}`}
                    className={`card p-4 transition-all duration-200 ${
                      onParameterClick ? 'cursor-pointer hover:border-oracle-red/50' : ''
                    } ${
                      isActive
                        ? 'border-oracle-red ring-1 ring-oracle-red/40 bg-oracle-red/5'
                        : 'hover:border-dark-500'
                    }`}
                    onClick={() => onParameterClick?.(param)}
                    role={onParameterClick ? 'button' : undefined}
                    tabIndex={onParameterClick ? 0 : undefined}
                    onKeyDown={(e) => {
                      if (onParameterClick && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault();
                        onParameterClick(param);
                      }
                    }}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm font-medium text-dark-300">
                            {param.name}
                          </h4>
                          {param.source_page && (
                            <span className="text-xs text-dark-400 bg-dark-700 px-1.5 py-0.5 rounded">
                              Page {param.source_page}
                            </span>
                          )}
                        </div>
                        <p className="text-lg font-semibold text-white break-words">
                          {String(param.value)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2 ml-4">
                        {isActive && (
                          <svg
                            className="w-4 h-4 text-oracle-red flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                            />
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                            />
                          </svg>
                        )}
                        <div
                          className={`px-2.5 py-1 rounded-full text-xs font-medium whitespace-nowrap border ${confidenceConfig.bg} ${confidenceConfig.color} ${confidenceConfig.border}`}
                        >
                          {confidenceConfig.label} ({Math.round(param.confidence * 100)}%)
                        </div>
                      </div>
                    </div>

                    {/* Confidence bar */}
                    <div className="mt-3">
                      <div className="w-full bg-dark-600 rounded-full h-1.5">
                        <div
                          className={`h-1.5 rounded-full transition-all duration-300 ${confidenceConfig.barColor}`}
                          style={{ width: `${param.confidence * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ExtractionPanel;
