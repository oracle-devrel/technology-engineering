import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Database } from 'lucide-react';

const DataSourceNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`bg-dark-800 rounded-lg border-2 ${selected ? 'border-emerald-400' : 'border-dark-600'} shadow-lg min-w-[180px]`}>
      <div className="bg-emerald-500/20 px-3 py-1.5 rounded-t-md border-b border-dark-600">
        <div className="flex items-center gap-2">
          <Database className="h-4 w-4 text-emerald-400" />
          <span className="text-sm font-medium text-emerald-300">Data Source</span>
        </div>
      </div>
      <div className="px-3 py-2">
        <p className="text-white text-sm font-medium truncate">{data.label as string}</p>
        {(data.config as Record<string, any>)?.source_type && (
          <p className="text-dark-400 text-xs mt-1">{(data.config as Record<string, any>).source_type}</p>
        )}
      </div>
      <Handle type="target" position={Position.Top} className="!bg-emerald-400 !w-3 !h-3 !border-2 !border-dark-800" />
      <Handle type="source" position={Position.Bottom} className="!bg-emerald-400 !w-3 !h-3 !border-2 !border-dark-800" />
    </div>
  );
};

export default memo(DataSourceNode);
