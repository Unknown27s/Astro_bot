import { cn } from '../../utils/cn';

export default function Spinner({
  size = 'md',
  variant = 'primary',
  className,
  ...props
}) {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-6 w-6',
    lg: 'h-8 w-8',
    xl: 'h-10 w-10',
  };

  const colors = {
    primary: 'text-purple-600',
    secondary: 'text-teal-600',
    success: 'text-green-600',
    error: 'text-red-600',
    white: 'text-white',
  };

  return (
    <div
      className={cn(
        'relative inline-block',
        sizes[size] || sizes.md,
        className
      )}
      {...props}
    >
      <svg
        className={cn(
          'animate-spin',
          colors[variant] || colors.primary,
          sizes[size] || sizes.md
        )}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}
