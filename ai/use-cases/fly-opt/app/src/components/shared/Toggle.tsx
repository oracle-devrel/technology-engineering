import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface ToggleProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  description?: string;
}

export const Toggle = forwardRef<HTMLInputElement, ToggleProps>(
  ({ label, description, className, checked, ...props }, ref) => {
    return (
      <label className={clsx('flex items-start gap-3 cursor-pointer', className)}>
        <div className="relative mt-0.5">
          <input
            ref={ref}
            type="checkbox"
            checked={checked}
            className="sr-only peer"
            {...props}
          />
          <div
            className={clsx(
              'w-11 h-6 bg-dark-border rounded-full',
              'transition-colors duration-200'
            )}
            style={checked ? { backgroundColor: '#C74634' } : undefined}
          />
          <div
            className={clsx(
              'absolute left-1 top-1 w-4 h-4 bg-white rounded-full',
              'transition-transform duration-200',
              'peer-checked:translate-x-5'
            )}
          />
        </div>
        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <span className="text-sm font-medium text-gray-200">{label}</span>
            )}
            {description && (
              <span className="text-xs text-gray-400 mt-0.5">{description}</span>
            )}
          </div>
        )}
      </label>
    );
  }
);

Toggle.displayName = 'Toggle';
