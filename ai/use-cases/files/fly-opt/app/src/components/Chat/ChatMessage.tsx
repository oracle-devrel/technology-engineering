import { useState, useMemo } from 'react';
import { User, Bot, ChevronDown, ChevronRight, Route, Clock, Truck, Download } from 'lucide-react';
import { clsx } from 'clsx';
import { Card } from '@/components/shared/Card';
import { Badge } from '@/components/shared/Badge';
import { Button } from '@/components/shared/Button';
import { MarkdownContent } from '@/components/shared/MarkdownContent';
import type { Message } from '@/types';
import { formatTimestamp, formatDistance, formatDuration, getVehiclePlate, getVehicleColor, setVehicleCountry } from '@/utils';
import { useConfigStore } from '@/store';

interface ChatMessageProps {
  message: Message;
  isStreaming?: boolean;
}

export function ChatMessage({ message, isStreaming = false }: ChatMessageProps) {
  const [showDetails, setShowDetails] = useState(false);
  const isUser = message.role === 'user';

  // Parse markdown for assistant messages
  const renderedContent = useMemo(() => {
    if (isUser) {
      return <p className="whitespace-pre-wrap">{message.content}</p>;
    }
    return <MarkdownContent content={message.content} />;
  }, [message.content, isUser]);

  return (
    <div
      className={clsx(
        'flex gap-3 animate-fade-in',
        isUser ? 'flex-row-reverse' : ''
      )}
    >
      {/* Avatar */}
      <div
        className={clsx(
          'shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-navy' : 'bg-[#C74634]/20'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-[#C74634]" />
        )}
      </div>

      {/* Message Content */}
      <div className={clsx('flex-1 max-w-[80%]', isUser ? 'text-right' : '')}>
        <div
          className={clsx(
            'inline-block text-left rounded-2xl px-4 py-3',
            isUser
              ? 'bg-navy text-white rounded-tr-none'
              : 'bg-dark-card text-gray-200 rounded-tl-none border border-dark-border'
          )}
        >
          {renderedContent}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-[#C74634] ml-1 animate-pulse" />
          )}
        </div>

        {/* Route Result Card */}
        {message.metadata?.cuoptResponse && (
          <div className="mt-2">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="flex items-center gap-2 text-sm text-sky-400 hover:underline"
            >
              {showDetails ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
              View Route Result
            </button>

            {showDetails && (
              <Card variant="bordered" className="mt-2" padding="sm">
                <CuOptResultCard result={message.metadata.cuoptResponse} />
              </Card>
            )}
          </div>
        )}

        {/* Timestamp */}
        <div
          className={clsx(
            'mt-1 text-xs text-gray-500',
            isUser ? 'text-right' : ''
          )}
        >
          {formatTimestamp(message.timestamp)}
          {message.metadata?.model && (
            <span className="ml-2 text-gray-600">
              via {message.metadata.model}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

function CuOptResultCard({ result }: { result: any }) {
  const { config: appConfig } = useConfigStore();

  // Set vehicle country based on config
  setVehicleCountry(appConfig.countryCode);

  const vehicleData = result.vehicle_data || [];

  // Use solution_cost as distance approximation (in km)
  const totalDistance = result.solution_cost || 0;
  const totalDuration = vehicleData.reduce(
    (sum: number, v: any) => sum + (v.route_duration || 0),
    0
  );

  const handleDownload = (format: 'json' | 'csv') => {
    let data: string;
    let filename: string;
    let mimeType: string;

    if (format === 'json') {
      data = JSON.stringify(result, null, 2);
      filename = 'cuopt-routes-result.json';
      mimeType = 'application/json';
    } else {
      // CSV format with UK plates
      const headers = 'plate,name,stops,route,duration\n';
      const rows = vehicleData.map((v: any) => {
        const vehicle = getVehiclePlate(v.vehicle_id);
        return `${vehicle.plate},${vehicle.name},${(v.route?.length || 2) - 2},"${v.route?.join('->')}",${v.route_duration || 0}`;
      }).join('\n');
      data = headers + rows;
      filename = 'cuopt-routes.csv';
      mimeType = 'text/csv';
    }

    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-3">
      {/* Download Buttons */}
      <div className="flex gap-2 justify-end">
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Download className="w-3 h-3" />}
          onClick={() => handleDownload('json')}
        >
          JSON
        </Button>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Download className="w-3 h-3" />}
          onClick={() => handleDownload('csv')}
        >
          CSV
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-dark-bg rounded-lg p-2 text-center">
          <Route className="w-4 h-4 text-[#C74634] mx-auto mb-1" />
          <div className="text-sm font-medium text-white">
            {formatDistance(totalDistance)}
          </div>
          <div className="text-xs text-gray-500">Distance</div>
        </div>
        <div className="bg-dark-bg rounded-lg p-2 text-center">
          <Clock className="w-4 h-4 text-[#C74634] mx-auto mb-1" />
          <div className="text-sm font-medium text-white">
            {formatDuration(totalDuration)}
          </div>
          <div className="text-xs text-gray-500">Duration</div>
        </div>
        <div className="bg-dark-bg rounded-lg p-2 text-center">
          <Truck className="w-4 h-4 text-[#C74634] mx-auto mb-1" />
          <div className="text-sm font-medium text-white">
            {result.num_vehicles || vehicleData.length}
          </div>
          <div className="text-xs text-gray-500">Vehicles</div>
        </div>
      </div>

      {/* Routes Summary - matching Route Optimizer format */}
      {vehicleData.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs text-gray-400 font-medium">
            Showing {Math.min(vehicleData.length, 10)} of {vehicleData.length} routes
          </div>
          {vehicleData.slice(0, 10).map((v: any, idx: number) => {
            const vehicle = getVehiclePlate(v.vehicle_id);
            const stopsCount = (v.route?.length || 2) - 2;
            const duration = v.route_duration || 0;
            const distance = v.route_distance || 0;

            return (
              <div
                key={idx}
                className="bg-dark-bg rounded-lg p-2 border border-dark-border"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: getVehicleColor(v.vehicle_id).color }}
                    />
                    <span className="text-white font-mono text-sm font-medium">
                      {vehicle.plate}
                    </span>
                    <span className="text-gray-500 text-xs">
                      {vehicle.name}
                    </span>
                  </div>
                  <span className="text-gray-400 text-xs">
                    {stopsCount} stops
                  </span>
                </div>
                <div className="flex justify-end gap-4 mt-1 text-xs text-gray-400">
                  <span>{formatDistance(distance)}</span>
                  <span>{formatDuration(duration)}</span>
                </div>
              </div>
            );
          })}
          {vehicleData.length > 10 && (
            <div className="text-xs text-gray-500 text-center py-1">
              +{vehicleData.length - 10} more vehicles (see Route Optimizer for full list)
            </div>
          )}
        </div>
      )}

      {/* Status Badge */}
      <div className="flex justify-between items-center">
        <Badge variant={result.status === 'SUCCESS' ? 'success' : 'warning'}>
          {result.status || 'Completed'}
        </Badge>
        {result.solve_time && (
          <span className="text-xs text-gray-500">
            Solved in {result.solve_time.toFixed(2)}s
          </span>
        )}
      </div>
    </div>
  );
}
