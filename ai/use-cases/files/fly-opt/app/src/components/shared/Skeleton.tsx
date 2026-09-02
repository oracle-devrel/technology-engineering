import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = 'text', width, height, className, ...props }, ref) => {
    const baseStyles = 'bg-dark-border animate-pulse';

    const variants = {
      text: 'rounded h-4',
      circular: 'rounded-full',
      rectangular: 'rounded-lg',
    };

    const style = {
      width: width,
      height: height,
    };

    return (
      <div
        ref={ref}
        className={clsx(baseStyles, variants[variant], className)}
        style={style}
        {...props}
      />
    );
  }
);

Skeleton.displayName = 'Skeleton';

// Skeleton presets
export function MetricSkeleton() {
  return (
    <div className="space-y-2">
      <Skeleton variant="text" width="60%" />
      <Skeleton variant="text" width="40%" height={32} />
    </div>
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-dark-card rounded-xl p-4 space-y-3">
      <Skeleton variant="text" width="40%" />
      <Skeleton variant="rectangular" height={100} />
      <div className="flex gap-2">
        <Skeleton variant="text" width="30%" />
        <Skeleton variant="text" width="30%" />
      </div>
    </div>
  );
}

export function TableRowSkeleton() {
  return (
    <div className="flex gap-4 py-3 px-4">
      <Skeleton variant="text" width="20%" />
      <Skeleton variant="text" width="25%" />
      <Skeleton variant="text" width="15%" />
      <Skeleton variant="text" width="20%" />
    </div>
  );
}
