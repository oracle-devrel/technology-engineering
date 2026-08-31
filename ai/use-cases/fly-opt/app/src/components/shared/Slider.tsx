import { InputHTMLAttributes, forwardRef } from 'react';
import { clsx } from 'clsx';

interface SliderProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  showValue?: boolean;
  valueFormatter?: (value: number) => string;
}

export const Slider = forwardRef<HTMLInputElement, SliderProps>(
  (
    {
      label,
      showValue = true,
      valueFormatter = (v) => String(v),
      className,
      value,
      ...props
    },
    ref
  ) => {
    const numValue = typeof value === 'string' ? parseFloat(value) : (value as number);

    return (
      <div className="w-full">
        {(label || showValue) && (
          <div className="flex justify-between items-center mb-2">
            {label && (
              <label className="text-sm font-medium text-gray-300">{label}</label>
            )}
            {showValue && (
              <span className="text-sm font-mono text-[#C74634]">
                {valueFormatter(numValue || 0)}
              </span>
            )}
          </div>
        )}
        <input
          ref={ref}
          type="range"
          value={value}
          className={clsx(
            'w-full h-2 bg-dark-border rounded-lg appearance-none cursor-pointer',
            'focus:outline-none focus:ring-2 focus:ring-[#C74634] focus:ring-offset-2 focus:ring-offset-dark-bg',
            '[&::-webkit-slider-thumb]:appearance-none',
            '[&::-webkit-slider-thumb]:w-4',
            '[&::-webkit-slider-thumb]:h-4',
            '[&::-webkit-slider-thumb]:bg-[#C74634]',
            '[&::-webkit-slider-thumb]:rounded-full',
            '[&::-webkit-slider-thumb]:cursor-pointer',
            '[&::-webkit-slider-thumb]:shadow-lg',
            '[&::-webkit-slider-thumb]:transition-transform',
            '[&::-webkit-slider-thumb]:hover:scale-110',
            className
          )}
          {...props}
        />
      </div>
    );
  }
);

Slider.displayName = 'Slider';
