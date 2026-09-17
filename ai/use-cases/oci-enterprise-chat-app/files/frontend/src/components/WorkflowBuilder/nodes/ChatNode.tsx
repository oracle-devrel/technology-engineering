import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { MessageSquare } from 'lucide-react';

const ChatNode: React.FC<NodeProps> = ({ data, selected }) => {
  return (
    <div className={`bg-dark-800 rounded-lg border-2 ${selected ? 'border-green-400' : 'border-dark-600'} shadow-lg min-w-[200px]`}>
      <div className="bg-green-500/20 px-3 py-2 rounded-t-md border-b border-dark-600">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-green-400" />
          <div className="flex flex-col">
            <span className="text-sm font-medium text-green-300">Chat</span>
            <span className="text-[10px] text-green-400/70 leading-tight">(Input &amp; Output)</span>
          </div>
        </div>
      </div>
      <div className="px-3 py-2.5">
        <p className="text-white text-sm font-medium truncate">{data.label as string}</p>
      </div>
      <Handle type="target" position={Position.Top} className="!bg-green-400 !w-3 !h-3 !border-2 !border-dark-800" />
      <Handle type="source" position={Position.Bottom} className="!bg-green-400 !w-3 !h-3 !border-2 !border-dark-800" />
    </div>
  );
};

export default memo(ChatNode);
