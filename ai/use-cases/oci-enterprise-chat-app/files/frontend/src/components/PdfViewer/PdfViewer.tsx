import React, { useState, useEffect, useRef } from 'react';
import { Worker, Viewer, SpecialZoomLevel } from '@react-pdf-viewer/core';
import { defaultLayoutPlugin } from '@react-pdf-viewer/default-layout';
import type { OnHighlightKeyword } from '@react-pdf-viewer/search';
import { ExtractedParameter } from '../../types';

import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/default-layout/lib/styles/index.css';

const HIGHLIGHT_COLORS: Record<string, string> = {
  'Date': 'rgba(59, 130, 246, 0.35)',       // blue
  'Amount': 'rgba(16, 185, 129, 0.35)',      // green
  'Email': 'rgba(168, 85, 247, 0.35)',       // purple
  'Phone Number': 'rgba(245, 158, 11, 0.35)',// amber
  'Percentage': 'rgba(236, 72, 153, 0.35)',  // pink
};
const DEFAULT_HIGHLIGHT_COLOR = 'rgba(118, 185, 0, 0.35)';

interface PdfViewerProps {
  pdfUrl: string | null;
  highlightedParam?: ExtractedParameter | null;
  allParameters?: ExtractedParameter[] | null;
}

const PdfViewer: React.FC<PdfViewerProps> = ({ pdfUrl, highlightedParam, allParameters }) => {
  const [error, setError] = useState<string | null>(null);
  const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);
  const highlightTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Use refs so the onHighlightKeyword callback always reads latest values
  const allParametersRef = useRef(allParameters);
  const highlightedParamRef = useRef(highlightedParam);
  useEffect(() => { allParametersRef.current = allParameters; }, [allParameters]);
  useEffect(() => { highlightedParamRef.current = highlightedParam; }, [highlightedParam]);

  const onHighlightKeyword = (props: OnHighlightKeyword) => {
    const keywordStr = props.keyword.source;
    const params = allParametersRef.current;
    const activeParam = highlightedParamRef.current;
    const matchedParam = params?.find(p => String(p.value) === keywordStr);
    const isActive = activeParam && String(activeParam.value) === keywordStr;

    if (props.highlightEle) {
      const color = matchedParam
        ? (HIGHLIGHT_COLORS[matchedParam.name] || DEFAULT_HIGHLIGHT_COLOR)
        : DEFAULT_HIGHLIGHT_COLOR;
      props.highlightEle.style.backgroundColor = color;
      props.highlightEle.style.borderRadius = '2px';

      if (isActive) {
        props.highlightEle.style.outline = '2px solid rgba(118, 185, 0, 0.9)';
        props.highlightEle.style.boxShadow = '0 0 8px rgba(118, 185, 0, 0.5)';
      }
    }
  };

  // Create plugin fresh each render — react-pdf-viewer expects this pattern
  // and it is lightweight (just config, no DOM work until Viewer mounts)
  const defaultLayoutPluginInstance = defaultLayoutPlugin({
    sidebarTabs: () => [],
    toolbarPlugin: {
      fullScreenPlugin: {
        onEnterFullScreen: (zoom) => {
          zoom(SpecialZoomLevel.PageFit);
        },
        onExitFullScreen: (zoom) => {
          zoom(SpecialZoomLevel.PageWidth);
        },
      },
      searchPlugin: {
        onHighlightKeyword,
      },
    },
  });

  const { toolbarPluginInstance } = defaultLayoutPluginInstance;
  const { searchPluginInstance } = toolbarPluginInstance;

  // Highlight all parameters when document loads or parameters change
  useEffect(() => {
    if (!isDocumentLoaded || !allParameters || allParameters.length === 0) {
      return;
    }

    if (highlightTimeoutRef.current) {
      clearTimeout(highlightTimeoutRef.current);
    }

    highlightTimeoutRef.current = setTimeout(() => {
      const keywords = allParameters.map(p => String(p.value));
      const uniqueKeywords = [...new Set(keywords)];
      searchPluginInstance.highlight(uniqueKeywords);
    }, 500);

    return () => {
      if (highlightTimeoutRef.current) {
        clearTimeout(highlightTimeoutRef.current);
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDocumentLoaded, allParameters]);

  // When a specific parameter is clicked, re-highlight and jump to its match
  useEffect(() => {
    if (!isDocumentLoaded || !highlightedParam) {
      return;
    }

    const keyword = String(highlightedParam.value);
    const allKeywords = allParameters
      ? [...new Set(allParameters.map(p => String(p.value)))]
      : [keyword];

    searchPluginInstance.highlight(allKeywords).then((matches) => {
      const matchIndex = matches.findIndex(
        m => m.pageText.includes(keyword)
      );
      if (matchIndex >= 0) {
        searchPluginInstance.jumpToMatch(matchIndex + 1);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightedParam, isDocumentLoaded]);

  // Reset loaded state when URL changes
  useEffect(() => {
    setIsDocumentLoaded(false);
  }, [pdfUrl]);

  if (!pdfUrl) {
    return (
      <div className="h-full flex items-center justify-center bg-dark-800">
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
                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-medium text-white">No document selected</h3>
            <p className="text-sm text-dark-300 mt-2">
              Upload a PDF document to view it here
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-dark-800">
      {error ? (
        <div className="h-full flex items-center justify-center bg-dark-800">
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
            <h3 className="text-lg font-medium text-white">Error loading PDF</h3>
            <p className="text-sm text-dark-300">{error}</p>
          </div>
        </div>
      ) : (
        <Worker workerUrl="https://unpkg.com/pdfjs-dist@3.11.174/build/pdf.worker.min.js">
          <div className="h-full">
            <Viewer
              fileUrl={pdfUrl}
              plugins={[defaultLayoutPluginInstance]}
              defaultScale={SpecialZoomLevel.PageWidth}
              onDocumentLoad={() => {
                setError(null);
                setIsDocumentLoaded(true);
              }}
            />
          </div>
        </Worker>
      )}
    </div>
  );
};

export default PdfViewer;
