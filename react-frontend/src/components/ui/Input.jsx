import { forwardRef } from 'react';
import { cn } from '../../utils/cn';

const Input = forwardRef(function Input(
  {
    type = 'text',
    placeholder = '',
    value,
    onChange,
    disabled = false,
    error = false,
    icon: Icon,
    label,
    required = false,
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
          {required && <span className="ml-1 text-red-600">*</span>}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <Icon className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 transform text-slate-500" />
        )}
        <input
          ref={ref}
          type={type}
          placeholder={placeholder}
          onChange={onChange}
          disabled={disabled}
          className={cn(
            'w-full rounded-lg border-2 border-slate-200 px-4 py-2.5',
            'bg-white text-slate-800 placeholder-slate-500',
            'font-sans text-base',
            'focus:border-purple-600 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:ring-offset-0',
            'disabled:cursor-not-allowed disabled:bg-slate-100 disabled:opacity-50',
            'transition-all duration-200',
            Icon && 'pl-10',
            error && 'border-red-600 focus:border-red-600 focus:ring-red-600',
            className
          )}
          {...valueProps}
          {...props}
        />
      </div>
      {error && typeof error === 'string' && (
        <p className="mt-1 text-sm text-red-600">{error}</p>
      )}
    </div>
  );
});

export default Input;
