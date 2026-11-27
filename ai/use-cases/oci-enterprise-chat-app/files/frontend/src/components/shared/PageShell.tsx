import { type ReactNode, useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';
import Tooltip from './Tooltip';

interface Props {
  title: string;
  subtitle?: string;
  children: ReactNode;
  actions?: ReactNode;
  fullWidth?: boolean;
}

export default function PageShell({ title, subtitle, children, actions, fullWidth = false }: Props) {
  const [maximized, setMaximized] = useState(false);

  if (maximized) {
    return (
      <div className="fixed inset-0 z-40 bg-dark-900 flex flex-col">
        <div className="h-10 border-b border-dark-700 flex items-center justify-between px-4">
          <span className="text-sm font-medium text-white">{title}</span>
          <div className="flex items-center gap-2">
            {actions}
            <Tooltip text="Exit full screen and show sidebar" position="bottom">
              <button onClick={() => setMaximized(false)} className="p-1 rounded hover:bg-dark-700 text-gray-400 hover:text-white">
                <Minimize2 size={14} />
              </button>
            </Tooltip>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">{children}</div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="h-14 border-b border-dark-700 flex items-center justify-between px-6">
        <div>
          <h1 className="text-lg font-semibold text-white">{title}</h1>
          {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2">
          {actions}
          <Tooltip text="Maximize to full screen — hides the sidebar for more space" position="bottom">
            <button onClick={() => setMaximized(true)} className="p-1.5 rounded hover:bg-dark-700 text-gray-400 hover:text-white">
              <Maximize2 size={14} />
            </button>
          </Tooltip>
        </div>
      </div>
      <div className={`flex-1 ${fullWidth ? 'overflow-hidden' : 'p-6 overflow-y-auto'} w-full`} style={{ minHeight: 0 }}>{children}</div>
    </div>
  );
}
