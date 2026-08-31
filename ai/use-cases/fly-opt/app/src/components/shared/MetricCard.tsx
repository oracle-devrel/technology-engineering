import { clsx } from 'clsx';
import { Card } from './Card';
import { Skeleton } from './Skeleton';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  isLoading?: boolean;
  variant?: 'default' | 'highlight';
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  isLoading = false,
  variant = 'default',
}: MetricCardProps) {
  if (isLoading) {
    return (
      <Card variant="bordered" padding="md">
        <div className="space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" height={32} />
        </div>
      </Card>
    );
  }

  return (
    <Card
      variant="bordered"
      padding="md"
      className={clsx(
        'transition-all duration-200 hover:border-dark-hover',
        variant === 'highlight' && 'border-oracle-red/30 bg-oracle-red/5'
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">{title}</p>
          <p
            className={clsx(
              'text-2xl font-bold mt-1 animate-count-up font-mono',
              variant === 'highlight' ? 'text-oracle-red' : 'text-white'
            )}
          >
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend && (
            <div
              className="flex items-center gap-1 mt-2 text-xs"
              style={{ color: '#C74634' }}
            >
              <span>{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}% vs baseline</span>
            </div>
          )}
        </div>
        {Icon && (
          <div
            className={clsx(
              'p-2 rounded-lg',
              variant === 'highlight'
                ? 'bg-oracle-red/20 text-oracle-red'
                : 'bg-dark-hover text-gray-400'
            )}
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </Card>
  );
}
