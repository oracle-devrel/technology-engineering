import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { ArrowDownToLine, FolderOpen } from 'lucide-react';

const InputNode: React.FC<NodeProps> = ({ data, selected }) => {
  const config = (data.config as Record<string, any>) || {};
  const isProject = config.input_type === 'project';
  const projectName = config.project?.project_id || config.project?.name || 'Project';

  return (
    <div className={`bg-dark-800 rounded-lg border-2 ${selected ? 'border-blue-400' : 'border-dark-600'} shadow-lg min-w-[180px]`}>
      <div className="bg-blue-500/20 px-3 py-1.5 rounded-t-md border-b border-dark-600">
        <div className="flex items-center gap-2">
          {isProject ? (
            <FolderOpen className="h-4 w-4 text-blue-400" />
          ) : (
            <ArrowDownToLine className="h-4 w-4 text-blue-400" />
          )}
          <span className="text-sm font-medium text-blue-300">Input</span>
          {isProject && (
            <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide bg-blue-500/30 text-blue-300 px-1.5 py-0.5 rounded">
              RAG
            </span>
          )}
        </div>
      </div>
      <div className="px-3 py-2">
        <p className="text-white text-sm font-medium truncate">{data.label as string}</p>
        {isProject ? (
          <div className="flex items-center gap-1.5 mt-1">
            <FolderOpen className="h-3 w-3 text-dark-400 flex-shrink-0" />
            <p className="text-dark-400 text-xs truncate">{projectName}</p>
          </div>
        ) : (
          config.input_type && (
            <p className="text-dark-400 text-xs mt-1">{config.input_type}</p>
          )
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-blue-400 !w-3 !h-3 !border-2 !border-dark-800" />
    </div>
  );
};

export default memo(InputNode);
