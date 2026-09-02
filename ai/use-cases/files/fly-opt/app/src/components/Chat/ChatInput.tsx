import { useState, useRef, KeyboardEvent, ChangeEvent } from 'react';
import { Send, Paperclip, Mic, Settings, X, FileText } from 'lucide-react';
import { Button } from '@/components/shared/Button';
import { Select } from '@/components/shared/Select';
import { Slider } from '@/components/shared/Slider';
import { useChatStore } from '@/store';
import type { ModelId, Stop } from '@/types';

interface ChatInputProps {
  onSend: (message: string, attachedStops?: Stop[]) => void;
  isProcessing: boolean;
}

// Parse CSV content to extract stops
function parseCSVToStops(csvContent: string): Stop[] {
  const lines = csvContent.trim().split('\n');
  if (lines.length < 2) return [];

  const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
  const latIdx = headers.findIndex(h => h === 'lat' || h === 'latitude');
  const lngIdx = headers.findIndex(h => h === 'lng' || h === 'lon' || h === 'longitude');
  const demandIdx = headers.findIndex(h => h === 'demand' || h === 'weight' || h === 'quantity');
  const labelIdx = headers.findIndex(h => h === 'label' || h === 'name' || h === 'address' || h === 'location');

  if (latIdx === -1 || lngIdx === -1) {
    throw new Error('CSV must contain lat/latitude and lng/lon/longitude columns');
  }

  const stops: Stop[] = [];
  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    if (values.length > Math.max(latIdx, lngIdx)) {
      const lat = parseFloat(values[latIdx]);
      const lng = parseFloat(values[lngIdx]);

      if (!isNaN(lat) && !isNaN(lng)) {
        stops.push({
          id: i,
          lat,
          lng,
          demand: demandIdx !== -1 ? parseInt(values[demandIdx]) || 1 : 1,
          label: labelIdx !== -1 ? values[labelIdx] : `Stop ${i}`,
        });
      }
    }
  }

  return stops;
}

export function ChatInput({ onSend, isProcessing }: ChatInputProps) {
  const { inputMessage, setInputMessage, config, setModel, setTemperature } =
    useChatStore();
  const [showSettings, setShowSettings] = useState(false);
  const [attachedFile, setAttachedFile] = useState<{ name: string; stops: Stop[] } | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setFileError('Please upload a CSV file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        const stops = parseCSVToStops(content);

        if (stops.length === 0) {
          setFileError('No valid stops found in CSV');
          return;
        }

        setAttachedFile({ name: file.name, stops });
        setFileError(null);
      } catch (err) {
        setFileError(err instanceof Error ? err.message : 'Failed to parse CSV');
      }
    };
    reader.readAsText(file);

    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveFile = () => {
    setAttachedFile(null);
    setFileError(null);
  };

  const handleSend = () => {
    if (inputMessage.trim() && !isProcessing) {
      onSend(inputMessage.trim(), attachedFile?.stops);
      setInputMessage('');
      setAttachedFile(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value);
    // Auto-resize
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`;
  };

  return (
    <div className="border-t border-dark-border bg-dark-card">
      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 border-b border-dark-border space-y-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Select
                label="Model"
                options={[
                  { value: 'openai.gpt-4o-mini', label: 'GPT-4o Mini (Recommended)' },
                  { value: 'openai.gpt-4o', label: 'GPT-4o' },
                  { value: 'openai.gpt-5.2-pro', label: 'GPT-5.2 Pro' },
                  { value: 'google.gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
                  { value: 'xai.grok-4', label: 'Grok 4' },
                ]}
                value={config.model}
                onChange={(e) => setModel(e.target.value as ModelId)}
              />
            </div>
            <div className="flex-1">
              <Slider
                label="Temperature"
                min={0}
                max={1}
                step={0.1}
                value={config.temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                valueFormatter={(v) => v.toFixed(1)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Attached File Indicator */}
      {(attachedFile || fileError) && (
        <div className="px-4 pt-3">
          {fileError && (
            <div className="flex items-center gap-2 text-red-400 text-sm bg-red-500/10 px-3 py-2 rounded-lg">
              <X className="w-4 h-4" />
              <span>{fileError}</span>
              <button
                onClick={() => setFileError(null)}
                className="ml-auto text-red-400 hover:text-red-300"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
          {attachedFile && (
            <div className="flex items-center gap-2 text-[#C74634] text-sm bg-[#C74634]/10 px-3 py-2 rounded-lg">
              <FileText className="w-4 h-4" />
              <span>{attachedFile.name}</span>
              <span className="text-gray-400">({attachedFile.stops.length} stops)</span>
              <button
                onClick={handleRemoveFile}
                className="ml-auto text-gray-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}

      {/* Input Area */}
      <div className="p-4">
        <div className="flex items-end gap-3">
          {/* File Upload */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".csv"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="shrink-0 p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            title="Attach CSV file with stops"
          >
            <Paperclip className="w-5 h-5" />
          </button>

          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={inputMessage}
              onChange={handleInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask about route optimization..."
              rows={1}
              className="w-full bg-dark-bg border border-dark-border rounded-xl px-4 py-3 pr-12 text-white placeholder-gray-500 resize-none focus:outline-none focus:ring-2 focus:ring-[#C74634] focus:border-transparent"
              disabled={isProcessing}
            />
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-white rounded transition-colors"
            >
              <Settings className="w-4 h-4" />
            </button>
          </div>

          {/* Voice Input */}
          <button className="shrink-0 p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors">
            <Mic className="w-5 h-5" />
          </button>

          {/* Send Button */}
          <Button
            variant="primary"
            size="md"
            onClick={handleSend}
            disabled={!inputMessage.trim() || isProcessing}
            isLoading={isProcessing}
            className="shrink-0"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>

        {/* Model Info */}
        <div className="mt-2 text-xs text-gray-500 flex items-center gap-4">
          <span>Model: {config.model}</span>
          <span>Temp: {config.temperature}</span>
        </div>
      </div>
    </div>
  );
}
