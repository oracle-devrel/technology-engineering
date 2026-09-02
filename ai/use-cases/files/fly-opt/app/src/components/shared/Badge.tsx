import { HTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'nvidia' | 'oci';

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  pulse?: boolean;
}

const variants: Record<BadgeVariant, string> = {
  default: 'bg-gray-600 text-gray-100',
  success: 'bg-green-600/20 text-green-400 border border-green-600/30',
  warning: 'bg-yellow-600/20 text-yellow-400 border border-yellow-600/30',
  error: 'bg-red-600/20 text-red-400 border border-red-600/30',
  info: 'bg-blue-600/20 text-blue-400 border border-blue-600/30',
  nvidia: 'bg-nvidia-green/20 text-nvidia-green border border-nvidia-green/30',
  oci: 'bg-oracle-red/20 text-oracle-red border border-oracle-red/30',
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = 'default', pulse = false, className, children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={clsx(
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
          variants[variant],
          className
        )}
        {...props}
      >
        {pulse && (
          <span className="relative flex h-2 w-2">
            <span
              className={clsx(
                'animate-ping absolute inline-flex h-full w-full rounded-full opacity-75',
                variant === 'success' && 'bg-green-400',
                variant === 'warning' && 'bg-yellow-400',
                variant === 'error' && 'bg-red-400',
                variant === 'info' && 'bg-blue-400',
                variant === 'nvidia' && 'bg-nvidia-green',
                variant === 'oci' && 'bg-oracle-red',
                variant === 'default' && 'bg-gray-400'
              )}
            />
            <span
              className={clsx(
                'relative inline-flex rounded-full h-2 w-2',
                variant === 'success' && 'bg-green-500',
                variant === 'warning' && 'bg-yellow-500',
                variant === 'error' && 'bg-red-500',
                variant === 'info' && 'bg-blue-500',
                variant === 'nvidia' && 'bg-nvidia-green',
                variant === 'oci' && 'bg-oracle-red',
                variant === 'default' && 'bg-gray-500'
              )}
            />
          </span>
        )}
        {children}
      </span>
    );
  }
);

Badge.displayName = 'Badge';
