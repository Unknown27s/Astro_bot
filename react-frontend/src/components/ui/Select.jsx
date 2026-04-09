import { forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { ChevronDown } from 'lucide-react';

const Select = forwardRef(function Select(
  {
    value,
    onChange,
    options = [],
    placeholder = 'Select an option',
    label,
    disabled = false,
    error = false,
    className,
    ...props
  },
  ref
) {
  const valueProps = value !== undefined ? { value } : {};

  return (
    <div className="w-full">
      {label && (
        <label className="mb-2 block text-sm font-medium text-slate-800">
          {label}
        </label>
      )}
      <div className="relative">
        <select
          ref={ref}
          onChange={onChange}
          disabled={disabled}
          className={cn(
            'w-full rounded-lg border-2 border-slate-200 px-4 py-2.5 pr-10',
            'bg-white text-slate-800',
            'cursor-pointer appearance-none font-sans text-base',
            'focus:border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:ring-offset-0',
            'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:opacity-50',
            'transition-all duration-200',
            error && 'border-red-600 focus:border-red-600 focus:ring-red-600',
            className
          )}
          {...valueProps}
          {...props}
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-5 w-5 -translate-y-1/2 transform text-slate-500" />
      </div>
      {error && typeof error === 'string' && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

export default Select;
