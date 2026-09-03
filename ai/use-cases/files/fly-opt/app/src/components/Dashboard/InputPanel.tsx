import { AIAssistant } from './AIAssistant';

interface InputPanelProps {
  onRunOptimization: () => void;
}

export function InputPanel({ onRunOptimization }: InputPanelProps) {
  return (
    <div className="w-96 bg-dark-card border-r border-dark-border flex flex-col h-full">
      <AIAssistant onRunOptimization={onRunOptimization} />
    </div>
  );
}
