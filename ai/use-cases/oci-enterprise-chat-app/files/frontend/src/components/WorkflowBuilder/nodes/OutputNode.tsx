import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ArrowUpFromLine, HardDrive, MessageSquare, FileText } from 'lucide-react';

const OutputNode: React.FC<NodeProps> = ({ data, selected }) => {
  const config = data.config as Record<string, any> | undefined;
  const outputType = config?.output_type as string | undefined;
  const bucketName = config?.bucket_name as string | undefined;
  const fileFormat = config?.file_format as string | undefined;

  const renderOutputTypeIcon = () => {
    if (outputType === 'object_store') {
      return (
        <div className="flex items-center gap-1.5">
          <div className="relative">
            <HardDrive className="h-3.5 w-3.5 text-amber-400" />
            {bucketName && (
              <span className="absolute -top-1.5 -right-2.5 bg-amber-500/30 text-amber-300 text-[9px] leading-none px-1 py-0.5 rounded font-medium whitespace-nowrap">
                {bucketName}
              </span>
            )}
          </div>
          <span className="text-dark-400 text-xs">{outputType}</span>
        </div>
      );
    }

    if (outputType === 'chat') {
      return (
        <div className="flex items-center gap-1.5">
          <MessageSquare className="h-3.5 w-3.5 text-amber-400" />
          <span className="text-dark-400 text-xs">{outputType}</span>
        </div>
      );
    }

    if (outputType) {
      return (
        <div className="flex items-center gap-1.5">
          <FileText className="h-3.5 w-3.5 text-amber-400" />
          <span className="text-dark-400 text-xs">{outputType}</span>
        </div>
      );
    }

    return null;
  };

  return (
    <div className={`bg-dark-800 rounded-lg border-2 ${selected ? 'border-amber-400' : 'border-dark-600'} shadow-lg min-w-[180px]`}>
      <div className="bg-amber-500/20 px-3 py-1.5 rounded-t-md border-b border-dark-600">
        <div className="flex items-center gap-2">
          <ArrowUpFromLine className="h-4 w-4 text-amber-400" />
          <span className="text-sm font-medium text-amber-300">Output</span>
        </div>
      </div>
      <div className="px-3 py-2">
        <p className="text-white text-sm font-medium truncate">{data.label as string}</p>
        {outputType && (
          <div className="mt-1.5 flex items-center gap-2">
            {renderOutputTypeIcon()}
            {outputType === 'object_store' && fileFormat && (
              <span className="bg-amber-500/20 text-amber-300 text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded">
                {fileFormat}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Target handle on top (always present) */}
      <Handle type="target" position={Position.Top} className="!bg-amber-400 !w-3 !h-3 !border-2 !border-dark-800" />

      {/* Source handle on bottom (only for chat output type, to connect back to Chat block) */}
      {outputType === 'chat' && (
        <Handle type="source" position={Position.Bottom} className="!bg-amber-400 !w-3 !h-3 !border-2 !border-dark-800" />
      )}
    </div>
  );
};

export default memo(OutputNode);
