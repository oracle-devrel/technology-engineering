import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Bot } from 'lucide-react';

const AgentNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`bg-dark-800 rounded-lg border-2 ${selected ? 'border-purple-400' : 'border-dark-600'} shadow-lg min-w-[180px]`}>
      <div className="bg-purple-500/20 px-3 py-1.5 rounded-t-md border-b border-dark-600">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-purple-400" />
          <span className="text-sm font-medium text-purple-300">Agent</span>
        </div>
      </div>
      <div className="px-3 py-2">
        <p className="text-white text-sm font-medium truncate">{data.label as string}</p>
        {(data.config as Record<string, any>)?.prompt && (
          <p className="text-dark-400 text-xs mt-1 truncate">{(data.config as Record<string, any>).prompt}</p>
        )}
      </div>

      {/* Input handles on the left edge */}
      <Handle
        type="target"
        position={Position.Left}
        id="input-0"
        className="!bg-purple-400 !w-2.5 !h-2.5 !border-2 !border-dark-800"
        style={{ top: '25%' }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input-1"
        className="!bg-purple-400 !w-2.5 !h-2.5 !border-2 !border-dark-800"
        style={{ top: '50%' }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="input-2"
        className="!bg-purple-400 !w-2.5 !h-2.5 !border-2 !border-dark-800"
        style={{ top: '75%' }}
      />

      {/* Output handles on the right edge */}
      <Handle
        type="source"
        position={Position.Right}
        id="output-0"
        className="!bg-purple-400 !w-2.5 !h-2.5 !border-2 !border-dark-800"
        style={{ top: '33%' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="output-1"
        className="!bg-purple-400 !w-2.5 !h-2.5 !border-2 !border-dark-800"
        style={{ top: '67%' }}
      />
    </div>
  );
};

export default memo(AgentNode);
