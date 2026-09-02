import { useState, useRef, useEffect } from 'react';
import { HelpCircle } from 'lucide-react';

interface TooltipProps {
  content: string | React.ReactNode;
  children?: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  showIcon?: boolean;
  iconClassName?: string;
}

export function Tooltip({
  content,
  children,
  position = 'top',
  showIcon = true,
  iconClassName = '',
}: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false);
  const [tooltipPosition, setTooltipPosition] = useState({ top: 0, left: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isVisible && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();

      let top = 0;
      let left = 0;

      switch (position) {
        case 'top':
          top = triggerRect.top - tooltipRect.height - 8;
          left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'bottom':
          top = triggerRect.bottom + 8;
          left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'left':
          top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
          left = triggerRect.left - tooltipRect.width - 8;
          break;
        case 'right':
          top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
          left = triggerRect.right + 8;
          break;
      }

      // Keep tooltip within viewport
      if (left < 8) left = 8;
      if (left + tooltipRect.width > window.innerWidth - 8) {
        left = window.innerWidth - tooltipRect.width - 8;
      }
      if (top < 8) top = triggerRect.bottom + 8; // Flip to bottom

      setTooltipPosition({ top, left });
    }
  }, [isVisible, position]);

  return (
    <div className="inline-flex items-center">
      {children}
      <div
        ref={triggerRef}
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
        className={`cursor-help ${children ? 'ml-1' : ''}`}
      >
        {showIcon && (
          <HelpCircle className={`w-3.5 h-3.5 text-gray-500 hover:text-gray-300 transition-colors ${iconClassName}`} />
        )}
      </div>
      {isVisible && (
        <div
          ref={tooltipRef}
          className="fixed z-[9999] px-3 py-2 text-xs text-white bg-gray-800 rounded-lg shadow-lg border border-gray-700 max-w-xs"
          style={{ top: tooltipPosition.top, left: tooltipPosition.left }}
        >
          {content}
          <div
            className={`absolute w-2 h-2 bg-gray-800 border-gray-700 transform rotate-45 ${
              position === 'top'
                ? 'bottom-[-5px] left-1/2 -translate-x-1/2 border-r border-b'
                : position === 'bottom'
                ? 'top-[-5px] left-1/2 -translate-x-1/2 border-l border-t'
                : position === 'left'
                ? 'right-[-5px] top-1/2 -translate-y-1/2 border-t border-r'
                : 'left-[-5px] top-1/2 -translate-y-1/2 border-b border-l'
            }`}
          />
        </div>
      )}
    </div>
  );
}

// Simple inline help text component with variant support
interface HelpTextProps {
  children: React.ReactNode;
  variant?: 'default' | 'warning' | 'success' | 'error';
}

export function HelpText({ children, variant = 'default' }: HelpTextProps) {
  const variantClasses = {
    default: 'text-gray-500',
    warning: 'text-yellow-500',
    success: 'text-green-500',
    error: 'text-red-500',
  };

  return (
    <div className={`flex items-start gap-1.5 mt-1 text-xs ${variantClasses[variant]}`}>
      <HelpCircle className="w-3 h-3 mt-0.5 shrink-0" />
      <span>{children}</span>
    </div>
  );
}
