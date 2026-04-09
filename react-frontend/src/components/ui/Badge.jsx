import { cn } from '../../utils/cn';

export default function Badge({
  children,
  variant = 'default',
  size = 'md',
  className,
  ...props
}) {
  const variants = {
    default: 'bg-slate-200 text-slate-800',
    primary: 'bg-purple-600 text-white',
    success: 'bg-green-600 text-white',
    warning: 'bg-amber-600 text-white',
    error: 'bg-red-600 text-white',
    info: 'bg-blue-600 text-white',
    secondary: 'bg-teal-600 text-white',
  };

  const sizes = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center rounded-full font-semibold',
        'transition-all duration-200',
        variants[variant] || variants.default,
        sizes[size] || sizes.md,
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
